#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fase 7.3: Generación de Fichas Resumen / Infografía de los 4 Perfiles Ciudadanos (08_generar_fichas.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

Lee exclusivamente de outputs/metricas_finales.json (cero cifras escritas a mano)
y genera en outputs/entregables/:
  - Fichas_Perfiles_ByteMe.png (300 DPI)
  - Fichas_Perfiles_ByteMe.pdf (vectorial de alta resolución)
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Polygon, Rectangle
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
METRICAS_PATH = PROJECT_ROOT / "outputs" / "metricas_finales.json"
OUT_ENTREGABLES = PROJECT_ROOT / "outputs" / "entregables"
OUT_ENTREGABLES.mkdir(parents=True, exist_ok=True)

CARD_THEMES = {
    0: {"primary": "#C2410C", "bg": "#FFF7ED", "border": "#FDBA74", "badge": "#9A3412"},
    1: {"primary": "#047857", "bg": "#ECFDF5", "border": "#6EE7B7", "badge": "#065F46"},
    2: {"primary": "#1D4ED8", "bg": "#EFF6FF", "border": "#93C5FD", "badge": "#1E40AF"},
    3: {"primary": "#6D28D9", "bg": "#F5F3FF", "border": "#C4B5FD", "badge": "#5B21B6"},
}


def draw_icon(ax, cid: int, x0: float, y0: float, color: str) -> None:
    """Dibuja un ícono geométrico vectorial distintivo para cada perfil en coordenadas de ejes (0..1)."""
    circ = Circle((x0, y0), 0.032, facecolor=color, edgecolor="white", linewidth=1.5, transform=ax.transAxes, zorder=6)
    ax.add_patch(circ)
    if cid == 0:
        # Barras intermitentes (alta-baja-alta-baja)
        for idx, h in enumerate([0.012, 0.028, 0.014, 0.026]):
            bx = x0 - 0.016 + idx * 0.009
            by = y0 - 0.014
            ax.add_patch(Rectangle((bx, by), 0.006, h, facecolor="white", transform=ax.transAxes, zorder=7))
    elif cid == 1:
        # Escudo / estrella de estabilidad alta
        pts = np.array([
            [x0, y0 + 0.018],
            [x0 + 0.015, y0 + 0.008],
            [x0 + 0.012, y0 - 0.014],
            [x0, y0 - 0.020],
            [x0 - 0.012, y0 - 0.014],
            [x0 - 0.015, y0 + 0.008],
        ])
        ax.add_patch(Polygon(pts, closed=True, facecolor="white", transform=ax.transAxes, zorder=7))
    elif cid == 2:
        # Flecha ascendente
        ax.plot(
            [x0 - 0.015, x0 - 0.004, x0 + 0.005, x0 + 0.015],
            [y0 - 0.012, y0 - 0.002, y0 - 0.006, y0 + 0.013],
            color="white", linewidth=2.4, transform=ax.transAxes, zorder=7
        )
        ax.plot(
            [x0 + 0.007, x0 + 0.015, x0 + 0.015],
            [y0 + 0.013, y0 + 0.013, y0 + 0.004],
            color="white", linewidth=2.4, transform=ax.transAxes, zorder=7
        )
    elif cid == 3:
        # Símbolo de liderazgo femenino y balanza comunitaria
        c_inner = Circle((x0, y0 + 0.006), 0.009, fill=False, edgecolor="white", linewidth=2.0, transform=ax.transAxes, zorder=7)
        ax.add_patch(c_inner)
        ax.plot([x0, x0], [y0 - 0.003, y0 - 0.017], color="white", linewidth=2.0, transform=ax.transAxes, zorder=7)
        ax.plot([x0 - 0.008, x0 + 0.008], [y0 - 0.011, y0 - 0.011], color="white", linewidth=2.0, transform=ax.transAxes, zorder=7)


