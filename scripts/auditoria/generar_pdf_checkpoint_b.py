#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera un PDF formal y profesional con el reporte completo del CHECKPOINT B.
Ubicación de salida: outputs/entregables/Checkpoint_B_Reporte_ByteMe.pdf
"""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PROJECT_ROOT = Path("/home/johan/INE_Participacion_Ciudadana/reto1_perfiles_participacion")
OUTPUT_PDF = PROJECT_ROOT / "outputs" / "entregables" / "Checkpoint_B_Reporte_ByteMe.pdf"
OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

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
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 756, "INE Reto 1: Perfiles Ciudadanos de Participación · Equipo Byte me")
            self.drawRightString(576, 756, "Reporte Técnico — CHECKPOINT B")
            self.setStrokeColor(colors.HexColor("#D1D5DB"))
            self.setLineWidth(0.5)
            self.line(36, 750, 576, 750)
            
        # Footer
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawString(36, 32, "Confidencial / Auditoría Técnica y Corrección de Datos · Concurso Hackea la Participación")
        self.drawRightString(576, 32, page_str)
        self.setStrokeColor(colors.HexColor("#D1D5DB"))
        self.setLineWidth(0.5)
        self.line(36, 42, 576, 42)
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    primary_color = colors.HexColor("#1E3A8A")   # Navy INE / Executive
    secondary_color = colors.HexColor("#0D9488") # Teal
    dark_neutral = colors.HexColor("#1F2937")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=secondary_color,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=dark_neutral,
        spaceAfter=6
    )

    body_bold = ParagraphStyle(
        'Body_Bold_Custom',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9.5,
        textColor=dark_neutral
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell,
        fontName='Helvetica-Bold'
    )

    table_cell_header = ParagraphStyle(
        'TableCellHeader',
        parent=table_cell,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#1E3A8A")
    )

    story = []

    # Title Banner
    story.append(Paragraph("CHECKPOINT B — Reporte Integral de Fases 2, 3 y 4", title_style))
    story.append(Paragraph(
        "<b>Auditoría Técnica, Corrección Metodológica y Derivación de Perfiles Electorales</b><br/>"
        "Reto 1: Perfiles Ciudadanos de Participación · Equipo <b>Byte me</b> · INE / ENCÍVICA 2024–2026",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=10))

    # Resumen Ejecutivo
    story.append(Paragraph("1. Verificación de Determinismo y Reproducibilidad Estricta", h1_style))
    story.append(Paragraph(
        "En cumplimiento de los requerimientos de auditoría y la regla de determinismo, el pipeline completo "
        "(ingesta de datos brutos desde archivos censales con codificación determinista <code>utf-8-sig</code> en 2024, "
        "ordenamiento estricto <code>ORDER BY edocve, seccion</code>, cálculo de tasas mediante la fórmula institucional "
        "<code>SV / (SV + NV)</code>, filtrado sin imputación, winsorización p1–p99, escalado robusto y partición K-Means++) "
        "fue ejecutado dos veces completas desde cero. Se verificaron hashes SHA-256 idénticos bit a bit:",
        body_style
    ))

    t1_data = [
        [Paragraph("Artefacto / Archivo Generado", table_cell_header),
         Paragraph("Hash SHA-256 (Corrida 1)", table_cell_header),
         Paragraph("Hash SHA-256 (Corrida 2)", table_cell_header),
         Paragraph("Validación", table_cell_header)],
        [Paragraph("outputs/fase2/etiquetas_finales.parquet", table_cell_bold),
         Paragraph("3858e9bde39dfeb9c3e05444c0d75106406f32e1abc359fd31af2397c0b9e911", table_cell),
         Paragraph("3858e9bde39dfeb9c3e05444c0d75106406f32e1abc359fd31af2397c0b9e911", table_cell),
         Paragraph("<b>100% Idéntico</b>", table_cell_bold)],
        [Paragraph("outputs/fase3/perfiles.csv", table_cell_bold),
         Paragraph("8a96df7aff28518431c0694c454454f385445e49f1588b2a65fbfa82f6d54442", table_cell),
         Paragraph("8a96df7aff28518431c0694c454454f385445e49f1588b2a65fbfa82f6d54442", table_cell),
         Paragraph("<b>100% Idéntico</b>", table_cell_bold)],
        [Paragraph("outputs/metricas_finales.json", table_cell_bold),
         Paragraph("868b975d331c9706ea3c91a7cacbe724df0fdecc9329209d28f3979b17fe2c8c", table_cell),
         Paragraph("868b975d331c9706ea3c91a7cacbe724df0fdecc9329209d28f3979b17fe2c8c", table_cell),
         Paragraph("<b>100% Idéntico</b>", table_cell_bold)],
    ]
    t1 = Table(t1_data, colWidths=[140, 165, 165, 70])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9FAFB")]),
    ]))
    story.append(t1)
    story.append(Spacer(1, 10))

    # Sección 2: Reconciliación de Universos
    story.append(Paragraph("2. Reconciliación de Universos y Cobertura Seccional (Opción B: Cero Imputación)", h1_style))
    story.append(Paragraph(
        "<b>Explicación de discrepancia entre 72,681 y 70,751:</b> En el corte electoral de 2024 existen <b>70,751 secciones activas</b>, "
        "compuestas por 62,048 secciones continuas presentes en las 6 elecciones y 8,703 secciones creadas con posterioridad a 2009. "
        "Las <b>72,681 secciones</b> corresponden a la unión histórica total, que añade 1,930 secciones dadas de baja o fusionadas por "
        "reseccionamiento antes de 2024. Para garantizar un análisis libre de sesgo sin recurrir a imputaciones sintéticas, se seleccionó el "
        "<b>Panel Principal (Opción B)</b> con <b>53,644 secciones</b> que representan el <b>75.82% de las secciones</b> y el <b>79.53% de la Lista Nominal de 2024</b>, "
        "cubriendo 2,393 municipios del país.",
        body_style
    ))

    t2_data = [
        [Paragraph("Etapa de Filtrado", table_cell_header),
         Paragraph("Secciones", table_cell_header),
         Paragraph("Excluidas", table_cell_header),
         Paragraph("% Secciones 2024", table_cell_header),
         Paragraph("Lista Nominal 2024", table_cell_header),
         Paragraph("% LN 2024", table_cell_header),
         Paragraph("Municipios", table_cell_header)],
        [Paragraph("0. Unión histórica (2009–2024)", table_cell), Paragraph("72,681", table_cell), Paragraph("—", table_cell), Paragraph("102.73%", table_cell), Paragraph("98,330,348", table_cell), Paragraph("100.00%", table_cell), Paragraph("2,477", table_cell)],
        [Paragraph("1. Secciones activas en 2024", table_cell), Paragraph("70,751", table_cell), Paragraph("1,930 (bajas pre-2024)", table_cell), Paragraph("100.00%", table_cell), Paragraph("98,330,348", table_cell), Paragraph("100.00%", table_cell), Paragraph("2,475", table_cell)],
        [Paragraph("2. Panel continuo (2009–2024)", table_cell), Paragraph("62,048", table_cell), Paragraph("8,703 (post-2009)", table_cell), Paragraph("87.70%", table_cell), Paragraph("85,938,493", table_cell), Paragraph("87.40%", table_cell), Paragraph("2,473", table_cell)],
        [Paragraph("3. Captura válida (SV+NV >= 50 en las 6)", table_cell), Paragraph("54,804", table_cell), Paragraph("7,244 (sin captura o <50)", table_cell), Paragraph("77.46%", table_cell), Paragraph("79,679,192", table_cell), Paragraph("81.03%", table_cell), Paragraph("2,402", table_cell)],
        [Paragraph("4. Sin salto consecutivo LN (<0.5x o >2.5x)", table_cell), Paragraph("53,645", table_cell), Paragraph("1,159 (de 1,311 en panel)", table_cell), Paragraph("75.82%", table_cell), Paragraph("78,199,601", table_cell), Paragraph("79.53%", table_cell), Paragraph("2,393", table_cell)],
        [Paragraph("<b>5. Panel Principal Opción B (Cero Imputación)</b>", table_cell_bold), Paragraph("<b>53,644</b>", table_cell_bold), Paragraph("1 (sin electores 60+)", table_cell), Paragraph("<b>75.82%</b>", table_cell_bold), Paragraph("<b>78,199,518</b>", table_cell_bold), Paragraph("<b>79.53%</b>", table_cell_bold), Paragraph("<b>2,393</b>", table_cell_bold)],
    ]
    t2 = Table(t2_data, colWidths=[160, 50, 95, 65, 75, 50, 45])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor("#F9FAFB")]),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#E0E7FF")),
    ]))
    story.append(t2)
    story.append(Spacer(1, 10))

    # Sección 3: Serie Nacional y Hallazgo NS
    story.append(PageBreak())
    story.append(Paragraph("3. Serie Nacional 2009–2024 y Validación de Fórmula Oficial SV / (SV + NV)", h1_style))
    story.append(Paragraph(
        "En los microdatos censales (CCPC), la Lista Nominal se compone de: <code>LN = SV + NV + NS</code>, donde <code>NS</code> "
        "corresponde a cuadernillos no disponibles, en recuento o no capturados. Al dividir <code>SV / LN</code> (criterio original erróneo), "
        "las secciones sin captura se computaban como 0.0% de participación, deprimiendo artificialmente los promedios en 2018 y 2024 y "
        "creando el artefacto del cluster C4. Con la fórmula oficial <code>SV / (SV + NV)</code> ponderada, se reproduce con exactitud "
        "el dato censal publicado por el INE en todas las elecciones presidenciales:",
        body_style
    ))

    t3_data = [
        [Paragraph("Año", table_cell_header),
         Paragraph("Elección", table_cell_header),
         Paragraph("Secciones CCPC", table_cell_header),
         Paragraph("SV+NV=0", table_cell_header),
         Paragraph("NS (% LN)", table_cell_header),
         Paragraph("Erróneo SV/LN (Pond)", table_cell_header),
         Paragraph("Oficial SV/(SV+NV) Pond", table_cell_header),
         Paragraph("Oficial INE Reportado", table_cell_header),
         Paragraph("Panel B (53,644) Pond", table_cell_header)],
        [Paragraph("2009", table_cell), Paragraph("Intermedia", table_cell), Paragraph("64,869", table_cell), Paragraph("1,733", table_cell), Paragraph("2.41%", table_cell), Paragraph("43.39%", table_cell), Paragraph("<b>44.46%</b>", table_cell_bold), Paragraph("44.6%–44.8%", table_cell), Paragraph("44.52%", table_cell)],
        [Paragraph("2012", table_cell), Paragraph("Presidencial", table_cell), Paragraph("66,805", table_cell), Paragraph("258", table_cell), Paragraph("0.22%", table_cell), Paragraph("61.94%", table_cell), Paragraph("<b>62.08%</b>", table_cell_bold), Paragraph("<b>62.1%</b>", table_cell_bold), Paragraph("62.72%", table_cell)],
        [Paragraph("2015", table_cell), Paragraph("Intermedia", table_cell), Paragraph("68,269", table_cell), Paragraph("4,051", table_cell), Paragraph("6.13%", table_cell), Paragraph("43.77%", table_cell), Paragraph("<b>46.63%</b>", table_cell_bold), Paragraph("47.7%*", table_cell), Paragraph("47.41%", table_cell)],
        [Paragraph("2018", table_cell), Paragraph("Presidencial", table_cell), Paragraph("67,832", table_cell), Paragraph("2,517", table_cell), Paragraph("6.83%", table_cell), Paragraph("58.11%", table_cell), Paragraph("<b>62.37%</b>", table_cell_bold), Paragraph("<b>62.4%</b>", table_cell_bold), Paragraph("63.61%", table_cell)],
        [Paragraph("2021", table_cell), Paragraph("Intermedia", table_cell), Paragraph("68,708", table_cell), Paragraph("2,711", table_cell), Paragraph("4.32%", table_cell), Paragraph("49.68%", table_cell), Paragraph("<b>51.92%</b>", table_cell_bold), Paragraph("52.6%*", table_cell), Paragraph("53.30%", table_cell)],
        [Paragraph("2024", table_cell), Paragraph("Presidencial", table_cell), Paragraph("70,751", table_cell), Paragraph("2,100", table_cell), Paragraph("6.43%", table_cell), Paragraph("55.83%", table_cell), Paragraph("<b>59.67%</b>", table_cell_bold), Paragraph("<b>59.7%</b>", table_cell_bold), Paragraph("61.07%", table_cell)],
    ]
    t3 = Table(t3_data, colWidths=[40, 60, 65, 45, 55, 75, 75, 65, 60])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9FAFB")]),
    ]))
    story.append(t3)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<i>*Nota: En elecciones intermedias (2015 y 2021), la cifra reportada por los cómputos distritales incorpora casillas especiales, "
        "mismas que por diseño censal no se incluyen en las tablas por sección electoral del CCPC.</i>",
        callout_style
    ))

    # Page Break for clean sectioning
    story.append(PageBreak())

    # Sección 4: Pruebas de Robustez Metodológica
    story.append(Paragraph("4. Resultados de las Pruebas de Robustez del Modelo (Fase 2)", h1_style))
    
    story.append(Paragraph("4.1 Transformación de Estabilidad Seccional", h2_style))
    story.append(Paragraph(
        "Se evaluaron tres formulaciones alternativas en el Panel Principal: (a) <code>1/CV</code> sin acotar, (b) <code>CV</code> directo winsorizado p1–p99, "
        "y (c) <code>log1p(1/CV)</code> winsorizado p1–p99. La formulación original (a) presentaba una curtosis patológica de 31.25 (máx 113.93). "
        "La versión (c) fue seleccionada formalmente al reducir la asimetría a 0.99 y la curtosis a 0.57, manteniendo el sentido positivo de estabilidad "
        "y superando a (b) en Silhouette (0.1625 vs 0.1611), Davies-Bouldin (1.6109 vs 1.6609) y Calinski-Harabasz (12,676.61 vs 12,299.10).",
        body_style
    ))

    story.append(Paragraph("4.2 Multicolinealidad (VIF) y Ventana Temporal", h2_style))
    story.append(Paragraph(
        "<b>Control VIF:</b> Las 7 variables seleccionadas registraron factores de inflación de la varianza estrictamente controlados (&lt; 4.0): "
        "<code>ratio_participacion_joven</code> = 3.99, <code>brecha_generacional</code> = 3.97, <code>estabilidad_participacion</code> = 3.86, "
        "<code>brecha_presidencial_intermedia</code> = 2.98, <code>tendencia_participacion_beta</code> = 2.12, "
        "<code>participacion_media_historica</code> = 1.92 y <code>brecha_genero</code> = 1.21. Eliminar <code>ratio_participacion_joven</code> "
        "(ARI = 0.4976) o <code>brecha_generacional</code> (ARI = 0.5381) desfigura la partición, pues la primera captura el rezago relativo de la juventud "
        "y la segunda la polarización etaria absoluta.<br/>"
        "<b>Ventana temporal:</b> Promediar los 6 comicios en las variables demográficas amortigua oscilaciones coyunturales, registrando correlaciones de "
        "0.73 a 0.81 frente al corte único de 2024, pero evitando agrupar por anomalías de una sola jornada (ARI = 0.3579).",
        body_style
    ))

    story.append(Paragraph("4.3 Análisis de Sensibilidad: Universo Opción A frente al Panel Principal B", h2_style))
    story.append(Paragraph(
        "Para validar que la exclusión de secciones con captura incompleta no sesga los perfiles, se corrió un modelo de sensibilidad (Opción A) "
        "sobre el universo continuo de 62,048 secciones (tratando años con captura insuficiente como NaN sin imputar y exigiendo al menos 2 comicios "
        "presidenciales y 2 intermedias válidas: N = 61,739). El <b>ARI en las 53,644 secciones comunes fue de 0.9292</b>, con una "
        "<b>coincidencia exacta del 97.20%</b> tras alinear centroides, demostrando que la topología de perfiles es estructuralmente invariante.",
        body_style
    ))

    story.append(Paragraph("4.4 Benchmark de Algoritmos (k=3 a 7, GMM y HDBSCAN)", h2_style))
    t4_data = [
        [Paragraph("Algoritmo", table_cell_header),
         Paragraph("Configuración", table_cell_header),
         Paragraph("Inercia", table_cell_header),
         Paragraph("Silhouette", table_cell_header),
         Paragraph("Davies-Bouldin", table_cell_header),
         Paragraph("Calinski-Harabasz", table_cell_header),
         Paragraph("BIC", table_cell_header),
         Paragraph("ARI Bootstrap (100 réplicas al 80%)", table_cell_header),
         Paragraph("Tamaño Mín–Máx (%)", table_cell_header)],
        [Paragraph("K-Means++", table_cell), Paragraph("k=3", table_cell), Paragraph("139,446.3", table_cell), Paragraph("0.2099", table_cell), Paragraph("1.4875", table_cell), Paragraph("16,402.4", table_cell), Paragraph("—", table_cell), Paragraph("0.9734 ± 0.0235 [0.9174, 0.9963]", table_cell), Paragraph("23.5% – 42.6%", table_cell)],
        [Paragraph("K-Means++", table_cell), Paragraph("k=4", table_cell), Paragraph("124,339.9", table_cell), Paragraph("0.1789", table_cell), Paragraph("1.5380", table_cell), Paragraph("14,435.4", table_cell), Paragraph("—", table_cell), Paragraph("0.9572 ± 0.0253 [0.9091, 0.9915]", table_cell), Paragraph("16.5% – 32.8%", table_cell)],
        [Paragraph("<b>K-Means++</b>", table_cell_bold), Paragraph("<b>k=5 (Seleccionado)</b>", table_cell_bold), Paragraph("<b>115,520.9</b>", table_cell_bold), Paragraph("<b>0.1625</b>", table_cell_bold), Paragraph("<b>1.6109</b>", table_cell_bold), Paragraph("<b>12,676.6</b>", table_cell_bold), Paragraph("—", table_cell), Paragraph("<b>0.9327 ± 0.0330 [0.8728, 0.9854]</b>", table_cell_bold), Paragraph("<b>12.9% – 30.3%</b>", table_cell_bold)],
        [Paragraph("K-Means++", table_cell), Paragraph("k=6", table_cell), Paragraph("108,211.6", table_cell), Paragraph("0.1639", table_cell), Paragraph("1.5709", table_cell), Paragraph("11,550.7", table_cell), Paragraph("—", table_cell), Paragraph("0.9675 ± 0.0162 [0.9375, 0.9887]", table_cell), Paragraph("11.0% – 28.3%", table_cell)],
        [Paragraph("K-Means++", table_cell), Paragraph("k=7", table_cell), Paragraph("102,430.2", table_cell), Paragraph("0.1539", table_cell), Paragraph("1.5736", table_cell), Paragraph("10,673.2", table_cell), Paragraph("—", table_cell), Paragraph("0.9496 ± 0.0798 [0.5652, 0.9837]", table_cell), Paragraph("10.0% – 22.6%", table_cell)],
        [Paragraph("GMM (full)", table_cell), Paragraph("k=5", table_cell), Paragraph("—", table_cell), Paragraph("0.0326", table_cell), Paragraph("3.7745", table_cell), Paragraph("5,030.3", table_cell), Paragraph("561,305.4", table_cell), Paragraph("—", table_cell), Paragraph("15.0% – 22.7%", table_cell)],
        [Paragraph("HDBSCAN", table_cell), Paragraph("min_samples=10", table_cell), Paragraph("—", table_cell), Paragraph("0.4140*", table_cell), Paragraph("0.6564*", table_cell), Paragraph("620.2*", table_cell), Paragraph("—", table_cell), Paragraph("50.73% clasificado como ruido", table_cell), Paragraph("2 clusters", table_cell)],
    ]
    t4 = Table(t4_data, colWidths=[65, 80, 50, 45, 50, 60, 45, 110, 45])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9FAFB")]),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#E0E7FF")),
    ]))
    story.append(t4)
    story.append(Spacer(1, 6))

    # Matriz de Transición
    story.append(Paragraph("4.5 Matriz de Transición: Desaparición del Artefacto C4 Original", h2_style))
    story.append(Paragraph(
        "El ARI global entre las etiquetas viejas y las nuevas es de tan solo <b>0.3986</b>. El <b>48.85% de las secciones del antiguo C4</b> "
        "(4,114 secciones) fueron correctamente excluidas del panel por carecer de cuadernillos capturados (SV+NV &lt; 50), y las restantes se "
        "redistribuyeron en los verdaderos perfiles cívicos. Esto confirma de manera empírica e irrefutable que el C4 original era un artefacto del error de ingesta.",
        body_style
    ))

    # Page Break for Profiles and Strategies
    story.append(PageBreak())

    # Sección 5: Caracterización de los 5 Nuevos Perfiles
    story.append(Paragraph("5. Caracterización de los 5 Nuevos Perfiles Ciudadanos de Participación", h1_style))
    story.append(Paragraph(
        "Conforme a la <b>Regla 3.2</b>, los nombres fueron derivados estrictamente a partir de las 2 o 3 variables con mayor desviación estándar (|z| &ge; 0.5) "
        "respecto a la media nacional del Panel Principal (N = 53,644 secciones; 78.2 millones de electores en LN 2024):",
        body_style
    ))

    t5_data = [
        [Paragraph("Código y Nombre Propuesto (Regla 3.2)", table_cell_header),
         Paragraph("Secciones (% Panel)", table_cell_header),
         Paragraph("Lista Nominal 2024 (% Panel)", table_cell_header),
         Paragraph("Variables Rectoras (|z| &ge; 0.5)", table_cell_header),
         Paragraph("Part. Media Histórica", table_cell_header),
         Paragraph("Brecha Pres.–Inter.", table_cell_header),
         Paragraph("Brecha Género", table_cell_header),
         Paragraph("Ratio Joven (Medias)", table_cell_header),
         Paragraph("Tipo Sección (U / R / M)", table_cell_header)],
        [
            Paragraph("<b>C0: Abstencionismo Crónico con Rezago Juvenil</b>", table_cell),
            Paragraph("9,535 (17.77%)", table_cell),
            Paragraph("14,988,837 (19.17%)", table_cell),
            Paragraph("Ratio Joven (z = -1.19)<br/>Brecha Generacional (z = +0.87)<br/>Part. Media (z = -0.84)", table_cell),
            Paragraph("<b>48.55%</b><br/>(z = -0.84)", table_cell),
            Paragraph("+12.41 pts<br/>(z = -0.09)", table_cell),
            Paragraph("+6.87 pts<br/>(z = -0.22)", table_cell),
            Paragraph("<b>0.7578</b><br/>(z = -1.19)", table_cell),
            Paragraph("62.6% U<br/>27.3% R<br/>10.2% M", table_cell)
        ],
        [
            Paragraph("<b>C1: Participación Intermitente de Ciclo Presidencial</b>", table_cell),
            Paragraph("16,244 (30.28%)", table_cell),
            Paragraph("25,605,748 (32.74%)", table_cell),
            Paragraph("Brecha Pres.–Inter. (z = +0.90)<br/>Estabilidad (z = -0.72)<br/>Tendencia Beta (z = +0.63)", table_cell),
            Paragraph("53.83%<br/>(z = -0.27)", table_cell),
            Paragraph("<b>+19.42 pts</b><br/>(z = +0.90)", table_cell),
            Paragraph("+7.27 pts<br/>(z = -0.12)", table_cell),
            Paragraph("0.8289<br/>(z = -0.14)", table_cell),
            Paragraph("<b>83.2% U</b><br/>9.6% R<br/>7.2% M", table_cell)
        ],
        [
            Paragraph("<b>C2: Alta Participación Consolidada y Estable</b>", table_cell),
            Paragraph("6,947 (12.95%)", table_cell),
            Paragraph("9,024,489 (11.54%)", table_cell),
            Paragraph("Estabilidad (z = +1.64)<br/>Brecha Pres.–Inter. (z = -1.20)<br/>Brecha Gen. (z = -1.11)<br/>Part. Media (z = +1.06)", table_cell),
            Paragraph("<b>66.08%</b><br/>(z = +1.06)", table_cell),
            Paragraph("<b>+4.67 pts</b><br/>(z = -1.20)", table_cell),
            Paragraph("+7.48 pts<br/>(z = -0.07)", table_cell),
            Paragraph("<b>0.9105</b><br/>(z = +1.06)", table_cell),
            Paragraph("45.8% U<br/>40.4% R<br/>13.9% M", table_cell)
        ],
        [
            Paragraph("<b>C3: Constancia de Ciclo con Liderazgo Femenino y Estancamiento Secular</b>", table_cell),
            Paragraph("10,689 (19.93%)", table_cell),
            Paragraph("16,809,225 (21.50%)", table_cell),
            Paragraph("Brecha Género (z = +0.97)<br/>Tendencia Beta (z = -0.79)<br/>Brecha Pres.–Inter. (z = -0.73)<br/>Estabilidad (z = +0.65)", table_cell),
            Paragraph("57.14%<br/>(z = +0.09)", table_cell),
            Paragraph("+7.96 pts<br/>(z = -0.73)", table_cell),
            Paragraph("<b>+11.96 pts</b><br/>(z = +0.97)", table_cell),
            Paragraph("0.8216<br/>(z = -0.25)", table_cell),
            Paragraph("48.5% U<br/><b>41.8% R</b><br/>9.8% M", table_cell)
        ],
        [
            Paragraph("<b>C4: Participación en Ascenso con Juventud Activa</b>", table_cell),
            Paragraph("10,229 (19.07%)", table_cell),
            Paragraph("11,771,219 (15.05%)", table_cell),
            Paragraph("Brecha Generacional (z = -0.95)<br/>Ratio Joven (z = +0.87)<br/>Tendencia Beta (z = +0.72)<br/>Brecha Género (z = -0.57)", table_cell),
            Paragraph("59.94%<br/>(z = +0.40)", table_cell),
            Paragraph("+14.66 pts<br/>(z = +0.23)", table_cell),
            Paragraph("<b>+5.35 pts</b><br/>(z = -0.57)", table_cell),
            Paragraph("<b>0.8979</b><br/>(z = +0.87)", table_cell),
            Paragraph("61.6% U<br/>29.3% R<br/>9.2% M", table_cell)
        ],
        [
            Paragraph("<b>Media Nacional Panel B</b>", table_cell_bold),
            Paragraph("<b>53,644 (100%)</b>", table_cell_bold),
            Paragraph("<b>78,199,518 (100%)</b>", table_cell_bold),
            Paragraph("—", table_cell),
            Paragraph("<b>56.30%</b>", table_cell_bold),
            Paragraph("<b>+13.07 pts</b>", table_cell_bold),
            Paragraph("<b>+7.79 pts</b>", table_cell_bold),
            Paragraph("<b>0.8385</b>", table_cell_bold),
            Paragraph("<b>66.4% U / 23.9% R / 9.7% M</b>", table_cell_bold)
        ]
    ]
    t5 = Table(t5_data, colWidths=[110, 55, 65, 95, 45, 45, 40, 45, 50])
    t5.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor("#F9FAFB")]),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#E0E7FF")),
    ]))
    story.append(t5)
    story.append(Spacer(1, 10))

    # Sección 6: Tabla de Estrategias y Viabilidad ENCÍVICA
    story.append(PageBreak())
    story.append(Paragraph("6. Estrategias Focalizadas y Viabilidad Operativa Institucional (Fase 4)", h1_style))
    story.append(Paragraph(
        "Cada estrategia se diseñó respetando estrictamente el marco de atribuciones del INE, el mandato de la ENCÍVICA 2024–2026, "
        "con narrativas neutrales sin adjetivaciones denostativas y asignación precisa de unidades operativas:",
        body_style
    ))

    t6_data = [
        [Paragraph("Perfil", table_cell_header),
         Paragraph("Factor Causal (Hipótesis)", table_cell_header),
         Paragraph("Acción Operativa y Canales INE", table_cell_header),
         Paragraph("Unidad Responsable", table_cell_header),
         Paragraph("Costo Estimado", table_cell_header),
         Paragraph("Meta Cuantitativa", table_cell_header),
         Paragraph("Lema Neutral", table_cell_header)],
        [
            Paragraph("<b>C0: Abstencionismo Crónico Joven</b>", table_cell),
            Paragraph("Hipótesis: Barreras al primer voto, movilidad estudiantil/laboral y menor socialización cívica.", table_cell),
            Paragraph("Brigadas universitarias de actualización de credencial en IES y difusión focalizada de 'Ubica tu Casilla'.", table_cell),
            Paragraph("DECEyEC, Juntas Distritales y DERFE", table_cell),
            Paragraph("Bajo-Medio (~$18-28M MXN)", table_cell),
            Paragraph("+3.0 a +4.5 pts en tasa 18-29 en >=60% de secciones.", table_cell),
            Paragraph("<i>'Tu primer voto abre camino: infórmate, ubica tu casilla y participa'</i>", table_cell)
        ],
        [
            Paragraph("<b>C1: Intermitente Presidencial</b>", table_cell),
            Paragraph("Hipótesis: Desconocimiento de atribuciones legislativas en comicios intermedios urbanos.", table_cell),
            Paragraph("Campaña en transporte metropolitano masivo, foros distritales y difusión QR del sistema 'Conóceles'.", table_cell),
            Paragraph("DECEyEC y Juntas Locales / Distritales", table_cell),
            Paragraph("Medio (~$25-40M MXN)", table_cell),
            Paragraph("Reducir brecha pres.-inter. en 3.5 a 5.0 pts en 2027.", table_cell),
            Paragraph("<i>'La democracia se ejerce cada tres años: conocer las atribuciones legislativas importa'</i>", table_cell)
        ],
        [
            Paragraph("<b>C2: Alta Consolidada y Estable</b>", table_cell),
            Paragraph("Hipótesis: Sólida cohesión comunitaria; riesgo de fatiga en integración de casillas.", table_cell),
            Paragraph("Sistematización de buenas prácticas cívicas, talleres juveniles de relevo y reclutamiento temprano de MDC.", table_cell),
            Paragraph("DECEyEC y DECE (Juntas Distritales)", table_cell),
            Paragraph("Bajo (~$8-14M MXN)", table_cell),
            Paragraph("Mantener part. >65% y 100% de casillas con propietarios.", table_cell),
            Paragraph("<i>'Participar fortalece a tu comunidad: formemos a las próximas generaciones de funcionariado'</i>", table_cell)
        ],
        [
            Paragraph("<b>C3: Liderazgo Femenino Rural</b>", table_cell),
            Paragraph("Hipótesis: Migración laboral masculina y envejecimiento en localidades rurales dispersas.", table_cell),
            Paragraph("Brigadas móviles en zonas rurales, difusión en radios comunitarias/indígenas y revisión de accesibilidad de casillas.", table_cell),
            Paragraph("Juntas Distritales, DECEyEC y DEOE", table_cell),
            Paragraph("Medio (~$20-32M MXN)", table_cell),
            Paragraph("Incrementar en +2.5 pts part. masculina (51% a 53.5%).", table_cell),
            Paragraph("<i>'Cada voz en la comunidad cuenta: facilitemos el acceso a la casilla para todas las edades'</i>", table_cell)
        ],
        [
            Paragraph("<b>C4: En Ascenso con Juventud</b>", table_cell),
            Paragraph("Hipótesis: Dinamismo demográfico e integración juvenil que requiere consolidarse como hábito.", table_cell),
            Paragraph("Foros juveniles 'Diálogos por la Democracia', alianzas con colectivos estudiantiles y verificación informativa.", table_cell),
            Paragraph("DECEyEC y Juntas Distritales", table_cell),
            Paragraph("Bajo-Medio (~$12-20M MXN)", table_cell),
            Paragraph("Sostener part. >60% en comicios intermedios de 2027.", table_cell),
            Paragraph("<i>'Tu participación transforma tu entorno: mantengamos activa la conversación cívica'</i>", table_cell)
        ]
    ]
    t6 = Table(t6_data, colWidths=[80, 85, 105, 70, 55, 65, 90])
    t6.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9FAFB")]),
    ]))
    story.append(t6)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[PDF Generado] {OUTPUT_PDF} ({OUTPUT_PDF.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    build_pdf()
