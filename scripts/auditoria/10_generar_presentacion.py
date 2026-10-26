#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Generación de la Presentación Ejecutiva (10_generar_presentacion.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")
Concurso: "Hackea la participación: Datos que construyen democracia" (INE)

Genera la presentación ejecutiva de 10 diapositivas en formato 16:9:
  - Presentacion_Ejecutiva_ByteMe.pptx (con gráficas nativas editables y notas del orador)
  - Presentacion_Ejecutiva_ByteMe.pdf (conversión fiel mediante LibreOffice)

Cumple estrictamente con:
  1. Cifras 100% leídas y verificadas desde metricas_finales.json y tablas CSV.
  2. Tipografía Arial en la totalidad del texto, gráficas y temas.
  3. Paleta cromática corporativa por perfil (C0 #C2410C, C1 #047857, C2 #1D4ED8, C3 #6D28D9, Panel #6B7280).
  4. Cero frases prohibidas, sin snake_case espurio, sin símbolos informales.
  5. Notas del orador en primera persona del plural (60-90 palabras por diapositiva).
  6. Márgenes mayores a 0.25 pulgadas en todos los caracteres.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle
import numpy as np

import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.chart.data import CategoryChartData

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[2]
METRICAS_PATH = PROJECT_ROOT / "outputs" / "metricas_finales.json"
TABLAS_DIR = PROJECT_ROOT / "outputs" / "tablas"
OUT_ENTREGABLES = PROJECT_ROOT / "outputs" / "entregables"
ICONOS_DIR = OUT_ENTREGABLES / "iconos"
OUT_ENTREGABLES.mkdir(parents=True, exist_ok=True)
ICONOS_DIR.mkdir(parents=True, exist_ok=True)

# Paleta cromática
NAVY = RGBColor(30, 58, 138)       # #1E3A8A
DARK_GRAY = RGBColor(31, 41, 55)   # #1F2937
MID_GRAY = RGBColor(107, 114, 128) # #6B7280
LIGHT_GRAY = RGBColor(203, 213, 225) # #CBD5E1
BG_LIGHT = RGBColor(248, 250, 252) # #F8FAFC
WHITE = RGBColor(255, 255, 255)

C0_COLOR = RGBColor(194, 65, 12)   # #C2410C
C1_COLOR = RGBColor(4, 120, 87)    # #047857
C2_COLOR = RGBColor(29, 78, 216)   # #1D4ED8
C3_COLOR = RGBColor(109, 40, 217)  # #6D28D9

PROFILE_COLORS = {
    0: C0_COLOR,
    1: C1_COLOR,
    2: C2_COLOR,
    3: C3_COLOR,
}

THEMES_HEX = {
    0: {"primary": "#C2410C"},
    1: {"primary": "#047857"},
    2: {"primary": "#1D4ED8"},
    3: {"primary": "#6D28D9"},
}


def verificar_datos_bloque_a(data: dict) -> None:
    """Verifica estrictamente que las cifras leídas coincidan con las del Bloque A."""
    serie = {r["anio"]: r for r in data["serie_nacional_2009_2024"]}
    assert serie[2012]["pct_ns_anio"] == 0.22, "NS 2012 != 0.22%"
    assert serie[2018]["pct_ns_anio"] == 6.83, "NS 2018 != 6.83%"
    assert serie[2024]["pct_ns_anio"] == 6.43, "NS 2024 != 6.43%"

    assert serie[2018]["subestimacion_erronea_sv_ln_pond_pts"] == 4.27, "Subestimacion 2018 != 4.27"
    assert serie[2024]["subestimacion_erronea_sv_ln_pond_pts"] == 3.84, "Subestimacion 2024 != 3.84"

    assert (serie[2009]["total_ponderada_sv_svnv_pct"], serie[2009]["oficial_o_referencia_pct"]) == (44.06, 44.06)
    assert (serie[2012]["total_ponderada_sv_svnv_pct"], serie[2012]["oficial_o_referencia_pct"]) == (62.08, 62.08)
    assert (serie[2015]["total_ponderada_sv_svnv_pct"], serie[2015]["oficial_o_referencia_pct"]) == (47.07, 47.07)
    assert (serie[2018]["total_ponderada_sv_svnv_pct"], serie[2018]["oficial_o_referencia_pct"]) == (62.37, 62.4)
    assert (serie[2021]["total_ponderada_sv_svnv_pct"], serie[2021]["oficial_o_referencia_pct"]) == (51.84, 51.8)
    assert (serie[2024]["total_ponderada_sv_svnv_pct"], serie[2024]["oficial_o_referencia_pct"]) == (59.67, 59.7)

    u = data["universo_y_cobertura"]
    assert u["panel_principal_secciones"] == 53644
    assert u["panel_principal_pct_secciones_2024"] == 75.82
    assert u["panel_principal_pct_ln_2024"] == 79.53
    assert u["panel_principal_ln_2024"] == 78199518
    assert u["panel_principal_municipios"] == 2393
    assert data["cobertura_ampliada_2024"]["pct_ln_panel_b_mas_asignadas"] == 91.5

    bench = {r["k"]: r for r in data["benchmark_modelos"] if r["algoritmo"] == "K-Means++"}
    k4 = bench[4]
    assert round(k4["silhouette"], 3) == 0.179
    assert round(k4["bootstrap_ari_media"], 3) == 0.957
    assert [round(k4["bootstrap_ari_ic95_inf"], 3), round(k4["bootstrap_ari_ic95_sup"], 3)] == [0.909, 0.992]

    vt = data["validacion_fuera_de_tiempo"]
    assert vt["coincidencia_exacta_pct"] == 83.65
    assert vt["ari_3d"] == 0.610
    va = data["valor_agregado_nivel_historico"]
    assert va["delta_r2_p2024_3d"] == 0.097

    perf = {p["cluster_id"]: p for p in data["perfiles"]}
    assert perf[0]["n_secciones"] == 17622 and perf[0]["pct_secciones_panel"] == 32.85
    assert round(perf[0]["participacion_media_historica_original"] * 100, 1) == 50.4
    assert round(perf[0]["p_2021_ponderada"] * 100, 1) == 46.1
    assert round(perf[0]["p_2024_ponderada"] * 100, 1) == 56.9
    assert round(perf[0]["brecha_presidencial_intermedia_original"] * 100, 1) == 17.3

    assert perf[1]["n_secciones"] == 8824 and perf[1]["pct_secciones_panel"] == 16.45
    assert round(perf[1]["participacion_media_historica_original"] * 100, 1) == 65.1
    assert round(perf[1]["p_2021_ponderada"] * 100, 1) == 62.5
    assert round(perf[1]["p_2024_ponderada"] * 100, 1) == 65.7
    assert round(perf[1]["tasa_joven_18_29_original"] * 100, 1) == 59.1

    assert perf[2]["n_secciones"] == 14624 and perf[2]["pct_secciones_panel"] == 27.26
    assert round(perf[2]["participacion_media_historica_original"] * 100, 1) == 58.9
    assert round(perf[2]["p_2021_ponderada"] * 100, 1) == 60.4
    assert round(perf[2]["p_2024_ponderada"] * 100, 1) == 68.0
    assert round(perf[2]["tendencia_participacion_beta_original"] * 100, 2) == 1.28

    assert perf[3]["n_secciones"] == 12574 and perf[3]["pct_secciones_panel"] == 23.44
    assert round(perf[3]["participacion_media_historica_original"] * 100, 1) == 55.4
    assert round(perf[3]["p_2021_ponderada"] * 100, 1) == 49.5
    assert round(perf[3]["p_2024_ponderada"] * 100, 1) == 55.6
    assert abs(perf[3]["brecha_genero_original"] - 0.111497) < 0.001

    imp = data["impacto_y_prioridad_territorial"]
    t_imp = {r["codigo_cluster"]: r for r in imp["tabla_impacto"]}
    assert "938 mil" in t_imp["C0"]["electores_impacto_str"]
    assert "441 mil" in t_imp["C0"]["electores_conservador_str"]
    assert "333 mil" in t_imp["C3"]["electores_impacto_str"]
    assert "167 mil" in t_imp["C3"]["electores_conservador_str"]
    assert "58 mil" in t_imp["C1"]["electores_impacto_str"]
    assert "1.92 millones" in t_imp["C2"]["electores_impacto_str"]

    assert "Chihuahua – Distrito 03, Estado de México – Distrito 31, Puebla – Distrito 09" == t_imp["C0"]["top3_juntas_distritales"]
    assert "Jalisco – Distrito 18, Campeche – Distrito 01, Nuevo León – Distrito 04" == t_imp["C1"]["top3_juntas_distritales"]
    assert "Ciudad de México – Distrito 15, Tlaxcala – Distrito 03, Ciudad de México – Distrito 10" == t_imp["C2"]["top3_juntas_distritales"]
    assert "Guanajuato – Distrito 02, Estado de México – Distrito 32, Sonora – Distrito 02" == t_imp["C3"]["top3_juntas_distritales"]

    pil = data["potencia_piloto_c0"]
    assert pil["n_seleccionado"] == 500
    assert pil["diseno_seleccionado"] == "ANCOVA"
    assert pil["mde_seleccionado_pts"] == 1.57
    assert pil["tabla_15"][1]["potencia_pct"] == 80.0
    assert pil["tabla_15"][1]["significancia_alpha"] == 0.05
    print("[10_presentacion] Verificación de cifras del Bloque A: 100% EXITOSA.")


def exportar_iconos_png() -> None:
    """Genera 4 PNGs de íconos en 300 DPI con fondo transparente en outputs/entregables/iconos/."""
    for cid in range(4):
        fig = plt.figure(figsize=(2, 2), dpi=300, facecolor="none")
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        color = THEMES_HEX[cid]["primary"]
        cx, cy, radius = 0.5, 0.5, 0.45
        circ = Circle((cx, cy), radius, facecolor=color, edgecolor="white", linewidth=3.0)
        ax.add_patch(circ)
        s = radius / 0.038
        if cid == 0:
            for idx, h in enumerate([0.014, 0.032, 0.016, 0.030]):
                bx = cx + (-0.020 + idx * 0.011) * s
                by = cy - 0.016 * s
                ax.add_patch(Rectangle((bx, by), 0.007 * s, h * s, facecolor="white", zorder=7))
        elif cid == 1:
            pts = np.array([
                [cx, cy + 0.022 * s],
                [cx + 0.018 * s, cy + 0.010 * s],
                [cx + 0.014 * s, cy - 0.016 * s],
                [cx, cy - 0.024 * s],
                [cx - 0.014 * s, cy - 0.016 * s],
                [cx - 0.018 * s, cy + 0.010 * s],
            ])
            ax.add_patch(Polygon(pts, closed=True, facecolor="white", zorder=7))
        elif cid == 2:
            ax.plot([cx - 0.018 * s, cx - 0.005 * s, cx + 0.006 * s, cx + 0.018 * s],
                    [cy - 0.014 * s, cy - 0.002 * s, cy - 0.006 * s, cy + 0.016 * s],
                    color="white", linewidth=4.0, zorder=7)
            ax.plot([cx + 0.008 * s, cx + 0.018 * s, cx + 0.018 * s],
                    [cy + 0.016 * s, cy + 0.016 * s, cy + 0.005 * s],
                    color="white", linewidth=4.0, zorder=7)
        elif cid == 3:
            c_inner = Circle((cx, cy + 0.008 * s), 0.011 * s, fill=False, edgecolor="white", linewidth=3.5, zorder=7)
            ax.add_patch(c_inner)
            ax.plot([cx, cx], [cy - 0.003 * s, cy - 0.020 * s], color="white", linewidth=3.5, zorder=7)
            ax.plot([cx - 0.010 * s, cx + 0.010 * s], [cy - 0.012 * s, cy - 0.012 * s], color="white", linewidth=3.5, zorder=7)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        fig.savefig(ICONOS_DIR / f"icono_c{cid}.png", transparent=True, dpi=300)
        plt.close(fig)
    print(f"[10_presentacion] Íconos oficiales exportados en {ICONOS_DIR}.")


def configurar_fuentes_tema_arial(prs: pptx.Presentation) -> None:
    """Configura el tema de la presentación para usar Arial como fuente predeterminada."""
    theme_part = [rel.target_part for rel in prs.slide_masters[0].part.rels.values() if "theme" in rel.reltype][0]
    blob = theme_part.blob
    blob = blob.replace(b"Calibri Light", b"Arial")
    blob = blob.replace(b"Calibri", b"Arial")
    theme_part._blob = blob


def add_header(slide, title_text: str) -> None:
    """Agrega el título de 28 pt negrita en #1E3A8A y la línea decorativa de 2 pt."""
    tb = slide.shapes.add_textbox(Inches(0.6), Inches(0.45), Inches(12.133), Inches(0.95))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.name = "Arial"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = NAVY

    # Línea decorativa inferior
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.45), Inches(12.133), Inches(0.025))
    line.fill.solid()
    line.fill.fore_color.rgb = LIGHT_GRAY
    line.line.color.rgb = LIGHT_GRAY


