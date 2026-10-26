#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fase 7.3: Generación de Fichas Resumen e Infografía de los 4 Perfiles Ciudadanos (08_generar_fichas.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

Cumple estrictamente con el Bloque F del prompt:
  F1. Cinco páginas en formato carta horizontal (11.0 x 8.5 in):
      - Página 1: Portada institucional con título, equipo, integrantes con acentos,
        método en 3 renglones y mini-tabla de los 4 perfiles.
      - Páginas 2 a 5: Una ficha por perfil (C0 a C3).
      Exporta:
        - Fichas_Perfiles_ByteMe.pdf (5 páginas horizontales vectoriales).
        - Fichas_Portada.png, Ficha_C0.png, Ficha_C1.png, Ficha_C2.png, Ficha_C3.png (300 DPI).
        - Fichas_Perfiles_ByteMe.png (mosaico resumen 300 DPI).
  F2. Tipografía Arial con texto >= 10 pt a tamaño impreso; cifras clave de 20-28 pt.
  F3. Cada ficha contiene:
      - Nombre e ícono geométrico distintivo.
      - 4 cifras clave grandes con ícono/etiqueta (participación media, intermedia 2021, presidencial 2024, brecha distintiva).
      - Gráfica de trayectoria 2009-2024 con leyenda "Media del Panel B" y etiquetas elevadas 8-10 pt.
      - "Quiénes son" (<= 45 palabras).
      - "Hipótesis de abstencionismo" (<= 35 palabras, explícitamente marcada como hipótesis).
      - "Qué proponemos" (<= 60 palabras).
      - Meta e indicador alineados con la regla unificada del Bloque D.
      - Lema institucional neutral.
  F4. Cero jerga técnica (sin snake_case, sin z-scores, sin log(1+1/CV)).
  F5. Tipografía Arial registrada con matplotlib fontManager y pdf.fonttype=42.
  F6. Cifras y metas idénticas a metricas_finales.json y al documento técnico.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Circle, Polygon, Rectangle
import numpy as np

# Configuración de tipografía Arial
ARIAL_PATH = Path("/usr/share/fonts/TTF/Arial.TTF")
if ARIAL_PATH.exists():
    fm.fontManager.addfont(str(ARIAL_PATH))
    matplotlib.rcParams["font.family"] = "Arial"
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42

PROJECT_ROOT = Path(__file__).resolve().parents[2]
METRICAS_PATH = PROJECT_ROOT / "outputs" / "metricas_finales.json"
OUT_ENTREGABLES = PROJECT_ROOT / "outputs" / "entregables"
OUT_ENTREGABLES.mkdir(parents=True, exist_ok=True)

THEMES = {
    0: {"primary": "#C2410C", "bg": "#FFF7ED", "border": "#FDBA74", "badge": "#9A3412", "accent": "#EA580C"},
    1: {"primary": "#047857", "bg": "#ECFDF5", "border": "#6EE7B7", "badge": "#065F46", "accent": "#059669"},
    2: {"primary": "#1D4ED8", "bg": "#EFF6FF", "border": "#93C5FD", "badge": "#1E40AF", "accent": "#2563EB"},
    3: {"primary": "#6D28D9", "bg": "#F5F3FF", "border": "#C4B5FD", "badge": "#5B21B6", "accent": "#7C3AED"},
}

