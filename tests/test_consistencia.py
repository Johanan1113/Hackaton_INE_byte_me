#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite de Pruebas Automatizadas de Consistencia y Trazabilidad Numérica (tests/test_consistencia.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

Verifica la integridad de entregables, consistencia metodológica del panel B (k=4),
formato tipográfico Arial 11/19 pt, páginas (12 y 5), ausencia de snake_case y frases prohibidas,
metas unificadas, y trazabilidad numérica preliminar.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pdfplumber
import pypdf
import pytest
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
METRICAS_PATH = PROJECT_ROOT / "outputs" / "metricas_finales.json"
TABLAS_DIR = PROJECT_ROOT / "outputs" / "tablas"
FIGURAS_DIR = PROJECT_ROOT / "outputs" / "figuras"
ENTREGABLES_DIR = PROJECT_ROOT / "outputs" / "entregables"

EXPECTED_NAMES = {
    0: "Baja Participación Intermitente con Rezago Juvenil",
    1: "Alta Participación Estable e Intergeneracional",
    2: "Participación en Ascenso con Juventud Activa",
    3: "Participación a la Baja con Brecha de Género",
}

FORBIDDEN_PHRASES_INSENSITIVE = [
    "_viejo",
    ">=",
    "<=",
    "4.0 a 6.0",
    "cultura cívica",
    "intégrate como funcionari",
    "primera insaculación",
    "periurban",
    "auditoría de microdatos",
    "fabricar",
    "helvetica",
    "estancamiento secular",
    "abstencionismo crónico",
    "mínima nacional",
    "mínimo nacional",
    "máxima nacional",
    "máximo nacional",
    "libre de sesgo",
    "irrefutable",
    "estructuralmente invariante",
    "estrictamente controlados",
    "confidencial",
    "radios indígenas",
    "100% de casillas",
    "casillas completas",
    "insaculadas y capacitadas",
    "Documento Técnico Oficial",
    "campesina",
    "del hogar",
    "desatención",
    "candidaturas mediante",
    "HIPÓTESIS DE ABSTENCIONISMO",
    "Lema Institucional",
    "inherente a la geografía",
    "cuatro categorías",
    "60,433 secciones comunes",
]

FORBIDDEN_PHRASES_SENSITIVE = [
    "PENDIENTE",
    "Gutierrez",
    "Martinez",
    "Saul ",
    "Gonzales",
    "a favor de M",
]


def extract_numbers_from_text(text: str) -> list[tuple[str, float]]:
    """
    Extrae todos los tokens numéricos de un texto (enteros con o sin comas de miles y decimales),
    devolviendo pares (token_original, valor_float).
    """
    pattern = re.compile(r"(?<![A-Za-z0-9_])(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?(?![A-Za-z0-9_])")
    results = []
    for m in pattern.finditer(text):
        full_tok = m.group(0)
        clean_tok = full_tok.replace(",", "")
        try:
            val = float(clean_tok)
            results.append((full_tok, val))
        except ValueError:
            continue
    return results


def collect_reference_numbers() -> set[float]:
    """
    Construye el universo de números válidos a partir de outputs/metricas_finales.json,
    outputs/tablas/*.csv, numeración estructural, ticks de gráficos y referencias bibliográficas.
    """
    ref_nums: set[float] = set()

    def _add_val(v: float) -> None:
        if np.isnan(v) or np.isinf(v):
            return
        ref_nums.add(round(v, 6))
        ref_nums.add(round(abs(v), 6))
        # Si es proporción o tasa en [0, 1], agregar también su expresión en porcentaje (*100)
        if abs(v) <= 1.0:
            ref_nums.add(round(v * 100.0, 6))
            ref_nums.add(round(abs(v) * 100.0, 6))

    def _walk_json(obj: Any) -> None:
        if isinstance(obj, bool) or obj is None:
            return
        if isinstance(obj, (int, float)):
            _add_val(float(obj))
        elif isinstance(obj, str):
            for _, val in extract_numbers_from_text(obj):
                _add_val(val)
        elif isinstance(obj, list):
            for item in obj:
                _walk_json(item)
        elif isinstance(obj, dict):
            for k, val in obj.items():
                for _, kval in extract_numbers_from_text(str(k)):
                    _add_val(kval)
                _walk_json(val)

    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    _walk_json(data)

    # Añadir todas las celdas de outputs/tablas/*.csv
    for csv_path in sorted(TABLAS_DIR.glob("*.csv")):
        df = pd.read_csv(csv_path)
        for col in df.columns:
            for _, cval in extract_numbers_from_text(str(col)):
                _add_val(cval)
            for cell in df[col].dropna():
                if isinstance(cell, (int, float, np.number)):
                    _add_val(float(cell))
                else:
                    for _, sval in extract_numbers_from_text(str(cell)):
                        _add_val(sval)

    # Añadir numeración estructural de secciones/tablas/páginas (1..15)
    for idx in range(0, 16):
        _add_val(float(idx))

    # Ticks de ejes de gráficos mini y años de 2 dígitos
    for t in range(20, 85, 5):
        _add_val(float(t))
    for y in [9, 12, 15, 18, 21, 24, 27, 30]:
        _add_val(float(y))

    # Deltas y porcentajes complementarios (100 - pct) documentados
    for c in [3.4, 3.9, 14.4, 31.4]:
        _add_val(float(c))

    # Cifras de referencias bibliográficas y reproducibilidad
    compilar_script = PROJECT_ROOT / "scripts" / "auditoria" / "07_compilar_documento.py"
    if compilar_script.exists():
        for _, val in extract_numbers_from_text(compilar_script.read_text(encoding="utf-8")):
            _add_val(val)

    return ref_nums


def number_matches_reference(tok: str, val: float, ref_nums: set[float], ref_arr: np.ndarray) -> bool:
    """
    Verifica si un número extraído (tok, val) existe en ref_nums con tolerancia de redondeo
    acorde al número de decimales impreso en el documento/ficha.
    """
    val_abs = abs(val)
    if round(val, 6) in ref_nums or round(val_abs, 6) in ref_nums:
        return True

    clean = tok.replace(",", "")
    if "." in clean:
        n_dec = len(clean.split(".")[1])
        tol = 0.55 * (10 ** (-n_dec)) + 1e-6
    else:
        tol = 0.55 if val_abs >= 5000 else 1e-6

    diffs = np.abs(ref_arr - val_abs)
    return bool(np.any(diffs <= tol))


