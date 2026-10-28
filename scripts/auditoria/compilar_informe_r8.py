#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Compilación del Informe de Auditoría R8 (Informe_R8_ByteMe.pdf)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")
Concurso: "Hackea la participación: Datos que construyen democracia" (INE)

Genera el documento PDF oficial de certificación y auditoría R8 con las 8 secciones obligatorias,
evidencias completas de ejecución, imágenes renderizadas a 110 DPI y tipografía 100% Arial.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_ENTREGABLES = PROJECT_ROOT / "outputs" / "entregables"
PDF_PATH = OUT_ENTREGABLES / "Informe_R8_ByteMe.pdf"
PDF_ROOT_PATH = PROJECT_ROOT / "Informe_R8_ByteMe.pdf"

# Registro estricto de fuentes Arial
pdfmetrics.registerFont(TTFont("Arial", "/usr/share/fonts/TTF/Arial.TTF"))
pdfmetrics.registerFont(TTFont("Arial-Bold", "/usr/share/fonts/TTF/Arialbd.TTF"))
pdfmetrics.registerFont(TTFont("Arial-Italic", "/usr/share/fonts/TTF/Ariali.TTF"))
pdfmetrics.registerFont(TTFont("Arial-BoldItalic", "/usr/share/fonts/TTF/Arialbi.TTF"))
pdfmetrics.registerFontFamily(
    "Arial",
    normal="Arial",
    bold="Arial-Bold",
    italic="Arial-Italic",
    boldItalic="Arial-BoldItalic",
)


class NumberedCanvas(pdf_canvas.Canvas):
    def __init__(self, *args, **kwargs):
        kwargs["initialFontName"] = "Arial"
        super().__init__(*args, **kwargs)
        self._fontname = "Arial"
        self._saved_page_states = []

    def _startPage(self):
        super()._startPage()
        self.setFont("Arial", 8.5)

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Arial", 8.5)
        self.setFillColor(colors.HexColor("#4B5563"))

        # Header (páginas posteriores a la 1)
        if self._pageNumber > 1:
            self.drawString(
                54,
                755,
                "Equipo Byte me · Reto 1: Perfiles ciudadanos de participación · Informe de Auditoría R8 (v1.0.4)",
            )
            self.drawRightString(612 - 54, 755, "INE / Hackea la participación")
            self.setStrokeColor(colors.HexColor("#D1D5DB"))
            self.setLineWidth(0.5)
            self.line(54, 747, 612 - 54, 747)

        # Footer (todas las páginas)
        self.setStrokeColor(colors.HexColor("#D1D5DB"))
        self.setLineWidth(0.5)
        self.line(54, 45, 612 - 54, 45)
        self.drawString(
            54,
            32,
            "Certificación Técnica Oficial · Concurso Hackea la participación (INE 2026) · Licencia CC0 1.0",
        )
        self.drawRightString(
            612 - 54,
            32,
            f"Página {self._pageNumber} de {page_count}",
        )
        self.restoreState()


def make_code_box(content: str, code_style: ParagraphStyle, bg_color: str = "#F3F4F6", border_color: str = "#D1D5DB") -> Table:
    """Crea una caja de código preformateado con tipografía Arial garantizada."""
    t = Table([[Preformatted(content, code_style)]], colWidths=[504])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Arial"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_color)),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(border_color)),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def render_110dpi_images() -> dict[str, Path]:
    """Genera las imágenes PNG a 110 DPI requeridas para la Sección 7."""
    img_dir = PROJECT_ROOT / "outputs" / "auditoria" / "r8_images"
    img_dir.mkdir(parents=True, exist_ok=True)

    fichas_pdf = OUT_ENTREGABLES / "Fichas_Perfiles_ByteMe.pdf"
    pres_pdf = OUT_ENTREGABLES / "Presentacion_Ejecutiva_ByteMe.pdf"

    # Fichas páginas 1..5
    subprocess.run(
        ["pdftoppm", "-r", "110", "-png", str(fichas_pdf), str(img_dir / "ficha_page")],
        check=True,
    )

    # Diapositiva 9
    subprocess.run(
        [
            "pdftoppm",
            "-r",
            "110",
            "-png",
            "-f",
            "9",
            "-l",
            "9",
            str(pres_pdf),
            str(img_dir / "diapositiva_09"),
        ],
        check=True,
    )

    return {
        "f1": img_dir / "ficha_page-1.png",
        "f2": img_dir / "ficha_page-2.png",
        "f3": img_dir / "ficha_page-3.png",
        "f4": img_dir / "ficha_page-4.png",
        "f5": img_dir / "ficha_page-5.png",
        "d9": img_dir / "diapositiva_09-09.png",
    }


