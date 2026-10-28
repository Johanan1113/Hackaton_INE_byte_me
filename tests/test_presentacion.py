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
import pandas as pd
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
    "1.21 millones",
    "893 mil",
    "316 mil",
    "1.83 millones",
    "+0.88 pts/año",
    "Baja Participación Intermitente con Rezago Juvenil",
    "Alta Participación Estable e Intergeneracional",
    "Participación en Ascenso con Juventud Activa",
    "Participación a la Baja con Brecha de Género",
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
        "Participación a la Baja con Brecha de Género",
    ]
    for nom in oficiales:
        assert nom in s1_text, f"Nombre oficial no encontrado en portada (diapositiva 1): '{nom}'"


def test_grafica_perfiles():
    """A1: Lee los valores de la gráfica en la diapositiva 5 del .pptx y los compara con tabla_07 (±0.05)."""
    assert PPTX_PATH.is_file(), f"No existe el archivo PPTX: {PPTX_PATH}"
    tabla_07_path = PROJECT_ROOT / "outputs" / "tablas" / "tabla_07_perfiles_k4_series_demografia.csv"
    assert tabla_07_path.is_file(), f"No existe tabla_07: {tabla_07_path}"

    df_t07 = pd.read_csv(tabla_07_path)
    prs = pptx.Presentation(PPTX_PATH)
    slide5 = prs.slides[4]
    chart = None
    for shape in slide5.shapes:
        if shape.has_chart:
            chart = shape.chart
            break
    assert chart is not None, "No se encontró la gráfica en la diapositiva 5"

    years = [2009, 2012, 2015, 2018, 2021, 2024]
    for series in chart.series:
        s_name = series.name
        if s_name == "Media del panel":
            row = df_t07[df_t07["codigo_cluster"] == "Panel_B"].iloc[0]
        else:
            row = df_t07[df_t07["codigo_cluster"] == s_name].iloc[0]

        expected_vals = [float(row[f"p_{y}_pond_pct"]) for y in years]
        chart_vals = list(series.values)
        assert len(chart_vals) == len(expected_vals), f"Longitud de serie distinta en {s_name}"
        for y_idx, (cv, ev) in enumerate(zip(chart_vals, expected_vals)):
            assert round(abs(cv - ev), 4) <= 0.05 or abs(cv - ev) <= 0.0501, (
                f"Discrepancia en {s_name} año {years[y_idx]}: chart={cv}, tabla={ev}"
            )


def test_diapositiva_08_impacto():
    """F: Verifica impacto en diapositiva 8: título 1.21M, cards 893k, 316k, 1.83M y base (SV+NV)."""
    prs = pptx.Presentation(PPTX_PATH)
    slide8 = prs.slides[7]
    text8 = ""
    for s in slide8.shapes:
        if s.has_text_frame:
            text8 += s.text_frame.text + "\n"
        if s.has_table:
            for row in s.table.rows:
                for cell in row.cells:
                    text8 += cell.text + " "
                text8 += "\n"

    assert "1.21 millones" in text8, "Falta '1.21 millones' en diapositiva 8"
    assert "893 mil" in text8, "Falta '893 mil' en diapositiva 8"
    assert "316 mil" in text8, "Falta '316 mil' en diapositiva 8"
    assert "1.83 millones" in text8, "Falta '1.83 millones' en diapositiva 8"
    assert "52 mil" in text8, "Falta '52 mil' en diapositiva 8"
    assert "(SV + NV) 2024" in text8, "Falta referencia a base (SV + NV) 2024 en diapositiva 8"


def test_diapositiva_09_mde_icc():
    """F: Verifica que la diapositiva 9 mencione MDE 1.57 pts, ICC = 0.543, m=5 (2.80 pts) y m=10 (3.81 pts)."""
    prs = pptx.Presentation(PPTX_PATH)
    slide9 = prs.slides[8]
    text9 = ""
    for s in slide9.shapes:
        if s.has_text_frame:
            text9 += s.text_frame.text + "\n"

    assert "1.57 pts" in text9, "Falta MDE seccional '1.57 pts' en diapositiva 9"
    assert "ICC = 0.543" in text9 and "0.5428" not in text9, "Falta 'ICC = 0.543' o persiste '0.5428' en diapositiva 9"
    assert "2.80 pts" in text9, "Falta '2.80 pts' en nota de diapositiva 9"
    assert "3.81 pts" in text9, "Falta '3.81 pts' en nota de diapositiva 9"


def test_diapositiva_10_cuatro_recomendaciones():
    """F: Verifica que la diapositiva 10 tenga el encabezado 'Cuatro recomendaciones al INE' y la 4ª recomendación."""
    prs = pptx.Presentation(PPTX_PATH)
    slide10 = prs.slides[9]
    text10 = ""
    for s in slide10.shapes:
        if s.has_text_frame:
            text10 += s.text_frame.text + "\n"

    assert "Cuatro recomendaciones al INE" in text10, "Falta encabezado 'Cuatro recomendaciones al INE'"
    assert "4. Usar la priorización por junta distrital y el piloto aleatorizado 2027 para evaluar qué funciona." in text10, (
        "Falta la 4ª recomendación en diapositiva 10"
    )


def test_notas_orador_sin_prohibidos():
    """F: Verifica que las notas de orador no contengan 'liderazgo', 'migración', '1.5 millones', y que d9 mencione asignables e ICC."""
    prs = pptx.Presentation(PPTX_PATH)
    for idx, slide in enumerate(prs.slides, 1):
        notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
        for forbidden in ["liderazgo", "Liderazgo", "migración", "migracion", "Migración", "1.5 millones"]:
            assert forbidden not in notes, f"Término prohibido '{forbidden}' encontrado en notas de diapositiva {idx}"

    notes9 = prs.slides[8].notes_slide.notes_text_frame.text
    assert "asignables" in notes9, "Notas de diapositiva 9 deben mencionar acciones asignables"
    assert "0.543" in notes9 or "0.5428" in notes9 or "conglomerados" in notes9 or "efecto de diseño" in notes9, (
        "Notas de diapositiva 9 deben mencionar efecto de conglomerados/diseño o ICC"
    )


def test_diapositiva_07_tendencia_corregida():
    """F: Verifica que la diapositiva 7 muestre '+0.88 pts/año' y 'tendencia corregida'."""
    prs = pptx.Presentation(PPTX_PATH)
    slide7 = prs.slides[6]
    text7 = ""
    for s in slide7.shapes:
        if s.has_text_frame:
            text7 += s.text_frame.text + "\n"

    assert "+0.88 pts/año" in text7, "Falta '+0.88 pts/año' en diapositiva 7"
    assert "tendencia corregida" in text7, "Falta 'tendencia corregida' en diapositiva 7"