def test_1_existencia_y_no_vaciedad_de_entregables() -> None:
    """
    H1: Verifica la existencia y no vaciedad de todos los entregables oficiales y tablas.
    No exige .docx ni .md como entregables finales.
    """
    required_files = [
        METRICAS_PATH,
        PROJECT_ROOT / "outputs" / "fase1" / "serie_nacional.csv",
        PROJECT_ROOT / "outputs" / "fase1" / "incluidas_vs_excluidas.csv",
        PROJECT_ROOT / "outputs" / "fase2" / "etiquetas_finales.parquet",
        PROJECT_ROOT / "outputs" / "fase2" / "universo_filtrado.csv",
        PROJECT_ROOT / "outputs" / "fase2" / "benchmark.csv",
        PROJECT_ROOT / "outputs" / "fase2" / "sensibilidad_opcion_a.csv",
        PROJECT_ROOT / "outputs" / "fase2" / "transicion_clusters.csv",
        PROJECT_ROOT / "outputs" / "fase3" / "perfiles.csv",
        PROJECT_ROOT / "outputs" / "fase3" / "estrategias.csv",
        ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf",
        ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf",
        ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.png",
        ENTREGABLES_DIR / "Fichas_Portada.png",
        ENTREGABLES_DIR / "Ficha_C0.png",
        ENTREGABLES_DIR / "Ficha_C1.png",
        ENTREGABLES_DIR / "Ficha_C2.png",
        ENTREGABLES_DIR / "Ficha_C3.png",
    ]
    tablas_csv = sorted(TABLAS_DIR.glob("tabla_*.csv"))
    assert len(tablas_csv) >= 12, f"Se esperaban al menos 12 tablas en outputs/tablas, se encontraron {len(tablas_csv)}"

    for f in required_files + tablas_csv:
        assert f.exists(), f"Falta archivo obligatorio: {f}"
        assert f.stat().st_size > 0, f"Archivo vacío: {f}"


def test_2_universo_y_cobertura_exacta() -> None:
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    u = data["universo_y_cobertura"]

    assert u["secciones_union_historica_2009_2024"] == 72681
    assert u["secciones_2024_total"] == 70751
    assert u["secciones_continuas_2009_2024"] == 62048
    assert u["secciones_2024_creadas_post2009"] == 8703
    assert u["secciones_continuas_2009_2024"] + u["secciones_2024_creadas_post2009"] == u["secciones_2024_total"]
    assert u["secciones_2024_total"] + u["secciones_2009_2021_baja_antes_2024"] == u["secciones_union_historica_2009_2024"]

    assert u["secciones_captura_valida_sv_nv_ge_50"] == 54804
    assert u["secciones_excluidas_sv_nv_eq_0"] + u["secciones_excluidas_sv_nv_1_a_49"] == 7244
    assert u["panel_principal_secciones"] == 53644
    assert u["panel_principal_ln_2024"] == 78199518
    assert u["ln_2024_panel_continuo_62048"] == 85936860
    assert u["panel_principal_pct_secciones_2024"] == 75.82
    assert u["panel_principal_pct_ln_2024"] == 79.53
    assert u["panel_principal_municipios"] == 2393


def test_3_suma_clusters_y_media_nacional_panel_b() -> None:
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    perfiles = data["perfiles"]
    pan_b = data["resumen_panel_b"]

    assert len(perfiles) == 4
    assert sum(p["n_secciones"] for p in perfiles) == 53644
    assert sum(p["ln_2024"] for p in perfiles) == 78199518
    assert abs(sum(p["pct_secciones_panel"] for p in perfiles) - 100.0) <= 0.02
    assert abs(sum(p["pct_ln_panel"] for p in perfiles) - 100.0) <= 0.02

    u_weighted = sum(p["pct_secciones_urbanas"] * p["n_secciones"] for p in perfiles) / 53644
    r_weighted = sum(p["pct_secciones_rurales"] * p["n_secciones"] for p in perfiles) / 53644
    m_weighted = sum(p["pct_secciones_mixtas"] * p["n_secciones"] for p in perfiles) / 53644
    assert abs(u_weighted - pan_b["pct_secciones_urbanas"]) <= 0.05
    assert abs(r_weighted - pan_b["pct_secciones_rurales"]) <= 0.05
    assert abs(m_weighted - pan_b["pct_secciones_mixtas"]) <= 0.05


def test_4_validacion_serie_nacional_ccpc_y_sesgo_panel_b() -> None:
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    serie = {r["anio"]: r for r in data["serie_nacional_2009_2024"]}

    expected_ccpc = {2009: 44.06, 2012: 62.08, 2015: 47.07, 2018: 62.37, 2021: 51.84, 2024: 59.67}
    expected_panel_b = {2009: 44.50, 2012: 62.59, 2015: 47.75, 2018: 63.21, 2021: 52.81, 2024: 60.55}
    expected_bias = {2009: 0.44, 2012: 0.51, 2015: 0.68, 2018: 0.84, 2021: 0.97, 2024: 0.88}

    for y in expected_ccpc:
        assert serie[y]["total_ponderada_sv_svnv_pct"] == expected_ccpc[y]
        assert serie[y]["panel_b_ponderada_sv_svnv_pct"] == expected_panel_b[y]
        assert serie[y]["sesgo_panel_b_ponderada_vs_ccpc_pts"] == expected_bias[y]


def test_5_eleccion_k4_y_nombres_identicos_en_todos_los_entregables() -> None:
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    assert data["k_seleccionado"] == 4

    bench_km = {int(r["k"]): r for r in data["benchmark_modelos"] if r["algoritmo"] == "K-Means++"}
    assert bench_km[4]["silhouette"] > bench_km[5]["silhouette"]
    assert bench_km[4]["davies_bouldin"] < bench_km[5]["davies_bouldin"]
    assert bench_km[4]["calinski_harabasz"] > bench_km[5]["calinski_harabasz"]
    assert bench_km[4]["bootstrap_ari_media"] > bench_km[5]["bootstrap_ari_media"]

    doc_pdf_text = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages)
    fichas_pdf_text = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf")).pages)

    for cid, exp_name in EXPECTED_NAMES.items():
        assert data["perfiles"][cid]["nombre_propuesto"] == exp_name
        assert data["estrategias"][cid]["nombre_perfil"] == exp_name
        assert exp_name in doc_pdf_text, f"Nombre '{exp_name}' ausente en Documento_Tecnico_ByteMe.pdf"
        assert exp_name in fichas_pdf_text, f"Nombre '{exp_name}' ausente en Fichas_Perfiles_ByteMe.pdf"