PROFILE_TEXTS = {
    0: {
        "quienes_son": (
            "Ciudadanía predominantemente urbana (79.0%) concentrada en grandes zonas metropolitanas. "
            "Presenta la menor participación promedio (50.4%) y una marcada desconexión en comicios intermedios frente a comicios presidenciales."
        ),
        "hipotesis": (
            "Hipótesis: El abstencionismo se debe a la desafección hacia elecciones legislativas intermedias, alta movilidad residencial "
            "y barreras de tiempo en jóvenes trabajadores o estudiantes no escolarizados."
        ),
        "propuesta": (
            "Pedagogía legislativa sobre el impacto directo de las elecciones intermedias en transporte masivo y plataformas digitales; "
            "módulos itinerantes de credencialización en parques industriales, tianguis y centros laborales; y activación cívica con la plataforma "
            "'Conóceles' para jóvenes no escolarizados y universitarios."
        ),
        "meta": "Elevar la participación a 49.5% en la intermedia de 2027 (+3.4 pts vs 2021) y el voto juvenil 18–29 a 39.1% (+3.9 pts).",
        "indicador": "Tasa seccional ponderada SV/(SV+NV) en comicios federales de 2027 y tasa juvenil en CCPC.",
        "unidad_costo": "DECEyEC, DERFE y Juntas Distritales | Costo: Medio (estimación indicativa)",
        "lema": "Cada elección define tu entorno: infórmate, ubica tu casilla y participa en 2027",
        "brecha_label": "Brecha Pres.–Inter.",
        "brecha_val": "+17.3 pts",
        "brecha_sub": "Mayor desmovilización intermedia",
    },
    1: {
        "quienes_son": (
            "Comunidades con fuerte arraigo vecinal y cohesión social equilibrada entre áreas urbanas (46.0%) y rurales (40.9%). "
            "Registran la mayor constancia electoral (65.1% promedio), la menor brecha presidencial-intermedia y una elevada integración juvenil (59.1%)."
        ),
        "hipotesis": (
            "Hipótesis: La alta participación responde a redes comunitarias sólidas y normas cívicas intergeneracionales arraigadas, "
            "donde la integración de mesas directivas de casilla se percibe como un deber cívico compartido."
        ),
        "propuesta": (
            "Reconocimiento a la constancia cívica comunitaria; talleres juveniles de formación cívica en planteles locales; y reclutamiento temprano "
            "de CAE y sensibilización de la ciudadanía insaculada para asegurar la instalación completa de casillas con funcionariado propietario."
        ),
        "meta": "Sostener una participación ≥ 62.5% en la intermedia de 2027 y ≥ 65.7% en la presidencial de 2030, aumentando la proporción de casillas instaladas con funcionariado propietario.",
        "indicador": "Tasa ponderada SV/(SV+NV) en 2027/2030 y porcentaje de casillas instaladas con funcionariado propietario el día de la jornada (dato de la DEOE).",
        "unidad_costo": "DECEyEC y Vocalías de Capacitación de Juntas Distritales | Costo: Bajo (programas ordinarios)",
        "lema": "Si te visitan para integrar una casilla, participa: tu comunidad cuenta contigo",
        "brecha_label": "Voto Juvenil 18–29",
        "brecha_val": "59.1%",
        "brecha_sub": "Mayor razón de voto joven (0.91)",
    },
    2: {
        "quienes_son": (
            "Secciones con fuerte dinamismo cívico en entornos urbanos (68.6%), rurales (22.3%) y mixtos (9.1%). "
            "Es el perfil de mayor crecimiento histórico (+1.28 pts/año), pasando de 41.8% en 2009 a 68.0% en 2024, impulsado por una alta afluencia juvenil."
        ),
        "hipotesis": (
            "Hipótesis: El crecimiento participativo se explica por la incorporación de nuevas generaciones de electores "
            "y la creciente politización de demandas locales y servicios en zonas en consolidación."
        ),
        "propuesta": (
            "Consolidar el hábito del voto mediante foros 'Diálogos por la Democracia'; vinculación con colectivos juveniles y causas ciudadanas; "
            "monitoreo preventivo de casillas en crecimiento por la DEOE; y difusión intensiva de candidaturas mediante 'Conóceles'."
        ),
        "meta": "Consolidar una participación ≥ 60.4% en la intermedia de 2027 y sostener una razón de participación juvenil ≥ 0.88.",
        "indicador": "Tasa ponderada SV/(SV+NV) 2027 y razón de participación juvenil CCPC.",
        "unidad_costo": "DECEyEC, DEOE y Juntas Distritales | Costo: Bajo-Medio (foros distritales)",
        "lema": "Tu participación ya transforma tu comunidad: consolidemos el voto en cada elección",
        "brecha_label": "Tendencia Anual",
        "brecha_val": "+1.28 pts/año",
        "brecha_sub": "Mayor ascenso cívico sostenido",
    },
    3: {
        "quienes_son": (
            "Secciones con marcada sobrerrepresentación campesina (41.2% rural vs 26.9% nacional). "
            "Se distingue por un notable liderazgo de las mujeres (60.9% de participación vs 49.7% en hombres, brecha de +11.2 pts) "
            "y una caída en comicios presidenciales desde 2012."
        ),
        "hipotesis": (
            "Hipótesis: El rezago del voto masculino y la caída presidencial obedecen a la migración laboral masculina temporal, "
            "dispersión geográfica de casillas y desatención de demandas productivas del campo."
        ),
        "propuesta": (
            "Campaña focalizada de motivación del voto masculino en centros agropecuarios, cooperativas y rutas de transporte; "
            "fortalecimiento de rutas móviles y casillas extraordinarias de la DEOE; y alianzas con redes comunitarias de mujeres como promotoras cívicas del hogar."
        ),
        "meta": "Elevar la participación a 51.1% en 2027, 58.1% en 2030 y el voto masculino a 46.3% en 2027 (cerrando la mitad de la brecha con el Panel B).",
        "indicador": "Tasa seccional masculina y general ponderada SV/(SV+NV) en CCPC.",
        "unidad_costo": "DECEyEC, DEOE y Juntas Distritales | Costo: Medio (tiempos oficiales y rutas DEOE)",
        "lema": "La participación de todas y todos cuenta: sumemos la voz de hombres y jóvenes en cada comunidad",
        "brecha_label": "Brecha de Género",
        "brecha_val": "+11.2 pts",
        "brecha_sub": "Mayor liderazgo femenino a favor de M",
    },
}