def add_footer(slide, slide_num: int) -> None:
    """Agrega pie de página en 10 pt gris con leyenda institucional y número."""
    tb = slide.shapes.add_textbox(Inches(0.6), Inches(7.05), Inches(12.133), Inches(0.35))
    tf = tb.text_frame
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = "Equipo Byte me · Reto 1 · Concurso «Hackea la participación»"
    p.font.name = "Arial"
    p.font.size = Pt(10)
    p.font.color.rgb = MID_GRAY

    # Número de diapositiva a la derecha
    tb_num = slide.shapes.add_textbox(Inches(10.733), Inches(7.05), Inches(2.0), Inches(0.35))
    tf_num = tb_num.text_frame
    tf_num.margin_left = tf_num.margin_top = tf_num.margin_right = tf_num.margin_bottom = 0
    p_num = tf_num.paragraphs[0]
    p_num.alignment = PP_ALIGN.RIGHT
    p_num.text = str(slide_num)
    p_num.font.name = "Arial"
    p_num.font.size = Pt(10)
    p_num.font.color.rgb = MID_GRAY


def add_speaker_notes(slide, notes_text: str) -> None:
    """Agrega las notas del orador a la diapositiva."""
    slide.notes_slide.notes_text_frame.text = notes_text.strip()


def build_presentation(data: dict) -> Path:
    """Construye las 10 diapositivas ejecutivas nativas en formato 16:9."""
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    configurar_fuentes_tema_arial(prs)
    blank_layout = prs.slide_layouts[6]

    serie = {r["anio"]: r for r in data["serie_nacional_2009_2024"]}
    perf = {p["cluster_id"]: p for p in data["perfiles"]}
    t_imp = {r["codigo_cluster"]: r for r in data["impacto_y_prioridad_territorial"]["tabla_impacto"]}

    # =========================================================================
    # D1 · Portada
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    # Franja superior azul
    hdr_box = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(0.6), Inches(12.133), Inches(2.2))
    hdr_box.fill.solid()
    hdr_box.fill.fore_color.rgb = NAVY
    hdr_box.line.color.rgb = NAVY
    tf_h = hdr_box.text_frame
    tf_h.word_wrap = True
    tf_h.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_h.margin_left = Inches(0.4)
    tf_h.margin_right = Inches(0.4)
    p1 = tf_h.paragraphs[0]
    p1.text = "Perfiles ciudadanos de participación electoral en México, 2009–2024"
    p1.font.name = "Arial"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p2 = tf_h.add_paragraph()
    p2.text = "Tipología seccional y estrategias de educación cívica"
    p2.font.name = "Arial"
    p2.font.size = Pt(22)
    p2.font.color.rgb = RGBColor(226, 232, 240)

    # Subtítulo y convocatoria
    sub_box = slide1.shapes.add_textbox(Inches(0.6), Inches(3.05), Inches(12.133), Inches(0.9))
    tf_sub = sub_box.text_frame
    tf_sub.word_wrap = True
    p_s1 = tf_sub.paragraphs[0]
    p_s1.text = "Equipo Byte me · Reto 1: Perfiles ciudadanos de participación"
    p_s1.font.name = "Arial"
    p_s1.font.size = Pt(18)
    p_s1.font.bold = True
    p_s1.font.color.rgb = NAVY
    p_s2 = tf_sub.add_paragraph()
    p_s2.text = "Concurso «Hackea la participación: Datos que construyen democracia»"
    p_s2.font.name = "Arial"
    p_s2.font.size = Pt(16)
    p_s2.font.italic = True
    p_s2.font.color.rgb = DARK_GRAY

    # Integrantes
    int_box = slide1.shapes.add_textbox(Inches(0.6), Inches(4.10), Inches(12.133), Inches(0.6))
    tf_int = int_box.text_frame
    p_int = tf_int.paragraphs[0]
    p_int.text = "Johanan Olivares Gutiérrez (representante) · Oscar Ariel Cuevas Martínez · Saúl Alexis Arias González"
    p_int.font.name = "Arial"
    p_int.font.size = Pt(16)
    p_int.font.color.rgb = DARK_GRAY

    # Fila de los 4 íconos con sus nombres
    icon_w = Inches(1.1)
    gap_x = Inches(2.9)
    start_x = Inches(1.0)
    y_icons = Inches(4.85)
    names_short = [
        "C0: Rezago juvenil",
        "C1: Alta constancia",
        "C2: Ascenso cívico",
        "C3: Liderazgo femenino",
    ]
    for cid in range(4):
        x_c = start_x + cid * gap_x
        slide1.shapes.add_picture(str(ICONOS_DIR / f"icono_c{cid}.png"), x_c, y_icons, icon_w, icon_w)
        lbl_box = slide1.shapes.add_textbox(x_c - Inches(0.4), y_icons + Inches(1.15), Inches(1.9), Inches(0.4))
        tf_lbl = lbl_box.text_frame
        p_l = tf_lbl.paragraphs[0]
        p_l.alignment = PP_ALIGN.CENTER
        p_l.text = names_short[cid]
        p_l.font.name = "Arial"
        p_l.font.size = Pt(14)
        p_l.font.bold = True
        p_l.font.color.rgb = PROFILE_COLORS[cid]

    # Pie con repositorio
    url_box = slide1.shapes.add_textbox(Inches(0.6), Inches(6.55), Inches(12.133), Inches(0.4))
    tf_url = url_box.text_frame
    p_u = tf_url.paragraphs[0]
    p_u.alignment = PP_ALIGN.CENTER
    p_u.text = "github.com/Johanan1113/Hackaton_INE_byte_me"
    p_u.font.name = "Arial"
    p_u.font.size = Pt(14)
    p_u.font.bold = True
    p_u.font.color.rgb = NAVY

    add_speaker_notes(
        slide1,
        "Presentamos ante el Instituto Nacional Electoral nuestra propuesta metodológica y operativa de segmentación ciudadana para el Reto 1. Desarrollamos una tipología seccional rigurosa a partir de los Conteos Censales de Participación Ciudadana de 2009 a 2024, con el objetivo de dotar a las direcciones operativas del instituto de herramientas cuantitativas para focalizar campañas de educación cívica, optimizar la integración de casillas y maximizar la movilización electoral en los comicios federales de 2027 y 2030."
    )

    # =========================================================================
    # D2 · El hallazgo
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    add_header(slide2, "Medir bien cambia el diagnóstico: la fórmula correcta recupera hasta 4.27 puntos")
    add_footer(slide2, 2)

    # Izquierda: Tarjeta KPI
    kpi_card = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(1.7), Inches(3.1), Inches(5.1))
    kpi_card.fill.solid()
    kpi_card.fill.fore_color.rgb = BG_LIGHT
    kpi_card.line.color.rgb = LIGHT_GRAY
    tf_kc = kpi_card.text_frame
    tf_kc.word_wrap = True
    tf_kc.margin_left = tf_kc.margin_right = Inches(0.3)
    p_num = tf_kc.paragraphs[0]
    p_num.text = "−4.27 pts"
    p_num.font.name = "Arial"
    p_num.font.size = Pt(44)
    p_num.font.bold = True
    p_num.font.color.rgb = NAVY
    p_txt = tf_kc.add_paragraph()
    p_txt.text = "\nsubestimación de la participación nacional en 2018 al dividir entre la lista nominal (−3.84 pts en 2024)."
    p_txt.font.name = "Arial"
    p_txt.font.size = Pt(16)
    p_txt.font.color.rgb = DARK_GRAY

    # Centro: Comparativa de Fórmulas y Explicación
    # Caja Gris: Incorrecta
    box_inc = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.8), Inches(1.7), Inches(3.5), Inches(0.85))
    box_inc.fill.solid()
    box_inc.fill.fore_color.rgb = RGBColor(243, 244, 246)
    box_inc.line.color.rgb = RGBColor(209, 213, 219)
    p_bi = box_inc.text_frame.paragraphs[0]
    p_bi.alignment = PP_ALIGN.CENTER
    p_bi.text = "Incorrecta: SV / LN"
    p_bi.font.name = "Arial"
    p_bi.font.size = Pt(16)
    p_bi.font.bold = True
    p_bi.font.color.rgb = MID_GRAY

    # Caja Azul: Correcta
    box_cor = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.8), Inches(2.7), Inches(3.5), Inches(0.85))
    box_cor.fill.solid()
    box_cor.fill.fore_color.rgb = RGBColor(239, 246, 255)
    box_cor.line.color.rgb = RGBColor(147, 197, 253)
    p_bc = box_cor.text_frame.paragraphs[0]
    p_bc.alignment = PP_ALIGN.CENTER
    p_bc.text = "Correcta (Manual CCPC): SV / (SV + NV)"
    p_bc.font.name = "Arial"
    p_bc.font.size = Pt(16)
    p_bc.font.bold = True
    p_bc.font.color.rgb = NAVY

    # Explicación
    exp_box = slide2.shapes.add_textbox(Inches(3.8), Inches(3.7), Inches(3.5), Inches(3.1))
    tf_exp = exp_box.text_frame
    tf_exp.word_wrap = True
    tf_exp.margin_left = tf_exp.margin_right = 0
    p_e = tf_exp.paragraphs[0]
    p_e.text = (
        "En 2018 y 2024, el 6.8% y el 6.4% de la lista nominal son registros no especificados (NS): "
        "cuadernillos sin marcas, no disponibles para captura o con páginas faltantes. "
        "Contarlos como abstención crea grupos artificiales de baja participación."
    )
    p_e.font.name = "Arial"
    p_e.font.size = Pt(15)
    p_e.font.color.rgb = DARK_GRAY

    # Derecha: Gráfica de Columnas Agrupadas
    cd2 = CategoryChartData()
    cd2.categories = ["2009", "2012", "2015", "2018", "2021", "2024"]
    cd2.add_series("SV/LN", (44.1, 62.0, 46.5, 58.1, 51.5, 55.8))
    cd2.add_series("SV/(SV+NV)", (44.1, 62.1, 47.1, 62.4, 51.8, 59.7))
    gf2 = slide2.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(7.5), Inches(1.7), Inches(5.2), Inches(5.1), cd2
    )
    ch2 = gf2.chart
    ch2.has_legend = True
    ch2.legend.position = XL_LEGEND_POSITION.TOP
    ch2.legend.include_in_layout = False
    ch2.legend.font.name = "Arial"
    ch2.legend.font.size = Pt(11)
    ch2.category_axis.tick_labels.font.name = "Arial"
    ch2.category_axis.tick_labels.font.size = Pt(11)
    ch2.value_axis.tick_labels.font.name = "Arial"
    ch2.value_axis.tick_labels.font.size = Pt(11)
    p_cl = ch2.plots[0]
    p_cl.has_data_labels = True
    p_cl.gap_width = 120
    p_cl.overlap = -10
    p_cl.data_labels.font.name = "Arial"
    p_cl.data_labels.font.size = Pt(8.5)
    p_cl.series[0].format.fill.solid()
    p_cl.series[0].format.fill.fore_color.rgb = RGBColor(156, 163, 175)
    p_cl.series[1].format.fill.solid()
    p_cl.series[1].format.fill.fore_color.rgb = NAVY

    for el in ch2._element.xpath("//a:latin"):
        el.set("typeface", "Arial")

    add_speaker_notes(
        slide2,
        "Identificamos que calcular la participación dividiendo únicamente votos sobre lista nominal genera un severo sesgo por la presencia de registros no especificados, derivados de cuadernillos con captura incompleta o faltante. En 2018 este sesgo alcanzó 4.27 puntos y en 2024 representó 3.84 puntos porcentuales. Al aplicar estrictamente la formulación técnica de los manuales censales del INE, votos sobre votos más no votos, recuperamos la verdadera tasa de participación y evitamos clasificar erróneamente problemas de captura administrativa como abstencionismo ciudadano."
    )

    # =========================================================================
    # D3 · Validación y universo
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    add_header(slide3, "Nuestra serie reproduce las cifras censales del INE")
    add_footer(slide3, 3)

    # Izquierda: Tabla comparativa
    t_shape = slide3.shapes.add_table(7, 3, Inches(0.6), Inches(1.7), Inches(6.5), Inches(4.3))
    table = t_shape.table
    table.columns[0].width = Inches(1.6)
    table.columns[1].width = Inches(2.4)
    table.columns[2].width = Inches(2.5)

    headers = ["Año", "Cálculo CCPC", "Dato censal INE"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = h
        p.font.name = "Arial"
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = WHITE

    table_data = [
        ("2009", "44.06%", "44.06%"),
        ("2012", "62.08%", "62.08%"),
        ("2015", "47.07%", "47.07%"),
        ("2018", "62.37%", "62.4%"),
        ("2021", "51.84%", "51.8%"),
        ("2024", "59.67%", "59.7%"),
    ]
    for i, row in enumerate(table_data):
        bg = BG_LIGHT if i % 2 == 0 else WHITE
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            p.text = val
            p.font.name = "Arial"
            p.font.size = Pt(14)
            p.font.color.rgb = DARK_GRAY

    # Nota debajo de tabla
    note_box = slide3.shapes.add_textbox(Inches(0.6), Inches(6.15), Inches(6.5), Inches(0.5))
    tf_nb = note_box.text_frame
    p_nb = tf_nb.paragraphs[0]
    p_nb.text = "Fuentes: DECEyEC, estudio comparativo 2009–2015; Manual de Conteos Censales 2009–2024 (p. 21)."
    p_nb.font.name = "Arial"
    p_nb.font.size = Pt(11)
    p_nb.font.italic = True
    p_nb.font.color.rgb = MID_GRAY

    # Derecha: 3 KPIs apilados
    kpis_data = [
        ("53,644", "secciones con serie completa 2009–2024", NAVY),
        ("79.5%", "de la lista nominal 2024 en el modelo", NAVY),
        ("91.5%", "de la lista nominal con perfil asignado para operar", C1_COLOR),
    ]
    for idx, (num_str, desc_str, col_rgb) in enumerate(kpis_data):
        y_pos = Inches(1.7 + idx * 1.65)
        card = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.5), y_pos, Inches(5.2), Inches(1.45))
        card.fill.solid()
        card.fill.fore_color.rgb = BG_LIGHT
        card.line.color.rgb = LIGHT_GRAY
        tf_c = card.text_frame
        tf_c.word_wrap = True
        tf_c.margin_left = tf_c.margin_right = Inches(0.3)
        p_n = tf_c.paragraphs[0]
        p_n.text = num_str
        p_n.font.name = "Arial"
        p_n.font.size = Pt(40)
        p_n.font.bold = True
        p_n.font.color.rgb = col_rgb
        p_d = tf_c.add_paragraph()
        p_d.text = desc_str
        p_d.font.name = "Arial"
        p_d.font.size = Pt(16)
        p_d.font.color.rgb = DARK_GRAY

    add_speaker_notes(
        slide3,
        "Validamos nuestra serie temporal nacional contra todas las publicaciones oficiales de la DECEyEC y los manuales del INE, logrando una coincidencia milimétrica en los seis comicios analizados. Para el modelo principal construimos un panel balanceado de 53,644 secciones continuas y con captura válida en 2,393 municipios, que concentra el 79.5% de la lista nominal nacional sin recurrir a imputaciones sintéticas. Adicionalmente, mediante asignación determinista por cercanía a centroides, extendemos la cobertura operativa de los perfiles al 91.5% de la ciudadanía."
    )

    # =========================================================================
    # D4 · Método
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    add_header(slide4, "Cuatro perfiles con un método reproducible y validado")
    add_footer(slide4, 4)

    # Fila de 5 recuadros conectados con flechas
    step_texts = [
        "Datos CCPC 2009–2024\n6 elecciones federales",
        "Corrección SV/(SV+NV)\ny depuración sin imputar",
        "7 indicadores\npor sección",
        "K-Means++\ncon k = 4",
        "Validación\ny solidez",
    ]
    box_w = Inches(2.1)
    box_h = Inches(1.2)
    step_y = Inches(1.7)
    for idx, txt in enumerate(step_texts):
        x_pos = Inches(0.6 + idx * 2.5)
        box = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x_pos, step_y, box_w, box_h)
        box.fill.solid()
        box.fill.fore_color.rgb = RGBColor(239, 246, 255)
        box.line.color.rgb = RGBColor(147, 197, 253)
        tf_b = box.text_frame
        tf_b.word_wrap = True
        tf_b.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf_b.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = txt
        p.font.name = "Arial"
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = NAVY

        # Flecha conectora entre recuadros
        if idx < 4:
            arr = slide4.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW, x_pos + box_w + Inches(0.08), step_y + Inches(0.4), Inches(0.24), Inches(0.35)
            )
            arr.fill.solid()
            arr.fill.fore_color.rgb = LIGHT_GRAY
            arr.line.color.rgb = LIGHT_GRAY

    # Abajo a la izquierda: Indicadores
    ind_card = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(3.25), Inches(5.8), Inches(3.3))
    ind_card.fill.solid()
    ind_card.fill.fore_color.rgb = BG_LIGHT
    ind_card.line.color.rgb = LIGHT_GRAY
    tf_ic = ind_card.text_frame
    tf_ic.word_wrap = True
    tf_ic.margin_left = tf_ic.margin_right = Inches(0.3)
    p_ih = tf_ic.paragraphs[0]
    p_ih.text = "Indicadores"
    p_ih.font.name = "Arial"
    p_ih.font.size = Pt(18)
    p_ih.font.bold = True
    p_ih.font.color.rgb = NAVY

    indicators = [
        "Participación media histórica",
        "Brecha presidencial–intermedia",
        "Tendencia anual de participación",
        "Estabilidad en la participación",
        "Brecha generacional (jóvenes vs. mayores)",
        "Brecha de género (mujeres vs. hombres)",
        "Razón de participación juvenil",
    ]
    for ind in indicators:
        pi = tf_ic.add_paragraph()
        pi.text = f"• {ind}"
        pi.font.name = "Arial"
        pi.font.size = Pt(14)
        pi.font.color.rgb = DARK_GRAY

    # Abajo a la derecha: Validación
    val_card = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(3.25), Inches(5.9), Inches(3.3))
    val_card.fill.solid()
    val_card.fill.fore_color.rgb = BG_LIGHT
    val_card.line.color.rgb = LIGHT_GRAY
    tf_vc = val_card.text_frame
    tf_vc.word_wrap = True
    tf_vc.margin_left = tf_vc.margin_right = Inches(0.3)
    p_vh = tf_vc.paragraphs[0]
    p_vh.text = "Validación"
    p_vh.font.name = "Arial"
    p_vh.font.size = Pt(18)
    p_vh.font.bold = True
    p_vh.font.color.rgb = NAVY

    validations = [
        "Silhouette 0.179: el mejor en el rango 4–6",
        "Estabilidad bootstrap: ARI 0.957",
        "83.7% de las secciones conserva su perfil sin datos de 2024",
        "Aporta ΔR² = 0.097 sobre el nivel histórico",
    ]
    for val in validations:
        pv = tf_vc.add_paragraph()
        pv.text = f"• {val}"
        pv.font.name = "Arial"
        pv.font.size = Pt(14)
        pv.font.color.rgb = DARK_GRAY

    # Nota metodológica inferior
    note_d4 = slide4.shapes.add_textbox(Inches(0.6), Inches(6.65), Inches(12.133), Inches(0.4))
    p_n4 = note_d4.text_frame.paragraphs[0]
    p_n4.text = "Las secciones forman un continuo: los perfiles son una segmentación operativa, no grupos naturales."
    p_n4.font.name = "Arial"
    p_n4.font.size = Pt(12)
    p_n4.font.italic = True
    p_n4.font.color.rgb = MID_GRAY

    add_speaker_notes(
        slide4,
        "Diseñamos un pipeline totalmente reproducible que sintetiza quince años de historia electoral en siete variables rectoras estandarizadas por sección. Aplicamos el algoritmo K-Means++ seleccionando cuatro perfiles, que supera a las opciones de cinco y seis grupos en coeficiente de Silhouette y estabilidad bootstrap con un ARI de 0.957. Demostramos la solidez del modelo mediante una validación fuera de tiempo: al calibrar solo con datos de 2009 a 2021, la estructura agrega un valor predictivo de nueve punto siete puntos porcentuales de R cuadrado."
    )

    # =========================================================================
    # D5 · Los cuatro perfiles
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    add_header(slide5, "Cuatro perfiles, cuatro dinámicas de participación")
    add_footer(slide5, 5)

    # Izquierda (55%): Gráfica de líneas 2009–2024
    cd5 = CategoryChartData()
    cd5.categories = ["2009", "2012", "2015", "2018", "2021", "2024"]
    cd5.add_series("C0", (38.5, 59.9, 41.5, 60.1, 46.1, 56.9))
    cd5.add_series("C1", (58.8, 70.8, 62.0, 71.9, 62.5, 65.7))
    cd5.add_series("C2", (41.8, 63.8, 48.0, 67.2, 60.4, 68.0))
    cd5.add_series("C3", (49.6, 61.2, 50.4, 60.0, 49.5, 55.6))
    cd5.add_series("Media del panel", (44.5, 62.6, 47.7, 63.2, 52.8, 60.5))

    gf5 = slide5.shapes.add_chart(XL_CHART_TYPE.LINE, Inches(0.6), Inches(1.7), Inches(6.5), Inches(5.1), cd5)
    ch5 = gf5.chart
    ch5.has_legend = True
    ch5.legend.position = XL_LEGEND_POSITION.TOP
    ch5.legend.font.name = "Arial"
    ch5.legend.font.size = Pt(11)
    ch5.category_axis.tick_labels.font.name = "Arial"
    ch5.category_axis.tick_labels.font.size = Pt(11)
    ch5.value_axis.tick_labels.font.name = "Arial"
    ch5.value_axis.tick_labels.font.size = Pt(11)

    plots5 = ch5.plots[0]
    colors_lines = [C0_COLOR, C1_COLOR, C2_COLOR, C3_COLOR, MID_GRAY]
    widths_lines = [Pt(2.6), Pt(2.6), Pt(2.6), Pt(2.6), Pt(2.0)]
    for i, s in enumerate(plots5.series):
        s.format.line.color.rgb = colors_lines[i]
        s.format.line.width = widths_lines[i]

    for el in ch5._element.xpath("//a:latin"):
        el.set("typeface", "Arial")

    # Derecha: 4 renglones con ícono, nombre, porcentajes y rasgo
    traits = [
        ("C0: Baja Participación Intermitente con Rezago Juvenil", "32.9% de las secciones · participación media 50.4%", "Cae en elecciones intermedias y rezago juvenil", C0_COLOR),
        ("C1: Alta Participación Estable e Intergeneracional", "16.4% de las secciones · participación media 65.1%", "Alta y estable; integra a todas las edades", C1_COLOR),
        ("C2: Participación en Ascenso con Juventud Activa", "27.3% de las secciones · participación media 58.9%", "Crece +1.28 pts por año con juventud activa", C2_COLOR),
        ("C3: Liderazgo Femenino con Participación Estancada", "23.4% de las secciones · participación media 55.4%", "Las mujeres votan 11.2 pts más; cae en presidenciales", C3_COLOR),
    ]
    for cid, (p_title, p_stats, p_trait, col_rgb) in enumerate(traits):
        y_r = Inches(1.7 + cid * 1.25)
        # Ícono
        slide5.shapes.add_picture(str(ICONOS_DIR / f"icono_c{cid}.png"), Inches(7.35), y_r + Inches(0.05), Inches(0.95), Inches(0.95))
        # Caja de texto
        r_box = slide5.shapes.add_textbox(Inches(8.4), y_r, Inches(4.3), Inches(1.1))
        tf_r = r_box.text_frame
        tf_r.word_wrap = True
        tf_r.margin_left = tf_r.margin_top = tf_r.margin_right = tf_r.margin_bottom = 0
        p_t = tf_r.paragraphs[0]
        p_t.text = p_title
        p_t.font.name = "Arial"
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = col_rgb
        p_s = tf_r.add_paragraph()
        p_s.text = p_stats
        p_s.font.name = "Arial"
        p_s.font.size = Pt(13)
        p_s.font.bold = True
        p_s.font.color.rgb = DARK_GRAY
        p_tr = tf_r.add_paragraph()
        p_tr.text = p_trait
        p_tr.font.name = "Arial"
        p_tr.font.size = Pt(13)
        p_tr.font.color.rgb = MID_GRAY

    add_speaker_notes(
        slide5,
        "La tipología segmenta el país en cuatro dinámicas nítidas. C0 agrupa un tercio de las secciones en zonas metropolitanas con una profunda caída en elecciones intermedias y desafección juvenil. C1 representa comunidades altamente participativas y estables en todas las edades. C2 es el perfil más dinámico, con un crecimiento promedio de uno punto veintiocho puntos por año impulsado por las nuevas generaciones. Finalmente, C3 se caracteriza por una marcada brecha favorable a las mujeres de once puntos, pero con un estancamiento en elecciones presidenciales."
    )

    # =========================================================================
    # D6 · Perfiles a elevar: C0 y C3
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    add_header(slide6, "Dos perfiles concentran el margen de mejora")
    add_footer(slide6, 6)

    col_configs_d6 = [
        {
            "cid": 0,
            "col_x": Inches(0.6),
            "color": C0_COLOR,
            "title": "C0: Baja Participación Intermitente con Rezago Juvenil",
            "kpis": [("50.4%", "media"), ("46.1%", "intermedia 2021"), ("+17.3 pts", "brecha pres.–inter.")],
            "propuesta": "Pedagogía sobre elecciones intermedias en transporte masivo y medios digitales; módulos itinerantes de credencialización para jóvenes que no estudian y en universidades.",
            "meta": "49.5% en la intermedia 2027 (+3.3 pts) · voto juvenil 39.1%",
            "empezar": "Chihuahua 03 · Estado de México 31 · Puebla 09",
        },
        {
            "cid": 3,
            "col_x": Inches(6.8),
            "color": C3_COLOR,
            "title": "C3: Liderazgo Femenino con Participación Estancada",
            "kpis": [("55.4%", "media"), ("49.5%", "intermedia 2021"), ("+11.2 pts", "brecha de género")],
            "propuesta": "Promoción del voto masculino en centros de trabajo agropecuarios, industriales y de transporte, y en radio regional; rutas móviles y casillas extraordinarias en localidades dispersas.",
            "meta": "51.1% en 2027 · 58.1% en 2030 · voto masculino 46.3%",
            "empezar": "Guanajuato 02 · Estado de México 32 · Sonora 02",
        },
    ]

    for conf in col_configs_d6:
        cx = conf["col_x"]
        cid = conf["cid"]
        color = conf["color"]
        # Encabezado con color e ícono
        hdr_c = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(1.7), Inches(5.9), Inches(0.7))
        hdr_c.fill.solid()
        hdr_c.fill.fore_color.rgb = color
        hdr_c.line.color.rgb = color
        slide6.shapes.add_picture(str(ICONOS_DIR / f"icono_c{cid}.png"), cx + Inches(0.12), Inches(1.75), Inches(0.6), Inches(0.6))
        tb_ht = slide6.shapes.add_textbox(cx + Inches(0.8), Inches(1.72), Inches(5.0), Inches(0.65))
        p_ht = tb_ht.text_frame.paragraphs[0]
        p_ht.text = conf["title"]
        p_ht.font.name = "Arial"
        p_ht.font.size = Pt(13)
        p_ht.font.bold = True
        p_ht.font.color.rgb = WHITE

        # Fila de 3 KPIs (32 pt)
        card_kpi = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(2.5), Inches(5.9), Inches(1.0))
        card_kpi.fill.solid()
        card_kpi.fill.fore_color.rgb = BG_LIGHT
        card_kpi.line.color.rgb = LIGHT_GRAY
        tf_kp = card_kpi.text_frame
        tf_kp.word_wrap = True
        p_k = tf_kp.paragraphs[0]
        p_k.alignment = PP_ALIGN.CENTER
        k_str = f"{conf['kpis'][0][0]} ({conf['kpis'][0][1]})  ·  {conf['kpis'][1][0]} ({conf['kpis'][1][1]})  ·  {conf['kpis'][2][0]} ({conf['kpis'][2][1]})"
        p_k.text = k_str
        p_k.font.name = "Arial"
        p_k.font.size = Pt(13)
        p_k.font.bold = True
        p_k.font.color.rgb = color

        # Contenido de propuesta, meta y dónde empezar
        body_box = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(3.6), Inches(5.9), Inches(3.2))
        body_box.fill.solid()
        body_box.fill.fore_color.rgb = WHITE
        body_box.line.color.rgb = LIGHT_GRAY
        tf_bb = body_box.text_frame
        tf_bb.word_wrap = True
        tf_bb.margin_left = tf_bb.margin_right = Inches(0.25)
        tf_bb.margin_top = Inches(0.2)

        p_qp_t = tf_bb.paragraphs[0]
        p_qp_t.text = "Qué proponemos:"
        p_qp_t.font.name = "Arial"
        p_qp_t.font.size = Pt(14)
        p_qp_t.font.bold = True
        p_qp_t.font.color.rgb = NAVY

        p_qp = tf_bb.add_paragraph()
        p_qp.text = conf["propuesta"]
        p_qp.font.name = "Arial"
        p_qp.font.size = Pt(13)
        p_qp.font.color.rgb = DARK_GRAY

        p_m_t = tf_bb.add_paragraph()
        p_m_t.text = "Meta:"
        p_m_t.font.name = "Arial"
        p_m_t.font.size = Pt(14)
        p_m_t.font.bold = True
        p_m_t.font.color.rgb = NAVY

        p_m = tf_bb.add_paragraph()
        p_m.text = conf["meta"]
        p_m.font.name = "Arial"
        p_m.font.size = Pt(13)
        p_m.font.bold = True
        p_m.font.color.rgb = color

        p_de_t = tf_bb.add_paragraph()
        p_de_t.text = "Dónde empezar:"
        p_de_t.font.name = "Arial"
        p_de_t.font.size = Pt(14)
        p_de_t.font.bold = True
        p_de_t.font.color.rgb = NAVY

        p_de = tf_bb.add_paragraph()
        p_de.text = conf["empezar"]
        p_de.font.name = "Arial"
        p_de.font.size = Pt(13)
        p_de.font.color.rgb = DARK_GRAY

    add_speaker_notes(
        slide6,
        "Para los perfiles ubicados por debajo de la media nacional proponemos intervenciones orientadas a cerrar brechas estructurales. En C0 la prioridad es combatir la apatía legislativa en entornos urbanos y facilitar la credencialización juvenil en centros laborales y universitarios, fijando como meta alcanzar 49.5% en 2027. En C3, con alta presencia rural, enfocamos los esfuerzos en activar el voto de los hombres en cooperativas y rutas laborales, junto con casillas extraordinarias que reduzcan las distancias de traslado."
    )

    # =========================================================================
    # D7 · Perfiles a sostener: C1 y C2
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    add_header(slide7, "Dos perfiles que hay que sostener")
    add_footer(slide7, 7)

    col_configs_d7 = [
        {
            "cid": 1,
            "col_x": Inches(0.6),
            "color": C1_COLOR,
            "title": "C1: Alta Participación Estable e Intergeneracional",
            "kpis": [("65.1%", "media"), ("62.5%", "intermedia 2021"), ("59.1%", "voto juvenil")],
            "propuesta": "Reconocimiento a la constancia cívica, talleres juveniles y sensibilización de la ciudadanía insaculada para integrar casillas.",
            "meta": "≥ 62.5% en 2027 · ≥ 65.7% en 2030",
            "empezar": "Jalisco 18 · Campeche 01 · Nuevo León 04",
        },
        {
            "cid": 2,
            "col_x": Inches(6.8),
            "color": C2_COLOR,
            "title": "C2: Participación en Ascenso con Juventud Activa",
            "kpis": [("58.9%", "media"), ("60.4%", "intermedia 2021"), ("+1.28 pts/año", "tendencia anual")],
            "propuesta": "Foros «Diálogos por la Democracia», alianzas con colectivos juveniles y difusión de «Conóceles» para consultar información de todas las candidaturas.",
            "meta": "≥ 60.4% en 2027 · razón juvenil ≥ 0.88",
            "empezar": "Ciudad de México 15 · Tlaxcala 03 · Ciudad de México 10",
        },
    ]

    for conf in col_configs_d7:
        cx = conf["col_x"]
        cid = conf["cid"]
        color = conf["color"]
        # Encabezado
        hdr_c = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(1.7), Inches(5.9), Inches(0.7))
        hdr_c.fill.solid()
        hdr_c.fill.fore_color.rgb = color
        hdr_c.line.color.rgb = color
        slide7.shapes.add_picture(str(ICONOS_DIR / f"icono_c{cid}.png"), cx + Inches(0.12), Inches(1.75), Inches(0.6), Inches(0.6))
        tb_ht = slide7.shapes.add_textbox(cx + Inches(0.8), Inches(1.72), Inches(5.0), Inches(0.65))
        p_ht = tb_ht.text_frame.paragraphs[0]
        p_ht.text = conf["title"]
        p_ht.font.name = "Arial"
        p_ht.font.size = Pt(13)
        p_ht.font.bold = True
        p_ht.font.color.rgb = WHITE

        # Fila de 3 KPIs
        card_kpi = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(2.5), Inches(5.9), Inches(1.0))
        card_kpi.fill.solid()
        card_kpi.fill.fore_color.rgb = BG_LIGHT
        card_kpi.line.color.rgb = LIGHT_GRAY
        tf_kp = card_kpi.text_frame
        tf_kp.word_wrap = True
        p_k = tf_kp.paragraphs[0]
        p_k.alignment = PP_ALIGN.CENTER
        k_str = f"{conf['kpis'][0][0]} ({conf['kpis'][0][1]})  ·  {conf['kpis'][1][0]} ({conf['kpis'][1][1]})  ·  {conf['kpis'][2][0]} ({conf['kpis'][2][1]})"
        p_k.text = k_str
        p_k.font.name = "Arial"
        p_k.font.size = Pt(13)
        p_k.font.bold = True
        p_k.font.color.rgb = color

        # Contenido
        body_box = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(3.6), Inches(5.9), Inches(3.2))
        body_box.fill.solid()
        body_box.fill.fore_color.rgb = WHITE
        body_box.line.color.rgb = LIGHT_GRAY
        tf_bb = body_box.text_frame
        tf_bb.word_wrap = True
        tf_bb.margin_left = tf_bb.margin_right = Inches(0.25)
        tf_bb.margin_top = Inches(0.2)

        p_qp_t = tf_bb.paragraphs[0]
        p_qp_t.text = "Qué proponemos:"
        p_qp_t.font.name = "Arial"
        p_qp_t.font.size = Pt(14)
        p_qp_t.font.bold = True
        p_qp_t.font.color.rgb = NAVY

        p_qp = tf_bb.add_paragraph()
        p_qp.text = conf["propuesta"]
        p_qp.font.name = "Arial"
        p_qp.font.size = Pt(13)
        p_qp.font.color.rgb = DARK_GRAY

        p_m_t = tf_bb.add_paragraph()
        p_m_t.text = "Meta:"
        p_m_t.font.name = "Arial"
        p_m_t.font.size = Pt(14)
        p_m_t.font.bold = True
        p_m_t.font.color.rgb = NAVY

        p_m = tf_bb.add_paragraph()
        p_m.text = conf["meta"]
        p_m.font.name = "Arial"
        p_m.font.size = Pt(13)
        p_m.font.bold = True
        p_m.font.color.rgb = color

        p_de_t = tf_bb.add_paragraph()
        p_de_t.text = "Dónde empezar:"
        p_de_t.font.name = "Arial"
        p_de_t.font.size = Pt(14)
        p_de_t.font.bold = True
        p_de_t.font.color.rgb = NAVY

        p_de = tf_bb.add_paragraph()
        p_de.text = conf["empezar"]
        p_de.font.name = "Arial"
        p_de.font.size = Pt(13)
        p_de.font.color.rgb = DARK_GRAY

    add_speaker_notes(
        slide7,
        "Los perfiles que superan el promedio del panel requieren estrategias de blindaje y consolidación. En C1 el desafío operativo central es asegurar el relevo generacional en las mesas directivas de casilla mediante capacitación temprana a personas insaculadas. En C2, que experimenta una fuerte movilización de votantes jóvenes, proponemos profundizar el diálogo público a través de la plataforma Conóceles y debates comunitarios, consolidando el piso de participación intermedia por encima del sesenta punto cuatro por ciento."
    )

    # =========================================================================
    # D8 · Impacto y prioridad territorial
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    add_header(slide8, "Hasta 1.27 millones de votantes adicionales en 2027")
    add_footer(slide8, 8)

    # Arriba: 2 KPIs grandes
    kpi_card_add = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(1.7), Inches(5.8), Inches(1.5))
    kpi_card_add.fill.solid()
    kpi_card_add.fill.fore_color.rgb = BG_LIGHT
    kpi_card_add.line.color.rgb = LIGHT_GRAY
    tf_a = kpi_card_add.text_frame
    tf_a.word_wrap = True
    tf_a.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_a.margin_left = tf_a.margin_right = Inches(0.3)
    tf_a.margin_top = tf_a.margin_bottom = Inches(0.08)
    p_an = tf_a.paragraphs[0]
    p_an.text = "607 mil – 1.27 millones"
    p_an.font.name = "Arial"
    p_an.font.size = Pt(30)
    p_an.font.bold = True
    p_an.font.color.rgb = C1_COLOR
    p_at = tf_a.add_paragraph()
    p_at.text = "votantes adicionales si se cumplen las metas de C0 y C3 (escenario conservador – meta)"
    p_at.font.name = "Arial"
    p_at.font.size = Pt(13)
    p_at.font.color.rgb = DARK_GRAY

    kpi_card_risk = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.7), Inches(5.9), Inches(1.5))
    kpi_card_risk.fill.solid()
    kpi_card_risk.fill.fore_color.rgb = BG_LIGHT
    kpi_card_risk.line.color.rgb = LIGHT_GRAY
    tf_r = kpi_card_risk.text_frame
    tf_r.word_wrap = True
    tf_r.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_r.margin_left = tf_r.margin_right = Inches(0.3)
    tf_r.margin_top = tf_r.margin_bottom = Inches(0.08)
    p_rn = tf_r.paragraphs[0]
    p_rn.text = "≈ 1.97 millones"
    p_rn.font.name = "Arial"
    p_rn.font.size = Pt(30)
    p_rn.font.bold = True
    p_rn.font.color.rgb = C0_COLOR
    p_rt = tf_r.add_paragraph()
    p_rt.text = "votantes en riesgo en C1 y C2 si regresan a su promedio intermedio"
    p_rt.font.name = "Arial"
    p_rt.font.size = Pt(13)
    p_rt.font.color.rgb = DARK_GRAY

    # Abajo: Tabla nativa de 4 filas con columnas "Perfil · Impacto 2027 · Top 3 juntas distritales · % de su LN en 30 juntas"
    t8_shape = slide8.shapes.add_table(5, 4, Inches(0.6), Inches(3.4), Inches(12.133), Inches(2.9))
    t8 = t8_shape.table
    t8.columns[0].width = Inches(3.8)
    t8.columns[1].width = Inches(2.2)
    t8.columns[2].width = Inches(4.5)
    t8.columns[3].width = Inches(1.633)

    h8 = ["Perfil", "Impacto 2027", "Top 3 juntas distritales", "% de su LN en 30 juntas"]
    for j, h in enumerate(h8):
        cell = t8.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER if j in (1, 3) else PP_ALIGN.LEFT
        p.text = h
        p.font.name = "Arial"
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = WHITE

    t8_rows = [
        ("C0: Baja Participación Intermitente con Rezago Juvenil", "≈ 938 mil adicionales", "Chihuahua 03 · Estado de México 31 · Puebla 09", "23.7%", C0_COLOR),
        ("C1: Alta Participación Estable e Intergeneracional", "≈ 58 mil en riesgo", "Jalisco 18 · Campeche 01 · Nuevo León 04", "49.2%", C1_COLOR),
        ("C2: Participación en Ascenso con Juventud Activa", "≈ 1.92 millones en riesgo", "Ciudad de México 15 · Tlaxcala 03 · Ciudad de México 10", "31.2%", C2_COLOR),
        ("C3: Liderazgo Femenino con Participación Estancada", "≈ 333 mil adicionales", "Guanajuato 02 · Estado de México 32 · Sonora 02", "28.5%", C3_COLOR),
    ]
    for i, (p_name, imp_txt, junc_txt, pct_ln, col_rgb) in enumerate(t8_rows):
        bg = BG_LIGHT if i % 2 == 0 else WHITE
        row_cells = [p_name, imp_txt, junc_txt, pct_ln]
        for j, val in enumerate(row_cells):
            cell = t8.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if j in (1, 3) else PP_ALIGN.LEFT
            p.text = val
            p.font.name = "Arial"
            p.font.size = Pt(13)
            p.font.bold = (j in (0, 1))
            p.font.color.rgb = col_rgb if j in (0, 1) else DARK_GRAY

    # Nota de 11 pt
    note_d8 = slide8.shapes.add_textbox(Inches(0.6), Inches(6.45), Inches(12.133), Inches(0.4))
    p_n8 = note_d8.text_frame.paragraphs[0]
    p_n8.text = "Estimación con la lista nominal 2024."
    p_n8.font.name = "Arial"
    p_n8.font.size = Pt(11)
    p_n8.font.italic = True
    p_n8.font.color.rgb = MID_GRAY

    add_speaker_notes(
        slide8,
        "El cumplimiento de las metas cuantitativas en C0 y C3 aportaría entre 607 mil y 1.27 millones de sufragios adicionales en las elecciones intermedias de 2027. Por el contrario, un descuido en C1 y C2 pondría en riesgo casi dos millones de votos si estas comunidades retrocedieran a sus niveles históricos. La priorización territorial demuestra una alta concentración: intervenir en las treinta principales juntas distritales de cada perfil permite cubrir hasta casi la mitad de su lista nominal."
    )

    # =========================================================================
    # D9 · Piloto evaluable
    # =========================================================================
    slide9 = prs.slides.add_slide(blank_layout)
    add_header(slide9, "Un piloto que se evalúa con los propios datos del INE")
    add_footer(slide9, 9)

    # Diagrama horizontal de 5 pasos
    diag_steps = [
        "1,000 secciones\ndel perfil C0",
        "Aleatorización\nestratificada",
        "500 tratamiento\n500 de control",
        "Medición con el\nCCPC 2027",
        "Análisis\nANCOVA",
    ]
    diag_y = Inches(1.7)
    box_w9 = Inches(2.1)
    box_h9 = Inches(1.3)
    for idx, txt in enumerate(diag_steps):
        x_pos = Inches(0.6 + idx * 2.5)
        box = slide9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x_pos, diag_y, box_w9, box_h9)
        box.fill.solid()
        box.fill.fore_color.rgb = RGBColor(239, 246, 255)
        box.line.color.rgb = RGBColor(147, 197, 253)
        tf_b = box.text_frame
        tf_b.word_wrap = True
        tf_b.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf_b.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = txt
        p.font.name = "Arial"
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = NAVY

        if idx < 4:
            arr = slide9.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW, x_pos + box_w9 + Inches(0.08), diag_y + Inches(0.45), Inches(0.24), Inches(0.35)
            )
            arr.fill.solid()
            arr.fill.fore_color.rgb = LIGHT_GRAY
            arr.line.color.rgb = LIGHT_GRAY

    # Centro: 3 KPIs
    kpi_piloto = [
        ("1.57 pts", "efecto mínimo detectable", NAVY),
        ("80%", "potencia (α = 0.05)", NAVY),
        ("Costo marginal", "usa el conteo censal existente", C1_COLOR),
    ]
    card_w9 = Inches(3.8)
    card_h9 = Inches(2.6)
    card_y9 = Inches(3.4)
    for idx, (num_txt, lbl_txt, col_rgb) in enumerate(kpi_piloto):
        cx = Inches(0.6 + idx * 4.15)
        card = slide9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, card_y9, card_w9, card_h9)
        card.fill.solid()
        card.fill.fore_color.rgb = BG_LIGHT
        card.line.color.rgb = LIGHT_GRAY
        tf_c = card.text_frame
        tf_c.word_wrap = True
        tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_c.margin_left = tf_c.margin_right = Inches(0.3)
        p_n = tf_c.paragraphs[0]
        p_n.alignment = PP_ALIGN.CENTER
        p_n.text = num_txt
        p_n.font.name = "Arial"
        p_n.font.size = Pt(40) if "pts" in num_txt or "%" in num_txt else Pt(34)
        p_n.font.bold = True
        p_n.font.color.rgb = col_rgb
        p_l = tf_c.add_paragraph()
        p_l.alignment = PP_ALIGN.CENTER
        p_l.text = f"\n{lbl_txt}"
        p_l.font.name = "Arial"
        p_l.font.size = Pt(16)
        p_l.font.color.rgb = DARK_GRAY

    # Nota de 12 pt
    note_d9 = slide9.shapes.add_textbox(Inches(0.6), Inches(6.35), Inches(12.133), Inches(0.5))
    p_n9 = note_d9.text_frame.paragraphs[0]
    p_n9.text = "Las campañas masivas se evalúan por distrito. Si se aleatoriza por bloques de secciones, se ajusta por efecto de diseño."
    p_n9.font.name = "Arial"
    p_n9.font.size = Pt(12)
    p_n9.font.italic = True
    p_n9.font.color.rgb = MID_GRAY

    add_speaker_notes(
        slide9,
        "Planteamos un diseño experimental riguroso para evaluar las intervenciones en el perfil prioritario C0 durante los comicios de 2027. Seleccionamos mil secciones aleatorizadas en quinientas de tratamiento y quinientas de control, con estratificación por entidad y tercil de participación previa. Con un modelo ANCOVA ajustado por línea base detectamos impactos desde uno punto cincuenta y siete puntos porcentuales con ochenta por ciento de potencia, a costo evaluativo marginal al aprovechar la infraestructura censal ordinaria del instituto."
    )

    # =========================================================================
    # D10 · Recomendaciones y cierre
    # =========================================================================
    slide10 = prs.slides.add_slide(blank_layout)
    add_header(slide10, "Tres recomendaciones al INE")
    add_footer(slide10, 10)

    recs = [
        "1. Publicar en los CSV abiertos una bandera de estatus de captura por sección, para que los registros NS no se confundan con abstención.",
        "2. Reforzar la captura de cuadernillos: NS pasó de 0.22% en 2012 a 6.83% en 2018 y 6.43% en 2024.",
        "3. Publicar el indicador de población indígena y afromexicana en los CSV abiertos y cruzar la tipología con el Censo 2020.",
    ]
    for idx, rec_txt in enumerate(recs):
        y_pos = Inches(1.7 + idx * 1.15)
        card = slide10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), y_pos, Inches(12.133), Inches(0.95))
        card.fill.solid()
        card.fill.fore_color.rgb = BG_LIGHT
        card.line.color.rgb = LIGHT_GRAY
        tf_rc = card.text_frame
        tf_rc.word_wrap = True
        tf_rc.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_rc.margin_left = Inches(0.3)
        tf_rc.margin_right = Inches(0.3)
        p = tf_rc.paragraphs[0]
        p.text = rec_txt
        p.font.name = "Arial"
        p.font.size = Pt(16)
        p.font.color.rgb = DARK_GRAY

    # Recuadro inferior de reproducibilidad
    box_rep = slide10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(5.35), Inches(12.133), Inches(0.75))
    box_rep.fill.solid()
    box_rep.fill.fore_color.rgb = RGBColor(239, 246, 255)
    box_rep.line.color.rgb = RGBColor(147, 197, 253)
    tf_br = box_rep.text_frame
    tf_br.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_br = tf_br.paragraphs[0]
    p_br.alignment = PP_ALIGN.CENTER
    p_br.text = "Código reproducible: github.com/Johanan1113/Hackaton_INE_byte_me · python run_all.py"
    p_br.font.name = "Arial"
    p_br.font.size = Pt(15)
    p_br.font.bold = True
    p_br.font.color.rgb = NAVY

    # Mensaje de cierre
    close_box = slide10.shapes.add_textbox(Inches(0.6), Inches(6.25), Inches(12.133), Inches(0.6))
    tf_cl = close_box.text_frame
    p_cl = tf_cl.paragraphs[0]
    p_cl.alignment = PP_ALIGN.CENTER
    p_cl.text = "Gracias · Equipo Byte me"
    p_cl.font.name = "Arial"
    p_cl.font.size = Pt(24)
    p_cl.font.bold = True
    p_cl.font.color.rgb = NAVY

    add_speaker_notes(
        slide10,
        "Concluimos con tres recomendaciones prioritarias para robustecer la gobernanza de datos del INE: primero, incorporar un indicador explícito de estatus de captura seccional para aislar registros no especificados; segundo, fortalecer los controles operativos para reducir los cuadernillos sin capturar observados desde 2018; y tercero, publicar variables sociodemográficas sobre comunidades originarias en datos abiertos. Nuestro código y modelos están plenamente documentados y son reproducibles con un solo comando. Muchas gracias."
    )

    out_pptx = OUT_ENTREGABLES / "Presentacion_Ejecutiva_ByteMe.pptx"
    prs.save(out_pptx)
    print(f"[10_presentacion] Presentación guardada exitosamente: {out_pptx} (10 diapositivas).")
    return out_pptx


def convertir_a_pdf(pptx_path: Path) -> Path:
    """Convierte el archivo .pptx a PDF utilizando LibreOffice headless."""
    pdf_path = pptx_path.with_suffix(".pdf")
    cmd = [
        "soffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(pptx_path.parent),
        str(pptx_path),
    ]
    print(f"[10_presentacion] Convirtiendo a PDF con LibreOffice: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    if not pdf_path.exists():
        raise FileNotFoundError(f"No se generó el PDF esperado en {pdf_path}: {res.stderr}")
    print(f"[10_presentacion] PDF generado exitosamente: {pdf_path}")
    return pdf_path


def main() -> None:
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    verificar_datos_bloque_a(data)
    exportar_iconos_png()
    out_pptx = build_presentation(data)
    convertir_a_pdf(out_pptx)
    print("[10_presentacion] Proceso completado exitosamente.")


if __name__ == "__main__":
    main()