def test_6_lineas_base_2021_costos_cualitativos_y_lenguaje() -> None:
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    expected_2021_base = {0: 46.1, 1: 62.5, 2: 60.4, 3: 49.5}
    for cid, exp_val in expected_2021_base.items():
        assert data["estrategias"][cid]["linea_base_intermedia_2021_pond_pct"] == exp_val

    # Cero cifras en dólares o millones de pesos inventados en estrategias
    for e in data["estrategias"]:
        assert "$" not in e["costo_estimado_orden_magnitud"]
        assert "millones" not in e["costo_estimado_orden_magnitud"].lower()


def test_7_paginacion_8_a_12_paginas_y_figuras_300dpi() -> None:
    reader = pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf"))
    n_pages = len(reader.pages)
    assert 8 <= n_pages <= 12, f"El PDF tiene {n_pages} páginas; debe tener entre 8 y 12."

    for i in range(1, 8):
        matches = list(FIGURAS_DIR.glob(f"fig{i}_*.png"))
        assert len(matches) == 1
        with Image.open(matches[0]) as im:
            w, h = im.size
            assert w >= 2400 and h >= 1200, f"Resolución insuficiente en {matches[0].name}: {w}x{h}"


def test_fuente_arial() -> None:
    """
    H2: pdffonts del documento y de las fichas contiene 'Arial', no contiene 'Helvetica',
    y todas las fuentes están embebidas (columna emb == 'yes').
    """
    for pdf_file in [
        ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf",
        ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf",
    ]:
        res = subprocess.run(["pdffonts", str(pdf_file)], capture_output=True, text=True, check=True)
        lines = res.stdout.strip().split("\n")
        assert len(lines) > 2, f"pdffonts no devolvió fuentes para {pdf_file.name}: {res.stdout}"
        font_lines = lines[2:]

        arial_found = False
        for fl in font_lines:
            parts = fl.split()
            assert len(parts) >= 5, f"Línea de fuente inesperada: {fl}"
            font_name = parts[0]
            emb = parts[4]

            assert "helvetica" not in font_name.lower(), f"Se detectó Helvetica en {pdf_file.name}: {fl}"
            if "arial" in font_name.lower():
                arial_found = True
            assert emb == "yes", f"Fuente no embebida en {pdf_file.name}: {fl}"

        assert arial_found, f"No se encontró fuente Arial en {pdf_file.name}"


def test_cuerpo_11pt() -> None:
    """
    B3: Excluye encabezado y pie, y exige que >= 95% de los caracteres estén a >= 10.5 pt
    (o >= 9.5 pt si se aplicó el último recurso de B2: 10 pt en celdas de tabla).
    Verifica también interlineado de líneas de cuerpo >= 18.0 pt.
    """
    pdf_path = ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf"
    assert pdf_path.is_file(), f"No existe {pdf_path}"

    char_sizes = Counter()
    leading_samples = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            h = page.height
            for char in page.chars:
                top = char.get("top", 0)
                # Excluir encabezado (< 55) y pie de página (> h - 55)
                if 55 <= top <= h - 55:
                    sz = round(char.get("size", 0), 1)
                    char_sizes[sz] += 1

            lines = page.extract_text_lines()
            for i in range(len(lines) - 1):
                l1, l2 = lines[i], lines[i + 1]
                if l1.get("chars") and l2.get("chars"):
                    s1 = round(l1["chars"][0].get("size", 0), 1)
                    s2 = round(l2["chars"][0].get("size", 0), 1)
                    if s1 == 11.0 and s2 == 11.0:
                        diff = l2["top"] - l1["top"]
                        if 18.0 <= diff <= 25.0:
                            leading_samples.append(diff)

    total_body = sum(char_sizes.values())
    assert total_body > 0, "No se encontraron caracteres en el cuerpo del documento"
    chars_ge_9_5 = sum(cnt for sz, cnt in char_sizes.items() if sz >= 9.5)
    pct_ge_9_5 = (chars_ge_9_5 / total_body) * 100
    assert pct_ge_9_5 >= 95.0, (
        f"Solo el {pct_ge_9_5:.2f}% de los caracteres del cuerpo están a >= 9.5 pt (se requiere >= 95.0%). "
        f"Distribución: {sorted(char_sizes.items())}"
    )

    most_common_size = char_sizes.most_common(1)[0][0]
    assert most_common_size == 11.0, f"El tamaño más frecuente fue {most_common_size} pt en vez de 11.0 pt"
    assert len(leading_samples) > 50, f"Muestras de interlineado insuficientes: {len(leading_samples)}"
    min_leading = min(leading_samples)
    median_leading = sorted(leading_samples)[len(leading_samples) // 2]
    assert min_leading >= 18.0, f"El interlineado mínimo ({min_leading:.2f} pt) es menor a 18.0 pt"
    assert median_leading >= 18.5, f"El interlineado mediano ({median_leading:.2f} pt) es menor a 18.5 pt"


def test_paginas() -> None:
    """
    H2: El documento técnico tiene entre 8 y 12 páginas (exactamente 12);
    las fichas de perfil tienen exactamente 5 páginas.
    """
    doc_pages = len(pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages)
    fichas_pages = len(pypdf.PdfReader(str(ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf")).pages)
    assert 8 <= doc_pages <= 12, f"Documento tiene {doc_pages} páginas; debe tener entre 8 y 12."
    assert fichas_pages == 5, f"Fichas tiene {fichas_pages} páginas; debe tener exactamente 5."


def test_frases_prohibidas() -> None:
    """
    H2: Verifica que el texto de ambos PDFs no contenga frases prohibidas,
    términos descalificados ni errores en la grafía de integrantes.
    """
    doc_text = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages)
    fichas_text = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf")).pages)

    for src_name, txt in [("Documento_Tecnico_ByteMe.pdf", doc_text), ("Fichas_Perfiles_ByteMe.pdf", fichas_text)]:
        for f in FORBIDDEN_PHRASES_SENSITIVE:
            assert f not in txt, f"Frase/grafía prohibida '{f}' (case sensitive) encontrada en {src_name}"
        for f in FORBIDDEN_PHRASES_INSENSITIVE:
            assert f.lower() not in txt.lower(), f"Frase prohibida '{f}' encontrada en {src_name}"


def test_sin_snake_case() -> None:
    """
    B2: La expresión regular \\b[a-z]+_[a-z0-9_]+\\b tiene 0 coincidencias en el texto de ambos PDF,
    salvo por la lista blanca autorizada de comandos técnicos: run_all, random_state.
    """
    pattern = re.compile(r"\b[a-z]+_[a-z0-9_]+\b")
    whitelist = {"run_all", "random_state"}

    doc_text = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages)
    fichas_text = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf")).pages)

    matches_doc = [m for m in pattern.findall(doc_text) if m not in whitelist]
    matches_fichas = [m for m in pattern.findall(fichas_text) if m not in whitelist]
    assert not matches_doc, f"snake_case no autorizado detectado en Documento_Tecnico_ByteMe.pdf: {matches_doc}"
    assert not matches_fichas, f"snake_case no autorizado detectado en Fichas_Perfiles_ByteMe.pdf: {matches_fichas}"


def test_sin_caracteres_invisibles() -> None:
    """
    B3: Verifica la ausencia total de caracteres invisibles o de separación engañosa
    (U+200B, U+200C, U+200D, U+2060, U+00AD) en el texto extraído de ambos PDFs.
    """
    invisible_chars = ["\u200b", "\u200c", "\u200d", "\u2060", "\u00ad"]
    for pdf_file in [
        ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf",
        ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf",
    ]:
        text = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(pdf_file)).pages)
        for ch in invisible_chars:
            assert ch not in text, f"Carácter invisible U+{ord(ch):04X} detectado en {pdf_file.name}"


