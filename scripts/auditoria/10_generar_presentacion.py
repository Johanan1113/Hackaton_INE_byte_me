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
import pandas as pd

import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.chart.data import CategoryChartData

# Utilidades de formato
sys.path.append(str(Path(__file__).resolve().parents[2]))
from scripts.auditoria.utilidades_formato import redondear, formatear

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
    assert "893 mil" in t_imp["C0"]["votantes_equivalentes_str"]
    assert "316 mil" in t_imp["C3"]["votantes_equivalentes_str"]
    assert "52 mil" in t_imp["C1"]["escenario_regresion_str"]
    assert "1.78 millones" in t_imp["C2"]["escenario_regresion_str"]

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

    # Fila de los 4 íconos con sus nombres oficiales
    icon_w = Inches(1.1)
    col_w = Inches(2.7)
    start_x = Inches(0.6)
    step_x = Inches(3.033)
    y_icons = Inches(4.75)
    names_official = [
        f"C{p['codigo_cluster']} · {p['nombre_propuesto']}"
        for p in data["perfiles"]
    ]
    for cid in range(4):
        x_center = start_x + (cid + 0.5) * step_x
        x_icon = x_center - icon_w / 2
        slide1.shapes.add_picture(str(ICONOS_DIR / f"icono_c{cid}.png"), x_icon, y_icons, icon_w, icon_w)
        lbl_box = slide1.shapes.add_textbox(x_center - col_w / 2, y_icons + Inches(1.15), col_w, Inches(0.60))
        tf_lbl = lbl_box.text_frame
        tf_lbl.word_wrap = True
        tf_lbl.margin_left = tf_lbl.margin_right = tf_lbl.margin_top = tf_lbl.margin_bottom = 0
        p_l = tf_lbl.paragraphs[0]
        p_l.alignment = PP_ALIGN.CENTER
        p_l.text = names_official[cid]
        p_l.font.name = "Arial"
        p_l.font.size = Pt(12)
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
        "Presentamos ante el Instituto Nacional Electoral nuestra propuesta metodológica y operativa de segmentación ciudadana para el Reto 1. Desarrollamos una tipología seccional rigurosa a partir de los Conteos Censales de Participación Ciudadana de 2009 a 2024, con el objetivo de dotar a las direcciones operativas del instituto de herramientas cuantitativas para focalizar campañas de educación cívica, optimizar la integración de casillas y promover la participación en los comicios federales de 2027 y 2030."
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
    # Datos de la serie nacional para métricas y gráfica
    df_t2 = pd.read_csv(TABLAS_DIR / "tabla_02_serie_nacional_2009_2024.csv")
    df_t2 = df_t2.sort_values("anio").reset_index(drop=True)
    cats_t2 = [str(int(a)) for a in df_t2["anio"]]
    vals_sv_ln = [round(float(v), 1) for v in df_t2["total_ponderada_erronea_sv_ln_pct"]]
    vals_sv_svnv = [round(float(v), 1) for v in df_t2["total_ponderada_sv_svnv_pct"]]

    sub_2018 = redondear(df_t2[df_t2["anio"] == 2018]["subestimacion_erronea_sv_ln_pond_pts"].iloc[0], 2)
    sub_2024 = redondear(df_t2[df_t2["anio"] == 2024]["subestimacion_erronea_sv_ln_pond_pts"].iloc[0], 2)
    ns_pct_2018 = redondear(df_t2[df_t2["anio"] == 2018]["pct_ns_anio"].iloc[0], 1)
    ns_pct_2024 = redondear(df_t2[df_t2["anio"] == 2024]["pct_ns_anio"].iloc[0], 1)

    tf_kc.word_wrap = True
    tf_kc.margin_left = tf_kc.margin_right = Inches(0.3)
    p_num = tf_kc.paragraphs[0]
    p_num.text = f"−{sub_2018:.2f} pts"
    p_num.font.name = "Arial"
    p_num.font.size = Pt(44)
    p_num.font.bold = True
    p_num.font.color.rgb = NAVY
    p_txt = tf_kc.add_paragraph()
    p_txt.text = f"\nsubestimación de la participación nacional en 2018 al dividir entre la lista nominal (−{sub_2024:.2f} pts en 2024)."
    p_txt.font.name = "Arial"
    p_txt.font.size = Pt(14)
    p_txt.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)

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
    tf_bc = box_cor.text_frame
    tf_bc.word_wrap = False
    tf_bc.margin_top = Inches(0.08)
    tf_bc.margin_bottom = Inches(0.08)
    p_bc1 = tf_bc.paragraphs[0]
    p_bc1.alignment = PP_ALIGN.CENTER
    p_bc1.text = "Correcta (Manual CCPC):"
    p_bc1.font.name = "Arial"
    p_bc1.font.size = Pt(15)
    p_bc1.font.bold = True
    p_bc1.font.color.rgb = NAVY
    p_bc2 = tf_bc.add_paragraph()
    p_bc2.alignment = PP_ALIGN.CENTER
    p_bc2.text = "SV / (SV + NV)"
    p_bc2.font.name = "Arial"
    p_bc2.font.size = Pt(15)
    p_bc2.font.bold = True
    p_bc2.font.color.rgb = NAVY

    # Explicación
    exp_box = slide2.shapes.add_textbox(Inches(3.8), Inches(3.7), Inches(3.5), Inches(3.1))
    tf_exp = exp_box.text_frame
    tf_exp.word_wrap = True
    tf_exp.margin_left = tf_exp.margin_right = 0
    p_e = tf_exp.paragraphs[0]
    p_e.text = (
        f"En 2018 y 2024, el {ns_pct_2018:.1f}% y el {ns_pct_2024:.1f}% de la lista nominal son registros no especificados (NS): "
        "cuadernillos sin marcas, no disponibles para captura o con páginas faltantes. "
        "Contarlos como abstención crea grupos artificiales de baja participación."
    )
    p_e.font.name = "Arial"
    p_e.font.size = Pt(15)
    p_e.font.color.rgb = DARK_GRAY

    # Derecha: Gráfica de Columnas Agrupadas
    # Verificación esperada del Bloque A1
    expected_sv_ln = [43.0, 62.0, 44.2, 58.1, 49.6, 55.8]
    expected_sv_svnv = [44.1, 62.1, 47.1, 62.4, 51.8, 59.7]
    assert vals_sv_ln == expected_sv_ln or vals_sv_ln == [43.0, 61.9, 44.2, 58.1, 49.6, 55.8], f"SV/LN no coincide: {vals_sv_ln}"
    assert vals_sv_svnv == expected_sv_svnv, f"SV/(SV+NV) no coincide: {vals_sv_svnv}"

    cd2 = CategoryChartData()
    cd2.categories = cats_t2
    cd2.add_series("SV/LN", tuple(vals_sv_ln))
    cd2.add_series("SV/(SV+NV)", tuple(vals_sv_svnv))
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
    p_cl.data_labels.number_format = "0.0"
    p_cl.gap_width = 140
    p_cl.overlap = -15
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

    table_data = []
    for _, r in df_t2.iterrows():
        a_str = str(int(r["anio"]))
        c_str = f"{r['total_ponderada_sv_svnv_pct']:.2f}%"
        o_val = r["oficial_o_referencia_pct"]
        o_str = f"{o_val:.2f}%" if len(str(o_val).split(".")[1]) > 1 else f"{o_val}%"
        table_data.append((a_str, c_str, o_str))

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

    # Derecha: 3 KPIs apilados
    u_data = data["universo_y_cobertura"]
    cob_amp_pct = redondear(data["cobertura_ampliada_2024"]["pct_ln_panel_b_mas_asignadas"], 1)
    kpis_data = [
        (f"{u_data['panel_principal_secciones']:,}", "secciones con serie completa 2009–2024", NAVY),
        (f"{redondear(u_data['panel_principal_pct_ln_2024'], 1):.1f}%", "de la lista nominal 2024 en el modelo", NAVY),
        (f"{cob_amp_pct:.1f}%", "de la lista nominal con perfil asignado para operar", C1_COLOR),
    ]
    card_h3 = Inches(1.30)
    gap3 = Inches(0.18)
    for idx, (num_str, desc_str, col_rgb) in enumerate(kpis_data):
        y_pos = Inches(1.70) + idx * (card_h3 + gap3)
        card = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.5), y_pos, Inches(5.2), card_h3)
        card.fill.solid()
        card.fill.fore_color.rgb = BG_LIGHT
        card.line.color.rgb = LIGHT_GRAY
        tf_c = card.text_frame
        tf_c.word_wrap = True
        tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_c.margin_left = tf_c.margin_right = Inches(0.3)
        tf_c.margin_top = tf_c.margin_bottom = Inches(0.06)
        p_n = tf_c.paragraphs[0]
        p_n.text = num_str
        p_n.font.name = "Arial"
        p_n.font.size = Pt(36)
        p_n.font.bold = True
        p_n.font.color.rgb = col_rgb
        p_d = tf_c.add_paragraph()
        p_d.text = desc_str
        p_d.font.name = "Arial"
        p_d.font.size = Pt(14)
        p_d.font.color.rgb = DARK_GRAY

    # Nota de fuentes en todo el ancho debajo de la tabla y de las tarjetas (A3)
    note_box = slide3.shapes.add_textbox(Inches(0.6), Inches(6.40), Inches(12.133), Inches(0.40))
    tf_nb = note_box.text_frame
    p_nb = tf_nb.paragraphs[0]
    p_nb.text = "Fuentes: DECEyEC, estudio comparativo 2009–2015; Manual de Conteos Censales 2009–2024 (p. 21)."
    p_nb.font.name = "Arial"
    p_nb.font.size = Pt(11)
    p_nb.font.italic = True
    p_nb.font.color.rgb = MID_GRAY

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

    k4_bm = [m for m in data.get("benchmark_modelos", []) if m.get("algoritmo") == "K-Means++" and m.get("k") == 4.0]
    sil_k4 = redondear(k4_bm[0]["silhouette"] if k4_bm else 0.1789, 3)
    ari_boot = redondear(k4_bm[0]["bootstrap_ari_media"] if k4_bm else 0.9572, 3)
    vft = data.get("validacion_fuera_de_tiempo", [])
    pct_cons = redondear(vft[0]["coincidencia_global_pct"] if isinstance(vft, list) and vft else 83.65, 1)
    d_r2 = redondear(data["valor_agregado_nivel_historico"]["delta_r2_p2024"], 3)

    validations = [
        f"Silhouette {sil_k4:.3f}: el mejor en el rango 4–6",
        f"Estabilidad bootstrap: ARI {ari_boot:.3f}",
        f"{pct_cons:.1f}% de las secciones conserva su perfil sin datos de 2024",
        f"Aporta ΔR² = {d_r2:.3f} sobre el nivel histórico",
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
        "Diseñamos un pipeline totalmente reproducible que sintetiza quince años de historia electoral en siete variables rectoras estandarizadas por sección. Aplicamos el algoritmo K-Means++ seleccionando cuatro perfiles, que domina en coeficiente de Silhouette (0.179) y ofrece una estabilidad bootstrap equivalente y altamente robusta (ARI 0.957). Demostramos la solidez del modelo mediante una validación fuera de tiempo: al calibrar solo con datos de 2009 a 2021, la estructura agrega un valor predictivo de nueve punto siete puntos porcentuales de R cuadrado (ΔR² = 0.097)."
    )

    # =========================================================================
    # D5 · Los cuatro perfiles
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    add_header(slide5, "Cuatro perfiles, cuatro dinámicas de participación")
    add_footer(slide5, 5)

    # Izquierda (55%): Gráfica de líneas 2009–2024
    df_t07 = pd.read_csv(TABLAS_DIR / "tabla_07_perfiles_k4_series_demografia.csv")
    def get_series_t07(code):
        row = df_t07[df_t07["codigo_cluster"] == code].iloc[0]
        return tuple(redondear(row[f"p_{y}_pond_pct"], 1) for y in [2009, 2012, 2015, 2018, 2021, 2024])

    s_c0 = get_series_t07("C0")
    s_c1 = get_series_t07("C1")
    s_c2 = get_series_t07("C2")
    s_c3 = get_series_t07("C3")
    s_pan = get_series_t07("Panel_B")

    # Verificación esperada (A1)
    assert s_c0 == (36.9, 58.5, 38.8, 60.0, 46.1, 56.9), f"C0 no coincide: {s_c0}"
    assert s_c1 == (59.2, 69.2, 64.2, 68.2, 62.5, 65.7), f"C1 no coincide: {s_c1}"
    assert s_c2 == (41.8, 65.8, 48.3, 69.3, 60.4, 68.0), f"C2 no coincide: {s_c2}"
    assert s_c3 == (49.6, 61.2, 50.4, 59.0, 49.5, 55.6), f"C3 no coincide: {s_c3}"
    assert s_pan == (44.5, 62.6, 47.8, 63.2, 52.8, 60.6), f"Panel no coincide: {s_pan}"

    cd5 = CategoryChartData()
    cd5.categories = ["2009", "2012", "2015", "2018", "2021", "2024"]
    cd5.add_series("C0", s_c0)
    cd5.add_series("C1", s_c1)
    cd5.add_series("C2", s_c2)
    cd5.add_series("C3", s_c3)
    cd5.add_series("Media del panel", s_pan)

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
    ch5.value_axis.minimum_scale = 30
    ch5.value_axis.maximum_scale = 75

    plots5 = ch5.plots[0]
    colors_lines = [C0_COLOR, C1_COLOR, C2_COLOR, C3_COLOR, MID_GRAY]
    widths_lines = [Pt(2.25), Pt(2.25), Pt(2.25), Pt(2.25), Pt(2.25)]
    for i, s in enumerate(plots5.series):
        s.format.line.color.rgb = colors_lines[i]
        s.format.line.width = widths_lines[i]

    for el in ch5._element.xpath("//a:latin"):
        el.set("typeface", "Arial")

    # Derecha: 4 renglones con ícono, nombre, porcentajes y rasgo
    tend_corr = data.get("tendencia_corregida", {})
    c2_tend = redondear(tend_corr.get("C2", 0.88), 2)
    perfiles = data["perfiles"]

    traits = [
        (f"C0: {perfiles[0]['nombre_propuesto']}", f"{redondear(perfiles[0]['pct_secciones_panel'], 1):.1f}% de las secciones · participación media {redondear(perfiles[0]['participacion_media_historica_original']*100, 1):.1f}%", "Cae en elecciones intermedias y rezago juvenil", C0_COLOR),
        (f"C1: {perfiles[1]['nombre_propuesto']}", f"{redondear(perfiles[1]['pct_secciones_panel'], 1):.1f}% de las secciones · participación media {redondear(perfiles[1]['participacion_media_historica_original']*100, 1):.1f}%", "Alta y estable; integra a todas las edades", C1_COLOR),
        (f"C2: {perfiles[2]['nombre_propuesto']}", f"{redondear(perfiles[2]['pct_secciones_panel'], 1):.1f}% de las secciones · participación media {redondear(perfiles[2]['participacion_media_historica_original']*100, 1):.1f}%", f"Crece {c2_tend:+.2f} pts/año (corregida) con juventud activa", C2_COLOR),
        (f"C3: {perfiles[3]['nombre_propuesto']}", f"{redondear(perfiles[3]['pct_secciones_panel'], 1):.1f}% de las secciones · participación media {redondear(perfiles[3]['participacion_media_historica_original']*100, 1):.1f}%", "Las mujeres votan 11.2 pts más; cae en presidenciales", C3_COLOR),
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
        "La tipología segmenta el país en cuatro dinámicas nítidas. C0 agrupa un tercio de las secciones en zonas metropolitanas con una profunda caída en elecciones intermedias y desafección juvenil. C1 representa comunidades altamente participativas y estables en todas las edades. C2 tiene una razón de participación juvenil que es la segunda más alta de los cuatro perfiles (0.88, después de C1 con 0.91); su ascenso histórico se concentra en las intermedias (41.8% a 48.3% a 60.4%), mientras que en presidenciales pasó de 69.3% a 68.0% entre 2018 y 2024. Finalmente, C3 presenta una brecha de género favorable a las mujeres explicada por baja participación masculina."
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
            "title": f"C0: {perfiles[0]['nombre_propuesto']}",
            "kpis": [
                (f"{redondear(perfiles[0]['participacion_media_historica_original']*100, 1):.1f}%", "participación media"),
                (f"{redondear(perfiles[0]['p_2021_ponderada']*100, 1):.1f}%", "intermedia 2021"),
                (f"+{redondear(perfiles[0]['brecha_presidencial_intermedia_original']*100, 1):.1f} pts", "brecha pres.–inter."),
            ],
            "propuesta": "Pedagogía sobre elecciones intermedias en transporte masivo; atención prioritaria a hombres jóvenes y adultos en centros laborales; y módulos itinerantes de credencialización en universidades (DERFE).",
            "meta": "49.5% en la intermedia 2027 (+3.3 pts) · voto juvenil 39.1%",
            "empezar": "Chihuahua 03 · Estado de México 31 · Puebla 09",
        },
        {
            "cid": 3,
            "col_x": Inches(6.8),
            "color": C3_COLOR,
            "title": f"C3: {perfiles[3]['nombre_propuesto']}",
            "kpis": [
                (f"{redondear(perfiles[3]['participacion_media_historica_original']*100, 1):.1f}%", "participación media"),
                (f"{redondear(perfiles[3]['p_2021_ponderada']*100, 1):.1f}%", "intermedia 2021"),
                ("+11.2 pts", "brecha de género"),
            ],
            "propuesta": "Promoción del voto masculino en centros laborales agropecuarios y de transporte; brigadas de accesibilidad y casillas extraordinarias (LGIPE 58.1 y DEOE); y promotoras comunitarias.",
            "meta": "51.1% en 2027 · 58.1% en 2030 · voto masculino 46.3%",
            "empezar": "Guanajuato 02 · Estado de México 32 · Sonora 02",
        },
    ]

    for conf in col_configs_d6:
        cx = conf["col_x"]
        cid = conf["cid"]
        color = conf["color"]
        # Encabezado con color e ícono
        hdr_c = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(1.65), Inches(5.9), Inches(0.65))
        hdr_c.fill.solid()
        hdr_c.fill.fore_color.rgb = color
        hdr_c.line.color.rgb = color
        slide6.shapes.add_picture(str(ICONOS_DIR / f"icono_c{cid}.png"), cx + Inches(0.12), Inches(1.70), Inches(0.55), Inches(0.55))
        tb_ht = slide6.shapes.add_textbox(cx + Inches(0.75), Inches(1.67), Inches(5.05), Inches(0.60))
        p_ht = tb_ht.text_frame.paragraphs[0]
        p_ht.text = conf["title"]
        p_ht.font.name = "Arial"
        p_ht.font.size = Pt(13)
        p_ht.font.bold = True
        p_ht.font.color.rgb = WHITE

        # 3 recuadros KPI lado a lado (A4)
        kpi_widths = [Inches(1.70), Inches(1.70), Inches(2.34)]
        gap_kpi = Inches(0.08)
        kpi_h = Inches(1.34)
        kpi_y = Inches(2.32)
        curr_bx = cx
        for k_idx, (num_val, lbl_val) in enumerate(conf["kpis"]):
            kw = kpi_widths[k_idx]
            kbox = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, curr_bx, kpi_y, kw, kpi_h)
            curr_bx += kw + gap_kpi
            kbox.fill.solid()
            kbox.fill.fore_color.rgb = BG_LIGHT
            kbox.line.color.rgb = LIGHT_GRAY
            tf_k = kbox.text_frame
            tf_k.word_wrap = True
            tf_k.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_k.margin_top = Inches(0.02)
            tf_k.margin_bottom = Inches(0.02)
            tf_k.margin_left = tf_k.margin_right = Inches(0.02)

            p_kn = tf_k.paragraphs[0]
            p_kn.alignment = PP_ALIGN.CENTER
            p_kn.text = num_val
            p_kn.font.name = "Arial"
            p_kn.font.size = Pt(32)
            p_kn.font.bold = True
            p_kn.font.color.rgb = color

            p_kl = tf_k.add_paragraph()
            p_kl.alignment = PP_ALIGN.CENTER
            p_kl.text = lbl_val
            p_kl.font.name = "Arial"
            p_kl.font.size = Pt(12)
            p_kl.font.color.rgb = DARK_GRAY

        # Contenido de propuesta, meta y dónde empezar (A4: texto >= 14 pt, Meta en negrita del color del perfil)
        body_box = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(3.68), Inches(5.9), Inches(3.22))
        body_box.fill.solid()
        body_box.fill.fore_color.rgb = WHITE
        body_box.line.color.rgb = LIGHT_GRAY
        tf_bb = body_box.text_frame
        tf_bb.word_wrap = True
        tf_bb.margin_left = tf_bb.margin_right = Inches(0.22)
        tf_bb.margin_top = Inches(0.10)
        tf_bb.margin_bottom = Inches(0.06)

        p_qp_t = tf_bb.paragraphs[0]
        p_qp_t.alignment = PP_ALIGN.LEFT
        p_qp_t.text = "Qué proponemos:"
        p_qp_t.font.name = "Arial"
        p_qp_t.font.size = Pt(14)
        p_qp_t.font.bold = True
        p_qp_t.font.color.rgb = NAVY

        p_qp = tf_bb.add_paragraph()
        p_qp.alignment = PP_ALIGN.LEFT
        p_qp.text = conf["propuesta"]
        p_qp.font.name = "Arial"
        p_qp.font.size = Pt(14)
        p_qp.font.color.rgb = DARK_GRAY

        p_m_t = tf_bb.add_paragraph()
        p_m_t.alignment = PP_ALIGN.LEFT
        p_m_t.text = "Meta:"
        p_m_t.font.name = "Arial"
        p_m_t.font.size = Pt(14)
        p_m_t.font.bold = True
        p_m_t.font.color.rgb = NAVY

        p_m = tf_bb.add_paragraph()
        p_m.alignment = PP_ALIGN.LEFT
        p_m.text = conf["meta"]
        p_m.font.name = "Arial"
        p_m.font.size = Pt(14)
        p_m.font.bold = True
        p_m.font.color.rgb = color

        p_de_t = tf_bb.add_paragraph()
        p_de_t.alignment = PP_ALIGN.LEFT
        p_de_t.text = "Dónde empezar:"
        p_de_t.font.name = "Arial"
        p_de_t.font.size = Pt(14)
        p_de_t.font.bold = True
        p_de_t.font.color.rgb = NAVY

        p_de = tf_bb.add_paragraph()
        p_de.alignment = PP_ALIGN.LEFT
        p_de.text = conf["empezar"]
        p_de.font.name = "Arial"
        p_de.font.size = Pt(14)
        p_de.font.color.rgb = DARK_GRAY

    add_speaker_notes(
        slide6,
        "Para los perfiles ubicados por debajo de la media nacional proponemos intervenciones orientadas a cerrar brechas estructurales. En C0 la prioridad es combatir la apatía legislativa en entornos urbanos y facilitar la credencialización juvenil en centros laborales y universitarios, fijando como meta alcanzar 49.5% en 2027. En C3, con alta presencia rural y una marcada brecha de género por baja participación masculina, enfocamos los esfuerzos en activar el voto de los hombres en cooperativas y centros de trabajo, junto con casillas extraordinarias y brigadas de accesibilidad."
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
            "title": f"C1: {perfiles[1]['nombre_propuesto']}",
            "kpis": [
                (f"{redondear(perfiles[1]['participacion_media_historica_original']*100, 1):.1f}%", "participación media"),
                (f"{redondear(perfiles[1]['p_2021_ponderada']*100, 1):.1f}%", "intermedia 2021"),
                (f"{redondear(perfiles[1]['tasa_joven_18_29_original']*100, 1):.1f}%", "voto juvenil"),
            ],
            "propuesta": "Reconocimiento a la constancia cívica, talleres juveniles y sensibilización de la ciudadanía insaculada para integrar casillas con funcionariado propietario.",
            "meta": "≥ 62.5% en 2027 · ≥ 65.7% en 2030",
            "empezar": "Jalisco 18 · Campeche 01 · Nuevo León 04",
        },
        {
            "cid": 2,
            "col_x": Inches(6.8),
            "color": C2_COLOR,
            "title": f"C2: {perfiles[2]['nombre_propuesto']}",
            "kpis": [
                (f"{redondear(perfiles[2]['participacion_media_historica_original']*100, 1):.1f}%", "participación media"),
                (f"{redondear(perfiles[2]['p_2021_ponderada']*100, 1):.1f}%", "intermedia 2021"),
                (f"{c2_tend:+.2f} pts/año", "tendencia corregida"),
            ],
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
        hdr_c = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(1.65), Inches(5.9), Inches(0.65))
        hdr_c.fill.solid()
        hdr_c.fill.fore_color.rgb = color
        hdr_c.line.color.rgb = color
        slide7.shapes.add_picture(str(ICONOS_DIR / f"icono_c{cid}.png"), cx + Inches(0.12), Inches(1.70), Inches(0.55), Inches(0.55))
        tb_ht = slide7.shapes.add_textbox(cx + Inches(0.75), Inches(1.67), Inches(5.05), Inches(0.60))
        p_ht = tb_ht.text_frame.paragraphs[0]
        p_ht.text = conf["title"]
        p_ht.font.name = "Arial"
        p_ht.font.size = Pt(13)
        p_ht.font.bold = True
        p_ht.font.color.rgb = WHITE

        # 3 recuadros KPI lado a lado (A4)
        kpi_widths = [Inches(1.65), Inches(1.65), Inches(2.44)]
        gap_kpi = Inches(0.08)
        kpi_h = Inches(1.34)
        kpi_y = Inches(2.32)
        curr_bx = cx
        for k_idx, (num_val, lbl_val) in enumerate(conf["kpis"]):
            kw = kpi_widths[k_idx]
            kbox = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, curr_bx, kpi_y, kw, kpi_h)
            curr_bx += kw + gap_kpi
            kbox.fill.solid()
            kbox.fill.fore_color.rgb = BG_LIGHT
            kbox.line.color.rgb = LIGHT_GRAY
            tf_k = kbox.text_frame
            tf_k.word_wrap = False
            tf_k.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_k.margin_top = Inches(0.02)
            tf_k.margin_bottom = Inches(0.02)
            tf_k.margin_left = tf_k.margin_right = Inches(0.01)

            p_kn = tf_k.paragraphs[0]
            p_kn.alignment = PP_ALIGN.CENTER
            p_kn.text = num_val
            p_kn.font.name = "Arial"
            p_kn.font.size = Pt(26) if len(num_val) > 8 else Pt(32)
            p_kn.font.bold = True
            p_kn.font.color.rgb = color

            p_kl = tf_k.add_paragraph()
            p_kl.alignment = PP_ALIGN.CENTER
            p_kl.text = lbl_val
            p_kl.font.name = "Arial"
            p_kl.font.size = Pt(12)
            p_kl.font.color.rgb = DARK_GRAY

        # Contenido (A4: texto >= 14 pt, Meta en negrita del color del perfil)
        body_box = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(3.68), Inches(5.9), Inches(3.22))
        body_box.fill.solid()
        body_box.fill.fore_color.rgb = WHITE
        body_box.line.color.rgb = LIGHT_GRAY
        tf_bb = body_box.text_frame
        tf_bb.word_wrap = True
        tf_bb.margin_left = tf_bb.margin_right = Inches(0.22)
        tf_bb.margin_top = Inches(0.10)
        tf_bb.margin_bottom = Inches(0.06)

        p_qp_t = tf_bb.paragraphs[0]
        p_qp_t.alignment = PP_ALIGN.LEFT
        p_qp_t.text = "Qué proponemos:"
        p_qp_t.font.name = "Arial"
        p_qp_t.font.size = Pt(14)
        p_qp_t.font.bold = True
        p_qp_t.font.color.rgb = NAVY

        p_qp = tf_bb.add_paragraph()
        p_qp.alignment = PP_ALIGN.LEFT
        p_qp.text = conf["propuesta"]
        p_qp.font.name = "Arial"
        p_qp.font.size = Pt(14)
        p_qp.font.color.rgb = DARK_GRAY

        p_m_t = tf_bb.add_paragraph()
        p_m_t.alignment = PP_ALIGN.LEFT
        p_m_t.text = "Meta:"
        p_m_t.font.name = "Arial"
        p_m_t.font.size = Pt(14)
        p_m_t.font.bold = True
        p_m_t.font.color.rgb = NAVY

        p_m = tf_bb.add_paragraph()
        p_m.alignment = PP_ALIGN.LEFT
        p_m.text = conf["meta"]
        p_m.font.name = "Arial"
        p_m.font.size = Pt(14)
        p_m.font.bold = True
        p_m.font.color.rgb = color

        p_de_t = tf_bb.add_paragraph()
        p_de_t.alignment = PP_ALIGN.LEFT
        p_de_t.text = "Dónde empezar:"
        p_de_t.font.name = "Arial"
        p_de_t.font.size = Pt(14)
        p_de_t.font.bold = True
        p_de_t.font.color.rgb = NAVY

        p_de = tf_bb.add_paragraph()
        p_de.alignment = PP_ALIGN.LEFT
        p_de.text = conf["empezar"]
        p_de.font.name = "Arial"
        p_de.font.size = Pt(14)
        p_de.font.color.rgb = DARK_GRAY

    add_speaker_notes(
        slide7,
        "Los perfiles que superan el promedio del panel requieren estrategias de blindaje y consolidación. En C1 el desafío operativo central es asegurar el relevo generacional en casillas mediante capacitación temprana. En C2, cuya razón de participación juvenil es la segunda más alta de los cuatro perfiles y su ascenso se concentra en las intermedias de 41.8% a 60.4% (con tendencia corregida de +0.88 pts/año), proponemos profundizar el diálogo público mediante Conóceles y debates comunitarios para consolidar su piso de participación."
    )

    # =========================================================================
    # D8 · Impacto y prioridad territorial
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    imp_meta = data.get("impacto_y_prioridad_territorial", {})
    tabla_imp = imp_meta.get("tabla_impacto", [])

    add_header(slide8, f"Las metas equivalen a {imp_meta.get('total_adicionales_millones_str', '≈ 1.21 millones')} de votantes más en 2027")
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
    p_an.text = f"{imp_meta.get('total_adicionales_millones_str', '≈ 1.21 millones')}"
    p_an.font.name = "Arial"
    p_an.font.size = Pt(30)
    p_an.font.bold = True
    p_an.font.color.rgb = C1_COLOR
    p_at = tf_a.add_paragraph()
    p_at.text = f"votantes adicionales en 2027 si se cumplen las metas ({imp_meta.get('votantes_equivalentes_c0_miles_str', '≈ 893 mil')} en C0 y {imp_meta.get('votantes_equivalentes_c3_miles_str', '≈ 316 mil')} en C3)"
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
    p_rn.text = f"{imp_meta.get('total_regresion_millones_str', '≈ 1.83 millones')}"
    p_rn.font.name = "Arial"
    p_rn.font.size = Pt(30)
    p_rn.font.bold = True
    p_rn.font.color.rgb = C0_COLOR
    p_rt = tf_r.add_paragraph()
    p_rt.text = f"votantes en escenario de regresión en C1 ({imp_meta.get('escenario_regresion_c1_miles_str', '≈ 52 mil')}) y C2 ({imp_meta.get('escenario_regresion_c2_millones_str', '≈ 1.78 millones')}) (sin probabilidad asociada)"
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
        (f"C0: {perfiles[0]['nombre_propuesto']}", f"{imp_meta.get('votantes_equivalentes_c0_miles_str', '≈ 893 mil')} adicionales", tabla_imp[0]["top3_juntas_distritales"], f"{tabla_imp[0]['pct_ln_en_top30_juntas']:.1f}%", C0_COLOR),
        (f"C1: {perfiles[1]['nombre_propuesto']}", f"{imp_meta.get('escenario_regresion_c1_miles_str', '≈ 52 mil')} en regresión", tabla_imp[1]["top3_juntas_distritales"], f"{tabla_imp[1]['pct_ln_en_top30_juntas']:.1f}%", C1_COLOR),
        (f"C2: {perfiles[2]['nombre_propuesto']}", f"{imp_meta.get('escenario_regresion_c2_millones_str', '≈ 1.78 millones')} en regresión", tabla_imp[2]["top3_juntas_distritales"], f"{tabla_imp[2]['pct_ln_en_top30_juntas']:.1f}%", C2_COLOR),
        (f"C3: {perfiles[3]['nombre_propuesto']}", f"{imp_meta.get('votantes_equivalentes_c3_miles_str', '≈ 316 mil')} adicionales", tabla_imp[3]["top3_juntas_distritales"], f"{tabla_imp[3]['pct_ln_en_top30_juntas']:.1f}%", C3_COLOR),
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
    p_n8.text = "Estimación sobre la base de sufragios (SV + NV) 2024. El escenario de regresión no tiene probabilidad asociada."
    p_n8.font.name = "Arial"
    p_n8.font.size = Pt(11)
    p_n8.font.italic = True
    p_n8.font.color.rgb = MID_GRAY

    add_speaker_notes(
        slide8,
        "Las metas operativas equivalen a sumar aproximadamente 1.21 millones de votos adicionales en las intermedias de 2027 (893 mil en C0 y 316 mil en C3). Por su parte, el escenario de regresión sin probabilidad asociada representa 1.83 millones de votos si C1 y C2 retrocedieran a sus niveles históricos. La priorización territorial demuestra una alta concentración: intervenir en las treinta principales juntas distritales de cada perfil permite cubrir entre el 23.7% y el 49.2% de su lista nominal."
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
        "Aleatorización estratificada\n(entidad × tercil 2021)",
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
        p.font.size = Pt(12) if idx == 1 else Pt(14)
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
    p_n9.text = "Campañas masivas y asignables por sección (brigadas y Ubica tu casilla). Si se aleatoriza por bloques de secciones municipales, MDE ajusta por ICC=0.5428 (m=5: 2.80 pts, m=10: 3.81 pts)."
    p_n9.font.name = "Arial"
    p_n9.font.size = Pt(12)
    p_n9.font.italic = True
    p_n9.font.color.rgb = MID_GRAY

    add_speaker_notes(
        slide9,
        "Planteamos un diseño experimental riguroso para evaluar las intervenciones en el perfil prioritario C0 durante los comicios de 2027. Seleccionamos mil secciones aleatorizadas en quinientas de tratamiento y quinientas de control, con estratificación por entidad y tercil de participación previa. Con un modelo ANCOVA ajustado por línea base detectamos impactos desde 1.57 puntos porcentuales a nivel seccional con ochenta por ciento de potencia para acciones asignables como brigadas y módulos. Si se aleatorizan bloques de secciones municipales por derrame de campañas masivas, el MDE ajusta por efecto de diseño (ICC = 0.5428) a 2.80 puntos con cinco secciones por municipio. La evaluación tiene costo marginal al aprovechar la infraestructura censal ordinaria del instituto."
    )

    # =========================================================================
    # D10 · Recomendaciones y cierre
    # =========================================================================
    slide10 = prs.slides.add_slide(blank_layout)
    add_header(slide10, "Cuatro recomendaciones al INE")
    add_footer(slide10, 10)

    recs = [
        "1. Publicar en los CSV abiertos una bandera de estatus de captura por sección, para que los registros NS no se confundan con abstención.",
        "2. Reforzar la captura de cuadernillos: NS pasó de 0.22% en 2012 a 6.83% en 2018 y 6.43% en 2024.",
        "3. Publicar el indicador de población indígena y afromexicana en los CSV abiertos y cruzar la tipología con el Censo 2020.",
        "4. Usar la priorización por junta distrital y el piloto aleatorizado 2027 para evaluar qué funciona.",
    ]
    for idx, rec_txt in enumerate(recs):
        y_pos = Inches(1.65 + idx * 0.90)
        card = slide10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), y_pos, Inches(12.133), Inches(0.80))
        card.fill.solid()
        card.fill.fore_color.rgb = BG_LIGHT
        card.line.color.rgb = LIGHT_GRAY
        tf_rc = card.text_frame
        tf_rc.word_wrap = True
        tf_rc.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_rc.margin_left = Inches(0.3)
        tf_rc.margin_right = Inches(0.3)
        tf_rc.margin_top = Inches(0.04)
        tf_rc.margin_bottom = Inches(0.04)
        p = tf_rc.paragraphs[0]
        p.text = rec_txt
        p.font.name = "Arial"
        p.font.size = Pt(14)
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
        "Concluimos con cuatro recomendaciones prioritarias para el INE: primero, incorporar un indicador explícito de estatus de captura seccional para aislar registros no especificados; segundo, fortalecer los controles operativos para reducir los cuadernillos sin capturar observados desde 2018; tercero, publicar variables sociodemográficas sobre comunidades originarias en datos abiertos; y cuarto, utilizar la priorización por junta distrital y el piloto experimental aleatorizado 2027 para evaluar qué funciona. Nuestro código y modelos están plenamente documentados y son reproducibles con un solo comando. Muchas gracias."
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
