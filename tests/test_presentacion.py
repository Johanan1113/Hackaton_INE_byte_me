#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite de Pruebas Automatizadas de la Presentación Ejecutiva (tests/test_presentacion.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

Verifica la integridad técnica, diseño, fuentes y contenido de la presentación:
1. Conteo de diapositivas y páginas (<= 10 y coincidentes).
2. Fuente Arial 100% embebida en el PDF.
3. Cifras clave y nombres oficiales de perfiles.
4. Ausencia de términos prohibidos y snake_case no permitido.
5. Márgenes de seguridad (> 0.25 pulg.) en todas las páginas.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pdfplumber
import pptx
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENTREGABLES_DIR = PROJECT_ROOT / "outputs" / "entregables"
PPTX_PATH = ENTREGABLES_DIR / "Presentacion_Ejecutiva_ByteMe.pptx"
PDF_PATH = ENTREGABLES_DIR / "Presentacion_Ejecutiva_ByteMe.pdf"

REQUIRED_TOKENS = [
    "4.27",
    "53,644",
    "79.5%",
    "0.957",
    "1.57",
    "1.27 millones",
    "607 mil",
    "Baja Participación Intermitente con Rezago Juvenil",
    "Alta Participación Estable e Intergeneracional",
    "Participación en Ascenso con Juventud Activa",
    "Liderazgo Femenino con Participación Estancada",
]

FORBIDDEN_TERMS = ["Oficial", ">=", "<=", "PENDIENTE"]
SNAKE_CASE_WHITELIST = {"run_all", "Hackaton_INE_byte_me", "byte_me"}


def test_diapositivas_y_paginas():
    """El .pptx tiene exactamente <= 10 diapositivas y el .pdf exactamente <= 10 páginas (deben coincidir)."""
    assert PPTX_PATH.is_file(), f"No existe el archivo PPTX: {PPTX_PATH}"
    assert PDF_PATH.is_file(), f"No existe el archivo PDF: {PDF_PATH}"

    prs = pptx.Presentation(PPTX_PATH)
    n_slides = len(prs.slides)

    with pdfplumber.open(PDF_PATH) as pdf:
        n_pages = len(pdf.pages)

    assert n_slides <= 10, f"El archivo PPTX tiene {n_slides} diapositivas (> 10)"
    assert n_pages <= 10, f"El archivo PDF tiene {n_pages} páginas (> 10)"
    assert n_slides == n_pages, f"Discrepancia entre diapositivas ({n_slides}) y páginas PDF ({n_pages})"