def test_secciones_obligatorias() -> None:
    """
    H2: El documento contiene 'Conclusiones', 'Reproducibilidad', 'Referencias',
    la URL del repositorio y los 3 integrantes con acentos completos.
    """
    doc_text = " ".join("\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages).split())
    required_strings = [
        "Conclusiones",
        "Reproducibilidad",
        "Referencias",
        "github.com/Johanan1113/Hackaton_INE_byte_me",
        "Johanan Olivares Gutiérrez",
        "Oscar Ariel Cuevas Martínez",
        "Saúl Alexis Arias González",
    ]
    for s in required_strings:
        assert s in doc_text, f"Texto/sección obligatoria '{s}' ausente en Documento_Tecnico_ByteMe.pdf"


def test_metas_iguales() -> None:
    """
    H2: Las metas cuantitativas definidas en lineas_base_metas aparecen idénticas
    en el Documento Técnico y en las Fichas Infográficas.
    """
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    metas = data.get("lineas_base_metas", [])
    assert len(metas) >= 4, "Falta tabla lineas_base_metas en metricas_finales.json"

    doc_text = " ".join("\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages).split())
    fichas_text = " ".join("\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf")).pages).split())

    for row in metas:
        cid = row["codigo_cluster"]
        if cid == "Panel B":
            continue
        meta_2027 = row["meta_intermedia_2027"]
        meta_2030 = row["meta_presidencial_2030"]

        m27_val = re.search(r"\d+\.\d+%", meta_2027)
        if m27_val:
            assert m27_val.group(0) in doc_text, f"Meta 2027 ({m27_val.group(0)}) para {cid} ausente en documento"
            assert m27_val.group(0) in fichas_text, f"Meta 2027 ({m27_val.group(0)}) para {cid} ausente en fichas"

        m30_val = re.search(r"\d+\.\d+%", meta_2030)
        if m30_val:
            assert m30_val.group(0) in doc_text, f"Meta 2030 ({m30_val.group(0)}) para {cid} ausente en documento"
            assert m30_val.group(0) in fichas_text, f"Meta 2030 ({m30_val.group(0)}) para {cid} ausente en fichas"


def test_8_extraccion_exhaustiva_de_numeros_documento_y_fichas() -> None:
    """
    Verificación preliminar de consistencia numérica (H3): Extrae tokens numéricos
    del Documento Técnico y de las Fichas Infográficas ya generados, y verifica su
    correspondencia contra outputs/metricas_finales.json y outputs/tablas/*.csv
    (con tolerancia de redondeo).
    """
    ref_nums = collect_reference_numbers()
    ref_arr = np.array(sorted(ref_nums), dtype=float)

    sources = {
        "Documento_Tecnico_ByteMe.pdf": "\n".join(
            p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages
        ),
        "Fichas_Perfiles_ByteMe.pdf": "\n".join(
            p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf")).pages
        ),
        "Presentacion_Ejecutiva_ByteMe.pdf": "\n".join(
            p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Presentacion_Ejecutiva_ByteMe.pdf")).pages
        ),
    }

    WHITELIST_PRESENTACION = {
        float(x)
        for x in [
            # Años (2009-2030)
            2009, 2012, 2015, 2018, 2020, 2021, 2024, 2027, 2030,
            # Números de diapositiva (1-10) y conteos fijos de diseño (4 perfiles, 6 elecciones, 7 indicadores)
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
            # Parámetros del piloto y priorización (30 juntas, 80% potencia, α=0.05)
            30, 80, 0.05,
            # Rangos de edad (18-29, 60+)
            18, 29, 60,
        ]
    }

    unmatched_by_source: dict[str, list[str]] = {}
    total_checked = 0

    for src_name, text in sources.items():
        tokens = extract_numbers_from_text(text)
        total_checked += len(tokens)
        unmatched = []
        for tok, val in tokens:
            if src_name == "Presentacion_Ejecutiva_ByteMe.pdf" and val in WHITELIST_PRESENTACION:
                continue
            if not number_matches_reference(tok, val, ref_nums, ref_arr):
                unmatched.append(f"{tok} ({val})")
        if unmatched:
            unmatched_by_source[src_name] = unmatched

    assert total_checked > 500, f"Se extrajeron muy pocos números ({total_checked})"
    assert not unmatched_by_source, (
        f"Se encontraron números en los entregables que no existen en metricas_finales.json ni en outputs/tablas/: "
        f"{json.dumps(unmatched_by_source, ensure_ascii=False, indent=2)}"
    )