def render_profile_card(ax, p: dict, e: dict, pan_b: dict) -> None:
    """Renderiza una ficha individual de perfil leyendo todos los datos de metricas_finales.json."""
    cid = p["cluster_id"]
    theme = CARD_THEMES[cid]
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Fondo de tarjeta y encabezado
    bg_box = FancyBboxPatch(
        (0.01, 0.01), 0.98, 0.98,
        boxstyle="round,pad=0.012,rounding_size=0.02",
        facecolor=theme["bg"], edgecolor=theme["border"], linewidth=1.8,
        transform=ax.transAxes, zorder=1
    )
    ax.add_patch(bg_box)

    hdr_box = FancyBboxPatch(
        (0.01, 0.875), 0.98, 0.115,
        boxstyle="round,pad=0.008,rounding_size=0.02",
        facecolor=theme["primary"], edgecolor=theme["primary"], linewidth=1.0,
        transform=ax.transAxes, zorder=2
    )
    ax.add_patch(hdr_box)

    draw_icon(ax, cid, 0.062, 0.932, theme["badge"])

    ax.text(
        0.11, 0.948, f"PERFIL {p['codigo_cluster']} — {p['nombre_propuesto']}",
        fontsize=11.0, fontweight="bold", color="white", va="center", ha="left", transform=ax.transAxes, zorder=5
    )
    cov_line = (
        f"Secciones: {p['n_secciones']:,} ({p['pct_secciones_panel']:.2f}% Panel B | {p['pct_secciones_2024_total']:.2f}% Nac. 2024)  •  "
        f"LN 2024: {p['ln_2024']:,} ({p['pct_ln_panel']:.2f}% Panel B | {p['pct_ln_2024_total']:.2f}% Nac. 2024)  •  "
        f"Municipios: {p['n_municipios_con_presencia']:,}"
    )
    ax.text(
        0.11, 0.900, cov_line,
        fontsize=7.1, color="#F3F4F6", fontweight="bold", va="center", ha="left", transform=ax.transAxes, zorder=5
    )

    # Bloque superior izquierdo (0.03..0.60): Indicadores Electorales, Demográficos y Territoriales
    ax.text(0.03, 0.850, "1. HUELLA ELECTORAL Y DEMOGRÁFICA (2009–2024)", fontsize=8.6, fontweight="bold", color=theme["primary"], transform=ax.transAxes)

    part_m = p["participacion_media_historica_original"] * 100
    part_z = p["participacion_media_historica_zscore"]
    b_pi = p["brecha_presidencial_intermedia_original"] * 100
    b_pi_z = p["brecha_presidencial_intermedia_zscore"]
    beta = p["tendencia_participacion_beta_original"] * 100
    beta_z = p["tendencia_participacion_beta_zscore"]
    est_v = p["estabilidad_participacion_original"]
    est_z = p["estabilidad_participacion_zscore"]

    j_pct = p["tasa_joven_18_29_original"] * 100
    m60_pct = p["tasa_mayor_60_mas_original"] * 100
    b_gen = p["brecha_generacional_original"] * 100
    b_gen_z = p["brecha_generacional_zscore"]
    r_jov = p["ratio_participacion_joven_original"]
    r_jov_z = p["ratio_participacion_joven_zscore"]

    muj_pct = p["tasa_mujeres_original"] * 100
    hom_pct = p["tasa_hombres_original"] * 100
    b_sex = p["brecha_genero_original"] * 100
    b_sex_z = p["brecha_genero_zscore"]

    m_pres = p["media_presidencial_original"] * 100
    m_inter = p["media_intermedia_original"] * 100

    metrics_lines = [
        ("Participación Media Hexanual:", f"{part_m:.2f}% (z = {part_z:+.2f}) | Pres: {m_pres:.2f}% vs Inter: {m_inter:.2f}%"),
        ("Brecha Presidencial–Intermedia:", f"{b_pi:+.2f} pts (z = {b_pi_z:+.2f})"),
        ("Tendencia Anual OLS (2009–2024):", f"{beta:+.2f} pts/año (z = {beta_z:+.2f})"),
        ("Estabilidad log(1 + 1/CV):", f"{est_v:.4f} (z = {est_z:+.2f})"),
        ("Jóvenes (18–29) vs Mayores (60+):", f"{j_pct:.2f}% vs {m60_pct:.2f}% | Brecha: {b_gen:+.2f} pts (z = {b_gen_z:+.2f})"),
        ("Ratio Participación Joven:", f"{r_jov:.4f} (z = {r_jov_z:+.2f})"),
        ("Mujeres vs Hombres:", f"{muj_pct:.2f}% vs {hom_pct:.2f}% | Brecha M-H: {b_sex:+.2f} pts (z = {b_sex_z:+.2f})"),
        ("Tipo de Sección (Secc. / LN):", (
            f"{p['pct_secciones_urbanas']:.1f}% U, {p['pct_secciones_rurales']:.1f}% R, {p['pct_secciones_mixtas']:.1f}% M | "
            f"LN: {p['pct_ln_urbana']:.1f}/{p['pct_ln_rural']:.1f}/{p['pct_ln_mixta']:.1f}%"
        )),
    ]

    y_curr = 0.820
    for k_lbl, v_lbl in metrics_lines:
        ax.text(0.03, y_curr, k_lbl, fontsize=7.2, fontweight="bold", color="#1F2937", transform=ax.transAxes)
        ax.text(0.265, y_curr, v_lbl, fontsize=7.2, color="#111827", transform=ax.transAxes)
        y_curr -= 0.0295

    top2_ent = "; ".join(p["top5_entidades_por_pct_secciones"].split("; ")[:2])
    ax.text(0.03, y_curr, "Principales Entidades:", fontsize=7.2, fontweight="bold", color="#1F2937", transform=ax.transAxes)
    ax.text(0.265, y_curr, top2_ent, fontsize=7.1, color="#111827", transform=ax.transAxes)

    # Mini gráfico de serie temporal ponderada 2009-2024 en la esquina superior derecha
    ax_in = ax.inset_axes([0.66, 0.635, 0.305, 0.195])
    years = [2009, 2012, 2015, 2018, 2021, 2024]
    y_pond = [p[f"p_{y}_ponderada"] * 100 for y in years]
    pan_pond = [pan_b[f"p_{y}_ponderada"] * 100 for y in years]

    ax_in.plot(years, pan_pond, linestyle="--", color="#9CA3AF", linewidth=1.2, label="Panel B")
    ax_in.plot(years, y_pond, marker="o", color=theme["primary"], linewidth=2.0, markersize=4.5, label=p["codigo_cluster"])
    for xv, yv in zip(years, y_pond):
        ax_in.annotate(f"{yv:.1f}%", (xv, yv), textcoords="offset points", xytext=(0, 4), ha="center", fontsize=6.3, fontweight="bold", color=theme["primary"])
    ax_in.set_xticks(years)
    ax_in.set_xticklabels([str(y) for y in years], fontsize=6.4)
    ax_in.set_ylim(30, 76)
    ax_in.set_title("Serie Ponderada SV/(SV+NV) (%)", fontsize=7.1, fontweight="bold", color="#1F2937", pad=3)
    ax_in.grid(True, alpha=0.5)

    # Línea divisoria horizontal
    ax.plot([0.03, 0.97], [0.545, 0.545], color=theme["border"], linewidth=1.2, transform=ax.transAxes)

    # Bloque inferior: Diagnóstico, Estrategia Focalizada, Meta 2027 y Viabilidad
    ax.text(
        0.03, 0.520,
        f"2. ESTRATEGIA DE PROMOCIÓN E INTERVENCIÓN INSTITUCIONAL (Línea Base Intermedia 2021: {e['linea_base_intermedia_2021_pond_pct']:.1f}% | Presidencial 2024: {e['linea_base_presidencial_2024_pond_pct']:.1f}%)",
        fontsize=8.1, fontweight="bold", color=theme["primary"], transform=ax.transAxes
    )

    strat_blocks = [
        ("Diagnóstico e Hipótesis:", e["hipotesis_factor_abstencionismo"]),
        ("Canal y Focalización:", e["canal_principal"]),
        ("Acción Operativa INE:", e["accion_operativa_ine"]),
        ("Meta Cuantitativa 2027/2030:", e["meta_cuantitativa"]),
        ("Unidad Responsable y Costo:", f"{e['unidad_responsable']}  |  Costo: {e['costo_estimado_orden_magnitud']}"),
    ]

    y_s = 0.492
    for b_title, b_text in strat_blocks:
        wrapped = textwrap.fill(b_text, width=104)
        n_lines = wrapped.count("\n") + 1
        ax.text(0.03, y_s, b_title, fontsize=7.0, fontweight="bold", color="#1F2937", va="top", transform=ax.transAxes)
        ax.text(0.220, y_s, wrapped, fontsize=6.75, color="#111827", va="top", transform=ax.transAxes)
        y_s -= (0.0170 * n_lines + 0.0058)

    # Lema neutral al pie de la tarjeta
    lema_box = FancyBboxPatch(
        (0.03, 0.018), 0.94, 0.038,
        boxstyle="round,pad=0.004,rounding_size=0.01",
        facecolor="white", edgecolor=theme["border"], linewidth=1.0,
        transform=ax.transAxes, zorder=3
    )
    ax.add_patch(lema_box)
    ax.text(
        0.50, 0.037, f"Lema Institucional Neutral: \"{e['lema_sugerido_neutral']}\"",
        fontsize=7.5, fontweight="bold", style="italic", color=theme["badge"],
        ha="center", va="center", transform=ax.transAxes, zorder=4
    )


