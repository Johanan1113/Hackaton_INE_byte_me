"""
Módulo 06: Generador de la Presentación Ejecutiva en PPTX y PDF (16:9 Widescreen)
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
import subprocess

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Configuración de Logging
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("06_presentation")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DATASETS = os.path.join(PROJECT_ROOT, "output", "datasets")
ENTREGABLES_DIR = os.path.join(PROJECT_ROOT, "entregables_finales")
ENTREGABLES_FIG = os.path.join(ENTREGABLES_DIR, "figures")
OUTPUT_PPTX = os.path.join(ENTREGABLES_DIR, "Presentacion_Ejecutiva_Reto1_ByteMe.pptx")
OUTPUT_PDF = os.path.join(ENTREGABLES_DIR, "Presentacion_Ejecutiva_Reto1_ByteMe.pdf")

# Paleta de Colores Institucional
COLOR_PURPLE = RGBColor(0x58, 0x2D, 0x73)   # Primario
COLOR_MAGENTA = RGBColor(0xD1, 0x36, 0x7E)  # Secundario
COLOR_TEAL = RGBColor(0x00, 0xA8, 0x96)     # Terciario
COLOR_AMBER = RGBColor(0xE6, 0x7E, 0x22)    # Soporte
COLOR_DARK = RGBColor(0x1E, 0x1E, 0x24)     # Texto
COLOR_MUTED = RGBColor(0x5A, 0x62, 0x75)    # Secundario
COLOR_LIGHT_BG = RGBColor(0xF9, 0xF9, 0xFB) # Fondo
COLOR_CARD_BG = RGBColor(0xFF, 0xFF, 0xFF)  # Tarjetas
COLOR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)    # Blanco
COLOR_BORDER = RGBColor(0xE2, 0xE8, 0xF0)   # Bordes

def add_header(slide, title_text, category_text="RETO 1: PERFILES CIUDADANOS DE PARTICIPACIÓN"):
    """Agrega pleca y encabezado estándar de estilo suizo corporativo."""
    # Barra superior morada
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    bar.fill.solid()
    bar.fill.fore_color.rgb = COLOR_PURPLE
    bar.line.fill.background()
    
    # Texto categoría / equipo
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.25), Inches(11.7), Inches(0.35))
    tf_c = cat_box.text_frame
    tf_c.word_wrap = True
    p_c = tf_c.paragraphs[0]
    p_c.text = f"{category_text.upper()}   |   EQUIPO: BYTE ME   |   INE / ENCÍVICA 2024"
    p_c.font.name = "Arial"
    p_c.font.size = Pt(9.5)
    p_c.font.bold = True
    p_c.font.color.rgb = COLOR_MAGENTA
    
    # Título principal de la diapositiva
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.55), Inches(11.7), Inches(0.75))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = title_text
    p_t.font.name = "Arial"
    p_t.font.size = Pt(22)
    p_t.font.bold = True
    p_t.font.color.rgb = COLOR_PURPLE

def add_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER):
    """Crea una tarjeta contenedora limpia para estructurar información."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
    else:
        card.line.fill.background()
    return card