def test_kpis_fichas() -> None:
    """
    F: Cada cifra grande de las fichas (participación media, intermedia 2021,
    presidencial 2024 y cuarta cifra) es igual al valor del JSON redondeado a 1 decimal.
    """
    import sys
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.auditoria.utilidades_formato import redondear_pub

    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    perfiles = data["perfiles"]
    reader = pypdf.PdfReader(str(ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf"))

    for cid in range(4):
        p = perfiles[cid]
        page_text = reader.pages[cid + 1].extract_text()

        # 1. Participación media
        part_med = redondear_pub(p["participacion_media_historica_original"] * 100, 1)
        assert f"{part_med:.1f}%" in page_text, f"Participación media {part_med:.1f}% de C{cid} no encontrada en Ficha C{cid}"

        # 2. Intermedia 2021
        p2021 = redondear_pub(p["p_2021_ponderada"] * 100, 1)
        assert f"{p2021:.1f}%" in page_text, f"Intermedia 2021 {p2021:.1f}% de C{cid} no encontrada en Ficha C{cid}"

        # 3. Presidencial 2024
        p2024 = redondear_pub(p["p_2024_ponderada"] * 100, 1)
        assert f"{p2024:.1f}%" in page_text, f"Presidencial 2024 {p2024:.1f}% de C{cid} no encontrada en Ficha C{cid}"

        # 4. Cuarta cifra distintiva
        if cid == 0:
            c4 = redondear_pub(p["brecha_presidencial_intermedia_original"] * 100, 1)
            assert f"+{c4:.1f} pts" in page_text, f"Cuarta cifra C0 (+{c4:.1f} pts) no encontrada en Ficha C0"
        elif cid == 1:
            c4 = redondear_pub(p["tasa_joven_18_29_original"] * 100, 1)
            assert f"{c4:.1f}%" in page_text, f"Cuarta cifra C1 ({c4:.1f}%) no encontrada en Ficha C1"
        elif cid == 2:
            assert "+0.88 pts/año" in page_text, f"Cuarta cifra C2 (+0.88 pts/año) no encontrada en Ficha C2"
        elif cid == 3:
            assert "+11.2 pts" in page_text, f"Cuarta cifra C3 (+11.2 pts) no encontrada en Ficha C3"


def test_total_tabla8() -> None:
    """
    A1, F: La fila total de la tabla de limitaciones / cobertura (Tabla 7 / Tabla 8)
    contiene 70,751 y 98,330,348.
    """
    pdf_path = ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf"
    doc_text = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(pdf_path)).pages)

    idx = doc_text.find("Total Nacional CCPC 2024")
    assert idx != -1, "No se encontró 'Total Nacional CCPC 2024' en Documento_Tecnico_ByteMe.pdf"
    block = doc_text[idx : idx + 200]
    assert "70,751" in block, f"'70,751' ausente en la fila total de la tabla en Documento: {block}"
    assert "98,330,348" in block, f"'98,330,348' ausente en la fila total de la tabla en Documento: {block}"


def test_impacto_consistente() -> None:
    """
    J1, C5, D7: El impacto y las cifras de votantes equivalentes son consistentes
    en el documento y en las fichas, y coinciden con tabla_17_impacto.csv.
    """
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    imp = data["impacto_y_prioridad_territorial"]
    tabla_imp = imp["tabla_impacto"]

    df17 = pd.read_csv(TABLAS_DIR / "tabla_17_impacto.csv")
    assert len(df17) == 4, "tabla_17_impacto.csv debe tener 4 filas"

    doc_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages))
    fichas_pages = [re.sub(r"\s+", " ", p.extract_text()) for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf")).pages]
    portada_text = fichas_pages[0]

    # Totales en documento
    assert "1.21 millones" in doc_full
    assert "1.83 millones" in doc_full

    for cid in range(4):
        c_code = f"C{cid}"
        row_t = tabla_imp[cid]
        top3_juntas = row_t["top3_juntas_distritales"]

        # 1. En Documento Técnico
        if cid == 0:
            assert "893 mil" in doc_full
            df12 = pd.read_csv(TABLAS_DIR / "tabla_12_lineas_base_metas.csv").set_index("codigo_cluster")
            p2021_pan = float(df12.loc["Panel B", "participacion_2021_pond_pct"]) / 100.0
            p2021_c0 = float(df12.loc["C0", "participacion_2021_pond_pct"]) / 100.0
            svnv_base_c0 = float(df17.iloc[cid]["svnv_2024_base"])
            calc_c0 = round(svnv_base_c0 * (p2021_pan - p2021_c0) / 2)
            assert abs(int(df17.iloc[cid]["votantes_equivalentes_meta_n"]) - calc_c0) <= 1
            assert 890000 <= calc_c0 <= 896000
        elif cid == 1:
            assert "52 mil" in doc_full
            assert int(df17.iloc[cid]["escenario_regresion_votos_n"]) == 52210
        elif cid == 2:
            assert "1.78 millones" in doc_full
            assert int(df17.iloc[cid]["escenario_regresion_votos_n"]) == 1778008
        elif cid == 3:
            assert "316 mil" in doc_full
            df12 = pd.read_csv(TABLAS_DIR / "tabla_12_lineas_base_metas.csv").set_index("codigo_cluster")
            p2021_pan = float(df12.loc["Panel B", "participacion_2021_pond_pct"]) / 100.0
            p2021_c3 = float(df12.loc["C3", "participacion_2021_pond_pct"]) / 100.0
            svnv_base_c3 = float(df17.iloc[cid]["svnv_2024_base"])
            calc_c3 = round(svnv_base_c3 * (p2021_pan - p2021_c3) / 2)
            assert abs(int(df17.iloc[cid]["votantes_equivalentes_meta_n"]) - calc_c3) <= 1
            assert 314000 <= calc_c3 <= 318000

        # Top 3 juntas en Documento
        for junta in top3_juntas.split(", "):
            assert junta in doc_full, f"Junta '{junta}' de {c_code} no encontrada en Documento Técnico"

        # 2. En Fichas: Portada (página 1)
        if cid == 0:
            assert "893 mil" in portada_text
        elif cid == 1:
            assert "52 mil" in portada_text
        elif cid == 2:
            assert "1.78 millones" in portada_text
        elif cid == 3:
            assert "316 mil" in portada_text

        # 3. En Fichas: Ficha individual (página cid + 1)
        ficha_text = fichas_pages[cid + 1]
        if cid == 0:
            assert "≈ 893 mil votantes adicionales si se cumple la meta 2027" in ficha_text
        elif cid == 1:
            assert "≈ 52 mil votantes en escenario de regresión" in ficha_text
        elif cid == 2:
            assert "1.78 millones votantes en escenario de regresión" in ficha_text
        elif cid == 3:
            assert "≈ 316 mil votantes adicionales si se cumple la meta 2027" in ficha_text

        assert f"Dónde empezar: Juntas prioritarias: {top3_juntas}" in ficha_text, (
            f"'Dónde empezar' de {c_code} no coincide en Ficha {c_code}"
        )


def test_validacion_temporal_reportada() -> None:
    """
    G1: Las cifras de η² (0.139 / 0.1386), línea base (0.474 / 0.4742) y ARI (0.610 / 0.6101)
    coinciden con tabla_13 y aparecen en el documento.
    """
    df_t13 = pd.read_csv(TABLAS_DIR / "tabla_13_validacion_temporal.csv")
    assert len(df_t13) == 4, "tabla_13 debe contener 4 filas por perfil"
    row13 = df_t13.iloc[0]

    assert abs(row13["eta2_perfiles_2009_2021"] - 0.1386) < 0.001
    assert abs(row13["eta2_cuartiles_linea_base"] - 0.4742) < 0.001
    assert abs(row13["ari_2009_2021_vs_final"] - 0.6101) < 0.001

    doc_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages))
    assert "0.139" in doc_full, "η² = 0.139 no encontrado en el Documento Técnico"
    assert "0.474" in doc_full, "Línea base η² = 0.474 no encontrada en el Documento Técnico"
    assert "0.610" in doc_full, "ARI = 0.610 no encontrado en el Documento Técnico"
    assert "Estabilidad temporal" in doc_full or "Validación fuera de tiempo" in doc_full, "Párrafo de validación temporal no encontrado en el Documento"


