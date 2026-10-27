#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fase 7.3: Generación de Fichas Resumen e Infografía de los 4 Perfiles Ciudadanos (08_generar_fichas.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

Cumple estrictamente con los Bloques E y G1 de la auditoría:
  E1. Aplica A2, D2, D3, D4, D5, D7 y D9 donde corresponda.
  E2. Sustituye 'Línea base intermedia oficial' por 'Línea base 2021 (cálculo CCPC)'.
      Quita el 'Hipótesis:' repetido después del título 'HIPÓTESIS'.
      Agrega a cada ficha una línea 'Entidades principales:' (top 3 de tabla_07).
  E3. 'Quiénes son': rasgos sin dato pasan a 'Hipótesis' o se eliminan.
  E4. Lema C2 -> 'Tu voto cuenta en cada elección: participa también en 2027'.
  E5. Portada: muestra los códigos C0–C3 junto a los íconos. Quita 'Entorno de software'.
  E6. Nada se sale de su recuadro; texto >= 10 pt.
  G1. Cifras leídas dinámicamente de metricas_finales.json y tablas.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Circle, Polygon, Rectangle
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from scripts.auditoria.utilidades_formato import redondear, redondear_pub

# Configuración de tipografía Arial
ARIAL_PATH = Path("/usr/share/fonts/TTF/Arial.TTF")
if ARIAL_PATH.exists():
    fm.fontManager.addfont(str(ARIAL_PATH))
    matplotlib.rcParams["font.family"] = "Arial"
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42

METRICAS_PATH = PROJECT_ROOT / "outputs" / "metricas_finales.json"
TABLA_07_PATH = PROJECT_ROOT / "outputs" / "tablas" / "tabla_07_perfiles_k4_series_demografia.csv"
TABLA_12_PATH = PROJECT_ROOT / "outputs" / "tablas" / "tabla_12_lineas_base_metas.csv"
TABLA_17_PATH = PROJECT_ROOT / "outputs" / "tablas" / "tabla_17_impacto.csv"
OUT_ENTREGABLES = PROJECT_ROOT / "outputs" / "entregables"
OUT_ENTREGABLES.mkdir(parents=True, exist_ok=True)

THEMES = {
    0: {"primary": "#C2410C", "bg": "#FFF7ED", "border": "#FDBA74", "badge": "#9A3412", "accent": "#EA580C"},
    1: {"primary": "#047857", "bg": "#ECFDF5", "border": "#6EE7B7", "badge": "#065F46", "accent": "#059669"},
    2: {"primary": "#1D4ED8", "bg": "#EFF6FF", "border": "#93C5FD", "badge": "#1E40AF", "accent": "#2563EB"},
    3: {"primary": "#6D28D9", "bg": "#F5F3FF", "border": "#C4B5FD", "badge": "#5B21B6", "accent": "#7C3AED"},
}


def cargar_cifras() -> dict:
    """Extrae todas las cifras y métricas requeridas desde tablas y JSON (Bloque 6)."""
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    t07_df = pd.read_csv(TABLA_07_PATH)
    t12_df = pd.read_csv(TABLA_12_PATH).set_index("codigo_cluster")
    t17_df = pd.read_csv(TABLA_17_PATH).set_index("codigo_cluster")
    serie = {r["anio"]: r for r in data.get("serie_nacional_2009_2024", [])}
    subest_2018 = float(serie.get(2018, {}).get("subestimacion_erronea_sv_ln_pond_pts", 4.27))
    texts_dict = build_profile_texts(data, t07_df)
    return {
        "data": data,
        "t07_df": t07_df,
        "t12_df": t12_df,
        "t17_df": t17_df,
        "texts_dict": texts_dict,
        "subest_2018": subest_2018,
    }


def get_top3_entidades(t07_df: pd.DataFrame, cid: int) -> str:
    """Extrae las 3 entidades principales con su porcentaje desde tabla_07."""
    row = t07_df[t07_df["codigo_cluster"] == f"C{cid}"].iloc[0]
    raw = str(row["top5_entidades_secciones"])
    parts = [p.strip() for p in raw.split(";")][:3]
    cleaned = []
    for p in parts:
        if "(" in p and "," in p:
            name, rest = p.split("(", 1)
            pct = rest.split(",", 1)[0].strip()
            cleaned.append(f"{name.strip()} ({pct})")
        else:
            cleaned.append(p)
    return ", ".join(cleaned)