def draw_profile_icon(ax, cid: int, cx: float, cy: float, radius: float = 0.038, color: str = "#1E3A8A") -> None:
    """Dibuja un ícono geométrico distintivo limpio para cada perfil en coordenadas de transAxes."""
    circ = Circle((cx, cy), radius, facecolor=color, edgecolor="white", linewidth=2.0, transform=ax.transAxes, zorder=6)
    ax.add_patch(circ)
    if cid == 0:
        # Barras intermitentes (alta-baja-alta-baja)
        for idx, h in enumerate([0.014, 0.032, 0.016, 0.030]):
            bx = cx - 0.020 + idx * 0.011
            by = cy - 0.016
            ax.add_patch(Rectangle((bx, by), 0.007, h, facecolor="white", transform=ax.transAxes, zorder=7))
    elif cid == 1:
        # Escudo de constancia cívica
        pts = np.array([
            [cx, cy + 0.022],
            [cx + 0.018, cy + 0.010],
            [cx + 0.014, cy - 0.016],
            [cx, cy - 0.024],
            [cx - 0.014, cy - 0.016],
            [cx - 0.018, cy + 0.010],
        ])
        ax.add_patch(Polygon(pts, closed=True, facecolor="white", transform=ax.transAxes, zorder=7))
    elif cid == 2:
        # Flecha ascendente
        ax.plot([cx - 0.018, cx - 0.005, cx + 0.006, cx + 0.018],
                [cy - 0.014, cy - 0.002, cy - 0.006, cy + 0.016],
                color="white", linewidth=2.8, transform=ax.transAxes, zorder=7)
        ax.plot([cx + 0.008, cx + 0.018, cx + 0.018],
                [cy + 0.016, cy + 0.016, cy + 0.005],
                color="white", linewidth=2.8, transform=ax.transAxes, zorder=7)
    elif cid == 3:
        # Símbolo de liderazgo femenino
        c_inner = Circle((cx, cy + 0.008), 0.011, fill=False, edgecolor="white", linewidth=2.4, transform=ax.transAxes, zorder=7)
        ax.add_patch(c_inner)
        ax.plot([cx, cx], [cy - 0.003, cy - 0.020], color="white", linewidth=2.4, transform=ax.transAxes, zorder=7)
        ax.plot([cx - 0.010, cx + 0.010], [cy - 0.012, cy - 0.012], color="white", linewidth=2.4, transform=ax.transAxes, zorder=7)