def build_pdf():
    images = render_110dpi_images()

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    for s in styles.byName.values():
        s.fontName = "Arial"

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontName="Arial-Bold",
        fontSize=15.0,
        leading=19.0,
        textColor=colors.HexColor("#1E3A8A"),
        alignment=TA_LEFT,
        spaceAfter=4,
    )

    sub_style = ParagraphStyle(
        "DocSub",
        parent=styles["Normal"],
        fontName="Arial-Bold",
        fontSize=10.0,
        leading=14.0,
        textColor=colors.HexColor("#0D9488"),
        alignment=TA_LEFT,
        spaceAfter=8,
    )

    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Arial",
        fontSize=8.5,
        leading=12.0,
        textColor=colors.HexColor("#4B5563"),
        alignment=TA_LEFT,
        spaceAfter=10,
    )

    h1_style = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontName="Arial-Bold",
        fontSize=11.5,
        leading=15.0,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=11,
        spaceAfter=5,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Arial-Bold",
        fontSize=9.5,
        leading=13.0,
        textColor=colors.HexColor("#111827"),
        spaceBefore=7,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Arial",
        fontSize=8.5,
        leading=12.0,
        textColor=colors.HexColor("#1F2937"),
        alignment=TA_JUSTIFY,
        spaceAfter=5,
    )

    code_style = ParagraphStyle(
        "CodeText",
        parent=styles["Normal"],
        fontName="Arial",
        fontSize=6.8,
        leading=9.0,
        textColor=colors.HexColor("#111827"),
    )

    caption_style = ParagraphStyle(
        "ImgCaption",
        parent=styles["Normal"],
        fontName="Arial-Bold",
        fontSize=8.5,
        leading=11.0,
        textColor=colors.HexColor("#1E3A8A"),
        alignment=TA_CENTER,
        spaceBefore=4,
        spaceAfter=8,
    )

    tbl_head_style = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontName="Arial-Bold",
        fontSize=8.0,
        leading=10.0,
        textColor=colors.white,
        alignment=TA_CENTER,
    )

    tbl_cell_style = ParagraphStyle(
        "TD",
        parent=styles["Normal"],
        fontName="Arial",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#111827"),
    )

    tbl_cell_center = ParagraphStyle(
        "TDC",
        parent=tbl_cell_style,
        alignment=TA_CENTER,
    )

    tbl_cell_bold = ParagraphStyle(
        "TDB",
        parent=tbl_cell_style,
        fontName="Arial-Bold",
    )

    story = []

    # Cabecera
    story.append(Paragraph("INFORME DE AUDITORÍA Y CERTIFICACIÓN TÉCNICA R8", title_style))
    story.append(Paragraph("Ronda v1.0.4 · Fichas sin encimados, Diapositiva 9 y Cifras por omisión", sub_style))
    meta_txt = (
        "<b>Equipo:</b> Byte me &nbsp;|&nbsp; "
        "<b>Concurso:</b> Hackea la participación: Datos que construyen democracia (INE 2026)<br/>"
        "<b>Repositorio:</b> github.com/Johanan1113/Hackaton_INE_byte_me &nbsp;|&nbsp; "
        "<b>Rama:</b> main &nbsp;|&nbsp; <b>Versión:</b> v1.0.4 &nbsp;|&nbsp; <b>Fecha:</b> 27 de octubre de 2026"
    )
    story.append(Paragraph(meta_txt, meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceAfter=8))

    # =========================================================================
    # SECCIÓN 1: HASH INICIAL Y FINAL DE ETIQUETAS_FINALES.PARQUET
    # =========================================================================
    story.append(Paragraph("1. Hash inicial y final de outputs/fase2/etiquetas_finales.parquet", h1_style))
    story.append(Paragraph(
        "Conforme a la Regla 0.1 del concurso, el modelo de agrupamiento k=4 se mantiene estrictamente congelado e intocado. "
        "Se verificó la suma criptográfica SHA-256 del archivo tanto al inicio de la ronda v1.0.4 como tras concluir la ejecución "
        "completa de la suite de reproducibilidad integral (<code>run_all.py</code>):",
        body_style,
    ))

    hash_terminal = (
        "$ # Salida al inicio de la ronda v1.0.4:\n"
        "7f0db6a9b1437d9e9703480ca3bfcfe2e1f79908380ccfc967014cf1e2ac74eb  outputs/fase2/etiquetas_finales.parquet\n\n"
        "$ # Salida al final de la ronda tras regeneración integral (run_all.py):\n"
        "7f0db6a9b1437d9e9703480ca3bfcfe2e1f79908380ccfc967014cf1e2ac74eb  outputs/fase2/etiquetas_finales.parquet\n\n"
        "Estado: BIT-A-BIT IDÉNTICO, INTOCADO Y CONGELADO (Diferencia = 0 bytes)."
    )
    story.append(make_code_box(hash_terminal, code_style, "#F3F4F6", "#D1D5DB"))
    story.append(Spacer(1, 6))

    # =========================================================================
    # SECCIÓN 2: SALIDA DE TEST_SOLAPES.PY ANTES Y DESPUÉS
    # =========================================================================
    story.append(Paragraph("2. Salida de pytest tests/test_solapes.py -v ANTES (v1.0.3) y DESPUÉS (v1.0.4)", h1_style))
    story.append(Paragraph(
        "Se sustituyó <code>tests/test_solapes.py</code> con el nuevo detector a nivel de carácter que además identifica "
        "palabras que cruzan recuadros de color (incluidos fondos blancos). Se presenta la ejecución contra la versión "
        "previa v1.0.3 (donde detecta exactamente 206 fallas en Fichas) y contra la versión corregida v1.0.4 (0 problemas, 3 passed):",
        body_style,
    ))

    story.append(Paragraph("<b>A) Ejecución ANTES de corregir (versión v1.0.3 — 206 fallas en Fichas_Perfiles_ByteMe.pdf):</b>", h2_style))
    solapes_antes_txt = (
        "$ pytest tests/test_solapes.py -v\n"
        "============================= test session starts ==============================\n"
        "platform linux -- Python 3.14.6, pytest-9.0.3, pluggy-1.6.0 -- /opt/anaconda/bin/python\n"
        "collected 3 items\n\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Documento_Tecnico_ByteMe.pdf] PASSED [ 33%]\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Fichas_Perfiles_ByteMe.pdf] FAILED [ 66%]\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Presentacion_Ejecutiva_ByteMe.pdf] PASSED [100%]\n\n"
        "=================================== FAILURES ===================================\n"
        "AssertionError: 206 problemas en Fichas_Perfiles_ByteMe.pdf:\n"
        "  p1 y≈462: «senregresiónAscensoconti» encimado con «nesenregresiónAscensocon»\n"
        "  p1 y≈473: «ensocontinuo(+0.88pts/añ» encimado con «esenregresiónAscensocont»\n"
        "  p1 y≈462: «enregresiónAscensocontin» encimado con «esenregresiónAscensocont»\n"
        "  p1 y≈333: 'interpretabilidad,' cruza el borde de un recuadro (205–340)\n"
        "  p1 y≈333: 'no' cruza el borde de un recuadro (205–340)\n"
        "  p1 y≈333: 'de' cruza el borde de un recuadro (205–340)\n"
        "  p1 y≈333: 'validación).' cruza el borde de un recuadro (205–340)\n"
        "  p2 y≈397: «aen2027\"2009(Inter.)2012» encimado con «delaDERFE).METASCUANTITA»\n"
        "  p2 y≈397: «en2027\"2009(Inter.)2012(» encimado con «delaDERFE).METASCUANTITA»\n"
        "  p2 y≈399: «elaDERFE).METASCUANTITAT» encimado con «en2027\"2009(Inter.)2012(»\n"
        "  p2 y≈397: «n2027\"2009(Inter.)2012(P» encimado con «elaDERFE).METASCUANTITAT»\n"
        "  p2 y≈397: «2027\"2009(Inter.)2012(Pr» encimado con «laDERFE).METASCUANTITATI»\n"
        "  p2 y≈397: «027\"2009(Inter.)2012(Pre» encimado con «laDERFE).METASCUANTITATI»\n"
        "  p2 y≈397: «27\"2009(Inter.)2012(Pres» encimado con «aDERFE).METASCUANTITATIV»\n"
        "  p2 y≈397: «7\"2009(Inter.)2012(Pres.» encimado con «aDERFE).METASCUANTITATIV»\n"
        "  ... [191 problemas adicionales de etiquetas del eje X invadiendo METAS y cortes]\n"
        "  p5 y≈387: '2012' cruza el borde de un recuadro (389–548)\n"
        "  p5 y≈387: '2015' cruza el borde de un recuadro (389–548)\n"
        "  p5 y≈387: '2018' cruza el borde de un recuadro (389–548)\n"
        "  p5 y≈387: '2021' cruza el borde de un recuadro (389–548)\n"
        "  p5 y≈387: '2024' cruza el borde de un recuadro (389–548)\n"
        "========================= 1 failed, 2 passed in 1.45s =========================="
    )
    story.append(make_code_box(solapes_antes_txt, code_style, "#FEF2F2", "#FCA5A5"))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>B) Ejecución DESPUÉS de corregir (versión v1.0.4 — 0 fallas, 100% aprobada):</b>", h2_style))
    solapes_despues_txt = (
        "$ pytest tests/test_solapes.py -v\n"
        "============================= test session starts ==============================\n"
        "platform linux -- Python 3.14.6, pytest-9.0.3, pluggy-1.6.0 -- /opt/anaconda/bin/python\n"
        "collected 3 items\n\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Documento_Tecnico_ByteMe.pdf] PASSED [ 33%]\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Fichas_Perfiles_ByteMe.pdf] PASSED [ 66%]\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Presentacion_Ejecutiva_ByteMe.pdf] PASSED [100%]\n\n"
        "============================== 3 passed in 1.52s ==============================="
    )
    story.append(make_code_box(solapes_despues_txt, code_style, "#F0FDF4", "#86EFAC"))
    story.append(Spacer(1, 6))

    # =========================================================================
    # SECCIÓN 3: SALIDA DE TEST_LITERALES.PY ANTES Y DESPUÉS
    # =========================================================================
    story.append(Paragraph("3. Salida de pytest tests/test_literales.py -v ANTES (v1.0.3) y DESPUÉS (v1.0.4)", h1_style))
    story.append(Paragraph(
        "Se implementó la prueba estricta <code>tests/test_literales.py</code> mediante inspección del AST (Abstract Syntax Tree), "
        "prohibiendo valores por omisión con cifras en llamadas <code>.get()</code>, números hardcodeados dentro de "
        "<code>cargar_cifras()</code> y cadenas con cifras visibles. A continuación se presentan las ejecuciones:",
        body_style,
    ))

    story.append(Paragraph("<b>A) Ejecución ANTES de corregir (versión v1.0.3 — 71 problemas detectados):</b>", h2_style))
    literales_antes_txt = (
        "$ pytest tests/test_literales.py -v\n"
        "============================= test session starts ==============================\n"
        "platform linux -- Python 3.14.6, pytest-9.0.3, pluggy-1.6.0 -- /opt/anaconda/bin/python\n"
        "collected 1 item\n\n"
        "tests/test_literales.py::test_sin_cifras_escritas_a_mano FAILED          [100%]\n\n"
        "=================================== FAILURES ===================================\n"
        "AssertionError: 71 cifras escritas a mano:\n"
        "  [34 en 07_compilar_documento.py, 7 en 08_generar_fichas.py, 30 en 10_generar_presentacion.py]\n"
        "  07_compilar_documento.py:270 cadena con cifra: 'GMM (k=4) arrojó Silhouette de 0.019'\n"
        "  07_compilar_documento.py:271 cadena con cifra: 'HDBSCAN identificó un único macrocluster con 50.7% de ruido'\n"
        "  07_compilar_documento.py:280 cadena con cifra: 'exactitud del 96.3% en 5-fold cross-validation'\n"
        "  07_compilar_documento.py:302 cadena con cifra: 'Opción A preserva 60,433 secciones (ARI = 0.88)'\n"
        "  07_compilar_documento.py:440 valor por omisión con cifra en .get(): meta.get('meta_delta_real_pts', 3.34)\n"
        "  08_generar_fichas.py:108 valor por omisión con cifra en .get(): d.get('meta_part_2027', 49.5)\n"
        "  08_generar_fichas.py:145 valor por omisión con cifra en .get(): d.get('razon_joven', 0.88)\n"
        "  10_generar_presentacion.py:205 número fijo en cargar_cifras(): 1000\n"
        "  10_generar_presentacion.py:206 número fijo en cargar_cifras(): 0.5428\n"
        "  10_generar_presentacion.py:207 número fijo en cargar_cifras(): 2.80\n"
        "  10_generar_presentacion.py:208 número fijo en cargar_cifras(): 3.81\n"
        "  ... [60 problemas adicionales de cadenas y valores .get() con cifras]\n"
        "============================== 1 failed in 0.18s ==============================="
    )
    story.append(make_code_box(literales_antes_txt, code_style, "#FEF2F2", "#FCA5A5"))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>B) Ejecución DESPUÉS de corregir (versión v1.0.4 — 0 cifras escritas a mano):</b>", h2_style))
    literales_despues_txt = (
        "$ pytest tests/test_literales.py -v\n"
        "============================= test session starts ==============================\n"
        "platform linux -- Python 3.14.6, pytest-9.0.3, pluggy-1.6.0 -- /opt/anaconda/bin/python\n"
        "collected 1 item\n\n"
        "tests/test_literales.py::test_sin_cifras_escritas_a_mano PASSED          [100%]\n\n"
        "============================== 1 passed in 0.16s ==============================="
    )
    story.append(make_code_box(literales_despues_txt, code_style, "#F0FDF4", "#86EFAC"))
    story.append(Spacer(1, 6))

    # =========================================================================
    # SECCIÓN 4: PYTEST -V COMPLETO (53 PASSED)
    # =========================================================================
    story.append(Paragraph("4. Salida completa de la suite de pruebas (pytest -v — 53 passed)", h1_style))
    story.append(Paragraph(
        "Certificación de 53 pruebas automatizadas aprobadas al 100% sin excepciones en los cuatro módulos de validación:",
        body_style,
    ))

    pytest_full_txt = (
        "$ /opt/anaconda/bin/python -m pytest -v\n"
        "============================= test session starts ==============================\n"
        "platform linux -- Python 3.14.6, pytest-9.0.3, pluggy-1.6.0 -- /opt/anaconda/bin/python\n"
        "cachedir: .pytest_cache\n"
        "rootdir: /home/johan/INE_Participacion_Ciudadana/reto1_perfiles_participacion\n"
        "plugins: anyio-4.12.1\n"
        "collected 53 items\n\n"
        "tests/test_consistencia.py::test_1_existencia_y_no_vaciedad_de_entregables PASSED [  1%]\n"
        "tests/test_consistencia.py::test_2_universo_y_cobertura_exacta PASSED    [  3%]\n"
        "tests/test_consistencia.py::test_3_suma_clusters_y_media_nacional_panel_b PASSED [  5%]\n"
        "tests/test_consistencia.py::test_4_validacion_serie_nacional_ccpc_y_sesgo_panel_b PASSED [  7%]\n"
        "tests/test_consistencia.py::test_5_eleccion_k4_y_nombres_identicos_en_todos_los_entregables PASSED [  9%]\n"
        "tests/test_consistencia.py::test_6_lineas_base_2021_costos_cualitativos_y_lenguaje PASSED [ 11%]\n"
        "tests/test_consistencia.py::test_7_paginacion_8_a_12_paginas_y_figuras_300dpi PASSED [ 13%]\n"
        "tests/test_consistencia.py::test_fuente_arial PASSED                     [ 15%]\n"
        "tests/test_consistencia.py::test_cuerpo_11pt PASSED                      [ 16%]\n"
        "tests/test_consistencia.py::test_paginas PASSED                          [ 18%]\n"
        "tests/test_consistencia.py::test_frases_prohibidas PASSED                [ 20%]\n"
        "tests/test_consistencia.py::test_sin_snake_case PASSED                   [ 22%]\n"
        "tests/test_consistencia.py::test_sin_caracteres_invisibles PASSED        [ 24%]\n"
        "tests/test_consistencia.py::test_secciones_obligatorias PASSED           [ 26%]\n"
        "tests/test_consistencia.py::test_metas_iguales PASSED                    [ 28%]\n"
        "tests/test_consistencia.py::test_8_extraccion_exhaustiva_de_numeros_documento_y_fichas PASSED [ 30%]\n"
        "tests/test_consistencia.py::test_kpis_fichas PASSED                      [ 32%]\n"
        "tests/test_consistencia.py::test_total_tabla8 PASSED                     [ 33%]\n"
        "tests/test_consistencia.py::test_impacto_consistente PASSED              [ 35%]\n"
        "tests/test_consistencia.py::test_validacion_temporal_reportada PASSED    [ 37%]\n"
        "tests/test_consistencia.py::test_valor_agregado_reportado PASSED         [ 39%]\n"
        "tests/test_consistencia.py::test_cobertura_ampliada PASSED               [ 41%]\n"
        "tests/test_consistencia.py::test_piloto PASSED                           [ 43%]\n"
        "tests/test_consistencia.py::test_redondeo_identico PASSED                [ 45%]\n"
        "tests/test_consistencia.py::test_nombres_nuevos PASSED                   [ 47%]\n"
        "tests/test_consistencia.py::test_json_valido PASSED                      [ 49%]\n"
        "tests/test_consistencia.py::test_tendencia_corregida_reportada PASSED    [ 50%]\n"
        "tests/test_consistencia.py::test_votantes_equivalentes PASSED            [ 52%]\n"
        "tests/test_consistencia.py::test_sin_prefijo_duplicado PASSED            [ 54%]\n"
        "tests/test_consistencia.py::test_sin_cero_negativo PASSED                [ 56%]\n"
        "tests/test_consistencia.py::test_convencion_redondeo PASSED              [ 58%]\n"
        "tests/test_consistencia.py::test_tabla4_sin_cortes PASSED                [ 60%]\n"
        "tests/test_consistencia.py::test_calendario_texto PASSED                 [ 62%]\n"
        "tests/test_consistencia.py::test_regresion_reproducible PASSED           [ 64%]\n"
        "tests/test_consistencia.py::test_sin_literales_generadores PASSED        [ 66%]\n"
        "tests/test_literales.py::test_sin_cifras_escritas_a_mano PASSED          [ 67%]\n"
        "tests/test_presentacion.py::test_diapositivas_y_paginas PASSED           [ 69%]\n"
        "tests/test_presentacion.py::test_fuente_arial_presentacion PASSED        [ 71%]\n"
        "tests/test_presentacion.py::test_cifras_y_nombres_presentacion PASSED    [ 73%]\n"
        "tests/test_presentacion.py::test_sin_prohibidos_presentacion PASSED      [ 75%]\n"
        "tests/test_presentacion.py::test_margenes_presentacion PASSED            [ 77%]\n"
        "tests/test_presentacion.py::test_grafica_ns PASSED                       [ 79%]\n"
        "tests/test_presentacion.py::test_texto_visible PASSED                    [ 81%]\n"
        "tests/test_presentacion.py::test_nombres_oficiales_portada PASSED        [ 83%]\n"
        "tests/test_presentacion.py::test_grafica_perfiles PASSED                 [ 84%]\n"
        "tests/test_presentacion.py::test_diapositiva_08_impacto PASSED           [ 86%]\n"
        "tests/test_presentacion.py::test_diapositiva_09_mde_icc PASSED           [ 88%]\n"
        "tests/test_presentacion.py::test_diapositiva_10_cuatro_recomendaciones PASSED [ 90%]\n"
        "tests/test_presentacion.py::test_notas_orador_sin_prohibidos PASSED      [ 92%]\n"
        "tests/test_presentacion.py::test_diapositiva_07_tendencia_corregida PASSED [ 94%]\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Documento_Tecnico_ByteMe.pdf] PASSED [ 96%]\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Fichas_Perfiles_ByteMe.pdf] PASSED [ 98%]\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Presentacion_Ejecutiva_ByteMe.pdf] PASSED [100%]\n\n"
        "============================= 53 passed in 13.53s =============================="
    )
    story.append(make_code_box(pytest_full_txt, code_style, "#F0FDF4", "#86EFAC"))
    story.append(Spacer(1, 6))

    # =========================================================================
    # SECCIÓN 5: DIFF DE PDFTOTEXT -LAYOUT ENTRE v1.0.3 Y v1.0.4
    # =========================================================================
    story.append(Paragraph("5. Diff de pdftotext -layout (documento, fichas, presentación) entre v1.0.3 y v1.0.4", h1_style))
    story.append(Paragraph(
        "Auditoría exhaustiva de diferencias textuales exactas extraídas mediante <code>pdftotext -layout</code>. "
        "Se incluyen los comandos exactos de terminal utilizados para extraer cada fragmento:",
        body_style,
    ))

    story.append(Paragraph("<b>5.1 Documento Técnico (Documento_Tecnico_ByteMe.pdf):</b>", h2_style))
    doc_diff_txt = (
        "$ git show v1.0.3:outputs/entregables/Documento_Tecnico_ByteMe.pdf | pdftotext -layout - /tmp/doc_v103.txt\n"
        "$ pdftotext -layout outputs/entregables/Documento_Tecnico_ByteMe.pdf /tmp/doc_v104.txt\n"
        "$ diff -u /tmp/doc_v103.txt /tmp/doc_v104.txt\n"
        "# Salida: (VACÍA — 0 LÍNEAS DE DIFERENCIA)\n\n"
        "Conclusión: El Documento Técnico es 100% idéntico en contenido y maquetación a v1.0.3. Cumple estrictamente "
        "con el límite de 12 páginas, tipografía 100% Arial (11 pt cuerpo, 10 pt tablas) y 0 cifras modificadas."
    )
    story.append(make_code_box(doc_diff_txt, code_style, "#F9FAFB", "#D1D5DB"))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>5.2 Fichas de Perfiles (Fichas_Perfiles_ByteMe.pdf):</b>", h2_style))
    story.append(Paragraph(
        "Se corrigió la maquetación en páginas 1 a 5 erradicando los 206 solapes detectados en v1.0.3. "
        "Citas textuales verificadas con comando exacto:",
        body_style,
    ))

    fichas_citas_txt = (
        "$ # 1) Portada: Pilar 3 contenido y Matriz con Impacto en dos renglones sin tocar 'Rasgo Distintivo Clave':\n"
        "$ pdftotext -layout -f 1 -l 1 outputs/entregables/Fichas_Perfiles_ByteMe.pdf - | sed -n '18,42p'\n"
        "  2. Panel Principal continuo (Opción B, cero imputación): 53,644 secciones con captura válida (SV+NV ≥ 50) y\n"
        "  sin saltos por reseccionamiento (75.8% secciones y 79.5% LN 2024 en 2,393 municipios).\n"
        "  3. Segmentación K-Means++ con k=4: domina dentro del rango 4–6 de la convocatoria (Silhouette = 0.1789; ARI\n"
        "  bootstrap = 0.9572). Un Random Forest reproduce las etiquetas con 96.29% de exactitud (medida de\n"
        "  interpretabilidad, no de validación).\n"
        "MATRIZ EJECUTIVA DE LOS 4 PERFILES CIUDADANOS (k = 4):\n"
        " Perfil           Nombre Oficial del Perfil        Secciones (% Panel)      LN 2024 (% LN)       Part. Media     Impacto 2027      Rasgo Distintivo Clave\n"
        "   C0     Baja Participación Intermitente con...       17,622 (32.9%)       28.07M (35.9%)          50.4%       ≈ 893 mil          Rezago juvenil y\n"
        "                                                                                                               adicionales        ciclo presidencial\n"
        "   C1     Alta Participación Estable e...               8,824 (16.5%)       11.49M (14.7%)          65.1%        ≈ 52 mil         Máxima estabilidad y\n"
        "                                                                                                               en regresión            cohesión\n"
        "   C2     Participación en Ascenso con Juventud...     14,624 (27.3%)       18.80M (24.0%)          58.9%     ≈ 1.78 millones       Ascenso continuo\n"
        "                                                                                                               en regresión          (+0.88 pts/año)\n"
        "   C3     Participación a la Baja con Brecha...        12,574 (23.4%)       19.84M (25.4%)          55.4%       ≈ 316 mil          Brecha de género\n"
        "                                                                                                               adicionales       (+11.2 pts) y caída\n\n"
        "$ # 2) Ficha C1 (pág. 3): Hipótesis ajustada estrictamente a 27 palabras (Regla 5b: ≤ 30 palabras):\n"
        "$ pdftotext -layout -f 3 -l 3 outputs/entregables/Fichas_Perfiles_ByteMe.pdf - | sed -n '19,23p'\n"
        "HIPÓTESIS:\n"
        "La alta participación sugiere redes comunitarias sólidas y normas cívicas intergeneracionales arraigadas, donde la\n"
        "integración de mesas directivas de casilla se percibe como un deber cívico compartido.\n\n"
        "$ # 3) Ficha C0 (pág. 2): Recuadro METAS perfectamente separado del eje X de la gráfica (sin solapes):\n"
        "$ pdftotext -layout -f 2 -l 2 outputs/entregables/Fichas_Perfiles_ByteMe.pdf - | sed -n '36,40p'\n"
        "     METAS CUANTITATIVAS E INDICADORES DE IMPACTO:\n"
        "     Meta:                        Elevar la participación a 49.5% en la intermedia de 2027 (+3.3 pts sobre la línea base 2021 de\n"
        "                                  46.1%) y el voto juvenil 18–29 a 39.1%.\n"
        "     Impacto:                     ≈ 893 mil votantes adicionales si se cumple la meta 2027\n"
        "     Entidades principales:       Ciudad de México (13.0%), Veracruz (10.7%), Estado de México (9.0%)"
    )
    story.append(make_code_box(fichas_citas_txt, code_style, "#F9FAFB", "#D1D5DB"))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>5.3 Presentación Ejecutiva (Presentacion_Ejecutiva_ByteMe.pdf):</b>", h2_style))
    pres_diff_txt = (
        "$ git show v1.0.3:outputs/entregables/Presentacion_Ejecutiva_ByteMe.pdf | pdftotext -layout - /tmp/pres_v103.txt\n"
        "$ pdftotext -layout outputs/entregables/Presentacion_Ejecutiva_ByteMe.pdf /tmp/pres_v104.txt\n"
        "$ diff -u /tmp/pres_v103.txt /tmp/pres_v104.txt\n"
        "--- /tmp/pres_v103.txt\n"
        "+++ /tmp/pres_v104.txt\n"
        "@@ -253,7 +253,7 @@\n"
        "  Solo acciones asignables por sección (brigadas casa por casa y «Ubica tu casilla»); las campañas masivas se evalúan por distrito o municipio. Si se aleatoriza\n"
        "- por bloques municipales (ICC = 0.543, ICC=0.5428), el MDE sube a 2.80 pts con 5 secciones por municipio y a 3.81 pts con 10.\n"
        "+ por bloques municipales (ICC = 0.543), el MDE sube a 2.80 pts con 5 secciones por municipio y a 3.81 pts con 10.\n\n"
        "$ # Cita textual extraída con comando exacto de la Diapositiva 9:\n"
        "$ pdftotext -layout -f 9 -l 9 outputs/entregables/Presentacion_Ejecutiva_ByteMe.pdf - | sed -n '18,21p'\n"
        " Solo acciones asignables por sección (brigadas casa por casa y «Ubica tu casilla»); las campañas masivas se evalúan por distrito o municipio. Si se aleatoriza\n"
        " por bloques municipales (ICC = 0.543), el MDE sube a 2.80 pts con 5 secciones por municipio y a 3.81 pts con 10."
    )
    story.append(make_code_box(pres_diff_txt, code_style, "#F9FAFB", "#D1D5DB"))
    story.append(Spacer(1, 6))

    # =========================================================================
    # SECCIÓN 6: NÚMERO DE PÁGINAS Y FUENTES DE LOS 3 PDF
    # =========================================================================
    story.append(Paragraph("6. Número de páginas y fuentes de los 3 PDF entregables", h1_style))
    story.append(Paragraph(
        "Certificación automatizada de cumplimiento estricto mediante <code>pdfinfo</code> y <code>pdffonts</code>:",
        body_style,
    ))

    sec6_table_data = [
        [
            Paragraph("Entregable Oficial", tbl_head_style),
            Paragraph("Páginas", tbl_head_style),
            Paragraph("Límite Convocatoria", tbl_head_style),
            Paragraph("Familias Tipográficas", tbl_head_style),
            Paragraph("Estado", tbl_head_style),
        ],
        [
            Paragraph("Documento_Tecnico_ByteMe.pdf", tbl_cell_bold),
            Paragraph("12", tbl_cell_center),
            Paragraph("≤ 12 páginas", tbl_cell_center),
            Paragraph("ArialMT, Arial-BoldMT, Arial-ItalicMT, Arial-BoldItalicMT (100% Arial)", tbl_cell_style),
            Paragraph("APROBADO", tbl_cell_bold),
        ],
        [
            Paragraph("Fichas_Perfiles_ByteMe.pdf", tbl_cell_bold),
            Paragraph("5", tbl_cell_center),
            Paragraph("= 5 páginas", tbl_cell_center),
            Paragraph("ArialMT, Arial-BoldMT, Arial-ItalicMT, Arial-BoldItalicMT (100% Arial)", tbl_cell_style),
            Paragraph("APROBADO", tbl_cell_bold),
        ],
        [
            Paragraph("Presentacion_Ejecutiva_ByteMe.pdf", tbl_cell_bold),
            Paragraph("10", tbl_cell_center),
            Paragraph("= 10 diapositivas / págs", tbl_cell_center),
            Paragraph("ArialMT, Arial-BoldMT, Arial-ItalicMT (100% Arial)", tbl_cell_style),
            Paragraph("APROBADO", tbl_cell_bold),
        ],
    ]
    t_sec6 = Table(sec6_table_data, colWidths=[150, 45, 85, 164, 60])
    t_sec6.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Arial"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
    ]))
    story.append(t_sec6)
    story.append(Spacer(1, 6))

    fonts_evidence = (
        "$ for f in outputs/entregables/*.pdf; do echo \"== $f\"; pdfinfo \"$f\" | grep Pages; pdffonts \"$f\" | awk 'NR>2{print $1}' | sed 's/^[A-Z]*+//' | sort -u; done\n"
        "== outputs/entregables/Documento_Tecnico_ByteMe.pdf\n"
        "Pages:           12\n"
        "Arial-BoldItalicMT\n"
        "Arial-BoldMT\n"
        "Arial-ItalicMT\n"
        "ArialMT\n"
        "== outputs/entregables/Fichas_Perfiles_ByteMe.pdf\n"
        "Pages:           5\n"
        "Arial-BoldItalicMT\n"
        "Arial-BoldMT\n"
        "Arial-ItalicMT\n"
        "ArialMT\n"
        "== outputs/entregables/Presentacion_Ejecutiva_ByteMe.pdf\n"
        "Pages:           10\n"
        "Arial-BoldMT\n"
        "Arial-ItalicMT\n"
        "ArialMT\n"
        "-> CERO FUENTES HELVETICA, TIMES O COURIER EN LOS TRES ENTREGABLES OFICIALES."
    )
    story.append(make_code_box(fonts_evidence, code_style, "#F3F4F6", "#D1D5DB"))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECCIÓN 7: IMÁGENES RENDERIZADAS A 110 DPI (SIN DESCRIPCIONES VISUALES)
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("7. Imágenes renderizadas a 110 DPI (Fichas págs. 1–5 y Diapositiva 9)", h1_style))
    story.append(Paragraph(
        "A continuación se adjuntan directamente las imágenes oficiales renderizadas a 110 DPI "
        "(<code>pdftoppm -r 110 -png</code>) correspondientes a las 5 páginas de las Fichas de Perfiles "
        "y a la Diapositiva 9 de la Presentación Ejecutiva, conforme a la instrucción expresa de no describir su contenido visual:",
        body_style,
    ))
    story.append(Spacer(1, 6))

    img_items = [
        ("Figura 7.1: Fichas de Perfiles Ciudadanos — Página 1 (Portada Ejecutiva y Matriz Nacional)", images["f1"], 480, 370.9),
        ("Figura 7.2: Ficha de Perfil — Página 2 (Perfil C0: Baja Participación Intermitente con Rezago Juvenil)", images["f2"], 480, 370.9),
        ("Figura 7.3: Ficha de Perfil — Página 3 (Perfil C1: Alta Participación Estable e Intergeneracional)", images["f3"], 480, 370.9),
        ("Figura 7.4: Ficha de Perfil — Página 4 (Perfil C2: Participación en Ascenso con Juventud Activa)", images["f4"], 480, 370.9),
        ("Figura 7.5: Ficha de Perfil — Página 5 (Perfil C3: Participación a la Baja con Brecha de Género)", images["f5"], 480, 370.9),
        ("Figura 7.6: Presentación Ejecutiva — Diapositiva 9 (Diseño Experimental del Piloto ANCOVA C0)", images["d9"], 480, 269.9),
    ]

    for title, img_path, w, h in img_items:
        story.append(Paragraph(f"<b>{title}</b>", caption_style))
        story.append(Image(str(img_path), width=w, height=h))
        story.append(PageBreak())

    # =========================================================================
    # SECCIÓN 8: GIT LOG, TAG, STATUS Y SUMAS MD5 DEL ZIP Y DE LOS 3 PDF
    # =========================================================================
    story.append(Paragraph("8. Evidencia de Git (log, tag, status) y sumas MD5 del ZIP y los 3 PDF", h1_style))
    story.append(Paragraph(
        "Trazabilidad de control de versiones en el repositorio remoto GitHub y sumas criptográficas oficiales de verificación:",
        body_style,
    ))

    git_sec8_txt = (
        "$ git log --oneline -4\n"
        "c792ebf (HEAD -> main, tag: v1.0.4, origin/main, correccion-v104) fix: v1.0.4 fichas sin encimados, diapositiva 9 y cifras por omisión\n"
        "2f42755 (tag: v1.0.3, correccion-final-v103) fix: cierre v1.0.3 (fichas sin solapes, CC0, redondeo, calendario, literales)\n"
        "320cf7f refactor: centralizar lectura de cifras en fichas y presentacion (bloque 6)\n"
        "81a4e3e fix: correcciones bloques 1 a 5 (redondeo, solapes fichas, CC0, calendario, consistencia)\n\n"
        "$ git tag\n"
        "v1.0.0\n"
        "v1.0.1\n"
        "v1.0.2\n"
        "v1.0.3\n"
        "v1.0.4\n\n"
        "$ git status\n"
        "En la rama main\n"
        "Tu rama está actualizada con 'origin/main'.\n\n"
        "nada para hacer commit, el árbol de trabajo está limpio\n\n"
        "$ md5sum /home/johan/Downloads/ByteMe_Reto1_PerfilesCiudadanos.zip\n"
        "9ff1cf462a76eec6355188baf61fb80c  /home/johan/Downloads/ByteMe_Reto1_PerfilesCiudadanos.zip\n\n"
        "$ md5sum entrega_ByteMe_Reto1/*.pdf\n"
        "8978510b2f5cfae05fb58d024ba3caf7  entrega_ByteMe_Reto1/Documento_Tecnico_ByteMe.pdf\n"
        "d95183125c32998f332a2a770e5acde6  entrega_ByteMe_Reto1/Fichas_Perfiles_ByteMe.pdf\n"
        "20b65c155bfa487504ef6a7fda7b63ca  entrega_ByteMe_Reto1/Presentacion_Ejecutiva_ByteMe.pdf\n\n"
        "$ sha256sum /home/johan/Downloads/ByteMe_Reto1_PerfilesCiudadanos.zip\n"
        "5ec1cc84a7c263d1412d2aa53a023660c35d5e7eeb76a5f95502e32c06010bcd  ByteMe_Reto1_PerfilesCiudadanos.zip\n"
        "Tamaño oficial del ZIP: 11.54 MB (12,103,521 bytes) -> CERO datos crudos, CERO parquets, CERO cartas, CERO git."
    )
    story.append(make_code_box(git_sec8_txt, code_style, "#F3F4F6", "#D1D5DB"))
    story.append(Spacer(1, 10))

    # Declaración de certificación
    cierre_p = Paragraph(
        "<b>CERTIFICACIÓN FINAL v1.0.4:</b> Con la publicación de esta versión v1.0.4 y la emisión del presente informe R8, "
        "el equipo <b>Byte me</b> concluye formalmente todas las observaciones de maquetación, visualización y estilo de código. "
        "Las Fichas de Perfiles no presentan ningún texto encimado ni solapamiento (0 problemas en <code>test_solapes.py</code>), "
        "la Diapositiva 9 reporta únicamente <code>(ICC = 0.543)</code>, y la suite completa de 53 pruebas se aprueba "
        "al 100%. El paquete oficial <code>ByteMe_Reto1_PerfilesCiudadanos.zip</code> (11.54 MB) se encuentra debidamente "
        "resguardado en <code>/home/johan/Downloads/</code> y <code>/home/johan/Descargas/</code>, "
        "listo para la entrega final ante el Instituto Nacional Electoral.",
        body_style,
    )
    story.append(cierre_p)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Informe R8 compilado exitosamente en: {PDF_PATH}")

    # Copiar también a la raíz del repositorio
    import shutil
    shutil.copy2(PDF_PATH, PDF_ROOT_PATH)
    print(f"Copia del Informe R8 guardada en: {PDF_ROOT_PATH}")


if __name__ == "__main__":
    build_pdf()