def build_profile_texts(data: dict, t07_df: pd.DataFrame) -> dict:
    """Construye dinámicamente los textos de los perfiles leyendo de datos y tablas (G1)."""
    perfiles = data["perfiles"]
    pan_b = data["resumen_panel_b"]
    tend_corr = data.get("tendencia_corregida", {})
    df12 = pd.read_csv(TABLA_12_PATH).set_index("codigo_cluster")
    df17 = pd.read_csv(TABLA_17_PATH).set_index("codigo_cluster")

    p0 = perfiles[0]
    p1 = perfiles[1]
    p2 = perfiles[2]
    p3 = perfiles[3]

    p0_urb = redondear_pub(p0['pct_secciones_urbanas'], 1)
    p0_part = redondear_pub(p0['participacion_media_historica_original'] * 100, 1)
    p0_homb = redondear_pub(p0['tasa_hombres_original'] * 100, 1)
    pan_b_homb = redondear_pub(pan_b['tasa_hombres_original'] * 100, 1)
    p0_brecha = redondear_pub(p0['brecha_presidencial_intermedia_original'] * 100, 1)

    p1_urb = redondear_pub(p1['pct_secciones_urbanas'], 1)
    p1_rur = redondear_pub(p1['pct_secciones_rurales'], 1)
    p1_part = redondear_pub(p1['participacion_media_historica_original'] * 100, 1)
    p1_jov = redondear_pub(p1['tasa_joven_18_29_original'] * 100, 1)
    p1_ratio = redondear_pub(p1['ratio_participacion_joven_original'], 2)
    p1_p2021 = redondear_pub(p1['p_2021_ponderada'] * 100, 1)
    p1_p2024 = redondear_pub(p1['p_2024_ponderada'] * 100, 1)

    p2_urb = redondear_pub(p2['pct_secciones_urbanas'], 1)
    p2_ratio = redondear_pub(p2['ratio_participacion_joven_original'], 2)
    p2_p2009 = redondear_pub(p2['p_2009_ponderada'] * 100, 1)
    p2_p2012 = redondear_pub(p2['p_2012_ponderada'] * 100, 1)
    p2_p2015 = redondear_pub(p2['p_2015_ponderada'] * 100, 1)
    p2_p2018 = redondear_pub(p2['p_2018_ponderada'] * 100, 1)
    p2_p2021 = redondear_pub(p2['p_2021_ponderada'] * 100, 1)
    p2_p2024 = redondear_pub(p2['p_2024_ponderada'] * 100, 1)
    c2_tend = redondear(tend_corr.get('C2', 0.88), 2)

    p3_rur = redondear_pub(p3['pct_secciones_rurales'], 1)
    pan_b_rur = redondear_pub(pan_b.get('pct_secciones_rurales_1d', 26.9), 1)
    p3_muj = redondear_pub(p3['tasa_mujeres_original'] * 100, 1)
    p3_homb = redondear_pub(p3['tasa_hombres_original'] * 100, 1)
    p3_brecha = redondear_pub(p3['brecha_genero_original'] * 100, 1)

    m0_meta = df12.loc["C0", "meta_intermedia_2027"]
    m0_delta = df17.loc["C0", "meta_delta_pts"]
    m0_base = redondear_pub(p0['p_2021_ponderada'] * 100, 1)
    m0_joven = df12.loc["C0", "meta_tasa_joven"]

    c0_imp_str = str(df17.loc["C0", "votantes_equivalentes_str"]).replace(" más", "").strip()
    c1_reg_str = df17.loc["C1", "escenario_regresion_str"]
    c2_reg_str = df17.loc["C2", "escenario_regresion_str"]
    c3_imp_str = str(df17.loc["C3", "votantes_equivalentes_str"]).replace(" más", "").strip()

    m3_meta = df12.loc["C3", "meta_intermedia_2027"]
    m3_pres = df12.loc["C3", "meta_presidencial_2030"]
    m3_homb = df12.loc["C3", "meta_tasa_hombres"]

    texts = {
        0: {
            "quienes_son": (
                f"Ciudadanía predominantemente urbana ({p0_urb:.1f}%) en grandes zonas metropolitanas. "
                f"Tiene la menor participación promedio ({p0_part:.1f}%), la menor participación masculina "
                f"({p0_homb:.1f}% vs. {pan_b_homb:.1f}% del panel) y la mayor caída en elecciones intermedias (+{p0_brecha:.1f} pts)."
            ),
            "hipotesis": (
                "Por probar: desafección hacia las elecciones intermedias, movilidad residencial en zonas urbanas "
                "y falta de tiempo en jóvenes que trabajan."
            ),
            "propuesta": (
                "Pedagogía electoral sobre comicios intermedios en transporte masivo; atención prioritaria a hombres jóvenes y adultos en centros laborales "
                "y parques industriales; y módulos itinerantes de credencialización en universidades (conforme a las atribuciones de la DERFE)."
            ),
            "meta": f"Elevar la participación a {m0_meta} en la intermedia de 2027 ({m0_delta} sobre la línea base 2021 de {m0_base:.1f}%) y el voto juvenil 18–29 a {m0_joven}.",
            "indicador": "Tasa seccional ponderada SV/(SV+NV) en comicios federales de 2027 y tasa juvenil en CCPC.",
            "unidad_costo": "DECEyEC, DERFE y Juntas Distritales | Costo: Medio (estimación indicativa)",
            "lema": "Cada elección define tu entorno: infórmate, ubica tu casilla y participa en 2027",
            "brecha_label": "Brecha Pres.–Inter.",
            "brecha_val": f"+{p0_brecha:.1f} pts",
            "brecha_sub": "Mayor desmovilización intermedia",
            "impacto_lbl": "Impacto:",
            "impacto_txt": f"{c0_imp_str} votantes adicionales si se cumple la meta 2027",
            "impacto_portada": f"{c0_imp_str} adicionales",
            "rasgo_portada": "Rezago juvenil y ciclo presidencial",
        },
        1: {
            "quienes_son": (
                f"Secciones con distribución equilibrada entre áreas urbanas ({p1_urb:.1f}%) y rurales ({p1_rur:.1f}%). "
                f"Registran la mayor constancia electoral ({p1_part:.1f}% promedio), la menor brecha presidencial-intermedia "
                f"y una elevada integración juvenil ({p1_jov:.1f}%)."
            ),
            "hipotesis": (
                "La alta participación sugiere redes comunitarias sólidas y normas cívicas intergeneracionales arraigadas (arraigo vecinal y cohesión social), "
                "donde la integración de mesas directivas de casilla se percibe como un deber cívico compartido."
            ),
            "propuesta": (
                "Reconocimiento a la constancia cívica comunitaria; talleres juveniles de formación cívica en planteles locales; y reclutamiento temprano "
                "de CAE y sensibilización de la ciudadanía insaculada para asegurar la instalación completa de casillas con funcionariado propietario."
            ),
            "meta": f"Sostener una participación ≥ {p1_p2021:.1f}% en la intermedia de 2027 y ≥ {p1_p2024:.1f}% en la presidencial de 2030, aumentando la proporción de casillas con funcionariado propietario.",
            "indicador": "Tasa ponderada SV/(SV+NV) 2027/2030 y % de casillas instaladas con funcionariado propietario (DEOE).",
            "unidad_costo": "DECEyEC y Vocalías de Capacitación de Juntas Distritales | Costo: Bajo (programas ordinarios)",
            "lema": "Si te visitan para integrar una casilla, participa: tu comunidad cuenta contigo",
            "brecha_label": "Voto Juvenil 18–29",
            "brecha_val": f"{p1_jov:.1f}%",
            "brecha_sub": f"Mayor razón de voto joven ({p1_ratio:.2f})",
            "impacto_lbl": "En regresión:",
            "impacto_txt": f"{c1_reg_str} votantes en escenario de regresión (sin probabilidad asociada)",
            "impacto_portada": f"{c1_reg_str} en regresión",
            "rasgo_portada": "Máxima estabilidad y cohesión",
        },
        2: {
            "quienes_son": (
                f"Secciones mayoritariamente urbanas ({p2_urb:.1f}%) con dinamismo cívico. "
                f"Su razón de participación juvenil es la segunda más alta ({p2_ratio:.2f}, después de C1 con {p1_ratio:.2f}). "
                f"El ascenso se concentra en las intermedias ({p2_p2009:.1f}% → {p2_p2015:.1f}% → {p2_p2021:.1f}%); "
                f"en presidenciales varió poco ({p2_p2012:.1f}% → {p2_p2018:.1f}% → {p2_p2024:.1f}%)."
            ),
            "hipotesis": (
                "El crecimiento en intermedias responde a la consolidación de demandas comunitarias en zonas en desarrollo, "
                "con un electorado joven activo que requiere incentivos específicos en elecciones intermedias."
            ),
            "propuesta": (
                "Consolidar el hábito del voto mediante foros 'Diálogos por la Democracia'; vinculación con colectivos juveniles y organizaciones vecinales; "
                "monitoreo preventivo de casillas en crecimiento por la DEOE; y difusión del sistema 'Conóceles' para consultar candidaturas."
            ),
            "meta": f"Consolidar una participación ≥ {p2_p2021:.1f}% en la intermedia de 2027 y sostener una razón de participación juvenil ≥ {p2_ratio:.2f}.",
            "indicador": "Tasa ponderada SV/(SV+NV) 2027 y razón de participación juvenil CCPC.",
            "unidad_costo": "DECEyEC, DEOE y Juntas Distritales | Costo: Bajo-Medio (foros distritales)",
            "lema": "Tu voto cuenta en cada elección: participa también en 2027",
            "brecha_label": "Tendencia Corregida",
            "brecha_val": f"{c2_tend:+.2f} pts/año",
            "brecha_sub": "Ascenso neto (P ~ año + pres)",
            "impacto_lbl": "En regresión:",
            "impacto_txt": f"{c2_reg_str} votantes en escenario de regresión (sin probabilidad asociada)",
            "impacto_portada": f"{c2_reg_str} en regresión",
            "rasgo_portada": f"Ascenso continuo ({c2_tend:+.2f} pts/año)",
        },
        3: {
            "quienes_son": (
                f"Secciones con marcada sobrerrepresentación rural ({p3_rur:.1f}% vs. {pan_b_rur:.1f}% del panel). "
                f"Se distingue por una pronunciada brecha de género a favor de las mujeres ({p3_muj:.1f}% en mujeres vs. {p3_homb:.1f}% en hombres, "
                f"brecha de +{p3_brecha:.1f} pts) y una caída en comicios presidenciales desde 2012."
            ),
            "hipotesis": (
                "El rezago del voto masculino y la caída presidencial obedecen a movilidad laboral o menor involucramiento en procesos electorales federales, "
                "además de dispersión geográfica de casillas."
            ),
            "propuesta": (
                "Campaña focalizada de motivación del voto masculino en centros agropecuarios y rutas de transporte; brigadas de accesibilidad "
                "y propuesta de casillas extraordinarias a los Consejos Distritales conforme a la LGIPE; y alianzas con promotoras cívicas comunitarias."
            ),
            "meta": f"Elevar la participación a {m3_meta} en 2027, {m3_pres} en 2030 y el voto masculino a {m3_homb} en 2027 (cerrando la mitad de la brecha con el Panel B).",
            "indicador": "Tasa seccional masculina y general ponderada SV/(SV+NV) en CCPC.",
            "unidad_costo": "DECEyEC, DEOE y Juntas Distritales | Costo: Medio (tiempos oficiales y rutas DEOE)",
            "lema": "La participación de todas y todos cuenta: sumemos la voz de hombres y jóvenes en cada comunidad",
            "brecha_label": "Brecha de Género",
            "brecha_val": f"+{p3_brecha:.1f} pts",
            "brecha_sub": "Las mujeres votan más que los hombres",
            "impacto_lbl": "Impacto:",
            "impacto_txt": f"{c3_imp_str} votantes adicionales si se cumple la meta 2027",
            "impacto_portada": f"{c3_imp_str} adicionales",
            "rasgo_portada": f"Brecha de género (+{p3_brecha:.1f} pts) y caída presidencial",
        },
    }

    for cid in range(4):
        c_code = f"C{cid}"
        texts[cid]["top3_entidades"] = get_top3_entidades(t07_df, cid)
        texts[cid]["top3_juntas"] = str(df17.loc[c_code, "top3_juntas_distritales"])

    return texts