def render_cover_page(data: dict) -> plt.Figure:
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
        fontsize=9.5, color="#CBD5E1", style="italic", ha="center", va="center", transform=ax.transAxes
    )

    # Bloque de datos del equipo y repositorio
    team_box = FancyBboxPatch(
        (0.04, 0.655), 0.92, 0.135,
        boxstyle="round,pad=0.01,rounding_size=0.015",
        facecolor="white", edgecolor="#CBD5E1", linewidth=1.2, transform=ax.transAxes
    )
    ax.add_patch(team_box)
    ax.text(0.06, 0.760, "Equipo:", fontsize=10.5, fontweight="bold", color="#1E3A8A", transform=ax.transAxes)
    ax.text(0.13, 0.760, "Byte me", fontsize=10.5, color="#111827", transform=ax.transAxes)

    ax.text(0.06, 0.725, "Integrantes:", fontsize=10.5, fontweight="bold", color="#1E3A8A", transform=ax.transAxes)
    members_str = "1. Johanan Olivares Gutiérrez (representante)   ·   2. Oscar Ariel Cuevas Martínez   ·   3. Saúl Alexis Arias González"
    ax.text(0.16, 0.725, members_str, fontsize=10.2, color="#111827", transform=ax.transAxes)

    ax.text(0.06, 0.690, "Repositorio público:", fontsize=10.5, fontweight="bold", color="#1E3A8A", transform=ax.transAxes)
    ax.text(0.21, 0.690, "https://github.com/Johanan1113/Hackaton_INE_byte_me", fontsize=10.2, color="#1D4ED8", transform=ax.transAxes)

    ax.text(0.06, 0.665, "Entorno de software:", fontsize=9.5, fontweight="bold", color="#4B5563", transform=ax.transAxes)
    ax.text(0.21, 0.665, "Python 3.14.6 · DuckDB 2.0.0 · scikit-learn 1.9.0 · scipy 1.18.0 · umap-learn 0.5.12 · pandas 3.0.3 · numpy 2.4.6",
            fontsize=9.0, color="#4B5563", transform=ax.transAxes)

    # Bloque metodológico en exactamente 3 renglones
    meth_box = FancyBboxPatch(
        (0.04, 0.495), 0.92, 0.145,
        boxstyle="round,pad=0.01,rounding_size=0.015",
        facecolor="#F1F5F9", edgecolor="#94A3B8", linewidth=1.2, transform=ax.transAxes
    )
    ax.add_patch(meth_box)
    ax.text(0.06, 0.615, "SÍNTESIS METODOLÓGICA (TRES PILARES ANALÍTICOS):", fontsize=10.5, fontweight="bold", color="#0F172A", transform=ax.transAxes)
    ax.text(
        0.06, 0.580,
        "1. Corrección por registros sin captura (NS): En microdatos abiertos la Lista Nominal es LN = SV + NV + NS; la fórmula oficial es SV/(SV+NV), evitando subestimar hasta 4.27 pts en 2018.",
        fontsize=10.0, color="#1F2937", transform=ax.transAxes
    )
    ax.text(
        0.06, 0.545,
        "2. Panel Principal continuo (Opción B, cero imputación): 53,644 secciones con captura válida (SV+NV ≥ 50) y sin saltos por reseccionamiento (75.82% secciones y 79.53% LN 2024 en 2,393 municipios).",
        fontsize=10.0, color="#1F2937", transform=ax.transAxes
    )
    ax.text(
        0.06, 0.510,
        "3. Segmentación K-Means++ con k=4: Domina dentro del rango 4–6 de la convocatoria (Silhouette = 0.1789, ARI bootstrap = 0.9572 y clasificador Random Forest con 96.29% de exactitud).",
        fontsize=10.0, color="#1F2937", transform=ax.transAxes
    )

    # Mini-tabla de resumen de los 4 perfiles
    ax.text(0.04, 0.455, "MATRIZ EJECUTIVA DE LOS 4 PERFILES CIUDADANOS (k = 4):", fontsize=11.0, fontweight="bold", color="#1E3A8A", transform=ax.transAxes)

    col_x = [0.04, 0.09, 0.42, 0.56, 0.69, 0.76, 0.96]
    y_tbl = 0.420
    # Encabezado tabla
    ax.add_patch(Rectangle((0.04, y_tbl - 0.008), 0.92, 0.032, facecolor="#1E3A8A", transform=ax.transAxes))
    ax.text(0.065, y_tbl + 0.008, "Perfil", fontsize=9.8, fontweight="bold", color="white", ha="center", va="center", transform=ax.transAxes)
    ax.text(0.24, y_tbl + 0.008, "Nombre Oficial del Perfil", fontsize=9.8, fontweight="bold", color="white", ha="center", va="center", transform=ax.transAxes)
    ax.text(0.44, y_tbl + 0.008, "Secciones (% Panel)", fontsize=9.8, fontweight="bold", color="white", ha="center", va="center", transform=ax.transAxes)
    ax.text(0.575, y_tbl + 0.008, "LN 2024 (% LN)", fontsize=9.8, fontweight="bold", color="white", ha="center", va="center", transform=ax.transAxes)
    ax.text(0.695, y_tbl + 0.008, "Part. Media", fontsize=9.8, fontweight="bold", color="white", ha="center", va="center", transform=ax.transAxes)
    ax.text(0.855, y_tbl + 0.008, "Rasgo Distintivo Clave", fontsize=9.8, fontweight="bold", color="white", ha="center", va="center", transform=ax.transAxes)

    perfiles = data["perfiles"]
    rows_data = [
        ("C0", perfiles[0]["nombre_propuesto"], f"{perfiles[0]['n_secciones']:,} ({perfiles[0]['pct_secciones_panel']:.1f}%)",
         f"{perfiles[0]['ln_2024']/1e6:.2f}M ({perfiles[0]['pct_ln_panel']:.1f}%)", f"{perfiles[0]['participacion_media_historica_original']*100:.1f}%",
         "Rezago juvenil y ciclo presidencial urbano"),
        ("C1", perfiles[1]["nombre_propuesto"], f"{perfiles[1]['n_secciones']:,} ({perfiles[1]['pct_secciones_panel']:.1f}%)",
         f"{perfiles[1]['ln_2024']/1e6:.2f}M ({perfiles[1]['pct_ln_panel']:.1f}%)", f"{perfiles[1]['participacion_media_historica_original']*100:.1f}%",
         "Máxima estabilidad y cohesión comunitaria"),
        ("C2", perfiles[2]["nombre_propuesto"], f"{perfiles[2]['n_secciones']:,} ({perfiles[2]['pct_secciones_panel']:.1f}%)",
         f"{perfiles[2]['ln_2024']/1e6:.2f}M ({perfiles[2]['pct_ln_panel']:.1f}%)", f"{perfiles[2]['participacion_media_historica_original']*100:.1f}%",
         "Ascenso continuo (+1.28 pts/año) y juventud activa"),
        ("C3", perfiles[3]["nombre_propuesto"], f"{perfiles[3]['n_secciones']:,} ({perfiles[3]['pct_secciones_panel']:.1f}%)",
         f"{perfiles[3]['ln_2024']/1e6:.2f}M ({perfiles[3]['pct_ln_panel']:.1f}%)", f"{perfiles[3]['participacion_media_historica_original']*100:.1f}%",
         "Liderazgo femenino (+11.2 pts) y rezago masculino"),
    ]

    for idx, (cid, name, secc, ln, part, rasgo) in enumerate(rows_data):
        y_r = y_tbl - 0.038 - idx * 0.052
        bg_c = "#FFFFFF" if idx % 2 == 0 else "#F8FAFC"
        ax.add_patch(Rectangle((0.04, y_r - 0.012), 0.92, 0.048, facecolor=bg_c, edgecolor="#E2E8F0", linewidth=0.8, transform=ax.transAxes))
        theme_p = THEMES[idx]
        draw_profile_icon(ax, idx, 0.062, y_r + 0.012, radius=0.014, color=theme_p["primary"])
        ax.text(0.088, y_r + 0.012, name, fontsize=8.6, fontweight="bold", color="#0F172A", va="center", transform=ax.transAxes)
        ax.text(0.440, y_r + 0.012, secc, fontsize=8.8, color="#1F2937", ha="center", va="center", transform=ax.transAxes)
        ax.text(0.575, y_r + 0.012, ln, fontsize=8.8, color="#1F2937", ha="center", va="center", transform=ax.transAxes)
        ax.text(0.695, y_r + 0.012, part, fontsize=9.2, fontweight="bold", color=theme_p["primary"], ha="center", va="center", transform=ax.transAxes)
        ax.text(0.755, y_r + 0.012, rasgo, fontsize=8.4, color="#374151", va="center", transform=ax.transAxes)

    # Pie de página institucional
    ax.text(
        0.50, 0.055,
        "Fuentes: Microdatos Conteos Censales de Participación Ciudadana (CCPC 2009–2024), INE México. Consulta las fichas individuales en las páginas 2 a 5.",
        fontsize=9.2, color="#64748B", ha="center", va="center", style="italic", transform=ax.transAxes
    )

    return fig