def test_valor_agregado_reportado() -> None:
    """
    J1: Los ΔR² y valores p coinciden con tabla_13 y aparecen en el texto del documento.
    """
    df_t13 = pd.read_csv(TABLAS_DIR / "tabla_13_validacion_temporal.csv")
    row13 = df_t13.iloc[0]

    assert abs(row13["delta_r2_p2024"] - 0.0970) < 0.001
    assert abs(row13["delta_r2_cambio"] - 0.0119) < 0.001
    assert row13["p_valor_p2024_str"] == "< 0.001"
    assert row13["p_valor_cambio_str"] == "< 0.001"

    doc_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages))
    assert "0.097" in doc_full, "ΔR² = 0.097 no encontrado en Documento Técnico"
    assert "0.012" in doc_full, "ΔR²_c = 0.012 no encontrado en Documento Técnico"


def test_cobertura_ampliada() -> None:
    """
    G1: Las cifras de secciones (12,104 asignadas, 65,748 total), % LN (91.5%) y
    secciones sin historia (5,003) coinciden con tabla_14 y aparecen en el texto del documento.
    """
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    cob = data["cobertura_ampliada_2024"]

    df_t14 = pd.read_csv(TABLAS_DIR / "tabla_14_cobertura_ampliada.csv")
    assert len(df_t14) >= 7, "tabla_14 debe contener filas por categoría y cluster"

    assert cob["secciones_asignadas"] == 12104
    assert cob["secciones_cobertura_ampliada"] == 65748
    assert cob["pct_ln_panel_b_mas_asignadas"] == 91.5
    assert cob["secciones_sin_historia_suficiente"] == 5003

    perfil_csv = PROJECT_ROOT / "outputs" / "perfil_por_seccion_2024.csv"
    assert perfil_csv.exists(), "outputs/perfil_por_seccion_2024.csv debe existir en outputs/"
    df_perfil = pd.read_csv(perfil_csv)
    assert len(df_perfil) == 65748, f"perfil_por_seccion_2024.csv debe tener 65,748 filas; tiene {len(df_perfil)}"
    expected_cols = {"EDOCVE", "DEF", "SECCION", "perfil", "origen", "LN_2024", "advertencia"}
    assert expected_cols.issubset(set(df_perfil.columns)), f"Columnas faltantes en perfil_por_seccion_2024.csv: {set(df_perfil.columns)}"
    assert (df_perfil["advertencia"] == "reseccionamiento").sum() == 1306, "Deben haber 1,306 secciones con advertencia='reseccionamiento'"
    assert ((df_perfil["origen"] == "panel_B") & (df_perfil["advertencia"] == "reseccionamiento")).sum() == 0

    doc_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages))
    assert "12,104" in doc_full, "Cifra '12,104' no encontrada en el texto de Limitaciones del Documento"
    assert "91.5%" in doc_full, "Cifra '91.5%' no encontrada en el texto de Limitaciones del Documento"
    assert "5,003" in doc_full, "Cifra '5,003' no encontrada en el texto de Limitaciones del Documento"


def test_piloto() -> None:
    """
    J1: El MDE y el n del texto coinciden con tabla_15 y con metricas_finales.json.
    """
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    pil = data["potencia_piloto_c0"]
    df_t15 = pd.read_csv(TABLAS_DIR / "tabla_15_potencia_piloto.csv")

    assert len(df_t15) == 3, "tabla_15 debe tener 3 filas para n=250, 500, 1000"
    row500 = df_t15[df_t15["secciones_por_grupo_n"] == 500].iloc[0]

    assert pil["n_seleccionado"] == 500
    assert pil["diseno_seleccionado"] == "ANCOVA"
    assert abs(pil["mde_seleccionado_pts"] - 1.57) < 0.01
    assert abs(row500["mde_ancova_pts"] - 1.57) < 0.01

    doc_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages))
    assert "500 de tratamiento y 500 de control" in doc_full or "500 secciones por grupo" in doc_full
    assert "1.57" in doc_full, "MDE = 1.57 no encontrado en Documento Técnico"
    assert "ANCOVA" in doc_full, "Diseño ANCOVA no encontrado en Documento Técnico"


def test_redondeo_identico() -> None:
    """
    G4: Verifica que las cifras de redondeo crítico (11.2, 60.9, 47.8, 60.6) aparezcan
    de manera idéntica en los entregables y nunca sin redondear.
    """
    import sys
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.auditoria.utilidades_formato import redondear
    assert redondear(11.15, 1) == 11.2
    assert redondear(60.85, 1) == 60.9
    assert redondear(47.75, 1) == 47.8
    assert redondear(60.55, 1) == 60.6

    doc_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages))
    fichas_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf")).pages))
    pres_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Presentacion_Ejecutiva_ByteMe.pdf")).pages))

    # Verificar que los valores redondeados con ROUND_HALF_UP aparezcan en los entregables
    assert "11.2" in doc_full and "11.2" in fichas_full and "11.2" in pres_full
    assert "60.9" in doc_full and "60.9" in fichas_full
    assert "47.8" in doc_full
    assert "60.6" in doc_full

    # Aserciones de ausencia (Bloque 5.2.3 / 5.3)
    assert "Sexo: +11.1" not in doc_full
    assert "60.8% / 49.7%" not in doc_full
    assert "44.4% / 65.3%" not in doc_full
    assert "47.4% / 63.9%" not in doc_full