def draw_profile_icon(ax, cid: int, cx: float, cy: float, radius: float = 0.038, color: str = "#1E3A8A") -> None:
    """Dibuja un ícono geométrico distintivo limpio para cada perfil en coordenadas de transAxes."""
    circ = Circle((cx, cy), radius, facecolor=color, edgecolor="white", linewidth=max(1.0, 2.0 * radius / 0.038), transform=ax.transAxes, zorder=6)
    ax.add_patch(circ)
    scale = radius / 0.038
    if cid == 0:
        # Reloj de arena / ciclo intermitente
        pts = np.array([
            [cx - 0.016 * scale, cy + 0.018 * scale],
            [cx + 0.016 * scale, cy + 0.018 * scale],
            [cx, cy],
            [cx + 0.016 * scale, cy - 0.018 * scale],
            [cx - 0.016 * scale, cy - 0.018 * scale],
            [cx, cy],
        ])
        ax.add_patch(Polygon(pts, closed=True, facecolor="white", transform=ax.transAxes, zorder=7))
    elif cid == 1:
        # Escudo de estabilidad cívica
        pts = np.array([
            [cx - 0.018 * scale, cy + 0.018 * scale],
            [cx + 0.018 * scale, cy + 0.018 * scale],
            [cx + 0.018 * scale, cy + 0.010 * scale],
            [cx + 0.014 * scale, cy - 0.016 * scale],
            [cx, cy - 0.024 * scale],
            [cx - 0.014 * scale, cy - 0.016 * scale],
            [cx - 0.018 * scale, cy + 0.010 * scale],
        ])
        ax.add_patch(Polygon(pts, closed=True, facecolor="white", transform=ax.transAxes, zorder=7))
    elif cid == 2:
        # Flecha ascendente
        ax.plot([cx - 0.018 * scale, cx - 0.005 * scale, cx + 0.006 * scale, cx + 0.018 * scale],
                [cy - 0.014 * scale, cy - 0.002 * scale, cy - 0.006 * scale, cy + 0.016 * scale],
                color="white", linewidth=max(1.0, 2.8 * scale), transform=ax.transAxes, zorder=7)
        ax.plot([cx + 0.008 * scale, cx + 0.018 * scale, cx + 0.018 * scale],
                [cy + 0.016 * scale, cy + 0.016 * scale, cy + 0.005 * scale],
                color="white", linewidth=max(1.0, 2.8 * scale), transform=ax.transAxes, zorder=7)
    elif cid == 3:
        # Símbolo distintivo de brecha de género
        c_inner = Circle((cx, cy + 0.008 * scale), 0.011 * scale, fill=False, edgecolor="white", linewidth=max(1.0, 2.4 * scale), transform=ax.transAxes, zorder=7)
        ax.add_patch(c_inner)
        ax.plot([cx, cx], [cy - 0.003 * scale, cy - 0.020 * scale], color="white", linewidth=max(1.0, 2.4 * scale), transform=ax.transAxes, zorder=7)
        ax.plot([cx - 0.010 * scale, cx + 0.010 * scale], [cy - 0.012 * scale, cy - 0.012 * scale], color="white", linewidth=max(1.0, 2.4 * scale), transform=ax.transAxes, zorder=7)