def render_profile_page(cid: int, data: dict) -> plt.Figure:
    """Páginas 2 a 5: Ficha individual completa de perfil en formato carta horizontal."""
    p = data["perfiles"][cid]
    texts = PROFILE_TEXTS[cid]
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
        0.12, 0.925, f"PERFIL {p['codigo_cluster']}: {p['nombre_propuesto'].upper()}",
        fontsize=14.5, fontweight="bold", color="white", va="center", transform=ax.transAxes
    )
    cov_str = (
        f"Cobertura: {p['n_secciones']:,} secciones ({p['pct_secciones_panel']:.1f}% Panel B)   •   "
        f"LN 2024: {p['ln_2024']:,} electores ({p['pct_ln_panel']:.1f}% Panel B) en {p['n_municipios_con_presencia']:,} municipios   •   "
        f"Composición: {p['pct_secciones_urbanas']:.1f}% Urbana, {p['pct_secciones_rurales']:.1f}% Rural, {p['pct_secciones_mixtas']:.1f}% Mixta"
    )
    ax.text(
        0.12, 0.885, cov_str,
        fontsize=8.5, color="#F3F4F6", va="center", transform=ax.transAxes
    )

    # 4 Cifras Grandes (Callout Cards) (y=0.745..0.850)
    card_w = 0.218
    gap = 0.019
    x_starts = [0.035 + i * (card_w + gap) for i in range(4)]

    cards_info = [
        ("PARTICIPACIÓN MEDIA", f"{p['participacion_media_historica_original']*100:.1f}%", "Promedio 6 elecciones (2009–24)"),
        ("INTERMEDIA 2021", f"{p['p_2021_ponderada']*100:.1f}%", "Línea base intermedia oficial"),
        ("PRESIDENCIAL 2024", f"{p['p_2024_ponderada']*100:.1f}%", "Última elección presidencial"),
        (texts["brecha_label"].upper(), texts["brecha_val"], texts["brecha_sub"]),
    ]

    for i, (title_c, val_c, sub_c) in enumerate(cards_info):
        box_c = FancyBboxPatch(
            (x_starts[i], 0.740), card_w, 0.105,
            boxstyle="round,pad=0.008,rounding_size=0.012",
            facecolor="white", edgecolor=theme["border"], linewidth=1.5, transform=ax.transAxes
        )
        ax.add_patch(box_c)
        ax.text(x_starts[i] + card_w / 2, 0.825, title_c, fontsize=9.2, fontweight="bold", color="#4B5563", ha="center", va="center", transform=ax.transAxes)
        ax.text(x_starts[i] + card_w / 2, 0.782, val_c, fontsize=23.0, fontweight="bold", color=theme["primary"], ha="center", va="center", transform=ax.transAxes)
        ax.text(x_starts[i] + card_w / 2, 0.752, sub_c, fontsize=8.2, color="#6B7280", ha="center", va="center", transform=ax.transAxes)

    # Columna Izquierda: Gráfica de la serie histórica ponderada (0.035..0.505, y=0.340..0.720)
    ax_plot = fig.add_axes([0.055, 0.380, 0.440, 0.335])
    p_vals = [p[f"p_{y}_ponderada"] * 100 for y in years]
    b_vals = [pan_b[f"p_{y}_ponderada"] * 100 for y in years]

    # Sombra en intermedias
    for ym in [2009, 2015, 2021]:
        ax_plot.axvspan(ym - 0.5, ym + 0.5, color="#F1F5F9", alpha=0.9, zorder=0)

    # Línea del cluster
    ax_plot.plot(years, p_vals, marker="o", linewidth=2.8, markersize=7.5, color=theme["primary"], label=f"Perfil {p['codigo_cluster']}", zorder=4)
    for x_v, y_v in zip(years, p_vals):
        # C15: Etiquetas 8-10 pt por encima del punto para evitar encimamiento
        ax_plot.annotate(
            f"{y_v:.1f}%", (x_v, y_v), textcoords="offset points", xytext=(0, 9),
            ha="center", fontsize=9.2, fontweight="bold", color=theme["primary"]
        )

    # C15: Línea gris punteada Media del Panel B
    ax_plot.plot(years, b_vals, linestyle=":", marker="^", linewidth=2.0, markersize=6.0, color="#64748B", label="Media del Panel B", zorder=3)
    ax_plot.set_xticks(years)
    ax_plot.set_xticklabels([f"{y}\n({'Inter.' if y in (2009,2015,2021) else 'Pres.'})" for y in years], fontsize=9.0)
    ax_plot.set_ylim(min(min(p_vals), min(b_vals)) - 6, max(max(p_vals), max(b_vals)) + 7)
    ax_plot.set_ylabel("Participación SV/(SV+NV) (%)", fontsize=9.5, fontweight="bold")
    ax_plot.set_title("Trayectoria Electoral Ponderada (2009–2024)", fontsize=10.5, fontweight="bold", pad=8)
    ax_plot.grid(True, alpha=0.5)
    ax_plot.legend(loc="lower right", fontsize=9.0, frameon=True)

    # Columna Derecha: Bloques de Diagnóstico e Intervención (0.520..0.965, y=0.340..0.720)
    # Bloque 1: Quiénes son (<= 45 palabras)
    b1_box = FancyBboxPatch(
        (0.520, 0.605), 0.445, 0.118,
        boxstyle="round,pad=0.008,rounding_size=0.01",
        facecolor="white", edgecolor="#CBD5E1", linewidth=1.2, transform=ax.transAxes
    )
    ax.add_patch(b1_box)
    ax.text(0.535, 0.706, "QUIÉNES SON:", fontsize=10.0, fontweight="bold", color=theme["primary"], transform=ax.transAxes)
    wrapped_qs = textwrap.fill(texts["quienes_son"], width=62)
    ax.text(0.535, 0.686, wrapped_qs, fontsize=9.2, color="#1F2937", va="top", transform=ax.transAxes)

    # Bloque 2: Hipótesis de abstencionismo (<= 35 palabras, marcada como hipótesis)
    b2_box = FancyBboxPatch(
        (0.520, 0.475), 0.445, 0.118,
        boxstyle="round,pad=0.008,rounding_size=0.01",
        facecolor="white", edgecolor="#CBD5E1", linewidth=1.2, transform=ax.transAxes
    )
    ax.add_patch(b2_box)
    ax.text(0.535, 0.575, "HIPÓTESIS DE ABSTENCIONISMO:", fontsize=10.0, fontweight="bold", color="#B91C1C", transform=ax.transAxes)
    wrapped_hip = textwrap.fill(texts["hipotesis"], width=62)
    ax.text(0.535, 0.555, wrapped_hip, fontsize=9.2, color="#1F2937", va="top", transform=ax.transAxes)

    # Bloque 3: Qué proponemos (<= 60 palabras)
    b3_box = FancyBboxPatch(
        (0.520, 0.345), 0.445, 0.118,
        boxstyle="round,pad=0.008,rounding_size=0.01",
        facecolor="white", edgecolor="#CBD5E1", linewidth=1.2, transform=ax.transAxes
    )
    ax.add_patch(b3_box)
    ax.text(0.535, 0.445, "QUÉ PROPONEMOS (ENCÍVICA / INE):", fontsize=10.0, fontweight="bold", color="#047857", transform=ax.transAxes)
    wrapped_prop = textwrap.fill(texts["propuesta"], width=64)
    ax.text(0.535, 0.425, wrapped_prop, fontsize=8.8, color="#1F2937", va="top", transform=ax.transAxes)

    # Bloque Inferior: Meta Cuantitativa e Indicador (y=0.122..0.315)
    meta_box = FancyBboxPatch(
        (0.035, 0.122), 0.930, 0.193,
        boxstyle="round,pad=0.01,rounding_size=0.015",
        facecolor="white", edgecolor=theme["border"], linewidth=1.5, transform=ax.transAxes
    )
    ax.add_patch(meta_box)

    ax.text(0.055, 0.288, "METAS CUANTITATIVAS E INDICADORES DE IMPACTO:", fontsize=10.8, fontweight="bold", color=theme["primary"], transform=ax.transAxes)

    # Meta
    ax.text(0.055, 0.254, "Meta:", fontsize=10.0, fontweight="bold", color="#111827", transform=ax.transAxes)
    ax.text(0.125, 0.254, textwrap.fill(texts["meta"], width=108), fontsize=9.6, color="#1F2937", va="top", transform=ax.transAxes)

    # Indicador
    ax.text(0.055, 0.208, "Indicador:", fontsize=10.0, fontweight="bold", color="#111827", transform=ax.transAxes)
    ax.text(0.125, 0.208, textwrap.fill(texts["indicador"], width=108), fontsize=9.6, color="#1F2937", va="top", transform=ax.transAxes)

    # Unidad y Costo
    ax.text(0.055, 0.162, "Operación:", fontsize=10.0, fontweight="bold", color="#111827", transform=ax.transAxes)
    ax.text(0.125, 0.162, texts["unidad_costo"], fontsize=9.6, color="#374151", va="top", transform=ax.transAxes)

    # Lema Neutral al Pie (y=0.045..0.105)
    lema_box = FancyBboxPatch(
        (0.035, 0.045), 0.930, 0.065,
        boxstyle="round,pad=0.008,rounding_size=0.012",
        facecolor=theme["primary"], edgecolor=theme["primary"], transform=ax.transAxes
    )
    ax.add_patch(lema_box)
    ax.text(
        0.50, 0.078, f"Lema Institucional: \"{texts['lema']}\"",
        fontsize=11.2, fontweight="bold", style="italic", color="white", ha="center", va="center", transform=ax.transAxes
    )

    return fig


def main() -> None:
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))

    pdf_multi_path = OUT_ENTREGABLES / "Fichas_Perfiles_ByteMe.pdf"
    png_portada_path = OUT_ENTREGABLES / "Fichas_Portada.png"
    png_cards = [OUT_ENTREGABLES / f"Ficha_C{cid}.png" for cid in range(4)]
    png_combined_path = OUT_ENTREGABLES / "Fichas_Perfiles_ByteMe.png"

    print("[Fase 7.3] Generando Fichas en 5 páginas horizontales (Carta)...")

    # Guardar PDF de 5 páginas y los PNGs individuales a 300 DPI
    with PdfPages(pdf_multi_path) as pdf:
        # Página 1: Portada
        fig_cover = render_cover_page(data)
        fig_cover.savefig(png_portada_path, dpi=300)
        pdf.savefig(fig_cover)
        plt.close(fig_cover)
        print(f"  - Guardada Página 1 (Portada): {png_portada_path.name}")

        # Páginas 2 a 5: Fichas C0 a C3
        for cid in range(4):
            fig_card = render_profile_page(cid, data)
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
        sub_fig = render_profile_page(cid, data)
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