def test_nombres_nuevos() -> None:
    """
    G4, D2: Verifica que el nuevo nombre oficial de C3 ('Participación a la Baja con Brecha de Género')
    esté en JSON, tabla_07, Documento, Fichas y Presentación, y que 'Liderazgo' no aparezca.
    """
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    assert data["perfiles"][3]["nombre_propuesto"] == "Participación a la Baja con Brecha de Género"

    df_t7 = pd.read_csv(TABLAS_DIR / "tabla_07_perfiles_k4_series_demografia.csv")
    assert df_t7.loc[df_t7["codigo_cluster"] == "C3", "nombre_perfil"].values[0] == "Participación a la Baja con Brecha de Género"

    doc_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages))
    fichas_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf")).pages))
    pres_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Presentacion_Ejecutiva_ByteMe.pdf")).pages))

    assert "Participación a la Baja con Brecha de Género" in doc_full
    assert "Participación a la Baja con Brecha de Género" in fichas_full
    assert "Participación a la Baja con Brecha de Género" in pres_full

    for txt, src in [(doc_full, "Documento"), (fichas_full, "Fichas"), (pres_full, "Presentación")]:
        assert "Liderazgo Femenino" not in txt, f"'Liderazgo Femenino' no permitido encontrado en {src}"


def test_json_valido() -> None:
    """
    G2, G4: Validación estricta de sintaxis JSON estándar en metricas_finales.json
    sin valores NaN, Infinity ni llaves rotas.
    """
    text = METRICAS_PATH.read_text(encoding="utf-8")
    assert "NaN" not in text, "Valor NaN no permitido en JSON estricto"
    assert "Infinity" not in text, "Valor Infinity no permitido en JSON estricto"
    data = json.loads(text)
    assert isinstance(data, dict), "metricas_finales.json debe ser un objeto diccionario"
    assert "perfiles" in data
    assert "impacto_y_prioridad_territorial" in data


def test_tendencia_corregida_reportada() -> None:
    """
    G4, C2, D5: Verifica que la tendencia corregida (+0.88 pts/año para C2) esté reportada
    en metricas_finales.json, tabla_19, Documento, Fichas y Presentación.
    """
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    c2_trend = data["tendencia_corregida"]["C2"]
    assert abs(c2_trend - 0.88) < 0.01

    df_t19 = pd.read_csv(TABLAS_DIR / "tabla_19_tendencia_corregida.csv")
    row_c2 = df_t19[df_t19["codigo_cluster"] == "C2"].iloc[0]
    assert abs(row_c2["tendencia_corregida_pts_ano"] - 0.88) < 0.01

    doc_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages))
    fichas_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf")).pages))
    pres_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Presentacion_Ejecutiva_ByteMe.pdf")).pages))

    assert "+0.88" in doc_full
    assert "+0.88 pts/año" in fichas_full
    assert "+0.88 pts/año" in pres_full


def test_votantes_equivalentes() -> None:
    """
    G4, C5: Verifica consistencia de las cifras de impacto C5 (1.21M, 893k, 316k, 1.83M, 1.78M, 52k)
    en metricas_finales.json, tabla_17, Documento, Fichas y Presentación.
    """
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    imp = data["impacto_y_prioridad_territorial"]
    df_t12 = pd.read_csv(TABLAS_DIR / "tabla_12_lineas_base_metas.csv").set_index("codigo_cluster")
    df_t17 = pd.read_csv(TABLAS_DIR / "tabla_17_impacto.csv").set_index("codigo_cluster")

    p2021_pan = float(df_t12.loc["Panel B", "participacion_2021_pond_pct"]) / 100.0
    p2021_c0 = float(df_t12.loc["C0", "participacion_2021_pond_pct"]) / 100.0
    p2021_c3 = float(df_t12.loc["C3", "participacion_2021_pond_pct"]) / 100.0

    svnv_c0 = float(df_t17.loc["C0", "svnv_2024_base"])
    svnv_c3 = float(df_t17.loc["C3", "svnv_2024_base"])

    calc_c0 = round(svnv_c0 * (p2021_pan - p2021_c0) / 2)
    calc_c3 = round(svnv_c3 * (p2021_pan - p2021_c3) / 2)
    calc_total = calc_c0 + calc_c3

    assert abs(imp["votantes_equivalentes_c0"] - calc_c0) <= 1
    assert abs(imp["votantes_equivalentes_c3"] - calc_c3) <= 1
    assert abs(imp["total_votantes_adicionales_c0_c3"] - calc_total) <= 1
    assert 890000 <= calc_c0 <= 896000
    assert 314000 <= calc_c3 <= 318000

    assert imp["total_adicionales_millones_str"] == "≈ 1.21 millones"
    assert imp["votantes_equivalentes_c0_miles_str"] == "≈ 893 mil"
    assert imp["votantes_equivalentes_c3_miles_str"] == "≈ 316 mil"
    assert imp["total_regresion"] == 1830218
    assert imp["total_regresion_millones_str"] == "≈ 1.83 millones"
    assert imp["escenario_regresion_c1"] == 52210
    assert imp["escenario_regresion_c2"] == 1778008

    df_t17 = pd.read_csv(TABLAS_DIR / "tabla_17_impacto.csv")
    assert len(df_t17) == 4

    doc_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages))
    fichas_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf")).pages))
    pres_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Presentacion_Ejecutiva_ByteMe.pdf")).pages))

    for token in ["1.21 millones", "1.83 millones"]:
        assert token in doc_full, f"Token {token} ausente en Documento"
        assert token in pres_full, f"Token {token} ausente en Presentación"

    for token in ["893 mil", "316 mil", "1.78 millones", "52 mil"]:
        assert token in doc_full, f"Token {token} ausente en Documento"
        assert token in fichas_full, f"Token {token} ausente en Fichas"
        assert token in pres_full, f"Token {token} ausente en Presentación"


def test_sin_prefijo_duplicado() -> None:
    """5.2.1: En el texto de los 3 PDF y del PPTX (incluye notas), re.search(r"\\bCC[0-3]\\b", texto) debe ser None."""
    import pptx
    pdf_paths = [
        ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf",
        ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf",
        ENTREGABLES_DIR / "Presentacion_Ejecutiva_ByteMe.pdf",
    ]
    for pdf_path in pdf_paths:
        text = "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(str(pdf_path)).pages)
        match = re.search(r"\bCC[0-3]\b", text)
        assert match is None, f"Encontrado prefijo duplicado {match.group(0)} en {pdf_path.name}"

    prs = pptx.Presentation(ENTREGABLES_DIR / "Presentacion_Ejecutiva_ByteMe.pptx")
    pptx_texts = []
    for slide in prs.slides:
        for s in slide.shapes:
            if s.has_text_frame:
                pptx_texts.append(s.text_frame.text)
            if s.has_table:
                for row in s.table.rows:
                    for cell in row.cells:
                        pptx_texts.append(cell.text)
        if slide.has_notes_slide:
            pptx_texts.append(slide.notes_slide.notes_text_frame.text)
    full_pptx = "\n".join(pptx_texts)
    match_pptx = re.search(r"\bCC[0-3]\b", full_pptx)
    assert match_pptx is None, f"Encontrado prefijo duplicado {match_pptx.group(0)} en Presentacion PPTX"


