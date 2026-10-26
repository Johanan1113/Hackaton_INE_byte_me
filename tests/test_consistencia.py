#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite de Pruebas Automatizadas de Consistencia y Trazabilidad Numérica (tests/test_consistencia.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

Incluye la prueba bloqueante (Punto 4 del usuario) que extrae TODOS los números
del Documento Técnico (MD y PDF) y de las Fichas Infográficas (PDF) ya generados,
y verifica que cada uno exista en outputs/metricas_finales.json o en outputs/tablas/*.csv
(con tolerancia de redondeo), listando cualquier cifra que no se encuentre.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
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

FORBIDDEN_PHRASES = [
    "libre de sesgo",
    "irrefutable",
    "estructuralmente invariante",
    "estrictamente controlados",
    "confidencial",
    "tendencia a la baja",
    "estancamiento secular",
    "abstencionismo crónico",
    "radios indígenas",
]


def extract_numbers_from_text(text: str) -> list[tuple[str, float]]:
    """
    Extrae todos los tokens numéricos de un texto (enteros con o sin comas de miles y decimales),
    devolviendo pares (token_original, valor_float).
    """
    # Eliminar fórmulas o identificadores de código tipo sha256 o rutas si aparecieran
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
    Construye el universo completo de números válidos a partir de outputs/metricas_finales.json
    y de todos los archivos CSV en outputs/tablas/*.csv (incluyendo sus representaciones en % y pts).
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

    # Añadir también todas las celdas de outputs/tablas/*.csv
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

    # Añadir numeración estructural de secciones/tablas/páginas del propio documento (1..12)
    for idx in range(0, 15):
        _add_val(float(idx))

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
        # Tolerancia de medio último dígito + margen por redondeo intermedio (ej. 0.55 para 1 decimal, 0.015 para 2)
        tol = 0.55 * (10 ** (-n_dec)) + 1e-6
    else:
        # Enteros: si es un entero > 100 (conteos de secciones o LN), exigir coincidencia exacta (o ±1 en CH redondeado)
        tol = 0.55 if val_abs >= 5000 else 1e-6

    diffs = np.abs(ref_arr - val_abs)
    return bool(np.any(diffs <= tol))


def test_1_existencia_y_no_vaciedad_de_entregables() -> None:
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
        ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.md",
        ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf",
        ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.docx",
        ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf",
        ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.png",
    ]
    for f in required_files:
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

    # Verificar que la fila Media Nacional Panel B coincide con el promedio ponderado por secciones de los 4 clusters
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

    md_text = (ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.md").read_text(encoding="utf-8")
    doc_pdf_text = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages)
    fichas_pdf_text = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf")).pages)

    for cid, exp_name in EXPECTED_NAMES.items():
        assert data["perfiles"][cid]["nombre_propuesto"] == exp_name
        assert data["estrategias"][cid]["nombre_perfil"] == exp_name
        assert exp_name in md_text, f"Nombre '{exp_name}' ausente en Documento_Tecnico_ByteMe.md"
        assert exp_name in doc_pdf_text, f"Nombre '{exp_name}' ausente en Documento_Tecnico_ByteMe.pdf"
        assert exp_name in fichas_pdf_text, f"Nombre '{exp_name}' ausente en Fichas_Perfiles_ByteMe.pdf"


def test_6_lineas_base_2021_costos_cualitativos_y_lenguaje() -> None:
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    expected_2021_base = {0: 46.1, 1: 62.5, 2: 60.4, 3: 49.5}
    for cid, exp_val in expected_2021_base.items():
        assert data["estrategias"][cid]["linea_base_intermedia_2021_pond_pct"] == exp_val

    md_text = (ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.md").read_text(encoding="utf-8")
    doc_pdf_text = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.pdf")).pages)
    fichas_pdf_text = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(ENTREGABLES_DIR / "Fichas_Perfiles_ByteMe.pdf")).pages)

    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in md_text.lower(), f"Frase prohibida '{phrase}' en MD"
        assert phrase not in doc_pdf_text.lower(), f"Frase prohibida '{phrase}' en PDF"
        assert phrase not in fichas_pdf_text.lower(), f"Frase prohibida '{phrase}' en Fichas"

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


def test_8_extraccion_exhaustiva_de_numeros_documento_y_fichas() -> None:
    """
    Test bloqueante (Punto 4): Extrae TODOS los números del Documento Técnico (MD y PDF)
    y de las Fichas Infográficas (PDF), y verifica que cada uno exista en
    outputs/metricas_finales.json o en outputs/tablas/*.csv (con tolerancia de redondeo).
    """
    ref_nums = collect_reference_numbers()
    ref_arr = np.array(sorted(ref_nums), dtype=float)

    sources = {
        "Documento_Tecnico_ByteMe.md": (ENTREGABLES_DIR / "Documento_Tecnico_ByteMe.md").read_text(encoding="utf-8"),
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