def test_fuente_arial_presentacion():
    """pdffonts sobre el PDF verifica que el 100% de las fuentes listadas sean variantes de Arial y tengan emb = yes."""
    assert PDF_PATH.is_file(), f"No existe el archivo PDF: {PDF_PATH}"
    cmd = ["pdffonts", str(PDF_PATH)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    lines = res.stdout.strip().splitlines()
    assert len(lines) >= 3, "pdffonts no devolvió fuentes en la salida"

    fonts_checked = 0
    for line in lines[2:]:  # Omitir las 2 líneas de encabezado
        parts = line.split()
        if len(parts) >= 5:
            font_name = parts[0]
            emb = parts[4]
            assert "Arial" in font_name, f"Fuente no Arial detectada: {font_name} en '{line}'"
            assert emb == "yes", f"Fuente no embebida: {font_name} (emb = {emb})"
            fonts_checked += 1

    assert fonts_checked > 0, "No se verificó ninguna fuente en el PDF"


def test_cifras_y_nombres_presentacion():
    """Comprueba que el texto del PDF contenga las cifras clave y nombres de perfiles requeridos."""
    assert PDF_PATH.is_file(), f"No existe el archivo PDF: {PDF_PATH}"
    full_text = ""
    with pdfplumber.open(PDF_PATH) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"

    missing = [tok for tok in REQUIRED_TOKENS if tok not in full_text]
    assert not missing, f"Faltan tokens requeridos en la presentación: {missing}"


def test_sin_prohibidos_presentacion():
    """Ningún 'Oficial', '>=', '<=', 'PENDIENTE', y ningún snake_case fuera de la lista blanca."""
    assert PDF_PATH.is_file(), f"No existe el archivo PDF: {PDF_PATH}"
    full_text = ""
    with pdfplumber.open(PDF_PATH) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"

    for forbidden in FORBIDDEN_TERMS:
        assert forbidden not in full_text, f"Término prohibido encontrado: {forbidden!r}"

    snakes = set(re.findall(r"\b[a-zA-Z]+_[a-zA-Z]+\b", full_text))
    violating = snakes - SNAKE_CASE_WHITELIST
    assert not violating, f"Identificadores snake_case no permitidos encontrados: {violating}"


def test_margenes_presentacion():
    """Con pdfplumber, ningún carácter fuera del área imprimible (márgenes > 0.25 pulgadas = 18 pt)."""
    assert PDF_PATH.is_file(), f"No existe el archivo PDF: {PDF_PATH}"
    violations = []
    margin_pt = 18.0  # 0.25 in * 72 pt/in

    with pdfplumber.open(PDF_PATH) as pdf:
        for p_idx, page in enumerate(pdf.pages, 1):
            w = float(page.width)
            h = float(page.height)
            for c in page.chars:
                if (
                    c["x0"] < margin_pt
                    or c["x1"] > (w - margin_pt)
                    or c["top"] < margin_pt
                    or c["bottom"] > (h - margin_pt)
                ):
                    violations.append(
                        (p_idx, c.get("text", "?"), c["x0"], c["x1"], c["top"], c["bottom"])
                    )

    assert not violations, f"Se encontraron {len(violations)} caracteres violando márgenes de 0.25 in: {violations[:5]}"


def test_grafica_ns():
    """A8: Verifica que los valores de la gráfica de diapositiva 2 coincidan con tabla_02 (±0.05)."""
    import pandas as pd
    tabla_02_path = PROJECT_ROOT / "outputs" / "tablas" / "tabla_02_serie_nacional_2009_2024.csv"
    assert tabla_02_path.is_file(), f"No existe {tabla_02_path}"
    df_t2 = pd.read_csv(tabla_02_path).sort_values("anio").reset_index(drop=True)

    prs = pptx.Presentation(PPTX_PATH)
    slide2 = prs.slides[1]

    chart = None
    for shape in slide2.shapes:
        if shape.has_chart:
            chart = shape.chart
            break
    assert chart is not None, "No se encontró gráfica en la diapositiva 2"

    series_names = [s.name for s in chart.series]
    assert "SV/LN" in series_names, f"Falta serie 'SV/LN' en la gráfica: {series_names}"
    assert "SV/(SV+NV)" in series_names, f"Falta serie 'SV/(SV+NV)' en la gráfica: {series_names}"

    idx_sv_ln = series_names.index("SV/LN")
    idx_sv_svnv = series_names.index("SV/(SV+NV)")

    chart_vals_sv_ln = list(chart.series[idx_sv_ln].values)
    chart_vals_sv_svnv = list(chart.series[idx_sv_svnv].values)

    expected_sv_ln = list(df_t2["total_ponderada_erronea_sv_ln_pct"])
    expected_sv_svnv = list(df_t2["total_ponderada_sv_svnv_pct"])

    assert len(chart_vals_sv_ln) == len(expected_sv_ln), "Longitud de serie SV/LN no coincide"
    for c_val, e_val in zip(chart_vals_sv_ln, expected_sv_ln):
        assert abs(c_val - e_val) <= 0.051, f"Valor SV/LN {c_val} difiere de {e_val} en > 0.05"

    assert len(chart_vals_sv_svnv) == len(expected_sv_svnv), "Longitud de serie SV/(SV+NV) no coincide"
    for c_val, e_val in zip(chart_vals_sv_svnv, expected_sv_svnv):
        assert abs(c_val - e_val) <= 0.051, f"Valor SV/(SV+NV) {c_val} difiere de {e_val} en > 0.05"


def test_texto_visible():
    """A8: Verifica que 'subestimación de la participación' esté presente en el PDF y no sea blanco en PPTX."""
    assert PDF_PATH.is_file(), f"No existe el archivo PDF: {PDF_PATH}"

    # Verificación en PDF (usando pdftotext con flujo continuo de columnas)
    cmd = ["pdftotext", "-f", "2", "-l", "2", str(PDF_PATH), "-"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    pdf_text = re.sub(r"\s+", " ", res.stdout)
    assert "subestimación de la participación" in pdf_text, "Texto no encontrado en la página 2 del PDF"

    # Verificación en PPTX (color no blanco)
    prs = pptx.Presentation(PPTX_PATH)
    slide2 = prs.slides[1]
    found = False
    for shape in slide2.shapes:
        if shape.has_text_frame and "subestimación de la participación" in shape.text_frame.text:
            found = True
            for p in shape.text_frame.paragraphs:
                if "subestimación de la participación" in p.text:
                    rgb = p.font.color.rgb
                    assert (rgb[0], rgb[1], rgb[2]) != (255, 255, 255), "El color del texto es blanco (invisible)"
    assert found, "Texto 'subestimación de la participación' no encontrado en formas de la diapositiva 2 del PPTX"


def test_nombres_oficiales_portada():
    """A8: Verifica que los 4 nombres oficiales de perfiles aparezcan en la diapositiva 1."""
    prs = pptx.Presentation(PPTX_PATH)
    slide1 = prs.slides[0]
    s1_text = ""
    for shape in slide1.shapes:
        if shape.has_text_frame:
            s1_text += shape.text_frame.text + "\n"

    oficiales = [
        "Baja Participación Intermitente con Rezago Juvenil",
        "Alta Participación Estable e Intergeneracional",
        "Participación en Ascenso con Juventud Activa",
        "Liderazgo Femenino con Participación Estancada",
    ]
    for nom in oficiales:
        assert nom in s1_text, f"Nombre oficial no encontrado en portada (diapositiva 1): '{nom}'"