def main() -> None:
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    perfiles = {p["cluster_id"]: p for p in data["perfiles"]}
    estrategias = {e["cluster_id"]: e for e in data["estrategias"]}
    pan_b = data["resumen_panel_b"]
    u = data["universo_y_cobertura"]
    bench_k4 = [r for r in data["benchmark_modelos"] if r["algoritmo"] == "K-Means++" and r["k"] == 4][0]

    fig = plt.figure(figsize=(20, 17.5), facecolor="white")
    gs = fig.add_gridspec(
        3, 2, height_ratios=[0.115, 1.0, 1.0],
        hspace=0.05, wspace=0.035, left=0.02, right=0.98, top=0.975, bottom=0.015
    )

    # Encabezado general
    ax_hdr = fig.add_subplot(gs[0, :])
    ax_hdr.axis("off")
    hdr_bg = FancyBboxPatch(
        (0.005, 0.04), 0.99, 0.92,
        boxstyle="round,pad=0.01,rounding_size=0.015",
        facecolor="#111827", edgecolor="#1F2937", transform=ax_hdr.transAxes
    )
    ax_hdr.add_patch(hdr_bg)
    ax_hdr.text(
        0.50, 0.72,
        "FICHAS TÉCNICAS E INFOGRÁFICAS DE LOS 4 PERFILES CIUDADANOS DE PARTICIPACIÓN ELECTORAL (2009–2024)",
        fontsize=15.0, fontweight="bold", color="white", ha="center", va="center", transform=ax_hdr.transAxes
    )
    sub_hdr_1 = (
        f"Equipo Byte me — Propuesta Técnica Reto 1 (Concurso INE: Hackea la participación)   •   "
        f"Fórmula Oficial CCPC: SV / (SV + NV)   •   "
        f"Panel Principal Opción B (Cero Imputación): {u['panel_principal_secciones']:,} secciones ({u['panel_principal_pct_secciones_2024']:.2f}% de 2024)"
    )
    sub_hdr_2 = (
        f"Lista Nominal 2024 cubierta: {u['panel_principal_ln_2024']:,} electores ({u['panel_principal_pct_ln_2024']:.2f}% de 2024) en {u['panel_principal_municipios']:,} municipios   •   "
        f"Modelo K-Means++ (k=4): Silhouette = {bench_k4['silhouette']:.4f}  |  Davies-Bouldin = {bench_k4['davies_bouldin']:.4f}  |  Calinski-Harabasz = {bench_k4['calinski_harabasz']:,.2f}  |  ARI Bootstrap = {bench_k4['bootstrap_ari_media']:.4f}"
    )
    ax_hdr.text(
        0.50, 0.42, sub_hdr_1,
        fontsize=9.2, color="#E5E7EB", fontweight="bold", ha="center", va="center", transform=ax_hdr.transAxes
    )
    ax_hdr.text(
        0.50, 0.18, sub_hdr_2,
        fontsize=8.8, color="#D1D5DB", fontweight="bold", ha="center", va="center", transform=ax_hdr.transAxes
    )

    # 4 tarjetas en cuadrícula 2x2
    positions = [(1, 0), (1, 1), (2, 0), (2, 1)]
    for cid, (row_i, col_i) in enumerate(positions):
        ax_card = fig.add_subplot(gs[row_i, col_i])
        render_profile_card(ax_card, perfiles[cid], estrategias[cid], pan_b)

    png_path = OUT_ENTREGABLES / "Fichas_Perfiles_ByteMe.png"
    pdf_path = OUT_ENTREGABLES / "Fichas_Perfiles_ByteMe.pdf"
    fig.savefig(png_path, dpi=300)
    fig.savefig(pdf_path, dpi=300)
    plt.close(fig)
    print(f"[Fase 7.3] Fichas generadas en:\n  - {png_path}\n  - {pdf_path}")


if __name__ == "__main__":
    main()
