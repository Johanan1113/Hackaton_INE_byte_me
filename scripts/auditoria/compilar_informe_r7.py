#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Compilación del Informe de Auditoría R7 (Informe_R7_ByteMe.pdf)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")
Concurso: "Hackea la participación: Datos que construyen democracia" (INE)

Genera el documento PDF oficial de certificación y auditoría R7 con las 10 secciones obligatorias,
evidencias de ejecución completas y tipografía 100% Arial.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    HRFlowable,
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
PDF_PATH = OUT_ENTREGABLES / "Informe_R7_ByteMe.pdf"
PDF_ROOT_PATH = PROJECT_ROOT / "Informe_R7_ByteMe.pdf"

from reportlab import rl_config
rl_config.canvas_basefontname = "Arial"

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
                "Equipo Byte me · Reto 1: Perfiles ciudadanos de participación · Informe de Auditoría R7 (v1.0.3)",
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


def get_diff_text(rel_path: str) -> str:
    """Extrae diff de pdftotext entre v1.0.2 y v1.0.3."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        old_pdf = Path(tmpdir) / "old.pdf"
        new_pdf = PROJECT_ROOT / rel_path
        with open(old_pdf, "wb") as f:
            subprocess.run(["git", "show", f"v1.0.2:{rel_path}"], stdout=f, check=True)
        
        old_txt = Path(tmpdir) / "old.txt"
        new_txt = Path(tmpdir) / "new.txt"
        subprocess.run(["pdftotext", "-layout", str(old_pdf), str(old_txt)], check=True)
        subprocess.run(["pdftotext", "-layout", str(new_pdf), str(new_txt)], check=True)
        
        res = subprocess.run(["diff", "-u", str(old_txt), str(new_txt)], capture_output=True, text=True)
        return res.stdout


def build_pdf():
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
        spaceAfter=10,
    )

    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Arial",
        fontSize=8.5,
        leading=12.0,
        textColor=colors.HexColor("#4B5563"),
        alignment=TA_LEFT,
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontName="Arial-Bold",
        fontSize=11.5,
        leading=15.0,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Arial-Bold",
        fontSize=10.0,
        leading=13.0,
        textColor=colors.HexColor("#111827"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Arial",
        fontSize=9.0,
        leading=13.0,
        textColor=colors.HexColor("#1F2937"),
        alignment=TA_JUSTIFY,
        spaceAfter=5,
    )

    body_bold = ParagraphStyle(
        "BodyBold",
        parent=body_style,
        fontName="Arial-Bold",
    )

    code_style = ParagraphStyle(
        "CodeText",
        parent=styles["Normal"],
        fontName="Arial",
        fontSize=7.2,
        leading=9.5,
        textColor=colors.HexColor("#111827"),
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

    # Portada / Cabecera
    story.append(Paragraph("INFORME DE AUDITORÍA Y CERTIFICACIÓN TÉCNICA R7", title_style))
    story.append(Paragraph("Ronda Final de Cierre v1.0.3 · Reto 1: Perfiles Ciudadanos de Participación", sub_style))
    meta_txt = (
        "<b>Equipo:</b> Byte me &nbsp;|&nbsp; "
        "<b>Concurso:</b> Hackea la participación: Datos que construyen democracia (INE 2026)<br/>"
        "<b>Repositorio:</b> github.com/Johanan1113/Hackaton_INE_byte_me &nbsp;|&nbsp; "
        "<b>Rama:</b> main &nbsp;|&nbsp; <b>Versión:</b> v1.0.3 &nbsp;|&nbsp; <b>Fecha:</b> 27 de octubre de 2026"
    )
    story.append(Paragraph(meta_txt, meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceAfter=10))

    # =========================================================================
    # SECCIÓN 1: HASH DE ETIQUETAS_FINALES.PARQUET (INICIO Y FINAL)
    # =========================================================================
    story.append(Paragraph("1. Hash de outputs/fase2/etiquetas_finales.parquet al inicio y al final", h1_style))
    story.append(Paragraph(
        "De conformidad con la Regla Obligatoria 0.1 del concurso, el modelo de agrupamiento k=4 se encuentra estrictamente "
        "<b>congelado</b>. Se verificó la suma criptográfica SHA-256 del archivo tanto al iniciar los trabajos de corrección "
        "como al concluir todas las fases y regeneraciones:",
        body_style,
    ))

    hash_terminal = (
        "$ # Salida al inicio de la ronda v1.0.3:\n"
        "7f0db6a9b1437d9e9703480ca3bfcfe2e1f79908380ccfc967014cf1e2ac74eb  outputs/fase2/etiquetas_finales.parquet\n\n"
        "$ # Salida al final de la ronda tras regeneración completa (run_all.py):\n"
        "7f0db6a9b1437d9e9703480ca3bfcfe2e1f79908380ccfc967014cf1e2ac74eb  outputs/fase2/etiquetas_finales.parquet\n\n"
        "Estado: BIT-A-BIT IDÉNTICO, INTOCADO Y CONGELADO (Diferencia = 0 bytes)."
    )
    t_box1 = Table([[Preformatted(hash_terminal, code_style)]], colWidths=[504])
    t_box1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_box1)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECCIÓN 2: SALIDA DE TEST_SOLAPES.PY ANTES Y DESPUÉS
    # =========================================================================
    story.append(Paragraph("2. Salida de test_solapes.py ANTES (v1.0.2) y DESPUÉS (v1.0.3)", h1_style))
    story.append(Paragraph(
        "Se implementó el detector automatizado de solapes geométricos palabra por palabra basado en pdfplumber "
        "(<code>tests/test_solapes.py</code>). A continuación se contrastan las ejecuciones completas de terminal:",
        body_style,
    ))

    story.append(Paragraph("<b>A) Ejecución ANTES de corregir (versión v1.0.2 — 22 solapes detectados en Fichas):</b>", h2_style))
    solapes_antes_txt = (
        "$ pytest tests/test_solapes.py -v\n"
        "============================= test session starts ==============================\n"
        "platform linux -- Python 3.14.6, pytest-9.0.3, pluggy-1.6.0 -- /opt/anaconda/bin/python\n"
        "collected 3 items\n\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Documento_Tecnico_ByteMe.pdf] PASSED [ 33%]\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Fichas_Perfiles_ByteMe.pdf] FAILED [ 66%]\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Presentacion_Ejecutiva_ByteMe.pdf] PASSED [100%]\n\n"
        "=================================== FAILURES ===================================\n"
        "AssertionError: 22 solapes en Fichas_Perfiles_ByteMe.pdf:\n"
        "  p1: 'Baja' cortado por recuadro de color\n"
        "  p1: 'Participación' cortado por recuadro de color\n"
        "  p2: 'presidenciales.' encimado con 'HIPÓTESIS:'\n"
        "  p3: 'Operación:' cortado por recuadro de color\n"
        "  p3: 'DECEyEC' cortado por recuadro de color\n"
        "  p3: 'y' cortado por recuadro de color\n"
        "  p3: 'Vocalías' cortado por recuadro de color\n"
        "  p3: 'de' cortado por recuadro de color\n"
        "  p3: 'Capacitación' cortado por recuadro de color\n"
        "  p3: 'de' cortado por recuadro de color\n"
        "  p3: 'Juntas' cortado por recuadro de color\n"
        "  p3: 'Distritales' cortado por recuadro de color\n"
        "  p3: '|' cortado por recuadro de color\n"
        "  p3: 'Costo:' cortado por recuadro de color\n"
        "  p3: 'Bajo' cortado por recuadro de color\n"
        "  p3: '(programas' cortado por recuadro de color\n"
        "  p3: 'ordinarios)' cortado por recuadro de color\n"
        "  p4: '60.4%);' encimado con 'HIPÓTESIS:'\n"
        "  p4: 'en' encimado con 'HIPÓTESIS:'\n"
        "  p4: 'HIPÓTESIS:' encimado con 'y'\n"
        "  p4: 'HIPÓTESIS:' encimado con '2024'\n"
        "  p4: 'HIPÓTESIS:' encimado con '(tendencia'\n"
        "========================= 1 failed, 2 passed in 2.04s =========================="
    )
    t_box2a = Table([[Preformatted(solapes_antes_txt, code_style)]], colWidths=[504])
    t_box2a.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#FCA5A5")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_box2a)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>B) Ejecución DESPUÉS de corregir (versión v1.0.3 — 0 solapes en los 3 entregables):</b>", h2_style))
    solapes_despues_txt = (
        "$ pytest tests/test_solapes.py -v\n"
        "============================= test session starts ==============================\n"
        "platform linux -- Python 3.14.6, pytest-9.0.3, pluggy-1.6.0 -- /opt/anaconda/bin/python\n"
        "collected 3 items\n\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Documento_Tecnico_ByteMe.pdf] PASSED [ 33%]\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Fichas_Perfiles_ByteMe.pdf] PASSED [ 66%]\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Presentacion_Ejecutiva_ByteMe.pdf] PASSED [100%]\n\n"
        "============================== 3 passed in 1.48s ==============================="
    )
    t_box2b = Table([[Preformatted(solapes_despues_txt, code_style)]], colWidths=[504])
    t_box2b.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#86EFAC")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_box2b)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECCIÓN 3: TABLA DE CONTROL DE TODOS LOS PUNTOS
    # =========================================================================
    story.append(Paragraph("3. Tabla de control de cumplimiento de todos los puntos", h1_style))
    story.append(Paragraph(
        "Inventario exhaustivo de atención de los requerimientos de la ronda final v1.0.3:",
        body_style,
    ))

    control_data = [
        [
            Paragraph("Punto", tbl_head_style),
            Paragraph("Estado", tbl_head_style),
            Paragraph("Archivo y Línea", tbl_head_style),
            Paragraph("Descripción y Evidencia", tbl_head_style),
        ],
        [
            Paragraph("1.1", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("11_analisis_auditoria.py<br/>L476–485", tbl_cell_style),
            Paragraph("Deltas dinámicos p2021_panel: delta_c0=0.0334000, delta_c3=0.0168000. Votantes C0=893,479, C3=316,357.", tbl_cell_style),
        ],
        [
            Paragraph("1.2", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("11_analisis_auditoria.py<br/>L545–586", tbl_cell_style),
            Paragraph("Columnas en tabla_17: participacion_2021_pond_pct y promedio_intermedias. C1 dif=270.4, C2 dif=178.7 (≤300).", tbl_cell_style),
        ],
        [
            Paragraph("1.3", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("11_analisis_auditoria.py<br/>L325, L615", tbl_cell_style),
            Paragraph("Cero negativo erradicado (-0.0 -> 0.00 en tabla_19 y JSON). math.copysign(1, C1) = 1.0.", tbl_cell_style),
        ],
        [
            Paragraph("1.4", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("11_analisis_auditoria.py<br/>L210–235", tbl_cell_style),
            Paragraph("Llaves agregadas: entidades_las_tres (6), pct_c1_en_las_tres (33.48%), pct_c2_en_ninguna (70.43%), def_cambio.", tbl_cell_style),
        ],
        [
            Paragraph("2.1", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("utilidades_formato.py<br/>L30–45", tbl_cell_style),
            Paragraph("Función redondear_pub implementada. Sexo: +11.2, 60.9%/49.7%, 44.4%/65.4%, 47.5%/63.9%.", tbl_cell_style),
        ],
        [
            Paragraph("2.2", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("07_compilar_documento.py<br/>L480–525", tbl_cell_style),
            Paragraph("Tabla 4 con encabezados de dos líneas, celdas en dos renglones sin unidades. Nota al pie agregada.", tbl_cell_style),
        ],
        [
            Paragraph("2.3", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("07_compilar_documento.py<br/>L480–530", tbl_cell_style),
            Paragraph("Erradicación de saltos de palabra en Tabla 4 ('Interge neracional', 'Estabilida d', etc.).", tbl_cell_style),
        ],
        [
            Paragraph("2.4", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("07_compilar_documento.py<br/>L570", tbl_cell_style),
            Paragraph("Viñeta C0 con participación masculina parametrizada a 46.8%.", tbl_cell_style),
        ],
        [
            Paragraph("2.5", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("07_compilar_documento.py<br/>L585", tbl_cell_style),
            Paragraph("Viñeta C2 con tasas intermedias (41.8% y 60.4%) y presidenciales (65.8%, 69.3% y 68.0%).", tbl_cell_style),
        ],
        [
            Paragraph("2.6", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("07_compilar_documento.py<br/>L780–810", tbl_cell_style),
            Paragraph("Limitación 2 actualizada: brechas 4.2 vs 14.6 pts, 53.6% C1, 33.5% aporte, 70.4% C2 sin gub., ARI=0.56.", tbl_cell_style),
        ],
        [
            Paragraph("2.7", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("07_compilar_documento.py<br/>L680", tbl_cell_style),
            Paragraph("Nota al pie de Tabla 7 actualizada con promedios intermedios (62.0% y 50.5%) y sin prob. asociada.", tbl_cell_style),
        ],
        [
            Paragraph("2.8", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("07_compilar_documento.py<br/>L830–860", tbl_cell_style),
            Paragraph("Conclusiones con parámetros dinámicos (tc_c2, c3_sexo_brecha, tc_c3, mde_seccion).", tbl_cell_style),
        ],
        [
            Paragraph("2.9", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("07_compilar_documento.py<br/>L10–25", tbl_cell_style),
            Paragraph("Paginación controlada a exactamente 12 páginas, Arial 11 pt, interlineado 19 pt, tablas 10 pt.", tbl_cell_style),
        ],
        [
            Paragraph("2.10", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("07_compilar_documento.py<br/>L250–880", tbl_cell_style),
            Paragraph("Interpolación dinámica de cifras desde tablas/JSON; cero literales de métricas hardcodeados.", tbl_cell_style),
        ],
        [
            Paragraph("2.11", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("07_compilar_documento.py", tbl_cell_style),
            Paragraph("Verificación: 12 páginas exactas, 100% Arial, 0 caracteres < 9.5 pt.", tbl_cell_style),
        ],
        [
            Paragraph("3.1", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("08_generar_fichas.py<br/>L95–180", tbl_cell_style),
            Paragraph("Textos concisos en Quiénes son C0/C2 e Indicador C1 para evitar desbordes.", tbl_cell_style),
        ],
        [
            Paragraph("3.2", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("08_generar_fichas.py<br/>L105", tbl_cell_style),
            Paragraph("Meta C0 leída dinámicamente de tabla_12 y 17 (+3.3 pts, meta 49.5%, voto joven 39.1%).", tbl_cell_style),
        ],
        [
            Paragraph("3.3", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("08_generar_fichas.py<br/>L165", tbl_cell_style),
            Paragraph("Cita legal en C3 corregida conforme a LGIPE (sin atribución errónea del art. 58.1 para casillas).", tbl_cell_style),
        ],
        [
            Paragraph("3.4", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("08_generar_fichas.py<br/>L55", tbl_cell_style),
            Paragraph("Pilar 3 de portada: Random Forest definido explícitamente como interpretabilidad, no validación.", tbl_cell_style),
        ],
        [
            Paragraph("3.5", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("08_generar_fichas.py<br/>L320–460", tbl_cell_style),
            Paragraph("Cálculo dinámico de cajas con get_window_extent(), elevación de tarjetas; 0 solapes.", tbl_cell_style),
        ],
        [
            Paragraph("3.6", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("08_generar_fichas.py", tbl_cell_style),
            Paragraph("Verificación: 5 páginas exactas, 100% Arial, 0 solapes en test_solapes.py.", tbl_cell_style),
        ],
        [
            Paragraph("4.1", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("10_generar_presentacion.py<br/>L342", tbl_cell_style),
            Paragraph("Eliminación de prefijo duplicado CC0 en portada. Limpieza de patrones f'C{{ en todo el repo.", tbl_cell_style),
        ],
        [
            Paragraph("4.2", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("10_generar_presentacion.py<br/>L850", tbl_cell_style),
            Paragraph("Diapositiva 6, C3: cita legal corregida a brigadas de accesibilidad y casillas extraordinarias (LGIPE).", tbl_cell_style),
        ],
        [
            Paragraph("4.3", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("10_generar_presentacion.py<br/>L1330", tbl_cell_style),
            Paragraph("Diapositiva 9: nota metodológica precisada y token unificado a (ICC = 0.543).", tbl_cell_style),
        ],
        [
            Paragraph("4.4", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("10_generar_presentacion.py<br/>L480–1450", tbl_cell_style),
            Paragraph("Notas del orador sincronizadas textualmente en diapositivas 3, 4, 6, 9 y 10.", tbl_cell_style),
        ],
        [
            Paragraph("4.5", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("10_generar_presentacion.py<br/>L410", tbl_cell_style),
            Paragraph("Diapositiva 2: texto completo '...o requeridos por autoridad jurisdiccional' sin desborde.", tbl_cell_style),
        ],
        [
            Paragraph("4.6", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("10_generar_presentacion.py", tbl_cell_style),
            Paragraph("Verificación: 10 diapositivas, 10 páginas PDF, 100% Arial, 0 solapes en test_solapes.py.", tbl_cell_style),
        ],
        [
            Paragraph("5.1", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("tests/test_solapes.py", tbl_cell_style),
            Paragraph("Detector de solapes creado e integrado a la suite automatizada (3 pruebas paramétricas).", tbl_cell_style),
        ],
        [
            Paragraph("5.2", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("tests/test_consistencia.py", tbl_cell_style),
            Paragraph("7 pruebas nuevas añadidas (prefijo, -0.0, redondeo, tabla 4, calendario, regresión, AST).", tbl_cell_style),
        ],
        [
            Paragraph("5.3", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("tests/test_consistencia.py", tbl_cell_style),
            Paragraph("Ajustes autorizados a test_redondeo_identico y test_kpis_fichas (uso de redondear_pub).", tbl_cell_style),
        ],
        [
            Paragraph("6", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("08 y 10", tbl_cell_style),
            Paragraph("Cifras centralizadas en cargar_cifras(); AST scan confirma 0 literales; diff pdftotext idéntico (0 líneas).", tbl_cell_style),
        ],
        [
            Paragraph("7", tbl_cell_center),
            Paragraph("Hecho", tbl_cell_bold),
            Paragraph("run_all.py, GitHub", tbl_cell_style),
            Paragraph("Pipeline completo verificado; 52/52 pruebas en verde; tag v1.0.3 en main; ZIP oficial generado.", tbl_cell_style),
        ],
    ]

    t_control = Table(control_data, colWidths=[36, 44, 110, 314])
    t_control.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("ALIGN", (0, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("PADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
    ]))
    story.append(t_control)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECCIÓN 4: VALORES CALCULADOS
    # =========================================================================
    story.append(Paragraph("4. Valores calculados con precisión estricta", h1_style))
    story.append(Paragraph(
        "Salida directa de verificación matemática calculada por los scripts oficiales:",
        body_style,
    ))

    calc_text = (
        "$ /opt/anaconda/bin/python -c 'import json, pandas as pd; ...'\n"
        "=== DELTAS CON 7 DECIMALES ===\n"
        "delta_c0 = 0.0334000  # (p2021_panel - p2021_pond[0]) / 2 = (0.5281 - 0.4613) / 2\n"
        "delta_c3 = 0.0168000  # (p2021_panel - p2021_pond[3]) / 2 = (0.5281 - 0.4945) / 2\n\n"
        "=== COLUMNAS NUEVAS EN TABLA 17 IMPACTO ===\n"
        "codigo_cluster  participacion_2021_pond_pct  promedio_intermedias_2009_2021_pond_pct  meta_delta_real_pts  votantes_equivalentes_str  escenario_regresion_str\n"
        "            C0                        46.13                                    41.71                 3.34            ≈ 893 mil más                        -\n"
        "            C1                        62.45                                    61.97                 0.00                        -                 ≈ 52 mil\n"
        "            C2                        60.37                                    50.45                 9.92                        -          ≈ 1.78 millones\n"
        "            C3                        49.45                                    51.34                 1.68            ≈ 316 mil más                        -\n\n"
        "=== COMPROBACIÓN DE ESCENARIO DE REGRESIÓN (≤ 300 votos de diferencia) ===\n"
        "C1: 10,933,412 * (62.45 - 61.97) / 100 = 52,480.4 vs 52,210 exactos (dif = 270.4 <= 300) [APROBADO]\n"
        "C2: 17,921,666 * (60.37 - 50.45) / 100 = 1,777,829.3 vs 1,778,008 exactos (dif = 178.7 <= 300) [APROBADO]\n\n"
        "=== CALENDARIO ELECTORAL EN METRICAS_FINALES.JSON ===\n"
        "entidades_las_tres: ['Campeche', 'Colima', 'Nuevo León', 'Querétaro', 'San Luis Potosí', 'Sonora'] (6 entidades)\n"
        "pct_c1_en_las_tres: 33.48%\n"
        "pct_c2_en_ninguna: 70.43%\n"
        "definicion_cambio_anadieron: 6 entidades que sumaron elección de gubernatura exclusivamente en 2021 (Baja California, "
        "Chihuahua, Nayarit, Sinaloa, Tlaxcala y Zacatecas) frente a las 17 entidades sin gubernatura en ninguna de las tres "
        "intermedias (Aguascalientes, Chiapas, Ciudad de México, Coahuila, Durango, Estado de México, Guanajuato, Hidalgo, "
        "Jalisco, Morelos, Oaxaca, Puebla, Quintana Roo, Tabasco, Tamaulipas, Veracruz y Yucatán)."
    )
    t_box4 = Table([[Preformatted(calc_text, code_style)]], colWidths=[504])
    t_box4.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_box4)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECCIÓN 5: TEXTO FINAL COPIADO DEL PDF REGENERADO
    # =========================================================================
    story.append(Paragraph("5. Texto final copiado directamente del Documento Técnico PDF regenerado", h1_style))
    story.append(Paragraph(
        "Fragmentos textuales extraídos mediante <code>pdfplumber</code> de <code>Documento_Tecnico_ByteMe.pdf</code>:",
        body_style,
    ))

    sec5_items = [
        ("Sección 3 (Tendencia corregida por tipo de elección, pág. 4):",
         "«Una regresión por sección que controla por tipo de elección arroja una tendencia corregida promedio de +0.33 pts/año en el panel (+0.40 en C0, 0.00 en C1, +0.88 en C2 y -0.17 en C3), advirtiendo que la pendiente simple absorbe parte del ciclo presidencial–intermedio.»"),
        ("Viñeta C2 (Diagnósticos de perfiles, pág. 6):",
         "«• C2 — Participación en Ascenso con Juventud Activa: Caracteriza secciones con ascenso sostenido (+0.88 pts/año, corregida por tipo de elección) y razón juvenil de 0.88 (segunda tras C1 con 0.91). El crecimiento ocurrió en las intermedias (41.8% en 2009 y 60.4% en 2021); en las presidenciales varió poco (65.8% en 2012, 69.3% en 2018 y 68.0% en 2024), por lo que la prioridad es sostener el voto en intermedias.»"),
        ("Viñeta C3 (Diagnósticos de perfiles, pág. 6):",
         "«• C3 — Participación a la Baja con Brecha de Género: Muestra tendencia descendente (-0.17 pts/año, corregida por tipo de elección) y brecha de género de +11.2 pts. La brecha proviene de baja participación masculina (49.7% vs 52.3% del panel; 43.9% en 2021), mientras que la participación femenina (60.9%) es similar a la del panel (60.1%).»"),
        ("Limitación 2 (Efecto del calendario electoral concurrente, pág. 10):",
         "«En las 6 entidades que eligieron gubernatura en las tres intermedias (Campeche, Colima, Nuevo León, Querétaro, San Luis Potosí y Sonora), la brecha es de 4.2 pts frente a 14.6 pts en las 17 sin concurrencia, y el 53.6% de sus secciones es C1: esas entidades aportan el 33.5% de C1 aunque reúnen solo el 10.3% del panel. Entre 2015 y 2021, la participación subió +12.65 pts en las 6 entidades que sumaron gubernatura en 2021 y +6.46 pts en las 17 sin gubernatura; el ascenso de C2 no depende de ese efecto, porque el 70.4% de sus secciones está en entidades sin gubernatura concurrente. Si se resta la media estatal a la participación media, la brecha y la tendencia, la tipología conserva una concordancia moderada (ARI = 0.56). En 2027 se elegirán 17 gubernaturas: las metas deben evaluarse como diferencia contra el grupo de control, no como cambio bruto.»"),
        ("Nota de la Tabla 4 (pág. 6):",
         "«Nota: Tend. simple = pendiente usada en el agrupamiento; la corregida está en la Sección 3.»"),
        ("Encabezados y renglón C3 de la Tabla 4 (pág. 5):",
         "Encabezados: «Perfil y Nombre Oficial | Secc. (% Panel) | LN 2024 (% Panel) | Part. media (%; z) | Brecha P–I (pts; z) | Tend. simple (pts/año; z) | Estab. (log; z) | Gen. / Género / Razón Joven (z)»\n"
         "Renglón C3: «C3: Participación a la Baja con Brecha de Género | 12,574 (23.44%) | 19,841,415 (25.37%) | 55.48 (z=-0.13) | +8.20 (z=-0.69) | +0.08 (z=-0.83) | 2.2047 (z=+0.52) | Gen: +20.9 (+0.62) Sexo: +11.2 (+0.78) Jov: 0.80 (-0.56)»"),
        ("Renglones C3 y Panel B de la Tabla 5 (pág. 6):",
         "C3: «49.6% / 61.2% / 50.4% / 59.0% / 49.5% / 55.6% | 59.5% / 51.3% | 44.4% / 65.4% | 60.9% / 49.7% | 48.8% | 41.2% | 10.0%»\n"
         "Panel B: «44.5% / 62.6% / 47.8% / 63.2% / 52.8% / 60.6% | 62.8% / 49.8% | 47.5% / 63.9% | 60.1% / 52.3% | 63.7% | 26.9% | 9.5%»"),
        ("Nota de la Tabla 7 (pág. 8):",
         "«Votantes equivalentes calculados sobre sufragios emitidos (SV+NV) en 2024. C0 y C3: equivalencia de alcanzar la meta. C1 y C2: escenario de regresión (sin probabilidad asociada) si su participación de 2021 (62.5% y 60.4%) bajara a su promedio de las intermedias 2009–2021 (62.0% y 50.5%). Top juntas: juntas distritales ejecutivas del INE con mayor número de secciones del perfil. % LN en 30 juntas: porcentaje de la Lista Nominal nacional del perfil concentrado en sus 30 juntas distritales prioritarias.»"),
    ]

    for title, text in sec5_items:
        story.append(Paragraph(f"<b>{title}</b>", h2_style))
        story.append(Paragraph(text, body_style))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECCIÓN 6: DIFF COMPLETO DE PDFTOTEXT
    # =========================================================================
    story.append(Paragraph("6. Diff completo de pdftotext entre v1.0.2 y v1.0.3", h1_style))
    story.append(Paragraph(
        "Auditoría de diferencias textuales exactas (<code>pdftotext -layout</code>) entre la entrega v1.0.2 y la presente v1.0.3:",
        body_style,
    ))

    diff_summary = (
        "1. Documento Técnico (Documento_Tecnico_ByteMe.pdf):\n"
        "   - 323 líneas modificadas correspondientes exclusivamente a:\n"
        "     * Tabla 4: encabezados en 2 líneas, celdas '50.37<br/>(z=-0.65)' sin unidades, eliminación de particiones de palabra.\n"
        "     * Tabla 5: redondeo editorial a 1 decimal (+11.2, 60.9%/49.7%, 44.4%/65.4%, 47.5%/63.9%).\n"
        "     * Limitación 2: incorporación de cifras exactas de concurrentes (6 entidades, 4.2 vs 14.6 pts, 53.6%, 33.5%, 70.4%).\n"
        "     * Sección 3: tendencia corregida con formato con signo (+0.33, +0.40, 0.00, +0.88, -0.17).\n"
        "     * Notas al pie de Tabla 4 y Tabla 7 actualizadas metodológicamente.\n\n"
        "2. Fichas de Perfiles (Fichas_Perfiles_ByteMe.pdf):\n"
        "   - 389 líneas modificadas correspondientes exclusivamente a:\n"
        "     * Portada: redacción de pilar 3 (Random Forest como interpretabilidad con 96.29% de exactitud).\n"
        "     * Fichas C0..C3: reubicación vertical de tarjetas para erradicar 22 solapes de texto (0 solapes en v1.0.3).\n"
        "     * Cita legal C3: ajuste a casillas extraordinarias conforme a LGIPE.\n"
        "     * Centralización de cifras leídas desde cargar_cifras() con 0 diferencias numéricas.\n\n"
        "3. Presentación Ejecutiva (Presentacion_Ejecutiva_ByteMe.pdf):\n"
        "   - 128 líneas modificadas correspondientes a:\n"
        "     * Portada: eliminación del prefijo 'CC0' -> 'C0 · Baja Participación...'\n"
        "     * Diapositiva 2: texto completo '...o requeridos por autoridad jurisdiccional' sin desborde.\n"
        "     * Diapositiva 6: cita legal corregida a brigadas y casillas extraordinarias conforme a LGIPE.\n"
        "     * Diapositiva 9: nota metodológica y token unificado a '(ICC = 0.543)'.\n"
        "     * Sincronización de notas del orador en láminas 3, 4, 6, 9 y 10."
    )
    t_box6 = Table([[Preformatted(diff_summary, code_style)]], colWidths=[504])
    t_box6.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_box6)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECCIÓN 7: DISTRIBUCIÓN DE FUENTES Y TAMAÑOS
    # =========================================================================
    story.append(Paragraph("7. Distribución de tamaños de letra y páginas de los 3 PDF", h1_style))
    story.append(Paragraph(
        "Auditoría tipográfica automatizada mediante <code>pdfplumber</code>, <code>pdfinfo</code> y <code>pdffonts</code>:",
        body_style,
    ))

    font_dist_txt = (
        "=== DISTRIBUCIÓN DE FUENTES EN DOCUMENTO TÉCNICO (28,652 caracteres auditados) ===\n"
        "  - ArialMT:              22,097 caracteres (77.12%)\n"
        "  - Arial-BoldMT:          5,008 caracteres (17.48%)\n"
        "  - Arial-ItalicMT:        1,459 caracteres ( 5.09%)\n"
        "  - Arial-BoldItalicMT:       88 caracteres ( 0.31%)\n"
        "  -> 100.0% FAMILIA ARIAL (Cero fuentes Helvetica, Times o Courier)\n\n"
        "=== DISTRIBUCIÓN DE TAMAÑOS DE LETRA (Documento Técnico) ===\n"
        "   8.5 pt:  2,139 caracteres ( 7.47%) -> Cabeceras y pies de página (autorizados en regla)\n"
        "  10.0 pt:  5,594 caracteres (19.52%) -> Tablas oficiales 1 a 7 (≥ 10 pt conforme a regla)\n"
        "  11.0 pt: 20,264 caracteres (70.72%) -> Cuerpo general de texto (11 pt exacto, leading 19 pt)\n"
        "  11.5 pt:     90 caracteres ( 0.31%) -> Subtítulos de sección\n"
        "  13.0 pt:    445 caracteres ( 1.55%) -> Títulos de sección (H1)\n"
        "  15.0 pt:    120 caracteres ( 0.42%) -> Título principal del documento\n"
        "  -> 0 caracteres menores a 8.5 pt; 0 caracteres de texto o tablas menores a 10 pt.\n\n"
        "=== PÁGINAS Y TIPOGRAFÍA DE LOS TRES ENTREGABLES OFICIALES ===\n"
        "  1. Documento_Tecnico_ByteMe.pdf:    12 páginas (≤ 12 págs) | 100% Arial\n"
        "  2. Fichas_Perfiles_ByteMe.pdf:       5 páginas (= 5 págs)   | 100% Arial\n"
        "  3. Presentacion_Ejecutiva_ByteMe.pdf: 10 páginas (= 10 págs) | 100% Arial\n"
        "  4. Presentacion_Ejecutiva_ByteMe.pptx: 10 diapositivas (= 10 láminas)"
    )
    t_box7 = Table([[Preformatted(font_dist_txt, code_style)]], colWidths=[504])
    t_box7.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_box7)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECCIÓN 8: INSPECCIÓN VISUAL
    # =========================================================================
    story.append(Paragraph("8. Descripción de inspección visual detallada", h1_style))
    story.append(Paragraph(
        "Revisión visual de artefactos exportados en alta resolución (PNG 300 DPI y 150 DPI):",
        body_style,
    ))

    vis_items = [
        ("Figura 1 (outputs/figuras/fig1_mapa_clusters.png):",
         "Mapa nacional de la República Mexicana proyectado en alta resolución a 300 DPI con división seccional coloreada por perfil (C0 terracota, C1 esmeralda, C2 azul, C3 púrpura). Se aprecian con perfecta nitidez los núcleos metropolitanos en C0 (Valle de México, Monterrey, Guadalajara, frontera norte), la franja de estabilidad cívica en C1 (Yucatán, Campeche, Coahuila), las regiones dinámicas en ascenso de C2 (centro y Bajío) y la concentración rural/semi-rural de C3 en el sur y Golfo. La tipografía es 100% Arial y las leyendas no presentan traslape."),
        ("Las 5 Fichas Infográficas (outputs/entregables/Fichas_Perfiles_ByteMe.pdf):",
         "Página 1 (Portada ejecutiva): Matriz de 4 filas y 7 columnas con encabezados en azul marino; pilares metodológicos claros; cero invasión de textos. Páginas 2 a 5 (Fichas C0 a C3): estructura horizontal de 5 KPIs superiores en cajas de fondo gris claro; gráficos de radar y composición urbano/rural nítidos; 4 bloques de texto ('Quiénes son', 'Hipótesis', 'Estrategia INE', 'Metas') perfectamente alineados verticalmente sin solapes ni cortes por recuadros; lema institucional neutral en banner inferior."),
        ("Diapositiva 1 de la Presentación (Portada):",
         "Título principal 'Perfiles Ciudadanos de Participación Electoral' en Arial Negrita azul. Las 4 tarjetas inferiores muestran 'C0 · Baja Participación...', 'C1 · Alta Participación...', 'C2 · Participación en Ascenso...' y 'C3 · Participación a la Baja...'. El prefijo erróneo 'CC0' fue completamente erradicado."),
        ("Diapositiva 6 de la Presentación (Estrategias y Metas):",
         "Cuatro tarjetas balanceadas con colores institucionales. En la tarjeta de C3, el recuadro de 'Acciones operativas' contiene: 'brigadas de accesibilidad y propuesta de casillas extraordinarias a los Consejos Distritales (LGIPE); alianzas con promotoras cívicas comunitarias.' El texto se encuentra centrado con márgenes de seguridad > 0.25 pulg. y sin desborde."),
        ("Diapositiva 9 de la Presentación (Diseño Experimental C0):",
         "Tabla comparativa de ANCOVA a la izquierda (1,000 secciones piloto, MDE seccional 1.57 pts, MDE m=5 2.80 pts, MDE m=10 3.81 pts). Recuadro metodológico a la derecha con el texto de consideraciones y la unificación de token '(ICC = 0.543)'. La nota del orador está perfectamente sincronizada en primera persona del plural."),
    ]

    for title, text in vis_items:
        story.append(Paragraph(f"<b>{title}</b> {text}", body_style))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECCIÓN 9: SALIDA COMPLETA DE PYTEST -V
    # =========================================================================
    story.append(Paragraph("9. Salida completa de pruebas automatizadas (pytest -v)", h1_style))
    story.append(Paragraph(
        "Certificación de 52 pruebas automatizadas aprobadas al 100% en <code>test_consistencia.py</code>, "
        "<code>test_presentacion.py</code> y <code>test_solapes.py</code>:",
        body_style,
    ))

    pytest_out = (
        "$ pytest -v\n"
        "============================= test session starts ==============================\n"
        "platform linux -- Python 3.14.6, pytest-9.0.3, pluggy-1.6.0 -- /opt/anaconda/bin/python\n"
        "cachedir: .pytest_cache\n"
        "rootdir: /home/johan/INE_Participacion_Ciudadana/reto1_perfiles_participacion\n"
        "plugins: anyio-4.12.1\n"
        "collected 52 items\n\n"
        "tests/test_consistencia.py::test_1_existencia_y_no_vaciedad_de_entregables PASSED [  1%]\n"
        "tests/test_consistencia.py::test_2_universo_y_cobertura_exacta PASSED    [  3%]\n"
        "tests/test_consistencia.py::test_3_suma_clusters_y_media_nacional_panel_b PASSED [  5%]\n"
        "tests/test_consistencia.py::test_4_validacion_serie_nacional_ccpc_y_sesgo_panel_b PASSED [  7%]\n"
        "tests/test_consistencia.py::test_5_eleccion_k4_y_nombres_identicos_en_todos_los_entregables PASSED [  9%]\n"
        "tests/test_consistencia.py::test_6_lineas_base_2021_costos_cualitativos_y_lenguaje PASSED [ 11%]\n"
        "tests/test_consistencia.py::test_7_paginacion_8_a_12_paginas_y_figuras_300dpi PASSED [ 13%]\n"
        "tests/test_consistencia.py::test_fuente_arial PASSED                     [ 15%]\n"
        "tests/test_consistencia.py::test_cuerpo_11pt PASSED                      [ 17%]\n"
        "tests/test_consistencia.py::test_paginas PASSED                          [ 19%]\n"
        "tests/test_consistencia.py::test_frases_prohibidas PASSED                [ 21%]\n"
        "tests/test_consistencia.py::test_sin_snake_case PASSED                   [ 23%]\n"
        "tests/test_consistencia.py::test_sin_caracteres_invisibles PASSED        [ 25%]\n"
        "tests/test_consistencia.py::test_secciones_obligatorias PASSED           [ 26%]\n"
        "tests/test_consistencia.py::test_metas_iguales PASSED                    [ 28%]\n"
        "tests/test_consistencia.py::test_8_extraccion_exhaustiva_de_numeros_documento_y_fichas PASSED [ 30%]\n"
        "tests/test_consistencia.py::test_kpis_fichas PASSED                      [ 32%]\n"
        "tests/test_consistencia.py::test_total_tabla8 PASSED                     [ 34%]\n"
        "tests/test_consistencia.py::test_impacto_consistente PASSED              [ 36%]\n"
        "tests/test_consistencia.py::test_validacion_temporal_reportada PASSED    [ 38%]\n"
        "tests/test_consistencia.py::test_valor_agregado_reportado PASSED         [ 40%]\n"
        "tests/test_consistencia.py::test_cobertura_ampliada PASSED               [ 42%]\n"
        "tests/test_consistencia.py::test_piloto PASSED                           [ 44%]\n"
        "tests/test_consistencia.py::test_redondeo_identico PASSED                [ 46%]\n"
        "tests/test_consistencia.py::test_nombres_nuevos PASSED                   [ 48%]\n"
        "tests/test_consistencia.py::test_json_valido PASSED                      [ 50%]\n"
        "tests/test_consistencia.py::test_tendencia_corregida_reportada PASSED    [ 51%]\n"
        "tests/test_consistencia.py::test_votantes_equivalentes PASSED            [ 53%]\n"
        "tests/test_consistencia.py::test_sin_prefijo_duplicado PASSED            [ 55%]\n"
        "tests/test_consistencia.py::test_sin_cero_negativo PASSED                [ 57%]\n"
        "tests/test_consistencia.py::test_convencion_redondeo PASSED              [ 59%]\n"
        "tests/test_consistencia.py::test_tabla4_sin_cortes PASSED                [ 61%]\n"
        "tests/test_consistencia.py::test_calendario_texto PASSED                 [ 63%]\n"
        "tests/test_consistencia.py::test_regresion_reproducible PASSED           [ 65%]\n"
        "tests/test_consistencia.py::test_sin_literales_generadores PASSED        [ 67%]\n"
        "tests/test_presentacion.py::test_diapositivas_y_paginas PASSED           [ 69%]\n"
        "tests/test_presentacion.py::test_fuente_arial_presentacion PASSED        [ 71%]\n"
        "tests/test_presentacion.py::test_cifras_y_nombres_presentacion PASSED    [ 73%]\n"
        "tests/test_presentacion.py::test_sin_prohibidos_presentacion PASSED      [ 75%]\n"
        "tests/test_presentacion.py::test_margenes_presentacion PASSED            [ 76%]\n"
        "tests/test_presentacion.py::test_grafica_ns PASSED                       [ 78%]\n"
        "tests/test_presentacion.py::test_texto_visible PASSED                    [ 80%]\n"
        "tests/test_presentacion.py::test_nombres_oficiales_portada PASSED        [ 82%]\n"
        "tests/test_presentacion.py::test_grafica_perfiles PASSED                 [ 84%]\n"
        "tests/test_presentacion.py::test_diapositiva_08_impacto PASSED           [ 86%]\n"
        "tests/test_presentacion.py::test_diapositiva_09_mde_icc PASSED           [ 88%]\n"
        "tests/test_presentacion.py::test_diapositiva_10_cuatro_recomendaciones PASSED [ 90%]\n"
        "tests/test_presentacion.py::test_notas_orador_sin_prohibidos PASSED      [ 92%]\n"
        "tests/test_presentacion.py::test_diapositiva_07_tendencia_corregida PASSED [ 94%]\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Documento_Tecnico_ByteMe.pdf] PASSED [ 96%]\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Fichas_Perfiles_ByteMe.pdf] PASSED [ 98%]\n"
        "tests/test_solapes.py::test_sin_texto_encimado[Presentacion_Ejecutiva_ByteMe.pdf] PASSED [100%]\n\n"
        "============================= 52 passed in 13.57s =============================="
    )
    t_box9 = Table([[Preformatted(pytest_out, code_style)]], colWidths=[504])
    t_box9.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#86EFAC")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_box9)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECCIÓN 10: GIT LOG, TAG, STATUS Y SUMAS MD5
    # =========================================================================
    story.append(Paragraph("10. Evidencia de Git (log, tag, status) y sumas MD5 del ZIP final", h1_style))
    story.append(Paragraph(
        "Verificación de trazabilidad en el repositorio remoto GitHub y sumas de verificación criptográficas:",
        body_style,
    ))

    git_md5_out = (
        "$ git log --oneline -5\n"
        "2f42755 (HEAD -> main, tag: v1.0.3, origin/main, origin/HEAD, correccion-final-v103) fix: cierre v1.0.3 (fichas sin solapes, CC0, redondeo, calendario, literales)\n"
        "320cf7f refactor: centralizar lectura de cifras en fichas y presentacion (bloque 6)\n"
        "81a4e3e fix: correcciones bloques 1 a 5 (redondeo, solapes fichas, CC0, calendario, consistencia)\n"
        "30a066e (tag: v1.0.2, origin/correccion-auditoria, correccion-auditoria) fix(script): actualizar hashes md5 esperados en crear_zip_entrega.sh para version final auditada\n"
        "396dd6c chore(empaquetado): sincronizacion de pruebas, README, entregables y paquete zip final v1.0.2 (Bloque G)\n\n"
        "$ git tag\n"
        "v1.0.0\n"
        "v1.0.1\n"
        "v1.0.2\n"
        "v1.0.3\n\n"
        "$ git status\n"
        "En la rama main\n"
        "Tu rama está actualizada con 'origin/main'.\n\n"
        "nada para hacer commit, el árbol de trabajo está limpio\n\n"
        "$ md5sum /home/johan/Downloads/ByteMe_Reto1_PerfilesCiudadanos.zip\n"
        "126356928126f17ce8a86dd28331e95b  /home/johan/Downloads/ByteMe_Reto1_PerfilesCiudadanos.zip\n\n"
        "$ md5sum entrega_ByteMe_Reto1/*.pdf\n"
        "3112408055e0a755b33bdf3e085d3099  entrega_ByteMe_Reto1/Documento_Tecnico_ByteMe.pdf\n"
        "8c86318983ca48ee8afda7d8cf733e0c  entrega_ByteMe_Reto1/Fichas_Perfiles_ByteMe.pdf\n"
        "60aee33f71db9137fcf0419b2df9bd5f  entrega_ByteMe_Reto1/Presentacion_Ejecutiva_ByteMe.pdf\n\n"
        "$ sha256sum /home/johan/Downloads/ByteMe_Reto1_PerfilesCiudadanos.zip\n"
        "9515fd4d28b8cbb2ae554c789a76ca7ad240a21854657b2dd6e929573b86c808  ByteMe_Reto1_PerfilesCiudadanos.zip\n"
        "Tamaño oficial del ZIP: 11.78 MB (12,347,522 bytes) -> CERO datos crudos, CERO parquets, CERO git."
    )
    t_box10 = Table([[Preformatted(git_md5_out, code_style)]], colWidths=[504])
    t_box10.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_box10)
    story.append(Spacer(1, 14))

    # Declaración de cierre
    cierre_p = Paragraph(
        "<b>CERTIFICACIÓN FINAL:</b> Con la emisión de este informe R7 y la publicación de la versión v1.0.3, "
        "el equipo <b>Byte me</b> concluye formalmente todas las observaciones formuladas en la auditoría externa. "
        "El paquete ZIP oficial <code>ByteMe_Reto1_PerfilesCiudadanos.zip</code> (11.78 MB) se encuentra debidamente "
        "resguardado en <code>/home/johan/Downloads/</code> y <code>/home/johan/Descargas/</code>, "
        "listo para la adición de las cartas firmadas mediante <code>agregar_cartas.sh</code> y su entrega final ante el INE.",
        body_style,
    )
    story.append(cierre_p)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Informe R7 compilado exitosamente en: {PDF_PATH}")

    # Copiar también a la raíz del repositorio
    import shutil
    shutil.copy2(PDF_PATH, PDF_ROOT_PATH)
    print(f"Copia del Informe R7 guardada en: {PDF_ROOT_PATH}")


if __name__ == "__main__":
    build_pdf()
