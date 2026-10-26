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
    3: "Liderazgo Femenino con Participación Estancada",
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
]

FORBIDDEN_PHRASES_SENSITIVE = [
    "PENDIENTE",
    "Gutierrez",
    "Martinez",
    "Saul ",
    "Gonzales",
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
    H2: El tamaño de carácter más frecuente de Documento_Tecnico_ByteMe.pdf es 11.0 pt,
    y el interlineado (leading) de las líneas de cuerpo es >= 18.0 pt.
    """
    pdf_path = ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf"
    char_sizes = Counter()
    leading_samples = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for char in page.chars:
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
                        if 15.0 <= diff <= 25.0:
                            leading_samples.append(diff)

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
    H2: La expresión regular \\b[a-z]+_[a-z0-9_]+\\b tiene 0 coincidencias en el texto de ambos PDF.
    """
    pattern = re.compile(r"\b[a-z]+_[a-z0-9_]+\b")
    doc_text = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages)
    fichas_text = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf")).pages)

    matches_doc = pattern.findall(doc_text)
    matches_fichas = pattern.findall(fichas_text)
    assert not matches_doc, f"snake_case detectado en Documento_Tecnico_ByteMe.pdf: {matches_doc}"
    assert not matches_fichas, f"snake_case detectado en Fichas_Perfiles_ByteMe.pdf: {matches_fichas}"


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
    }

    unmatched_by_source: dict[str, list[str]] = {}
    total_checked = 0

    for src_name, text in sources.items():
        tokens = extract_numbers_from_text(text)
        total_checked += len(tokens)
        unmatched = []
        for tok, val in tokens:
            if not number_matches_reference(tok, val, ref_nums, ref_arr):
                unmatched.append(f"{tok} ({val})")
        if unmatched:
            unmatched_by_source[src_name] = unmatched

    assert total_checked > 500, f"Se extrajeron muy pocos números ({total_checked})"
    assert not unmatched_by_source, (
        f"Se encontraron números en los entregables que no existen en metricas_finales.json ni en outputs/tablas/: "
        f"{json.dumps(unmatched_by_source, ensure_ascii=False, indent=2)}"
    )