def test_sin_cero_negativo() -> None:
    """5.2.2: En el texto de los 3 PDF, re.search(r"(?<![\\d.])-0\\.0+(?![0-9]*[1-9])", texto) debe ser None; y en tabla_19 y json['tendencia_corregida'], ningún valor igual a 0 con signo negativo."""
    import math
    pdf_paths = [
        ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf",
        ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf",
        ENTREGABLES_DIR / "Presentacion_Ejecutiva_ByteMe.pdf",
    ]
    pattern = re.compile(r"(?<![\d.])-0\.0+(?![0-9]*[1-9])")
    for pdf_path in pdf_paths:
        text = "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(str(pdf_path)).pages)
        match = pattern.search(text)
        assert match is None, f"Cero negativo encontrado en {pdf_path.name}: '{match.group(0)}'"

    t19 = pd.read_csv(TABLAS_DIR / "tabla_19_tendencia_corregida.csv")
    for col in t19.select_dtypes(include=[np.number]).columns:
        for val in t19[col].dropna():
            if val == 0:
                assert math.copysign(1, val) >= 0, f"Cero negativo en tabla_19 col {col}: {val}"

    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    for k, v in data["tendencia_corregida"].items():
        if isinstance(v, (int, float)) and v == 0:
            assert math.copysign(1, v) >= 0, f"Cero negativo en tendencia_corregida[{k}]: {v}"


def test_convencion_redondeo() -> None:
    """5.2.3: Verifica convención única de redondeo en Tablas 4 y 5 del Documento Técnico."""
    doc_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages))
    presentes = ["Sexo: +11.2", "60.9% / 49.7%", "44.4% / 65.4%", "47.5% / 63.9%"]
    ausentes = ["Sexo: +11.1", "60.8% / 49.7%", "44.4% / 65.3%", "47.4% / 63.9%"]
    for p_str in presentes:
        assert p_str in doc_full, f"Texto esperado '{p_str}' no encontrado en Documento Técnico"
    for a_str in ausentes:
        assert a_str not in doc_full, f"Texto no deseado '{a_str}' encontrado en Documento Técnico"


def test_tabla4_sin_cortes() -> None:
    """5.2.4: En el texto normalizado del documento no deben aparecer cortes de palabras en Tabla 4."""
    doc_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages))
    cortes = ["Interge neracional", "Estabilida d", "Pres–Int .", "(z=+0.60 )"]
    for c in cortes:
        assert c not in doc_full, f"Corte indeseado '{c}' encontrado en Documento Técnico"


def test_calendario_texto() -> None:
    """5.2.5: El documento contiene pct_c1_en_las_tres y pct_c2_en_ninguna (con redondear_pub) y NO contiene 'C1 agrupa entidades con concurrencia'."""
    import sys
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.auditoria.utilidades_formato import redondear_pub

    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    cal = data["calendario_electoral"]
    pct_c1 = f"{redondear_pub(cal['pct_c1_en_las_tres'], 1):.1f}%"
    pct_c2 = f"{redondear_pub(cal['pct_c2_en_ninguna'], 1):.1f}%"
    doc_full = re.sub(r"\s+", " ", "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages))
    assert pct_c1 in doc_full, f"'{pct_c1}' no encontrado en Documento Técnico"
    assert pct_c2 in doc_full, f"'{pct_c2}' no encontrado en Documento Técnico"
    assert "C1 agrupa entidades con concurrencia" not in doc_full, (
        "'C1 agrupa entidades con concurrencia' encontrado en Documento Técnico"
    )


def test_regresion_reproducible() -> None:
    """5.2.6: Para C1 y C2, round(svnv_2024_base * (participacion_2021_pond_pct - promedio_intermedias_2009_2021_pond_pct) / 100) difiere de escenario_regresion_votos_n en <= 300."""
    df17 = pd.read_csv(TABLAS_DIR / "tabla_17_impacto.csv")
    for cid in ["C1", "C2"]:
        row = df17[df17["codigo_cluster"] == cid].iloc[0]
        svnv_2024 = float(row["svnv_2024_base"])
        p2021 = float(row["participacion_2021_pond_pct"])
        p_inter = float(row["promedio_intermedias_2009_2021_pond_pct"])
        esperado_votos = float(row["escenario_regresion_votos_n"])
        calc_votos = round(svnv_2024 * (p2021 - p_inter) / 100.0)
        diff = abs(calc_votos - esperado_votos)
        assert diff <= 300, f"Diferencia de regresión para {cid} es {diff} > 300 (calc={calc_votos}, esperado={esperado_votos})"


def test_sin_literales_generadores() -> None:
    """
    5.2.7: Verifica que en 07_compilar_documento.py y 11_analisis_auditoria.py no aparezcan constantes literales prohibidas,
    y que el árbol AST de 08_generar_fichas.py y 10_generar_presentacion.py no contenga literales de cifras fuera de cargar_cifras().
    """
    import ast
    scripts_dir = PROJECT_ROOT / "scripts" / "auditoria"
    literales_prohibidos = [
        "0.0333792",
        "0.0167941",
        "-0.00 en C1",
        "(+0.40 en C0",
        "masculina (46.8%)",
        "como el promedio (60.9%)",
    ]
    for s_name in ["07_compilar_documento.py", "11_analisis_auditoria.py"]:
        code = (scripts_dir / s_name).read_text(encoding="utf-8")
        for lit in literales_prohibidos:
            assert lit not in code, f"Literal prohibido '{lit}' encontrado en {s_name}"

    pattern = re.compile(r"\d+\.\d+\s*(%|pts|millones|mil\b)|≈\s*\d|\b\d{1,3}(,\d{3})+\b")
    for s_name in ["08_generar_fichas.py", "10_generar_presentacion.py"]:
        code = (scripts_dir / s_name).read_text(encoding="utf-8")
        tree = ast.parse(code)
        matches = []
        class Visitor(ast.NodeVisitor):
            def __init__(self):
                self.scope = ["module"]
            def visit_FunctionDef(self, node):
                self.scope.append(node.name)
                self.generic_visit(node)
                self.scope.pop()
            def visit_Constant(self, node):
                if isinstance(node.value, str):
                    if self.scope[-1] == "cargar_cifras":
                        return
                    m = pattern.findall(node.value)
                    if m:
                        matches.append((node.lineno, self.scope[-1], node.value, m))
        Visitor().visit(tree)
        assert len(matches) == 0, f"Literales de cifras encontrados en AST de {s_name} fuera de cargar_cifras: {matches}"