def build_presentation():
    logger.info("=== GENERACIÓN DE PRESENTACIÓN EJECUTIVA (PPTX) ===")
    os.makedirs(ENTREGABLES_DIR, exist_ok=True)
    
    # Cargar fichas enriquecidas
    fichas_path = os.path.join(OUTPUT_DATASETS, "arquetipos_fichas.json")
    with open(fichas_path, "r", encoding="utf-8") as f:
        fichas = json.load(f)
        
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]  # Diapositiva en blanco
    
    # =========================================================================
    # SLIDE 1: PORTADA
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    # Fondo con bloque lateral púrpura
    side_rect = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(4.5), Inches(7.5))
    side_rect.fill.solid()
    side_rect.fill.fore_color.rgb = COLOR_PURPLE
    side_rect.line.fill.background()
    
    # Texto lateral institucional
    sb_box = s1.shapes.add_textbox(Inches(0.6), Inches(1.5), Inches(3.4), Inches(4.5))
    tf_sb = sb_box.text_frame
    tf_sb.word_wrap = True
    
    p = tf_sb.paragraphs[0]
    p.text = "INSTITUTO NACIONAL\nELECTORAL"
    p.font.name = "Arial"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_after = Pt(20)
    
    p2 = tf_sb.add_paragraph()
    p2.text = "Concurso Oficial:\n\"Hackea la Participación:\nDatos que construyen democracia\"\n\nCCPC 2009–2024\nENCÍVICA 2024"
    p2.font.name = "Arial"
    p2.font.size = Pt(13)
    p2.font.color.rgb = RGBColor(0xEB, 0xD4, 0xF5)
    
    # Contenido principal de portada
    main_box = s1.shapes.add_textbox(Inches(5.0), Inches(1.0), Inches(7.5), Inches(5.5))
    tf_m = main_box.text_frame
    tf_m.word_wrap = True
    
    p_badge = tf_m.paragraphs[0]
    p_badge.text = "RETO 1: PERFILES CIUDADANOS DE PARTICIPACIÓN"
    p_badge.font.name = "Arial"
    p_badge.font.size = Pt(12)
    p_badge.font.bold = True
    p_badge.font.color.rgb = COLOR_MAGENTA
    p_badge.space_after = Pt(10)
    
    p_title = tf_m.add_paragraph()
    p_title.text = "Segmentación No Supervisada, Dinámica Longitudinal (2009–2024) y Estrategias Cívicas Focalizadas"
    p_title.font.name = "Arial"
    p_title.font.size = Pt(26)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_PURPLE
    p_title.space_after = Pt(25)
    
    p_team = tf_m.add_paragraph()
    p_team.text = "EQUIPO: BYTE ME\n"
    p_team.font.name = "Arial"
    p_team.font.size = Pt(15)
    p_team.font.bold = True
    p_team.font.color.rgb = COLOR_DARK
    
    p_members = tf_m.add_paragraph()
    p_members.text = (
        "• Johanan Olivares Gutierrez (Representante  |  Científico de Datos Principal / MLOps)\n"
        "• Oscar Ariel Cuevas Martinez (Especialista en Modelación Social Computacional)\n"
        "• Saul Alexis Arias Gonzales (Diseñador de Información para Políticas Públicas)"
    )
    p_members.font.name = "Arial"
    p_members.font.size = Pt(11.5)
    p_members.font.color.rgb = COLOR_MUTED
    p_members.space_before = Pt(8)
    
    # =========================================================================
    # SLIDE 2: EL RETO DEMOCRÁTICO EN DATOS (2009 - 2024)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "El Reto Democrático en Datos: 15 Años de Elecciones Federales")
    
    kpis = [
        ("62,048", "Secciones Electorales", "Panel balanceado longitudinal con 100% de presencia en 6 elecciones federales (2009-2024).", COLOR_PURPLE),
        ("53.6%", "Participación Media", "Promedio nacional histórico con oscilaciones entre el 43.8% (2009) y el 62.5% (2012).", COLOR_TEAL),
        ("+12.3%", "Brecha Presidencial", "Desplome sistemático en elecciones intermedias que en ciertos perfiles alcanza hasta 24.1%.", COLOR_AMBER),
        ("+7.4%", "Brecha Pro-Mujeres", "Las mujeres superan sistemáticamente a los hombres en asistencia a urnas en todo el país.", COLOR_MAGENTA)
    ]
    
    for i, (kpi, label, desc, col) in enumerate(kpis):
        left = Inches(0.8 + i * 2.95)
        add_card(s2, left, Inches(1.5), Inches(2.8), Inches(4.8))
        
        box = s2.shapes.add_textbox(left + Inches(0.2), Inches(1.7), Inches(2.4), Inches(4.3))
        tf = box.text_frame
        tf.word_wrap = True
        
        pk = tf.paragraphs[0]
        pk.text = kpi
        pk.font.name = "Arial"
        pk.font.size = Pt(30)
        pk.font.bold = True
        pk.font.color.rgb = col
        pk.space_after = Pt(6)
        
        pl = tf.add_paragraph()
        pl.text = label
        pl.font.name = "Arial"
        pl.font.size = Pt(13)
        pl.font.bold = True
        pl.font.color.rgb = COLOR_DARK
        pl.space_after = Pt(12)
        
        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.name = "Arial"
        pd.font.size = Pt(10.5)
        pd.font.color.rgb = COLOR_MUTED
        
    foot_box = s2.shapes.add_textbox(Inches(0.8), Inches(6.5), Inches(11.7), Inches(0.5))
    foot_box.text_frame.paragraphs[0].text = "Fuente: Conteos Censales de Participación Ciudadana (CCPC 2009–2024), procesados con DuckDB in-memory por el equipo Byte me."
    foot_box.text_frame.paragraphs[0].font.size = Pt(9.5)
    foot_box.text_frame.paragraphs[0].font.color.rgb = COLOR_MUTED
    
    # =========================================================================
    # SLIDE 3: METODOLOGÍA Y PIPELINE DE INGENIERÍA
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Metodología: Pipeline Resiliente ante Redistritaciones")
    
    steps = [
        ("1. Ingesta Vectorizada", "DuckDB In-Memory", "Lectura directa sobre archivos ZIP de 6 elecciones federales sin colapsar memoria RAM (procesamiento en <40s)."),
        ("2. Armonización Cartográfica", "62,048 Secciones Clave", "Control de las redistritaciones 2017 y 2022: se aisló el conjunto seccional continuo (85.4% del país, 99.1% de municipios)."),
        ("3. Ingeniería de Tasas", "Control VIF < 3.5", "Sustitución de tasas colineales por la Brecha Generacional y el Ratio Joven. Eliminación total de multicolinealidad."),
        ("4. Escalado Robusto", "RobustScaler (Mediana/IQR)", "Normalización resistente a casillas atípicas y preservación de distancias relativas para clustering.")
    ]
    
    for i, (title, sub, txt) in enumerate(steps):
        top = Inches(1.5 + i * 1.3)
        add_card(s3, Inches(0.8), top, Inches(11.7), Inches(1.15))
        
        box = s3.shapes.add_textbox(Inches(1.0), top + Inches(0.12), Inches(11.3), Inches(0.9))
        tf = box.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.text = f"{title}   |   {sub}"
        p1.font.name = "Arial"
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_PURPLE
        p1.space_after = Pt(4)
        
        p2 = tf.add_paragraph()
        p2.text = txt
        p2.font.name = "Arial"
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = COLOR_DARK
        
    # =========================================================================
    # SLIDE 4: VALIDACIÓN MATEMÁTICA Y BENCHMARKING DE CLUSTERING
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "Validación Matemática: K-Means++ vs. GMM vs. HDBSCAN")
    
    # Tarjeta izquierda con tabla de métricas
    add_card(s4, Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.3))
    t_box = s4.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.4), Inches(4.8))
    tf_tb = t_box.text_frame
    tf_tb.word_wrap = True
    
    p_th = tf_tb.paragraphs[0]
    p_th.text = "Resultados del Benchmark Cuantitativo:"
    p_th.font.size = Pt(13)
    p_th.font.bold = True
    p_th.font.color.rgb = COLOR_PURPLE
    p_th.space_after = Pt(10)
    
    p_res = tf_tb.add_paragraph()
    p_res.text = (
        "• K-Means++ (k=5) [CAMPEÓN ★]:\n"
        "   - Silhouette: 0.1805  |  Davies-Bouldin: 1.4233 (Mínimo óptimo)\n"
        "   - Estabilidad Bootstrap: ARI = 0.8411 (10 semillas al 80%)\n"
        "   - Asignación: 100% clasificado (cero ruido residual).\n\n"
        "• K-Means++ (k=3 a 7):\n"
        "   - Codo claro de inercia en k=5; desaceleración en k>5.\n\n"
        "• Gaussian Mixture Models (GMM):\n"
        "   - Sobreajuste en k>=4 (Silhouette negativo, DB > 3.10).\n\n"
        "• HDBSCAN:\n"
        "   - Identificó que el electorado forma un continuum denso,\n"
        "     justificando la partición por centroides de Voronoi."
    )
    p_res.font.size = Pt(10.5)
    p_res.font.color.rgb = COLOR_DARK
    
    # Imagen de benchmark a la derecha
    fig_bm = os.path.join(ENTREGABLES_FIG, "01_clustering_benchmark_metrics.png")
    if os.path.exists(fig_bm):
        s4.shapes.add_picture(fig_bm, Inches(6.8), Inches(1.5), width=Inches(5.7), height=Inches(5.3))
        
    # =========================================================================
    # SLIDE 5: MAPA GENERAL DE ARQUETIPOS ELECTORALES (UMAP & PCA)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Mapa General de Arquetipos Electorales (Topología UMAP)")
    
    # Imagen UMAP
    fig_umap = os.path.join(ENTREGABLES_FIG, "02_umap_clusters_projection.png")
    if os.path.exists(fig_umap):
        s5.shapes.add_picture(fig_umap, Inches(0.8), Inches(1.5), width=Inches(6.8), height=Inches(5.3))
        
    # Tarjeta explicativa derecha
    add_card(s5, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.3))
    box_u = s5.shapes.add_textbox(Inches(8.0), Inches(1.7), Inches(4.3), Inches(4.8))
    tf_u = box_u.text_frame
    tf_u.word_wrap = True
    
    pu_title = tf_u.paragraphs[0]
    pu_title.text = "Estructura del Manifold Electoral:"
    pu_title.font.size = Pt(13)
    pu_title.font.bold = True
    pu_title.font.color.rgb = COLOR_PURPLE
    pu_title.space_after = Pt(10)
    
    pu_txt = tf_u.add_paragraph()
    pu_txt.text = (
        "• Varianza Explicada PCA: 60.12% en 2 componentes (PC1 = 37.9%, PC2 = 22.2%).\n\n"
        "• Eje Horizontal: Intensidad y lealtad histórica del voto (de abstención a alta concurrencia).\n\n"
        "• Eje Vertical: Volatilidad presidencial vs. sesgo demográfico de género/edad.\n\n"
        "• Separabilidad Confirmada: Clasificador Random Forest reconstruye las etiquetas con 94.08% de exactitud y ANOVA F-test con p < 10⁻¹⁵."
    )
    pu_txt.font.size = Pt(10.5)
    pu_txt.font.color.rgb = COLOR_DARK
    
    # =========================================================================
    # SLIDE 6: FICHAS DE PERFIL 1 Y 2 (C2 Y C4)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Perfiles Prioritarios: Abstencionismo Urbano y Juventud")
    
    # Tarjeta C2
    add_card(s6, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.3))
    b_c2 = s6.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.3), Inches(4.8))
    tf_c2 = b_c2.text_frame
    tf_c2.word_wrap = True
    
    p = tf_c2.paragraphs[0]
    p.text = "C2: Abstencionismo Estructural Urbano"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_AMBER
    p.space_after = Pt(6)
    
    p_sub = tf_c2.add_paragraph()
    p_sub.text = "35.9% de secciones  |  32.93 M electores (38.3% del Padrón Nacional)"
    p_sub.font.size = Pt(10.5)
    p_sub.font.bold = True
    p_sub.font.color.rgb = COLOR_DARK
    p_sub.space_after = Pt(10)
    
    p_body = tf_c2.add_paragraph()
    p_body.text = (
        "• Comportamiento: Participación media de 50.4%, la más baja del país. 93% secciones urbanas en CDMX, Puebla y Veracruz.\n\n"
        "• Factor Causal: Jornadas laborales dominicales, lejanía por reseccionamiento urbano y cinismo ante la política partidista.\n\n"
        "• Lema Cívico: \"Tu ciudad es tu decisión: el costo del silencio se paga en servicios y transporte\".\n\n"
        "• Acción INE: Casillas extraordinarias en nodos de transporte y convenios patronales de permisos dominicales."
    )
    p_body.font.size = Pt(10)
    p_body.font.color.rgb = COLOR_DARK
    
    # Tarjeta C4
    add_card(s6, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.3))
    b_c4 = s6.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.3), Inches(4.8))
    tf_c4 = b_c4.text_frame
    tf_c4.word_wrap = True
    
    p = tf_c4.paragraphs[0]
    p.text = "C4: Juventud Movilizada en Expansión"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEAL
    p.space_after = Pt(6)
    
    p_sub = tf_c4.add_paragraph()
    p_sub.text = "13.6% de secciones  |  11.10 M electores (12.9% del Padrón Nacional)"
    p_sub.font.size = Pt(10.5)
    p_sub.font.bold = True
    p_sub.font.color.rgb = COLOR_DARK
    p_sub.space_after = Pt(10)
    
    p_body = tf_c4.add_paragraph()
    p_body.text = (
        "• Comportamiento: Máximo dinamismo juvenil relativo (ratio 0.88 respecto a la media seccional). Edomex, Veracruz, Guanajuato.\n\n"
        "• Factor Causal: Movilización por causas sociales (empleo, clima, derechos); deserción tras el primer voto por falta de representación.\n\n"
        "• Lema Cívico: \"El futuro no espera: votar es exigir empleo digno, medio ambiente y derechos\".\n\n"
        "• Acción INE: Módulos itinerantes en campus universitarios y debates cívicos en formatos de streaming."
    )
    p_body.font.size = Pt(10)
    p_body.font.color.rgb = COLOR_DARK
    
    # =========================================================================
    # SLIDE 7: FICHAS DE PERFIL 3 Y 4 (C1 Y C0)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Perfiles: Volatilidad Presidencial y Núcleo Femenino")
    
    # Tarjeta C1
    add_card(s7, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.3))
    b_c1 = s7.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.3), Inches(4.8))
    tf_c1 = b_c1.text_frame
    tf_c1.word_wrap = True
    
    p = tf_c1.paragraphs[0]
    p.text = "C1: Pivote Presidencial Volátil"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_PURPLE
    p.space_after = Pt(6)
    
    p_sub = tf_c1.add_paragraph()
    p_sub.text = "20.3% de secciones  |  14.67 M electores (17.1% del Padrón Nacional)"
    p_sub.font.size = Pt(10.5)
    p_sub.font.bold = True
    p_sub.font.color.rgb = COLOR_DARK
    p_sub.space_after = Pt(10)
    
    p_body = tf_c1.add_paragraph()
    p_body.text = (
        "• Comportamiento: Votan masivamente en presidenciales (68%), pero se desploman 24.1 puntos porcentuales en comicios intermedios.\n\n"
        "• Factor Causal: Narrativa hiperpresidencialista mediática; desconocimiento del papel del Congreso en la vida diaria.\n\n"
        "• Lema Cívico: \"Tu voz en cada periodo: el Congreso y tu municipio deciden tu presupuesto\".\n\n"
        "• Acción INE: Campañas de pedagogía legislativa anticipadas 6 meses antes de elecciones intermedias."
    )
    p_body.font.size = Pt(10)
    p_body.font.color.rgb = COLOR_DARK
    
    # Tarjeta C0
    add_card(s7, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.3))
    b_c0 = s7.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.3), Inches(4.8))
    tf_c0 = b_c0.text_frame
    tf_c0.word_wrap = True
    
    p = tf_c0.paragraphs[0]
    p.text = "C0: Voto Femenino Consistente"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_MAGENTA
    p.space_after = Pt(6)
    
    p_sub = tf_c0.add_paragraph()
    p_sub.text = "23.9% de secciones  |  22.59 M electores (26.3% del Padrón Nacional)"
    p_sub.font.size = Pt(10.5)
    p_sub.font.bold = True
    p_sub.font.color.rgb = COLOR_DARK
    p_sub.space_after = Pt(10)
    
    p_body = tf_c0.add_paragraph()
    p_body.text = (
        "• Comportamiento: Máxima brecha pro-mujeres del país (+13.3% sobre hombres). Columna vertebral vecinal en Sinaloa y Chihuahua.\n\n"
        "• Factor Causal: Fuerte capital social de base; barreras de dobles jornadas y tareas de cuidados no remuneradas.\n\n"
        "• Lema Cívico: \"Mujeres al frente: la fuerza organizada que transforma comunidades\".\n\n"
        "• Acción INE: Formación cívica con perspectiva de género y ludotecas de apoyo para funcionarias y votantes con infantes."
    )
    p_body.font.size = Pt(10)
    p_body.font.color.rgb = COLOR_DARK
    
    # =========================================================================
    # SLIDE 8: FICHA PERFIL 5 (C3) Y RADAR CHART COMPARATIVO
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Perfil Rural / Mayor y Huella Cívica Multivariable")
    
    # Tarjeta C3 izquierda
    add_card(s8, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.3))
    b_c3 = s8.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.3), Inches(4.8))
    tf_c3 = b_c3.text_frame
    tf_c3.word_wrap = True
    
    p = tf_c3.paragraphs[0]
    p.text = "C3: Voto Tradicional Rural y Mayor"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEAL
    p.space_after = Pt(6)
    
    p_sub = tf_c3.add_paragraph()
    p_sub.text = "6.2% de secciones  |  4.65 M electores (5.4% del Padrón Nacional)"
    p_sub.font.size = Pt(10.5)
    p_sub.font.bold = True
    p_sub.font.color.rgb = COLOR_DARK
    p_sub.space_after = Pt(10)
    
    p_body = tf_c3.add_paragraph()
    p_body.text = (
        "• Comportamiento: Máxima afluencia histórica de México (66.4% de participación media). 58% rural en Nuevo León, San Luis Potosí y Oaxaca.\n\n"
        "• Factor Causal: Voto concebido como deber moral y comunitario intergeneracional. Barreras de distancia física y dispersión geográfica.\n\n"
        "• Lema Cívico: \"Tradición que une: el valor de la palabra y el compromiso comunitario\".\n\n"
        "• Acción INE: Transporte comunitario coordinado, señalética bilingüe en lenguas originarias y accesibilidad para adultos mayores."
    )
    p_body.font.size = Pt(10)
    p_body.font.color.rgb = COLOR_DARK
    
    # Radar Chart derecha
    fig_radar = os.path.join(ENTREGABLES_FIG, "04_radar_clusters_profiles.png")
    if os.path.exists(fig_radar):
        s8.shapes.add_picture(fig_radar, Inches(6.8), Inches(1.5), width=Inches(5.7), height=Inches(5.3))
        
    # =========================================================================
    # SLIDE 9: MATRIZ ESTRATÉGICA ENCÍVICA / INE
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Matriz Estratégica Institucional para la ENCÍVICA")
    
    # Tabla resumen de acciones
    rows = [
        ("C2: Abstencionismo Urbano", "Reducir el costo del voto", "Transporte masivo, apps y corporativos", "Casillas especiales urbanas y convenios patronales"),
        ("C0: Femenino Consistente", "Reconocer liderazgos locales", "Redes vecinales y centros de salud", "Ludotecas infantiles junto a casillas y formación"),
        ("C1: Pivote Presidencial", "Frenar caída en intermedias", "Medios masivos locales y radio", "Campañas pedagógicas previas sobre el Congreso"),
        ("C4: Juventud en Expansión", "Fidelizar post-primer voto", "Universidades, streaming y TikTok", "Módulos itinerantes y debates cívicos de causas"),
        ("C3: Rural y Mayor", "Garantizar accesibilidad física", "Radio indigenista y asambleas ejidales", "Transporte coordinado y señalética bilingüe")
    ]
    
    # Encabezado tabla
    th_card = add_card(s9, Inches(0.8), Inches(1.5), Inches(11.7), Inches(0.55), bg_color=COLOR_PURPLE)
    b_th = s9.shapes.add_textbox(Inches(0.9), Inches(1.55), Inches(11.5), Inches(0.45))
    tf_th = b_th.text_frame
    p_th = tf_th.paragraphs[0]
    p_th.text = "ARQUETIPO              OBJETIVO CÍVICO             CANAL PRIORITARIO                   ACCIÓN OPERATIVA INE"
    p_th.font.size = Pt(11)
    p_th.font.bold = True
    p_th.font.color.rgb = COLOR_WHITE
    
    for i, (arq, obj, can, acc) in enumerate(rows):
        top = Inches(2.15 + i * 0.95)
        add_card(s9, Inches(0.8), top, Inches(11.7), Inches(0.85))
        
        box = s9.shapes.add_textbox(Inches(1.0), top + Inches(0.1), Inches(11.3), Inches(0.65))
        tf = box.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = f"• {arq}:  {obj}\n   Canal: {can}   |   Acción: {acc}"
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_DARK
        
    # =========================================================================
    # SLIDE 10: CONCLUSIONES Y FACTIBILIDAD DE DESPLIEGUE
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Conclusiones Estratégicas y Factibilidad de Despliegue")
    
    concl = [
        ("Factibilidad Inmediata", "Uso Directo de Infraestructura INE", "No requiere reformas legislativas; se instrumenta a través de los acuerdos de Consejo General del INE y planes de trabajo de las Juntas Distritales."),
        ("Micro-Focalización Territorial", "Superación de Campañas Genéricas", "La ENCÍVICA cuenta ahora con la georreferenciación de las 62,048 secciones asignadas a cada perfil para asignar presupuesto con precisión quirúrgica."),
        ("Ética y Datos Abiertos", "100% Reproducible y Transparente", "Pipeline completamente auditado en Python con datos agregados seccionales libres de PII, garantizando protección de datos y soberanía tecnológica.")
    ]
    
    for i, (tit, subt, txt) in enumerate(concl):
        top = Inches(1.5 + i * 1.5)
        add_card(s10, Inches(0.8), top, Inches(11.7), Inches(1.3))
        
        box = s10.shapes.add_textbox(Inches(1.1), top + Inches(0.15), Inches(11.1), Inches(1.0))
        tf = box.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = f"{tit}  •  {subt}"
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = COLOR_PURPLE
        p.space_after = Pt(4)
        
        p2 = tf.add_paragraph()
        p2.text = txt
        p2.font.size = Pt(11)
        p2.font.color.rgb = COLOR_DARK
        
    foot_box = s10.shapes.add_textbox(Inches(0.8), Inches(6.4), Inches(11.7), Inches(0.6))
    p_f = foot_box.text_frame.paragraphs[0]
    p_f.text = "Equipo Byte me  |  Johanan Olivares Gutierrez  •  Oscar Ariel Cuevas Martinez  •  Saul Alexis Arias Gonzales"
    p_f.font.size = Pt(10.5)
    p_f.font.bold = True
    p_f.font.color.rgb = COLOR_MAGENTA
    p_f.alignment = PP_ALIGN.CENTER
    
    # Guardar PPTX
    prs.save(OUTPUT_PPTX)
    logger.info(f"Presentación PPTX guardada exitosamente: {OUTPUT_PPTX}")
    assert len(prs.slides) <= 10, f"La presentación excede 10 slides: {len(prs.slides)}"
    logger.info(f"✓ Validación reglamentaria superada: exactamente {len(prs.slides)} diapositivas.")
    
    # Conversión a PDF vía LibreOffice
    logger.info("Convirtiendo presentación PPTX a PDF con LibreOffice...")
    cmd = ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", ENTREGABLES_DIR, OUTPUT_PPTX]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0 and os.path.exists(OUTPUT_PDF):
        logger.info(f"Presentación convertida exitosamente a PDF: {OUTPUT_PDF} ({os.path.getsize(OUTPUT_PDF)/1024:.1f} KB)")
    else:
        logger.error(f"Error en conversión libreoffice: {proc.stderr}")
        
    return OUTPUT_PPTX, OUTPUT_PDF

if __name__ == "__main__":
    build_presentation()