def render_cover_page(data: dict, texts: dict, cifras: dict = None) -> plt.Figure:
    """Página 1: Portada ejecutiva en formato carta horizontal."""
    fig = plt.figure(figsize=(11.0, 8.5), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    # Marco exterior
    border = FancyBboxPatch(
        (0.03, 0.03), 0.94, 0.94,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        facecolor="#F8FAFC", edgecolor="#1E3A8A", linewidth=2.2, transform=ax.transAxes
    )
    ax.add_patch(border)

    # Banner superior institucional
    hdr = FancyBboxPatch(
        (0.04, 0.81), 0.92, 0.14,
        boxstyle="round,pad=0.01,rounding_size=0.015",
        facecolor="#1E3A8A", edgecolor="#1E3A8A", transform=ax.transAxes
    )
    ax.add_patch(hdr)
    ax.text(
        0.50, 0.905, "FICHAS TÉCNICAS E INFOGRÁFICAS DE PARTICIPACIÓN ELECTORAL",
        fontsize=16.0, fontweight="bold", color="white", ha="center", va="center", transform=ax.transAxes
    )
    ax.text(
        0.50, 0.855, "Perfiles ciudadanos de participación electoral en México, 2009–2024: tipología seccional y estrategias de educación cívica",
        fontsize=11.0, color="#E2E8F0", ha="center", va="center", transform=ax.transAxes
    )
    ax.text(
        0.50, 0.825, "Concurso INE: 'Hackea la participación: Datos que construyen democracia' · Reto 1: Perfiles ciudadanos de participación",
        fontsize=10.0, color="#CBD5E1", style="italic", ha="center", va="center", transform=ax.transAxes
    )

    # Bloque de datos del equipo y repositorio (E5: eliminado entorno de software)
    team_box = FancyBboxPatch(
        (0.04, 0.675), 0.92, 0.115,
        boxstyle="round,pad=0.01,rounding_size=0.015",
        facecolor="white", edgecolor="#CBD5E1", linewidth=1.2, transform=ax.transAxes
    )
    ax.add_patch(team_box)
    ax.text(0.06, 0.755, "Equipo:", fontsize=10.5, fontweight="bold", color="#1E3A8A", transform=ax.transAxes)
    ax.text(0.13, 0.755, "Byte me", fontsize=10.5, color="#111827", transform=ax.transAxes)

    ax.text(0.06, 0.720, "Integrantes:", fontsize=10.5, fontweight="bold", color="#1E3A8A", transform=ax.transAxes)
    members_str = "1. Johanan Olivares Gutiérrez (representante)   ·   2. Oscar Ariel Cuevas Martínez   ·   3. Saúl Alexis Arias González"
    ax.text(0.16, 0.720, members_str, fontsize=10.2, color="#111827", transform=ax.transAxes)

    ax.text(0.06, 0.685, "Repositorio público:", fontsize=10.5, fontweight="bold", color="#1E3A8A", transform=ax.transAxes)
    ax.text(0.21, 0.685, "https://github.com/Johanan1113/Hackaton_INE_byte_me", fontsize=10.2, color="#1D4ED8", transform=ax.transAxes)

    # Bloque metodológico en exactamente 3 renglones
    meth_box = FancyBboxPatch(
        (0.04, 0.455), 0.92, 0.200,
        boxstyle="round,pad=0.01,rounding_size=0.015",
        facecolor="#F1F5F9", edgecolor="#94A3B8", linewidth=1.2, transform=ax.transAxes
    )
    ax.add_patch(meth_box)
    ax.text(0.06, 0.625, "SÍNTESIS METODOLÓGICA (TRES PILARES ANALÍTICOS):", fontsize=11.0, fontweight="bold", color="#0F172A", transform=ax.transAxes)
    univ = data.get("universo_y_cobertura", {})
    pan_b_secc = univ.get("panel_principal_secciones", 53644)
    pan_b_pct_secc = redondear(univ.get("panel_principal_pct_secciones_2024", 75.82), 1)
    pan_b_pct_ln = redondear(univ.get("panel_principal_pct_ln_2024", 79.53), 1)
    pan_b_mun = univ.get("panel_principal_municipios", 2393)

    subest_val = cifras["subest_2018"] if (cifras and "subest_2018" in cifras) else float(data.get("serie_nacional_2009_2024", [{}])[3].get("subestimacion_erronea_sv_ln_pond_pts", 0.0))
    p1_text = textwrap.fill(f"1. Corrección por registros sin captura (NS): En microdatos abiertos la Lista Nominal es LN = SV + NV + NS; la fórmula oficial es SV/(SV+NV), evitando subestimar hasta {subest_val:.2f} pts en 2018.", width=108)
    p2_text = textwrap.fill(f"2. Panel Principal continuo (Opción B, cero imputación): {pan_b_secc:,} secciones con captura válida (SV+NV ≥ 50) y sin saltos por reseccionamiento ({pan_b_pct_secc:.1f}% secciones y {pan_b_pct_ln:.1f}% LN 2024 en {pan_b_mun:,} municipios).", width=108)
    bench_k4 = [r for r in data["benchmark_modelos"] if r.get("algoritmo") == "K-Means++" and int(r.get("k", 0)) == 4][0]
    sil_val = bench_k4["silhouette"]
    ari_boot_val = bench_k4["bootstrap_ari_media"]
    rf_acc_val = data["interpretabilidad_rf_anova"][0]["rf_cv5_accuracy_media"] * 100
    p3_text = textwrap.fill(
        f"3. Segmentación K-Means++ con k=4: domina dentro del rango 4–6 de la convocatoria "
        f"(Silhouette = {sil_val:.4f}; ARI bootstrap = {ari_boot_val:.4f}). "
        f"Un Random Forest reproduce las etiquetas con {rf_acc_val:.2f}% de exactitud (medida de interpretabilidad, no de validación).",
        width=108
    )
    ax.text(0.06, 0.588, p1_text, fontsize=10.0, color="#1F2937", va="top", transform=ax.transAxes)
    ax.text(0.06, 0.540, p2_text, fontsize=10.0, color="#1F2937", va="top", transform=ax.transAxes)
    ax.text(0.06, 0.492, p3_text, fontsize=10.0, color="#1F2937", va="top", transform=ax.transAxes)

    # Mini-tabla de resumen de los 4 perfiles (Bloque 3.5: espacio holgado sin solapes)
    ax.text(0.04, 0.418, "MATRIZ EJECUTIVA DE LOS 4 PERFILES CIUDADANOS (k = 4):", fontsize=11.2, fontweight="bold", color="#1E3A8A", transform=ax.transAxes)

    y_tbl = 0.380
    # Encabezado tabla
    ax.add_patch(Rectangle((0.04, y_tbl - 0.005), 0.92, 0.030, facecolor="#1E3A8A", transform=ax.transAxes))
    ax.text(0.070, y_tbl + 0.010, "Perfil", fontsize=10.0, fontweight="bold", color="white", ha="center", va="center", transform=ax.transAxes)
    ax.text(0.220, y_tbl + 0.010, "Nombre Oficial del Perfil", fontsize=10.0, fontweight="bold", color="white", ha="center", va="center", transform=ax.transAxes)
    ax.text(0.405, y_tbl + 0.010, "Secciones (% Panel)", fontsize=10.0, fontweight="bold", color="white", ha="center", va="center", transform=ax.transAxes)
    ax.text(0.530, y_tbl + 0.010, "LN 2024 (% LN)", fontsize=10.0, fontweight="bold", color="white", ha="center", va="center", transform=ax.transAxes)
    ax.text(0.640, y_tbl + 0.010, "Part. Media", fontsize=10.0, fontweight="bold", color="white", ha="center", va="center", transform=ax.transAxes)
    ax.text(0.745, y_tbl + 0.010, "Impacto 2027", fontsize=10.0, fontweight="bold", color="white", ha="center", va="center", transform=ax.transAxes)
    ax.text(0.865, y_tbl + 0.010, "Rasgo Distintivo Clave", fontsize=10.0, fontweight="bold", color="white", ha="center", va="center", transform=ax.transAxes)

    perfiles = data["perfiles"]
    rows_data = []
    for idx in range(4):
        cid_str = f"C{idx}"
        p = perfiles[idx]
        t = texts[idx]
        rows_data.append((
            cid_str,
            p["nombre_propuesto"],
            f"{p['n_secciones']:,} ({redondear_pub(p['pct_secciones_panel'], 1):.1f}%)",
            f"{p['ln_2024']/1e6:.2f}M ({redondear_pub(p['pct_ln_panel'], 1):.1f}%)",
            f"{redondear_pub(p['participacion_media_historica_original']*100, 1):.1f}%",
            t["impacto_portada"],
            t["rasgo_portada"],
        ))

    for idx, (cid, name, secc, ln, part, imp_txt, rasgo) in enumerate(rows_data):
        y_r = y_tbl - 0.046 - idx * 0.060
        bg_c = "#FFFFFF" if idx % 2 == 0 else "#F8FAFC"
        ax.add_patch(Rectangle((0.04, y_r - 0.013), 0.92, 0.054, facecolor=bg_c, edgecolor="#E2E8F0", linewidth=0.8, transform=ax.transAxes))
        theme_p = THEMES[idx]
        # E5: ícono y código C0-C3 juntos
        draw_profile_icon(ax, idx, 0.058, y_r + 0.014, radius=0.013, color=theme_p["primary"])
        ax.text(0.078, y_r + 0.014, f"C{idx}", fontsize=10.0, fontweight="bold", color=theme_p["primary"], ha="center", va="center", transform=ax.transAxes)
        wrapped_name = textwrap.fill(name, width=22)
        ax.text(0.100, y_r + 0.014, wrapped_name, fontsize=10.0, fontweight="bold", color="#0F172A", va="center", transform=ax.transAxes)
        ax.text(0.405, y_r + 0.014, secc, fontsize=10.0, color="#1F2937", ha="center", va="center", transform=ax.transAxes)
        ax.text(0.530, y_r + 0.014, ln, fontsize=10.0, color="#1F2937", ha="center", va="center", transform=ax.transAxes)
        ax.text(0.640, y_r + 0.014, part, fontsize=10.0, fontweight="bold", color=theme_p["primary"], ha="center", va="center", transform=ax.transAxes)
        ax.text(0.745, y_r + 0.014, imp_txt, fontsize=10.0, fontweight="bold", color="#1E3A8A", ha="center", va="center", transform=ax.transAxes)
        wrapped_rasgo = textwrap.fill(rasgo, width=18)
        ax.text(0.865, y_r + 0.014, wrapped_rasgo, fontsize=10.0, color="#374151", ha="center", va="center", transform=ax.transAxes)

    # Pie de página institucional
    ax.text(
        0.50, 0.065,
        "Fuentes: Microdatos Conteos Censales de Participación Ciudadana (CCPC 2009–2024), INE México. Consulta las fichas individuales en las páginas 2 a 5.",
        fontsize=10.0, color="#64748B", ha="center", va="center", style="italic", transform=ax.transAxes
    )

    return fig


def render_profile_page(cid: int, data: dict, texts_dict: dict) -> plt.Figure:
    """Páginas 2 a 5: Ficha individual completa de perfil en formato carta horizontal."""
    p = data["perfiles"][cid]
    texts = texts_dict[cid]
    theme = THEMES[cid]
    pan_b = data["resumen_panel_b"]
    serie_nac = data["serie_nacional_2009_2024"]
    years = [r["anio"] for r in serie_nac]

    fig = plt.figure(figsize=(11.0, 8.5), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    # Marco exterior
    border = FancyBboxPatch(
        (0.025, 0.025), 0.95, 0.95,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        facecolor=theme["bg"], edgecolor=theme["border"], linewidth=2.0, transform=ax.transAxes
    )
    ax.add_patch(border)

    # Banner superior
    hdr = FancyBboxPatch(
        (0.035, 0.865), 0.93, 0.095,
        boxstyle="round,pad=0.01,rounding_size=0.015",
        facecolor=theme["primary"], edgecolor=theme["primary"], transform=ax.transAxes
    )
    ax.add_patch(hdr)

    draw_profile_icon(ax, cid, 0.075, 0.912, radius=0.028, color=theme["badge"])

    ax.text(
        0.12, 0.925, f"PERFIL {p['codigo_cluster']}: {p['nombre_propuesto']}",
        fontsize=14.5, fontweight="bold", color="white", va="center", transform=ax.transAxes
    )
    cov_str = (
        f"Cobertura: {p['n_secciones']:,} secc. ({redondear(p['pct_secciones_panel'], 1):.1f}%)   •   "
        f"LN: {p['ln_2024']/1e6:.2f}M ({redondear(p['pct_ln_panel'], 1):.1f}%) en {p['n_municipios_con_presencia']:,} mun.   •   "
        f"Composición: {redondear(p['pct_secciones_urbanas'], 1):.1f}% Urb., {redondear(p['pct_secciones_rurales'], 1):.1f}% Rur., {redondear(p['pct_secciones_mixtas'], 1):.1f}% Mix."
    )
    ax.text(
        0.12, 0.885, cov_str,
        fontsize=10.0, color="#F3F4F6", va="center", transform=ax.transAxes
    )

    # 4 Cifras Grandes (Callout Cards) (y=0.740..0.845)
    card_w = 0.218
    gap = 0.019
    x_starts = [0.035 + i * (card_w + gap) for i in range(4)]

    # E2: Línea base 2021 (cálculo CCPC)
    cards_info = [
        ("PARTICIPACIÓN MEDIA", f"{redondear(p['participacion_media_historica_original']*100, 1):.1f}%", "Promedio 6 elecciones (2009–24)"),
        ("INTERMEDIA 2021", f"{redondear(p['p_2021_ponderada']*100, 1):.1f}%", "Línea base 2021 (cálculo CCPC)"),
        ("PRESIDENCIAL 2024", f"{redondear(p['p_2024_ponderada']*100, 1):.1f}%", "Última elección presidencial"),
        (texts["brecha_label"].upper(), texts["brecha_val"], texts["brecha_sub"]),
    ]

    for i, (title_c, val_c, sub_c) in enumerate(cards_info):
        box_c = FancyBboxPatch(
            (x_starts[i], 0.740), card_w, 0.105,
            boxstyle="round,pad=0.008,rounding_size=0.012",
            facecolor="white", edgecolor=theme["border"], linewidth=1.5, transform=ax.transAxes
        )
        ax.add_patch(box_c)
        ax.text(x_starts[i] + card_w / 2, 0.825, title_c, fontsize=10.0, fontweight="bold", color="#4B5563", ha="center", va="center", transform=ax.transAxes)
        ax.text(x_starts[i] + card_w / 2, 0.782, val_c, fontsize=23.0, fontweight="bold", color=theme["primary"], ha="center", va="center", transform=ax.transAxes)
        ax.text(x_starts[i] + card_w / 2, 0.752, sub_c, fontsize=10.0, color="#6B7280", ha="center", va="center", transform=ax.transAxes)

    # Columna Izquierda: Gráfica de la serie histórica ponderada (0.055..0.495, y=0.380..0.695)
    ax_plot = fig.add_axes([0.055, 0.380, 0.440, 0.315])
    p_vals = [p[f"p_{y}_ponderada"] * 100 for y in years]
    b_vals = [pan_b[f"p_{y}_ponderada"] * 100 for y in years]

    # Sombra en intermedias
    for ym in [2009, 2015, 2021]:
        ax_plot.axvspan(ym - 0.5, ym + 0.5, color="#F1F5F9", alpha=0.9, zorder=0)

    # Línea del cluster
    ax_plot.plot(years, p_vals, marker="o", linewidth=2.8, markersize=7.5, color=theme["primary"], label=f"Perfil {p['codigo_cluster']}", zorder=4)
    for i_x, (x_v, y_v) in enumerate(zip(years, p_vals)):
        is_dip = False
        if i_x == 0 and len(p_vals) > 1 and y_v < p_vals[1]:
            is_dip = True
        elif i_x == len(p_vals) - 1 and len(p_vals) > 1 and y_v < p_vals[i_x - 1]:
            is_dip = True
        elif 0 < i_x < len(p_vals) - 1 and y_v < p_vals[i_x - 1] and y_v < p_vals[i_x + 1]:
            is_dip = True

        dy = -14 if is_dip else 11
        va_align = "top" if is_dip else "bottom"
        ax_plot.annotate(
            f"{redondear(y_v, 1):.1f}%", (x_v, y_v), textcoords="offset points", xytext=(0, dy),
            ha="center", va=va_align, fontsize=10.0, fontweight="bold", color=theme["primary"],
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85),
            zorder=5
        )

    # Línea gris punteada Media del Panel B
    ax_plot.plot(years, b_vals, linestyle=":", marker="^", linewidth=2.0, markersize=6.0, color="#64748B", label="Media del Panel B", zorder=3)
    ax_plot.set_xticks(years)
    ax_plot.set_xticklabels([f"{y}\n({'Inter.' if y in (2009,2015,2021) else 'Pres.'})" for y in years], fontsize=10.0)
    ax_plot.set_ylim(min(min(p_vals), min(b_vals)) - 6, max(max(p_vals), max(b_vals)) + 7)
    ax_plot.tick_params(axis="y", labelsize=10.0)
    # ax_plot.set_ylabel
    ax_plot.set_title("Trayectoria Ponderada: Participación SV/(SV+NV) (%)", fontsize=10.5, fontweight="bold", pad=6)
    ax_plot.grid(True, alpha=0.5)
    ax_plot.legend(loc="lower right", fontsize=10.0, frameon=True)

    # Columna Derecha: Bloques de Diagnóstico e Intervención (medición dinámica per Bloque 3.5)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    inv = ax.transAxes.inverted()

    # Bloque 1: Quiénes son
    y1_top = 0.722
    t1_title = ax.text(0.535, y1_top - 0.012, "QUIÉNES SON:", fontsize=10.5, fontweight="bold", color=theme["primary"], va="top", transform=ax.transAxes, zorder=3)
    fig.canvas.draw()
    y1_title_bot = t1_title.get_window_extent(r).transformed(inv).y0

    wrapped_qs = textwrap.fill(texts["quienes_son"], width=58)
    t1_body = ax.text(0.535, y1_title_bot - 0.005, wrapped_qs, fontsize=10.0, color="#1F2937", va="top", transform=ax.transAxes, zorder=3)
    fig.canvas.draw()
    y1_body_bot = t1_body.get_window_extent(r).transformed(inv).y0

    h1 = (y1_top - y1_body_bot) + 0.010
    b1_box = FancyBboxPatch(
        (0.520, y1_top - h1), 0.445, h1,
        boxstyle="round,pad=0.008,rounding_size=0.01",
        facecolor="white", edgecolor="#CBD5E1", linewidth=1.2, transform=ax.transAxes, zorder=2
    )
    ax.add_patch(b1_box)

    # Bloque 2: Hipótesis (al menos 4 pt debajo, usamos 0.012 = 7.3 pt)
    y2_top = (y1_top - h1) - 0.012
    t2_title = ax.text(0.535, y2_top - 0.012, "HIPÓTESIS:", fontsize=10.5, fontweight="bold", color="#B91C1C", va="top", transform=ax.transAxes, zorder=3)
    fig.canvas.draw()
    y2_title_bot = t2_title.get_window_extent(r).transformed(inv).y0

    wrapped_hip = textwrap.fill(texts["hipotesis"], width=58)
    t2_body = ax.text(0.535, y2_title_bot - 0.005, wrapped_hip, fontsize=10.0, color="#1F2937", va="top", transform=ax.transAxes, zorder=3)
    fig.canvas.draw()
    y2_body_bot = t2_body.get_window_extent(r).transformed(inv).y0

    h2 = (y2_top - y2_body_bot) + 0.010
    b2_box = FancyBboxPatch(
        (0.520, y2_top - h2), 0.445, h2,
        boxstyle="round,pad=0.008,rounding_size=0.01",
        facecolor="white", edgecolor="#CBD5E1", linewidth=1.2, transform=ax.transAxes, zorder=2
    )
    ax.add_patch(b2_box)

    # Bloque 3: Qué proponemos (al menos 4 pt debajo)
    y3_top = (y2_top - h2) - 0.012
    t3_title = ax.text(0.535, y3_top - 0.012, "QUÉ PROPONEMOS (ENCÍVICA / INE):", fontsize=10.5, fontweight="bold", color="#047857", va="top", transform=ax.transAxes, zorder=3)
    fig.canvas.draw()
    y3_title_bot = t3_title.get_window_extent(r).transformed(inv).y0

    wrapped_prop = textwrap.fill(texts["propuesta"], width=58)
    t3_body = ax.text(0.535, y3_title_bot - 0.005, wrapped_prop, fontsize=10.0, color="#1F2937", va="top", transform=ax.transAxes, zorder=3)
    fig.canvas.draw()
    y3_body_bot = t3_body.get_window_extent(r).transformed(inv).y0

    h3 = (y3_top - y3_body_bot) + 0.010
    b3_box = FancyBboxPatch(
        (0.520, y3_top - h3), 0.445, h3,
        boxstyle="round,pad=0.008,rounding_size=0.01",
        facecolor="white", edgecolor="#CBD5E1", linewidth=1.2, transform=ax.transAxes, zorder=2
    )
    ax.add_patch(b3_box)

    # Bloque Inferior: Metas Cuantitativas e Indicadores de Impacto (y=0.114..0.355, Bloque 3.5)
    meta_box = FancyBboxPatch(
        (0.035, 0.114), 0.930, 0.241,
        boxstyle="round,pad=0.01,rounding_size=0.015",
        facecolor="white", edgecolor=theme["border"], linewidth=1.5, transform=ax.transAxes, zorder=2
    )
    ax.add_patch(meta_box)

    ax.text(0.055, 0.334, "METAS CUANTITATIVAS E INDICADORES DE IMPACTO:", fontsize=10.8, fontweight="bold", color=theme["primary"], transform=ax.transAxes, zorder=3)

    y_curr = 0.312

    # 1. Meta
    wrapped_meta = textwrap.fill(texts["meta"], width=96)
    n_lines_meta = wrapped_meta.count("\n") + 1
    ax.text(0.055, y_curr, "Meta:", fontsize=10.0, fontweight="bold", color="#111827", va="top", transform=ax.transAxes, zorder=3)
    ax.text(0.200, y_curr, wrapped_meta, fontsize=10.0, color="#1F2937", va="top", transform=ax.transAxes, zorder=3)
    y_curr -= (0.014 + n_lines_meta * 0.0135)

    # 2. Impacto / En regresión (D7)
    ax.text(0.055, y_curr, texts["impacto_lbl"], fontsize=10.0, fontweight="bold", color="#111827", va="top", transform=ax.transAxes, zorder=3)
    ax.text(0.200, y_curr, texts["impacto_txt"], fontsize=10.0, fontweight="bold", color=theme["primary"], va="top", transform=ax.transAxes, zorder=3)
    y_curr -= 0.023

    # 3. Entidades principales (E2: top 3 de tabla_07)
    ax.text(0.055, y_curr, "Entidades principales:", fontsize=10.0, fontweight="bold", color="#111827", va="top", transform=ax.transAxes, zorder=3)
    ax.text(0.200, y_curr, texts["top3_entidades"], fontsize=10.0, color="#1F2937", va="top", transform=ax.transAxes, zorder=3)
    y_curr -= 0.023

    # 4. Dónde empezar (Juntas distritales)
    ax.text(0.055, y_curr, "Dónde empezar:", fontsize=10.0, fontweight="bold", color="#111827", va="top", transform=ax.transAxes, zorder=3)
    ax.text(0.200, y_curr, f"Juntas prioritarias: {texts['top3_juntas']}", fontsize=10.0, color="#1F2937", va="top", transform=ax.transAxes, zorder=3)
    y_curr -= 0.023

    # 5. Indicador
    wrapped_ind = textwrap.fill(texts["indicador"], width=96)
    n_lines_ind = wrapped_ind.count("\n") + 1
    ax.text(0.055, y_curr, "Indicador:", fontsize=10.0, fontweight="bold", color="#111827", va="top", transform=ax.transAxes, zorder=3)
    ax.text(0.200, y_curr, wrapped_ind, fontsize=10.0, color="#1F2937", va="top", transform=ax.transAxes, zorder=3)
    y_curr -= (0.014 + n_lines_ind * 0.0135)

    # 6. Operación
    wrapped_op = textwrap.fill(texts["unidad_costo"], width=96)
    ax.text(0.055, y_curr, "Operación:", fontsize=10.0, fontweight="bold", color="#111827", va="top", transform=ax.transAxes, zorder=3)
    ax.text(0.200, y_curr, wrapped_op, fontsize=10.0, color="#374151", va="top", transform=ax.transAxes, zorder=3)

    # Lema al Pie (y=0.042..0.100) (borde superior = 0.100, al menos 12 pt debajo de meta_box)
    lema_box = FancyBboxPatch(
        (0.035, 0.042), 0.930, 0.058,
        boxstyle="round,pad=0.008,rounding_size=0.012",
        facecolor=theme["primary"], edgecolor=theme["primary"], transform=ax.transAxes, zorder=2
    )
    ax.add_patch(lema_box)
    ax.text(
        0.50, 0.071, f"Lema propuesto: \"{texts['lema']}\"",
        fontsize=11.2, fontweight="bold", style="italic", color="white", ha="center", va="center", transform=ax.transAxes, zorder=3
    )

    return fig


def main() -> None:
    print("[Fase 7.3] Construyendo textos dinámicos desde JSON y tablas...")
    cifras = cargar_cifras()
    data = cifras["data"]
    texts_dict = cifras["texts_dict"]

    pdf_multi_path = OUT_ENTREGABLES / "Fichas_Perfiles_ByteMe.pdf"
    png_portada_path = OUT_ENTREGABLES / "Fichas_Portada.png"
    png_cards = [OUT_ENTREGABLES / f"Ficha_C{cid}.png" for cid in range(4)]
    png_combined_path = OUT_ENTREGABLES / "Fichas_Perfiles_ByteMe.png"

    print("[Fase 7.3] Generando Fichas en 5 páginas horizontales (Carta)...")

    # Guardar PDF de 5 páginas y los PNGs individuales a 300 DPI
    with PdfPages(pdf_multi_path) as pdf:
        # Página 1: Portada
        fig_cover = render_cover_page(data, texts_dict, cifras)
        fig_cover.savefig(png_portada_path, dpi=300)
        pdf.savefig(fig_cover)
        plt.close(fig_cover)
        print(f"  - Guardada Página 1 (Portada): {png_portada_path.name}")

        # Páginas 2 a 5: Fichas C0 a C3
        for cid in range(4):
            fig_card = render_profile_page(cid, data, texts_dict)
            fig_card.savefig(png_cards[cid], dpi=300)
            pdf.savefig(fig_card)
            plt.close(fig_card)
            print(f"  - Guardada Página {cid+2} (Ficha C{cid}): {png_cards[cid].name}")

    print(f"  - PDF multipágina (5 páginas): {pdf_multi_path}")

    # Generar también una imagen combinada de alta resolución para Fichas_Perfiles_ByteMe.png (mosaico 2x2 de perfiles)
    fig_mosaic = plt.figure(figsize=(22.0, 17.0), facecolor="white")
    gs = fig_mosaic.add_gridspec(2, 2, hspace=0.04, wspace=0.03, left=0.02, right=0.98, top=0.98, bottom=0.02)
    positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for cid, (r_idx, c_idx) in enumerate(positions):
        sub_fig = render_profile_page(cid, data, texts_dict)
        sub_png = OUT_ENTREGABLES / f"temp_c{cid}.png"
        sub_fig.savefig(sub_png, dpi=150)
        plt.close(sub_fig)

        ax_m = fig_mosaic.add_subplot(gs[r_idx, c_idx])
        ax_m.axis("off")
        im_data = plt.imread(str(sub_png))
        ax_m.imshow(im_data)
        sub_png.unlink()

    fig_mosaic.savefig(png_combined_path, dpi=300)
    plt.close(fig_mosaic)
    print(f"  - Imagen combinada 300 DPI: {png_combined_path.name}")
    print("[Fase 7.3] Fichas generadas con éxito.")


if __name__ == "__main__":
    main()
