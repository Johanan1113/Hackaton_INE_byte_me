"""
Módulo 05: Compilador del Documento Técnico Oficial en PDF (ReportLab)
Convocatoria: Concurso "Hackea la Participación: Datos que construyen democracia" (CCPC 2009–2024 / ENCÍVICA)
Reto 1: Perfiles ciudadanos de participación
Equipo: Byte me
Integrantes:
  - Johanan Olivares Gutierrez (Representante)
  - Oscar Ariel Cuevas Martinez
  - Saul Alexis Arias Gonzales
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
import pypdf

# Configuración de Logging
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("05_report_pdf")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DATASETS = os.path.join(PROJECT_ROOT, "output", "datasets")
OUTPUT_FIGURES = os.path.join(PROJECT_ROOT, "output", "figures")
ENTREGABLES_DIR = os.path.join(PROJECT_ROOT, "entregables_finales")
ENTREGABLES_FIG = os.path.join(ENTREGABLES_DIR, "figures")
OUTPUT_PDF = os.path.join(ENTREGABLES_DIR, "Documento_Tecnico_Reto1_ByteMe.pdf")
PIPELINE_LOG = os.path.join(PROJECT_ROOT, "pipeline.log")

file_handler = logging.FileHandler(PIPELINE_LOG, mode="a", encoding="utf-8")
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(file_handler)

# Paleta de Colores Institucional INE y ENCÍVICA
COLOR_PURPLE = colors.HexColor("#582D73")    # Primario
COLOR_MAGENTA = colors.HexColor("#D1367E")   # Secundario / Acento
COLOR_TEAL = colors.HexColor("#00A896")      # Terciario
COLOR_AMBER = colors.HexColor("#E67E22")     # Soporte
COLOR_DARK = colors.HexColor("#1E1E24")      # Texto Primario
COLOR_MUTED = colors.HexColor("#5A6275")     # Texto Secundario
COLOR_LIGHT_BG = colors.HexColor("#F9F9FB")  # Fondo claro tarjetas
COLOR_BORDER = colors.HexColor("#E2E8F0")    # Bordes
COLOR_WHITE = colors.HexColor("#FFFFFF")

# Márgenes normativos: 2.0 cm laterales (56.7 pt), 2.5 cm superior/inferior (70.87 pt)
MARGIN_LR = 56.7
MARGIN_TB = 70.87
PRINTABLE_WIDTH = 612 - 2 * MARGIN_LR  # 498.6 pt

class NumberedCanvas(canvas.Canvas):
    """Canvas de dos pasos para numeración dinámica 'Página X de Y' y encabezados institucionales."""
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
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        # Encabezado para páginas 2 en adelante
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(COLOR_PURPLE)
            self.drawString(MARGIN_LR, 745, "INSTITUTO NACIONAL ELECTORAL")
            self.setFont("Helvetica", 8)
            self.setFillColor(COLOR_MUTED)
            self.drawString(MARGIN_LR + 145, 745, "|  Concurso CCPC 2009–2024 / ENCÍVICA  •  Reto 1")
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(COLOR_MAGENTA)
            self.drawRightString(612 - MARGIN_LR, 745, "Equipo: Byte me")
            
            # Pleca superior institucional
            self.setStrokeColor(COLOR_MAGENTA)
            self.setLineWidth(1.0)
            self.line(MARGIN_LR, 737, 612 - MARGIN_LR, 737)
        
        # Pie de página para todas las páginas
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.5)
        self.line(MARGIN_LR, 48, 612 - MARGIN_LR, 48)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(COLOR_MUTED)
        self.drawString(MARGIN_LR, 36, "Hackea la Participación: Datos que construyen democracia  •  Documento Técnico Oficial")
        self.drawRightString(612 - MARGIN_LR, 36, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()

def build_technical_document():
    logger.info("=== GENERACIÓN DEL DOCUMENTO TÉCNICO OFICIAL (PDF) ===")
    os.makedirs(ENTREGABLES_DIR, exist_ok=True)
    os.makedirs(ENTREGABLES_FIG, exist_ok=True)
    
    # Cargar datos enriquecidos
    fichas_path = os.path.join(OUTPUT_DATASETS, "arquetipos_fichas.json")
    with open(fichas_path, "r", encoding="utf-8") as f:
        fichas = json.load(f)
        
    benchmark_df = pd.read_parquet(os.path.join(OUTPUT_DATASETS, "clustering_benchmark_metrics.parquet"))
    feat_imp_df = pd.read_parquet(os.path.join(OUTPUT_DATASETS, "feature_importance.parquet"))
    
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=letter,
        leftMargin=MARGIN_LR,
        rightMargin=MARGIN_LR,
        topMargin=MARGIN_TB,
        bottomMargin=MARGIN_TB
    )
    
    styles = getSampleStyleSheet()
    
    # Estilos tipográficos normativos: Arial/Helvetica 11 pt, interlineado 1.5 (leading=16.5)
    style_cover_badge = ParagraphStyle(
        "CoverBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=COLOR_MAGENTA,
        spaceAfter=4
    )
    style_cover_title = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=COLOR_PURPLE,
        spaceAfter=8
    )
    style_cover_subtitle = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=COLOR_DARK,
        spaceAfter=12
    )
    style_h1 = ParagraphStyle(
        "Header1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=COLOR_PURPLE,
        spaceBefore=8,
        spaceAfter=5,
        keepWithNext=True
    )
    style_h2 = ParagraphStyle(
        "Header2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=COLOR_MAGENTA,
        spaceBefore=6,
        spaceAfter=4,
        keepWithNext=True
    )
    style_body = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=16.5,  # Interlineado 1.5 exacto reglamentario
        textColor=COLOR_DARK,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )
    style_callout = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        leading=14,
        textColor=COLOR_PURPLE,
        alignment=TA_JUSTIFY
    )
    style_table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=COLOR_DARK,
        alignment=TA_CENTER
    )
    style_table_cell_left = ParagraphStyle(
        "TableCellLeft",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=COLOR_DARK,
        alignment=TA_LEFT
    )
    style_table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=COLOR_WHITE,
        alignment=TA_CENTER
    )
    
    story = []
    
    # =========================================================================
    # PÁGINA 1: PORTADA INSTITUCIONAL Y METADATOS OFICIALES
    # =========================================================================
    story.append(Paragraph("INSTITUTO NACIONAL ELECTORAL  •  ENCÍVICA 2024", style_cover_badge))
    story.append(Paragraph("Concurso \"Hackea la Participación: Datos que construyen democracia\"", style_h2))
    story.append(Paragraph("Reto 1: Perfiles ciudadanos de participación", style_cover_title))
    story.append(Paragraph(
        "Modelado de Aprendizaje No Supervisado, Armonización Cartográfica Longitudinal (2009–2024) "
        "y Formulación de Estrategias Cívicas Focalizadas",
        style_cover_subtitle
    ))
    story.append(HRFlowable(width="100%", thickness=2.0, color=COLOR_PURPLE, spaceAfter=10))
    
    # Ficha técnica del equipo participante
    team_data = [
        [
            Paragraph("<b>Identificación Oficial del Equipo</b>", style_table_header),
            Paragraph("<b>Información Institucional</b>", style_table_header)
        ],
        [
            Paragraph("<b>Nombre del Equipo:</b> Byte me", style_table_cell_left),
            Paragraph("<b>Convocatoria:</b> Concurso CCPC 2009–2024 / ENCÍVICA", style_table_cell_left)
        ],
        [
            Paragraph("<b>Representante:</b> Johanan Olivares Gutierrez", style_table_cell_left),
            Paragraph("<b>Reto:</b> Reto 1: Perfiles ciudadanos de participación", style_table_cell_left)
        ],
        [
            Paragraph("<b>Integrante 2:</b> Oscar Ariel Cuevas Martinez", style_table_cell_left),
            Paragraph("<b>Universo Analizado:</b> 62,048 Secciones Electorales (100% continuas)", style_table_cell_left)
        ],
        [
            Paragraph("<b>Integrante 3:</b> Saul Alexis Arias Gonzales", style_table_cell_left),
            Paragraph("<b>Padrón Representado:</b> 85,936,860 Electores (LN 2024)", style_table_cell_left)
        ]
    ]
    t_team = Table(team_data, colWidths=[249, 249])
    t_team.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PURPLE),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
        ('PADDING', (0, 0), (-1, -1), 4.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(t_team)
    story.append(Spacer(1, 10))
    
    # Resumen Ejecutivo de Apertura
    story.append(Paragraph("Resumen Ejecutivo", style_h1))
    story.append(Paragraph(
        "El presente documento técnico presenta la solución desarrollada por el equipo <b>Byte me</b> para el "
        "<b>Reto 1: Perfiles ciudadanos de participación</b>. A través de la explotación integral de los Conteos Censales de "
        "Participación Ciudadana (CCPC) en seis comicios federales (2009 a 2024), se construyó una infraestructura analítica "
        "capaz de armonizar la cartografía histórica del país ante las redistritaciones de 2017 y 2022, aislando una submuestra "
        "panel balanceada de <b>62,048 secciones electorales</b> con 100% de presencia longitudinal.",
        style_body
    ))
    story.append(Paragraph(
        "Mediante un riguroso benchmark entre algoritmos no supervisados (K-Means++, Gaussian Mixture Models y HDBSCAN), "
        "se seleccionó una estructura campeona de <b>5 conglomerados (k=5)</b> que optimiza la estabilidad matemática "
        "(Índice de Rand Ajustado ARI = 0.841) y la interpretabilidad de política pública electoral. Los perfiles descubiertos "
        "evidencian que el abstencionismo en México no es homogéneo: el 35.9% de las secciones sufre un <i>Abstencionismo Estructural Urbano</i>, "
        "mientras que sectores juveniles y femeninos requieren mecanismos y canales diferenciados según su comportamiento de asistencia a las urnas.",
        style_body
    ))
    story.append(PageBreak())
    
    # =========================================================================
    # PÁGINA 2: RESUMEN EJECUTIVO EXTENDIDO Y CUADRO SINÓPTICO
    # =========================================================================
    story.append(Paragraph("1. Síntesis de Arquetipos y Hallazgos Principales", style_h1))
    story.append(Paragraph(
        "El análisis multidimensional permitió clasificar al 100% del padrón electoral nacional en cinco perfiles sociodemográficos "
        "y conductuales consistentes a lo largo de 15 años de historia democrática. La comprensión de estos perfiles es el insumo fundamental "
        "para que la Estrategia Nacional de Educación Cívica (ENCÍVICA) supere los esfuerzos de comunicación genéricos y pase a una "
        "intervención basada en micro-focalización territorial y etaria.",
        style_body
    ))
    
    # Tabla sinóptica de los 5 arquetipos
    sinop_table = [
        [
            Paragraph("<b>Arquetipo Ciudadano</b>", style_table_header),
            Paragraph("<b>Secciones (%)</b>", style_table_header),
            Paragraph("<b>Padrón 2024</b>", style_table_header),
            Paragraph("<b>Part. Media</b>", style_table_header),
            Paragraph("<b>Dinámica Central</b>", style_table_header)
        ],
        [
            Paragraph("<b>C2: Abstencionismo Estructural Urbano</b>", style_table_cell_left),
            Paragraph(f"{fichas['2']['pct_secciones']}% ({fichas['2']['secciones']:,})", style_table_cell),
            Paragraph(f"{fichas['2']['padron_2024']/1e6:.2f} M ({fichas['2']['pct_padron']}%)", style_table_cell),
            Paragraph(f"{fichas['2']['participacion_media']*100:.1f}%", style_table_cell),
            Paragraph("Apatía cívica metropolitana; alta fatiga de participación.", style_table_cell_left)
        ],
        [
            Paragraph("<b>C0: Voto Femenino Consistente</b>", style_table_cell_left),
            Paragraph(f"{fichas['0']['pct_secciones']}% ({fichas['0']['secciones']:,})", style_table_cell),
            Paragraph(f"{fichas['0']['padron_2024']/1e6:.2f} M ({fichas['0']['pct_padron']}%)", style_table_cell),
            Paragraph(f"{fichas['0']['participacion_media']*100:.1f}%", style_table_cell),
            Paragraph("Máximo diferencial pro-mujeres (+13.3%); lealtad cívica vecinal.", style_table_cell_left)
        ],
        [
            Paragraph("<b>C1: Pivote Presidencial Volátil</b>", style_table_cell_left),
            Paragraph(f"{fichas['1']['pct_secciones']}% ({fichas['1']['secciones']:,})", style_table_cell),
            Paragraph(f"{fichas['1']['padron_2024']/1e6:.2f} M ({fichas['1']['pct_padron']}%)", style_table_cell),
            Paragraph(f"{fichas['1']['participacion_media']*100:.1f}%", style_table_cell),
            Paragraph("Desplome de 24.1 puntos en intermedias; alta volatilidad.", style_table_cell_left)
        ],
        [
            Paragraph("<b>C4: Juventud Movilizada en Expansión</b>", style_table_cell_left),
            Paragraph(f"{fichas['4']['pct_secciones']}% ({fichas['4']['secciones']:,})", style_table_cell),
            Paragraph(f"{fichas['4']['padron_2024']/1e6:.2f} M ({fichas['4']['pct_padron']}%)", style_table_cell),
            Paragraph(f"{fichas['4']['participacion_media']*100:.1f}%", style_table_cell),
            Paragraph("Mayor tasa relativa en jóvenes (18-29); áreas periurbanas.", style_table_cell_left)
        ],
        [
            Paragraph("<b>C3: Voto Tradicional Rural y Mayor</b>", style_table_cell_left),
            Paragraph(f"{fichas['3']['pct_secciones']}% ({fichas['3']['secciones']:,})", style_table_cell),
            Paragraph(f"{fichas['3']['padron_2024']/1e6:.2f} M ({fichas['3']['pct_padron']}%)", style_table_cell),
            Paragraph(f"{fichas['3']['participacion_media']*100:.1f}%", style_table_cell),
            Paragraph("Máxima afluencia histórica (66.4%); bastión rural y tercera edad.", style_table_cell_left)
        ]
    ]
    t_sinop = Table(sinop_table, colWidths=[130, 75, 75, 55, 163])
    t_sinop.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PURPLE),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(t_sinop)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Aportaciones Clave para el INE", style_h2))
    story.append(Paragraph(
        "1. <b>Focalización del Gasto Educativo y Cívico:</b> El hallazgo de que el 35.9% de las secciones pertenecen a un perfil "
        "de abstencionismo estructural urbano permite a la Dirección Ejecutiva de Capacitación Electoral y Educación Cívica (DECEyEC) "
        "concentrar recursos pedagógicos en centros corporativos, de transporte masivo y campus metropolitanos, abandonando la dispersión "
        "presupuestal indiscriminada.",
        style_body
    ))
    story.append(Paragraph(
        "2. <b>Estrategia contra la Volatilidad Intermedia:</b> La identificación del <i>Pivote Presidencial Volátil</i> (14.67 millones de votantes "
        "que se ausentan masivamente cuando no se renueva el Ejecutivo Federal) brinda la evidencia cuantitativa para desplegar campañas "
        "anticipadas de pedagogía legislativa sobre el papel del Congreso y los gobiernos locales.",
        style_body
    ))
    story.append(Paragraph(
        "3. <b>Empoderamiento de la Mujer en Comunidad:</b> El arquetipo de <i>Voto Femenino Consistente</i> confirma empíricamente que "
        "las mujeres constituyen la columna vertebral de la participación ciudadana en México, lo que fundamenta programas institucionales de "
        "reconocimiento a liderazgos comunitarios y facilidades operativas de cuidados para funcionarias de casilla.",
        style_body
    ))
    story.append(PageBreak())
    
    # =========================================================================
    # PÁGINA 3: PLANTEAMIENTO DEL PROBLEMA Y PREGUNTA GUÍA
    # =========================================================================
    story.append(Paragraph("2. Planteamiento del Problema y Pregunta Guía", style_h1))
    story.append(Paragraph(
        "A lo largo de las últimas dos décadas, la participación ciudadana en las elecciones federales de México ha oscilado entre "
        "un mínimo de 43.8% en elecciones intermedias (2009) y un máximo de 62.5% en elecciones presidenciales (2012), situándose en 58.6% "
        "en 2018 y 56.6% en 2024. No obstante, las cifras nacionales promedio enmascaran disparidades geográficas, generacionales y de género "
        "profundas.",
        style_body
    ))
    story.append(Paragraph(
        "Mientras que ciertas secciones rurales o tradicionales mantienen tasas de concurrencia superiores al 70%, amplias franjas de zonas "
        "metropolitanas experimentan un abstencionismo crónico que desciende del 40%. Del mismo modo, la participación de los jóvenes de 18 a 29 "
        "años sufre un declive sistemático posterior a su primera experiencia electoral, cayendo hasta 15 puntos por debajo del promedio de los "
        "adultos mayores de 60 años.",
        style_body
    ))
    
    story.append(Paragraph("Pregunta Central de Investigación", style_h2))
    story.append(Paragraph(
        "¿De qué manera pueden estructurarse perfiles arquetípicos de participación a partir de la serie longitudinal 2009–2024 de los Conteos "
        "Censales del INE, controlando el rediseño cartográfico y la colinealidad demográfica, para fundamentar estrategias diferenciadas "
        "en la ENCÍVICA que reduzcan las brechas de abstencionismo y fortalezcan la cultura democrática?",
        style_callout
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Objetivos Específicos del Estudio", style_h2))
    story.append(Paragraph(
        "• <b>Armonizar la serie censal histórica:</b> Integrar los microdatos seccionales de seis procesos federales mediante un marco espacial "
        "consistente que resuelva las distorsiones ocasionadas por las distritaciones 2017 y 2022.",
        style_body
    ))
    story.append(Paragraph(
        "• <b>Formular indicadores de dinámica temporal:</b> Modelar la volatilidad electoral (brecha presidencial-intermedia), la trayectoria "
        "longitudinal ($\beta_1$) y las divergencias etarias y por razón de sexo.",
        style_body
    ))
    story.append(Paragraph(
        "• <b>Ejecutar un benchmark multialgorítmico riguroso:</b> Comparar técnicas de agrupamiento basadas en centroides, mixturas probabilísticas "
        "y densidad para garantizar una partición matemáticamente óptima.",
        style_body
    ))
    story.append(Paragraph(
        "• <b>Traducir los hallazgos en política pública:</b> Proporcionar a la autoridad electoral una matriz accionable que asigne canales, "
        "narrativas y mecanismos operativos específicos para cada segmento ciudadano identificado.",
        style_body
    ))
    story.append(PageBreak())
    
    # =========================================================================
    # PÁGINA 4: MARCO METODOLÓGICO Y TRATAMIENTO DE FUENTES
    # =========================================================================
    story.append(Paragraph("3. Marco Metodológico y Tratamiento de Fuentes", style_h1))
    story.append(Paragraph(
        "La fuente primaria corresponde a los Conteos Censales de Participación Ciudadana (CCPC) elaborados por el INE para las elecciones "
        "federales de 2009, 2012, 2015, 2018, 2021 y 2024. Cada registro censal proviene de la captura sistemática de las marcas de voto en los "
        "cuadernillos de Lista Nominal tras la jornada comicial, totalizando millones de registros desagregados por sexo y edad cumplida.",
        style_body
    ))
    
    story.append(Paragraph("Tratamiento de la Redistritación Histórica y Sanidad F1", style_h2))
    story.append(Paragraph(
        "Debido a que los 300 distritos electorales federales sufrieron reconfiguraciones mayores en 2017 y 2022 por mandato constitucional, "
        "el análisis longitudinal a nivel distrital presentaría rupturas territoriales severas. Por ello, se definió como unidad primaria de "
        "análisis la <b>Sección Electoral</b> mediante la clave única compuesta (<code>EDOCVE_SECCION</code>).",
        style_body
    ))
    story.append(Paragraph(
        "Se ejecutó una consolidación longitudinal estricta por <i>inner join</i>, preservando <b>62,048 secciones con presencia ininterrumpida</b> "
        "en los seis comicios analizados. Esta selección conserva el <b>85.37%</b> de todas las secciones censadas en la historia del INE y cubre "
        "el <b>99.11% de los municipios del país</b> (2,455 municipios). En términos de sanidad F1, se verificó la ausencia de valores negativos y "
        "se aplicó <i>capping</i> al 100% en casillas especiales donde concurren electores en tránsito que no pertenecen a la lista nominal local.",
        style_body
    ))
    
    story.append(Paragraph("Formulación Matemática de Características y Control VIF", style_h2))
    story.append(Paragraph(
        "Para el modelado no supervisado se construyeron tasas normalizadas e indicadores longitudinales. Con el propósito de evitar redundancia, "
        "se evaluó el Factor de Inflación de la Varianza (VIF). Todas las variables seleccionadas registran un VIF menor a 3.50:",
        style_body
    ))
    
    feat_formula_table = [
        [
            Paragraph("<b>Variable Construida</b>", style_table_header),
            Paragraph("<b>Fórmula / Definición Operativa</b>", style_table_header),
            Paragraph("<b>Media ± Desv.</b>", style_table_header),
            Paragraph("<b>VIF</b>", style_table_header)
        ],
        [
            Paragraph("<code>Participación Media</code> (P̄)", style_table_cell_left),
            Paragraph("P̄ = ⅙ ∑ (Votantes_t / LN_t) para t ∈ {2009, 12, 15, 18, 21, 24}", style_table_cell_left),
            Paragraph("53.64% ± 9.94%", style_table_cell),
            Paragraph("1.69", style_table_cell)
        ],
        [
            Paragraph("<code>Brecha Presidencial</code> (Δ_pres)", style_table_cell_left),
            Paragraph("Δ_pres = ⅓ ∑ P_presidenciales − ⅓ ∑ P_intermedias", style_table_cell_left),
            Paragraph("+12.29% ± 10.42%", style_table_cell),
            Paragraph("1.64", style_table_cell)
        ],
        [
            Paragraph("<code>Tendencia Temporal</code> (β₁)", style_table_cell_left),
            Paragraph("Pendiente OLS univariada del tiempo (t ∈ [0,15] años) vs. Part.", style_table_cell_left),
            Paragraph("+0.0046 ± 0.0103", style_table_cell),
            Paragraph("1.55", style_table_cell)
        ],
        [
            Paragraph("<code>Estabilidad Cívica</code> (CV⁻¹)", style_table_cell_left),
            Paragraph("Inverso del coeficiente de variación seccional: P̄ / (σ_P + 10⁻⁶)", style_table_cell_left),
            Paragraph("5.71 ± 4.35", style_table_cell),
            Paragraph("1.49", style_table_cell)
        ],
        [
            Paragraph("<code>Brecha Generacional</code>", style_table_cell_left),
            Paragraph("Tasa Adultos Mayores (60+) − Tasa Jóvenes (18 a 29 años)", style_table_cell_left),
            Paragraph("+15.62% ± 7.13%", style_table_cell),
            Paragraph("3.43", style_table_cell)
        ],
        [
            Paragraph("<code>Brecha de Género</code> (G_gap)", style_table_cell_left),
            Paragraph("Diferencia neta pro-femenina: % Part. Mujeres − % Part. Hombres", style_table_cell_left),
            Paragraph("+7.36% ± 4.19%", style_table_cell),
            Paragraph("1.17", style_table_cell)
        ],
        [
            Paragraph("<code>Ratio Juvenil</code>", style_table_cell_left),
            Paragraph("Tasa relativa de participación juvenil: TasaJoven / P̄", style_table_cell_left),
            Paragraph("0.8379 ± 0.0696", style_table_cell),
            Paragraph("3.50", style_table_cell)
        ]
    ]
    t_feat = Table(feat_formula_table, colWidths=[125, 230, 85, 58])
    t_feat.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PURPLE),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
        ('PADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(t_feat)
    story.append(PageBreak())
    
    # =========================================================================
    # PÁGINA 5: BENCHMARKING DE MODELOS Y VALIDACIÓN MATEMÁTICA
    # =========================================================================
    story.append(Paragraph("4. Benchmarking de Modelos No Supervisados y Validación", style_h1))
    story.append(Paragraph(
        "Se evaluaron comparativamente tres familias algorítmicas con distintas asunciones geométricas: <b>K-Means++</b> (partición euclidiana "
        "con inicialización inteligente), <b>Gaussian Mixture Models (GMM)</b> (modelado probabilístico con matrices de covarianza completas) y "
        "<b>HDBSCAN</b> (agrupamiento jerárquico basado en densidad natural).",
        style_body
    ))
    
    # Tabla de métricas
    bm_rows = [
        [
            Paragraph("<b>Algoritmo</b>", style_table_header),
            Paragraph("<b>k</b>", style_table_header),
            Paragraph("<b>Silhouette</b>", style_table_header),
            Paragraph("<b>Davies-Bouldin</b>", style_table_header),
            Paragraph("<b>Calinski-Har.</b>", style_table_header),
            Paragraph("<b>BIC / AIC</b>", style_table_header),
            Paragraph("<b>Estabilidad ARI</b>", style_table_header)
        ]
    ]
    for _, r in benchmark_df.iterrows():
        alg = r["Algoritmo"]
        k_val = str(int(r["k"])) if not np.isnan(r["k"]) else "N/A"
        sil_val = f"{r['Silhouette']:.4f}" if not np.isnan(r['Silhouette']) else "N/A"
        db_val = f"{r['Davies-Bouldin']:.4f}" if not np.isnan(r['Davies-Bouldin']) else "N/A"
        ch_val = f"{r['Calinski-Harabasz']:,.0f}" if not np.isnan(r['Calinski-Harabasz']) else "N/A"
        bic_aic = f"{r['BIC']/1e3:.0f}k / {r['AIC']/1e3:.0f}k" if not np.isnan(r['BIC']) else "-"
        ari_val = f"{r['Estabilidad_ARI']:.4f}" if not np.isnan(r['Estabilidad_ARI']) else "-"
        
        is_champ = (alg == "K-Means++" and k_val == "5")
        wrap = (lambda txt: f"<b>{txt}</b>") if is_champ else (lambda txt: str(txt))
        star = " (★)" if is_champ else ""
        
        bm_rows.append([
            Paragraph(wrap(f"{alg}{star}"), style_table_cell_left),
            Paragraph(wrap(k_val), style_table_cell),
            Paragraph(wrap(sil_val), style_table_cell),
            Paragraph(wrap(db_val), style_table_cell),
            Paragraph(wrap(ch_val), style_table_cell),
            Paragraph(wrap(bic_aic), style_table_cell),
            Paragraph(wrap(ari_val), style_table_cell)
        ])
    
    t_bm = Table(bm_rows, colWidths=[95, 25, 65, 75, 75, 90, 73])
    t_bm.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PURPLE),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
        ('PADDING', (0, 0), (-1, -1), 2.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(t_bm)
    story.append(Spacer(1, 6))
    
    story.append(Paragraph(
        "<b>Criterio de Elección del Modelo Campeón:</b> K-Means++ con k=5 logra el mínimo global en el índice Davies-Bouldin (1.4233, "
        "indicando la mayor compacidad intra-cluster y separación inter-cluster) y una sobresaliente estabilidad Bootstrap (ARI = 0.8411 "
        "en 10 submuestreos aleatorios al 80%). GMM mostró sobreajuste y coeficientes Silhouette negativos en k mayores. HDBSCAN demostró "
        "que el fenómeno electoral se distribuye de forma continua sin vacíos de densidad, justificando la partición de Voronoi generada por centroides.",
        style_callout
    ))
    story.append(Spacer(1, 4))
    
    # Gráfica de Benchmark calibrada
    fig_bm_path = os.path.join(ENTREGABLES_FIG, "01_clustering_benchmark_metrics.png")
    if os.path.exists(fig_bm_path):
        story.append(Image(fig_bm_path, width=5.8*inch, height=2.4*inch))
        story.append(Paragraph("<b>Figura 1:</b> Curvas de validación de clustering: Codo de Inercia, Silhouette Score, Davies-Bouldin y Estabilidad Bootstrap ARI.", style_table_cell))
    
    story.append(PageBreak())
    
    # =========================================================================
    # PÁGINA 6: SEPARABILIDAD ESPACIAL Y EXPLICABILIDAD (RANDOM FOREST)
    # =========================================================================
    story.append(Paragraph("5. Separabilidad Espacial, Proyecciones y Explicabilidad", style_h1))
    story.append(Paragraph(
        "Se aplicó Análisis de Componentes Principales (PCA) y la proyección no lineal UMAP para auditar la estructura topológica latente. "
        "Las dos primeras componentes principales explican el <b>60.12% de la varianza</b>. La PC1 está alineada con la intensidad y estabilidad "
        "de la participación, mientras que la PC2 captura la polarización generacional y la volatilidad presidencial-intermedia.",
        style_body
    ))
    
    fig_umap_path = os.path.join(ENTREGABLES_FIG, "02_umap_clusters_projection.png")
    if os.path.exists(fig_umap_path):
        story.append(Image(fig_umap_path, width=5.2*inch, height=2.0*inch))
        story.append(Paragraph("<b>Figura 2:</b> Manifold UMAP bidimensional mostrando la frontera de decisión continua entre los 5 arquetipos cívicos.", style_table_cell))
        story.append(Spacer(1, 4))
        
    story.append(Paragraph("Explicabilidad mediante Random Forest y ANOVA F-Test", style_h2))
    story.append(Paragraph(
        "Se ajustó un modelo <code>RandomForestClassifier</code> multiclase sobre las etiquetas asignadas, obteniendo una <b>exactitud del 94.08%</b>. "
        "El ANOVA F-test confirmó diferencias estadísticamente significativas en las siete dimensiones evaluadas (p < 10⁻¹⁵). "
        "La <i>Estabilidad de Participación</i> (F = 32,985) y la <i>Brecha Presidencial vs. Intermedia</i> (F = 14,948) resultaron ser los "
        "predictores de mayor peso discriminante en la formación de los arquetipos.",
        style_body
    ))
    
    fig_imp_path = os.path.join(ENTREGABLES_FIG, "05_feature_importance_rf.png")
    if os.path.exists(fig_imp_path):
        story.append(Image(fig_imp_path, width=5.5*inch, height=1.6*inch))
        story.append(Paragraph("<b>Figura 3:</b> Importancia de variables por reducción de impureza Gini y pérdida de exactitud por permutación.", style_table_cell))
        
    story.append(PageBreak())
    
    # =========================================================================
    # PÁGINA 7: CARACTERIZACIÓN DETALLADA DE PERFILES - PARTE I
    # =========================================================================
    story.append(Paragraph("6. Caracterización Detallada de los Perfiles Ciudadanos (Parte I)", style_h1))
    story.append(Paragraph(
        "A continuación se desglosan los primeros tres arquetipos cívicos, caracterizados por su peso en el padrón electoral, su perfil demográfico "
        "y sus factores causales de abstención o participación:",
        style_body
    ))
    
    # Radar chart calibrado
    fig_radar_path = os.path.join(ENTREGABLES_FIG, "04_radar_clusters_profiles.png")
    if os.path.exists(fig_radar_path):
        story.append(Image(fig_radar_path, width=3.4*inch, height=2.1*inch))
        story.append(Paragraph("<b>Figura 4:</b> Huella cívica comparativa (Radar Chart) de los 5 arquetipos en variables normalizadas.", style_table_cell))
        story.append(Spacer(1, 4))
        
    story.append(Paragraph("Arquetipo C2: Abstencionismo Estructural Urbano (35.9% secciones | 32.93 M electores)", style_h2))
    story.append(Paragraph(
        "Concentrado en grandes urbes (93% secciones urbanas en CDMX, Puebla y Veracruz; part. media 50.4%). "
        "<b>Factores Causales:</b> Jornadas laborales prolongadas en domingo, lejanía de casillas por reseccionamiento urbano y cinismo institucional.",
        style_body
    ))
    
    story.append(Paragraph("Arquetipo C0: Voto Femenino Consistente (23.9% secciones | 22.59 M electores)", style_h2))
    story.append(Paragraph(
        "Las mujeres lideran la participación con brecha récord de +13.3% sobre hombres (Sinaloa, Chihuahua y Sonora). "
        "<b>Factores Causales:</b> Gran capital social comunitario femenino; enfrentan barreras de dobles jornadas y labores de cuidados no remunerados.",
        style_body
    ))
    
    story.append(Paragraph("Arquetipo C1: Pivote Presidencial Volátil (20.3% secciones | 14.67 M electores)", style_h2))
    story.append(Paragraph(
        "Alta concurrencia en elecciones presidenciales (68%), con desplome de 24.1 puntos en intermedias (Jalisco, Edomex, CDMX). "
        "<b>Factores Causales:</b> Dependencia del clima mediático presidencialista; desinterés en el Congreso por desconocimiento de sus atribuciones.",
        style_body
    ))
    story.append(PageBreak())
    
    # =========================================================================
    # PÁGINA 8: CARACTERIZACIÓN DETALLADA DE PERFILES - PARTE II
    # =========================================================================
    story.append(Paragraph("7. Caracterización Detallada de los Perfiles Ciudadanos (Parte II)", style_h1))
    story.append(Paragraph(
        "Los dos arquetipos complementarios presentan dinámicas determinantes en materia de edad y dispersión territorial:",
        style_body
    ))
    
    story.append(Paragraph("Arquetipo C4: Juventud Movilizada en Expansión (13.6% secciones | 11.10 M electores)", style_h2))
    story.append(Paragraph(
        "Secciones periurbanas y universitarias (Edomex, Veracruz, Guanajuato) con el mayor ratio de participación juvenil relativo (0.88). "
        "<b>Factores Causales:</b> Electorado motivado por causas sociales (empleo digno, justicia ambiental), pero con alta volatilidad si perciben campañas políticas arcaicas.",
        style_body
    ))
    
    story.append(Paragraph("Arquetipo C3: Voto Tradicional Rural y Mayor (6.2% secciones | 4.65 M electores)", style_h2))
    story.append(Paragraph(
        "Bastiones de lealtad cívica con la mayor participación del país (66.4%), fuerte composición rural (58% R) y afluencia de adultos mayores de 60 años. "
        "<b>Factores Causales:</b> El sufragio se percibe como una obligación moral comunitaria; sus barreras principales son de índole física y transporte.",
        style_body
    ))
    story.append(Spacer(1, 4))
    
    # Boxplots demográficos calibrados
    fig_bp_path = os.path.join(ENTREGABLES_FIG, "06_demographic_boxplots.png")
    if os.path.exists(fig_bp_path):
        story.append(Image(fig_bp_path, width=5.6*inch, height=2.4*inch))
        story.append(Paragraph("<b>Figura 5:</b> Distribuciones de participación, brecha presidencial, voto juvenil y brecha de género por arquetipo.", style_table_cell))
        
    story.append(PageBreak())
    
    # =========================================================================
    # PÁGINA 9: ESTRATEGIAS DIFERENCIADAS (ENCÍVICA / INE)
    # =========================================================================
    story.append(Paragraph("8. Estrategias Diferenciadas de Fomento Cívico (ENCÍVICA)", style_h1))
    story.append(Paragraph(
        "Con base en la evidencia empírica generada por el equipo <b>Byte me</b>, se diseñó la siguiente matriz de intervención institucional para "
        "que el Instituto Nacional Electoral y las Juntas Distritales Ejecutivas (JDE) desplieguen acciones orientadas a cada arquetipo:",
        style_body
    ))
    
    strat_matrix_data = [
        [
            Paragraph("<b>Perfil Ciudadano</b>", style_table_header),
            Paragraph("<b>Objetivo Cívico</b>", style_table_header),
            Paragraph("<b>Canal Prioritario</b>", style_table_header),
            Paragraph("<b>Encuadre / Mensaje Clave</b>", style_table_header),
            Paragraph("<b>Mecanismo Operativo INE</b>", style_table_header)
        ],
        [
            Paragraph("<b>C2: Abstencionismo Urbano</b><br/>(32.93 M electores)", style_table_cell_left),
            Paragraph("Reducir la apatía y el costo de oportunidad del voto.", style_table_cell_left),
            Paragraph("Centros de trabajo, transporte masivo (Metro/Metrobús), apps de movilidad.", style_table_cell_left),
            Paragraph("\"Tu ciudad la decides tú: el costo del abstencionismo se paga en transporte y servicios\".", style_table_cell_left),
            Paragraph("Casillas extraordinarias en nodos de transporte y convenios con cámaras empresariales para voto dominical.", style_table_cell_left)
        ],
        [
            Paragraph("<b>C0: Femenino Consistente</b><br/>(22.59 M electores)", style_table_cell_left),
            Paragraph("Empoderar liderazgos locales y remover barreras de cuidados.", style_table_cell_left),
            Paragraph("Redes comunitarias, escuelas, centros de salud y cooperativas de mujeres.", style_table_cell_left),
            Paragraph("\"Mujeres construyendo democracia: la fuerza que transforma nuestras comunidades\".", style_table_cell_left),
            Paragraph("Capacitación cívica comunitaria con enfoque de género y ludotecas infantiles temporales junto a casillas.", style_table_cell_left)
        ],
        [
            Paragraph("<b>C1: Pivote Presidencial</b><br/>(14.67 M electores)", style_table_cell_left),
            Paragraph("Contrarrestar el desplome en elecciones intermedias.", style_table_cell_left),
            Paragraph("Medios masivos locales, radio comunitaria y redes geolocalizadas.", style_table_cell_left),
            Paragraph("\"El Congreso y tu municipio deciden tu presupuesto: ninguna elección es secundaria\".", style_table_cell_left),
            Paragraph("Campañas pedagógicas 6 meses antes de elecciones intermedias sobre el rol del Poder Legislativo.", style_table_cell_left)
        ],
        [
            Paragraph("<b>C4: Juventud en Expansión</b><br/>(11.10 M electores)", style_table_cell_left),
            Paragraph("Fidelizar la participación juvenil post-primer voto.", style_table_cell_left),
            Paragraph("Universidades, TikTok, Instagram, festivales y eventos culturales.", style_table_cell_left),
            Paragraph("\"Votar es exigir: empleo digno, vivienda accesible, justicia ambiental y futuro digital\".", style_table_cell_left),
            Paragraph("Módulos itinerantes del INE en campus universitarios y debates cívicos juveniles sobre causas sociales.", style_table_cell_left)
        ],
        [
            Paragraph("<b>C3: Rural / Mayor</b><br/>(4.65 M electores)", style_table_cell_left),
            Paragraph("Proteger la alta concurrencia y facilitar accesibilidad física.", style_table_cell_left),
            Paragraph("Radio indigenista, asambleas ejidales y perifoneo en lenguas originarias.", style_table_cell_left),
            Paragraph("\"El valor de nuestra palabra: compromiso cívico que inspira a las nuevas generaciones\".", style_table_cell_left),
            Paragraph("Transporte comunitario coordinado, señalética bilingüe en lenguas maternas y plantillas braille prioritarias.", style_table_cell_left)
        ]
    ]
    t_strat = Table(strat_matrix_data, colWidths=[90, 95, 100, 105, 108])
    t_strat.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PURPLE),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
        ('PADDING', (0, 0), (-1, -1), 2.2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(t_strat)
    story.append(Spacer(1, 4))
    
    fig_geo_path = os.path.join(ENTREGABLES_FIG, "07_geographic_distribution.png")
    if os.path.exists(fig_geo_path):
        story.append(Image(fig_geo_path, width=5.5*inch, height=1.9*inch))
        story.append(Paragraph("<b>Figura 6:</b> Distribución territorial (Urbana/Rural) y volumen absoluto de electores (LN 2024) por arquetipo ciudadano.", style_table_cell))
        
    story.append(PageBreak())
    
    # =========================================================================
    # PÁGINA 10: GOBERNANZA DE DATOS, REPRODUCIBILIDAD Y FIRMAS
    # =========================================================================
    story.append(Paragraph("9. Gobernanza de Datos, Ética y Reproducibilidad MLOps", style_h1))
    story.append(Paragraph(
        "En estricto apego a las políticas de Datos Abiertos y Protección de Datos Personales, todo el análisis fue ejecutado sobre "
        "datos agregados seccionales derivados de cuadernillos censales, sin involucrar datos de identificación individual (PII). "
        "Los sesgos algorítmicos fueron mitigados mediante el escalado robusto por medianas e IQR y el control exhaustivo de multicolinealidad.",
        style_body
    ))
    
    repro_table_data = [
        [Paragraph("<b>Componente / Entorno</b>", style_table_header), Paragraph("<b>Especificación Técnica del Pipeline</b>", style_table_header)],
        [Paragraph("Lenguaje y Sistema Operativo", style_table_cell_left), Paragraph("Python 3.14.8 (Linux x86_64, Kernel 6.8)", style_table_cell_left)],
        [Paragraph("Motor de Ingesta In-Memory", style_table_cell_left), Paragraph("DuckDB 2.0.0 (Procesamiento vectorizado sobre archivos ZIP)", style_table_cell_left)],
        [Paragraph("Modelado Estadístico y MLOps", style_table_cell_left), Paragraph("scikit-learn 1.9.0, scipy 1.18.0, umap-learn 0.5.12, python-pptx 1.0.2", style_table_cell_left)],
        [Paragraph("Compilador Editorial PDF", style_table_cell_left), Paragraph("ReportLab 5.1.0 (Platypus Flowables & NumberedCanvas 2-Pass)", style_table_cell_left)],
        [Paragraph("Semillas Aleatorias Fijadas", style_table_cell_left), Paragraph("random_state = 42 (K-Means, GMM, PCA, UMAP, RF, Bootstrap)", style_table_cell_left)],
        [Paragraph("Universo Analizado y Válido", style_table_cell_left), Paragraph("62,048 secciones continuas (100% clasificadas, 0 NaNs, 0 Infs, 0 Ruido)", style_table_cell_left)]
    ]
    t_repro = Table(repro_table_data, colWidths=[170, 328])
    t_repro.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PURPLE),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(t_repro)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Conclusiones Finales", style_h2))
    story.append(Paragraph(
        "El Reto 1 demuestra que los datos censales del INE contienen patrones conductuales estructurados y estables a lo largo del tiempo. "
        "La segmentación en cinco perfiles arquetípicos desarrollada por <b>Byte me</b> traslada la analítica de datos a la acción "
        "institucional, dotando a la ENCÍVICA de herramientas cuantitativas precisas para construir una ciudadanía más activa, incluyente "
        "y comprometida con la democracia mexicana.",
        style_body
    ))
    story.append(Spacer(1, 15))
    
    # Firmas del Equipo
    sign_table_data = [
        [
            Paragraph("____________________________________________<br/><b>Johanan Olivares Gutierrez</b><br/>Representante del Equipo<br/>Científico de Datos Principal / MLOps", style_table_cell),
            Paragraph("____________________________________________<br/><b>Oscar Ariel Cuevas Martinez</b><br/>Integrante del Equipo<br/>Especialista en Modelación Social", style_table_cell)
        ],
        [
            Paragraph("<br/>____________________________________________<br/><b>Saul Alexis Arias Gonzales</b><br/>Integrante del Equipo<br/>Diseñador de Información de Políticas Públicas", style_table_cell),
            Paragraph("<br/><b>INSTITUTO NACIONAL ELECTORAL</b><br/>Concurso CCPC 2009–2024 / ENCÍVICA<br/><i>\"Datos que construyen democracia\"</i>", style_table_cell)
        ]
    ]
    t_sign = Table(sign_table_data, colWidths=[249, 249])
    t_sign.setStyle(TableStyle([
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(t_sign)
    
    # Construir documento
    doc.build(story, canvasmaker=NumberedCanvas)
    
    # Comprobar número exacto de páginas
    reader = pypdf.PdfReader(OUTPUT_PDF)
    actual_pages = len(reader.pages)
    pdf_size_kb = os.path.getsize(OUTPUT_PDF) / 1024
    logger.info(f"Documento Técnico generado con éxito: {actual_pages} páginas ({pdf_size_kb:.1f} KB).")
    assert 8 <= actual_pages <= 12, f"FALLO REGLAMENTARIO: El documento tiene {actual_pages} páginas; debe tener entre 8 y 12."
    logger.info(f"✓ Validación reglamentaria superada: {actual_pages} páginas cumple la condición 8 <= páginas <= 12.")
    return OUTPUT_PDF, actual_pages

if __name__ == "__main__":
    build_technical_document()
