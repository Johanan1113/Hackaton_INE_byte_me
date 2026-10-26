#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fase 6: Generación Reproducible de las 7 Figuras a 300 DPI para k=4 (06_generar_figuras.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

Lee exclusivamente de outputs/metricas_finales.json y outputs/fase2/etiquetas_finales.parquet
para garantizar consistencia numérica y de nombres en las 7 figuras en outputs/figuras/:
  1. fig1_mapa_clusters.png
  2. fig2_evolucion_temporal.png
  3. fig3_radar_centroides.png
  4. fig4_brechas_demograficas.png
  5. fig5_urbano_rural_entidades.png
  6. fig6_benchmark_k.png
  7. fig7_proyeccion_pca_umap.png
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
METRICAS_PATH = PROJECT_ROOT / "outputs" / "metricas_finales.json"
PARQUET_PATH = PROJECT_ROOT / "outputs" / "fase2" / "etiquetas_finales.parquet"
OUT_FIGURAS = PROJECT_ROOT / "outputs" / "figuras"
OUT_FIGURAS.mkdir(parents=True, exist_ok=True)

# Paleta institucional sobria y daltónico-segura para los 4 perfiles (k=4)
CLUSTER_COLORS = {
    0: "#D95F02",  # C0: Naranja terracota (Baja Participación Intermitente con Rezago Juvenil)
    1: "#1B9E77",  # C1: Verde esmeralda (Alta Participación Estable e Intergeneracional)
    2: "#2B5C8F",  # C2: Azul profundo (Participación en Ascenso con Juventud Activa)
    3: "#7570B3",  # C3: Púrpura índigo (Liderazgo Femenino con Participación Estancada)
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Liberation Sans"],
    "axes.edgecolor": "#374151",
    "axes.linewidth": 0.8,
    "grid.color": "#E5E7EB",
    "grid.linestyle": "--",
    "grid.linewidth": 0.6,
})


def load_inputs() -> tuple[dict, pd.DataFrame]:
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    df_b = pd.read_parquet(PARQUET_PATH)
    return data, df_b


def generate_fig1_mapa_clusters(data: dict, df_b: pd.DataFrame) -> None:
    """Figura 1: Composición porcentual de los 4 perfiles por entidad federativa y LN 2024."""
    perfiles = {p["cluster_id"]: p for p in data["perfiles"]}

    ct = pd.crosstab(df_b["entidad"], df_b["cluster"], normalize="index") * 100
    for c in range(4):
        if c not in ct.columns:
            ct[c] = 0.0
    ct = ct[[0, 1, 2, 3]]
    # Ordenar por proporción conjunta de C1 (Alta Estable) + C2 (En Ascenso)
    ct["alta_ascenso"] = ct[1] + ct[2]
    ct = ct.sort_values("alta_ascenso", ascending=True)
    states = ct.index.tolist()

    ln_by_state = df_b.groupby("entidad")["ln_2024"].sum().reindex(states) / 1e6

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(14, 9.5), gridspec_kw={"width_ratios": [3.3, 1.1]}, sharey=True
    )

    y_pos = np.arange(len(states))
    left = np.zeros(len(states))
    for c in [1, 2, 3, 0]:
        vals = ct[c].values
        lbl = f"{perfiles[c]['codigo_cluster']}: {perfiles[c]['nombre_propuesto']} ({perfiles[c]['pct_secciones_panel']:.1f}%)"
        ax1.barh(
            y_pos, vals, left=left, height=0.74, color=CLUSTER_COLORS[c],
            edgecolor="white", linewidth=0.4, label=lbl
        )
        for i, v in enumerate(vals):
            if v >= 13.0:
                ax1.text(
                    left[i] + v / 2, y_pos[i], f"{v:.0f}%",
                    va="center", ha="center", color="white", fontsize=7.5, fontweight="bold"
                )
        left += vals

    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(states, fontsize=8.5, fontweight="bold", color="#1F2937")
    ax1.set_xlim(0, 100)
    ax1.set_xlabel("Porcentaje de secciones del Panel Principal en la entidad (%)", fontsize=9.5, fontweight="bold")
    ax1.set_title("A. Distribución de los 4 Perfiles por Entidad Federativa", fontsize=11, fontweight="bold", pad=10)
    ax1.grid(axis="x", alpha=0.5)
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=2, frameon=True, fontsize=8.5)

    bars2 = ax2.barh(y_pos, ln_by_state.values, height=0.70, color="#4B5563", alpha=0.85)
    for bar, v in zip(bars2, ln_by_state.values):
        ax2.text(v + 0.08, bar.get_y() + bar.get_height() / 2, f"{v:.2f}M", va="center", ha="left", fontsize=7.5, color="#1F2937")
    ax2.set_xlim(0, max(ln_by_state.values) * 1.25)
    ax2.set_xlabel("Lista Nominal 2024 en Panel B (Millones)", fontsize=9.5, fontweight="bold")
    ax2.set_title("B. Lista Nominal Cubierta", fontsize=11, fontweight="bold", pad=10)
    ax2.grid(axis="x", alpha=0.5)

    u = data["universo_y_cobertura"]
    fig.suptitle(
        f" Especialización Territorial de los Perfiles de Participación (k=4 | N = {u['panel_principal_secciones']:,} secciones; "
        f"{u['panel_principal_pct_ln_2024']:.2f}% de LN 2024)",
        fontsize=12.5, fontweight="bold", y=0.98, color="#111827"
    )
    fig.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig(OUT_FIGURAS / "fig1_mapa_clusters.png", dpi=300)
    plt.close(fig)


def generate_fig2_evolucion_temporal(data: dict) -> None:
    """Figura 2: Evolución temporal 2009-2024 por perfil (k=4) y validación de fórmula SV/(SV+NV) vs SV/LN."""
    perfiles = data["perfiles"]
    serie_nac = data["serie_nacional_2009_2024"]
    years = [r["anio"] for r in serie_nac]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8), gridspec_kw={"width_ratios": [1.35, 1.0]})

    # Sombrear elecciones intermedias
    for y_mid in [2009, 2015, 2021]:
        ax1.axvspan(y_mid - 0.6, y_mid + 0.6, color="#F3F4F6", alpha=0.8, zorder=0)

    for p in perfiles:
        c = p["cluster_id"]
        y_vals = [p[f"p_{y}_ponderada"] * 100 for y in years]
        lbl = f"{p['codigo_cluster']}: {p['nombre_propuesto']} (n={p['n_secciones']:,})"
        ax1.plot(
            years, y_vals, marker="o", linewidth=2.4, markersize=6.5,
            color=CLUSTER_COLORS[c], label=lbl, zorder=4
        )
        for x_val, y_val in zip(years, y_vals):
            if c == 1:
                dx, dy = 0, 7
            elif c == 2:
                dx, dy = (0, -10) if x_val in (2012, 2018) else (0, 6)
            elif c == 3:
                dx, dy = (0, 6) if x_val in (2009, 2015) else (0, -10)
            else:
                dx, dy = 0, -11
            ax1.annotate(
                f"{y_val:.1f}%", (x_val, y_val), textcoords="offset points",
                xytext=(dx, dy), ha="center", fontsize=7.3, fontweight="bold", color=CLUSTER_COLORS[c]
            )

    nac_ccpc = [r["total_ponderada_sv_svnv_pct"] for r in serie_nac]
    pan_b_pond = [r["panel_b_ponderada_sv_svnv_pct"] for r in serie_nac]
    ax1.plot(years, nac_ccpc, linestyle="--", marker="s", linewidth=1.8, markersize=5, color="#111827",
             label="Total Nacional CCPC Ponderado SV/(SV+NV)", zorder=5)
    ax1.plot(years, pan_b_pond, linestyle=":", marker="^", linewidth=1.6, markersize=5, color="#6B7280",
             label="Media Panel B (53,644 sec.) Ponderada", zorder=3)

    ax1.set_xticks(years)
    ax1.set_xticklabels([f"{y}\n({'Inter.' if y in (2009,2015,2021) else 'Pres.'})" for y in years], fontsize=8.5)
    ax1.set_ylim(29, 76)
    ax1.set_ylabel("Participación Electoral Ponderada SV / (SV + NV) (%)", fontsize=9.5, fontweight="bold")
    ax1.set_title("A. Trayectoria Hexanual de los 4 Perfiles (2009–2024)", fontsize=10.8, fontweight="bold")
    ax1.grid(True, alpha=0.6)
    ax1.legend(loc="lower right", fontsize=7.4, frameon=True)

    # Panel B: Comparación SV/(SV+NV) vs SV/LN errónea y % NS
    err_ln = [r["total_ponderada_erronea_sv_ln_pct"] for r in serie_nac]
    ns_pct = [r["pct_ns_anio"] for r in serie_nac]

    ax2_twin = ax2.twinx()
    bars = ax2_twin.bar(years, ns_pct, width=1.1, color="#FCA5A5", alpha=0.45, label="NS como % de Lista Nominal")
    for b, v in zip(bars, ns_pct):
        ax2_twin.text(b.get_x() + b.get_width() / 2, v + 0.25, f"NS: {v:.2f}%", ha="center", va="bottom", fontsize=7.2, color="#991B1B")

    ax2.plot(years, nac_ccpc, marker="o", linewidth=2.3, color="#047857", label="Fórmula Oficial CCPC: SV / (SV + NV)")
    ax2.plot(years, err_ln, marker="X", linestyle="--", linewidth=2.0, color="#DC2626", label="Criterio Erróneo Original: SV / LN")

    for x_val, y_ok, y_er in zip(years, nac_ccpc, err_ln):
        if abs(y_ok - y_er) >= 1.5:
            ax2.annotate(
                f"-{y_ok - y_er:.2f} pts", xy=(x_val, y_er), xytext=(x_val, y_er + 4.8),
                ha="center", fontsize=7.3, fontweight="bold", color="#DC2626",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="#FCA5A5", alpha=0.92),
                arrowprops=dict(arrowstyle="->", color="#DC2626", lw=0.8)
            )

    ax2.set_xticks(years)
    ax2.set_xticklabels([str(y) for y in years], fontsize=8.5)
    ax2.set_ylim(30, 73)
    ax2_twin.set_ylim(0, 26)
    ax2.set_ylabel("Participación Nacional Ponderada (%)", fontsize=9.5, fontweight="bold")
    ax2_twin.set_ylabel("Cuadernillos No Capturados NS (% de LN)", fontsize=9.0, color="#991B1B", fontweight="bold")
    ax2.set_title("B. Efecto de Registros NS sobre SV/LN vs SV/(SV+NV)", fontsize=10.8, fontweight="bold")
    ax2.grid(True, alpha=0.6)

    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=7.6, frameon=True)

    fig.suptitle(
        "Dinámica Electoral 2009–2024: Perfiles Seccionales (k=4) y Corrección del Sesgo por Cuadernillos No Disponibles (NS)",
        fontsize=12, fontweight="bold", y=0.98
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(OUT_FIGURAS / "fig2_evolucion_temporal.png", dpi=300)
    plt.close(fig)


def generate_fig3_radar_centroides(data: dict) -> None:
    """Figura 3: Heatmap de centroides (z-score + valor original) y perfil paralelo de las 7 variables."""
    perfiles = data["perfiles"]
    feat_info = [
        ("participacion_media_historica", "Participación Media\nHistórica (%)", lambda v: f"{v*100:.1f}%"),
        ("brecha_presidencial_intermedia", "Brecha Presidencial-\nIntermedia (pts)", lambda v: f"{v*100:+.1f} pts"),
        ("tendencia_participacion_beta", "Tendencia Anual\nOLS (pts/año)", lambda v: f"{v*100:+.2f} pts/a"),
        ("estabilidad_participacion", "Índice de Estabilidad\nlog(1 + 1/CV)", lambda v: f"{v:.2f}"),
        ("brecha_generacional", "Brecha Generacional\n60+ vs 18-29 (pts)", lambda v: f"{v*100:+.1f} pts"),
        ("brecha_genero", "Brecha de Género\nM vs H (pts)", lambda v: f"{v*100:+.1f} pts"),
        ("ratio_participacion_joven", "Ratio Participación\nJoven (18-29 / Total)", lambda v: f"{v:.3f}"),
    ]

    z_mat = np.zeros((4, len(feat_info)))
    annot_mat = [["" for _ in range(len(feat_info))] for _ in range(4)]

    for i, p in enumerate(perfiles):
        for j, (fcol, _, fmt_fn) in enumerate(feat_info):
            z = p[f"{fcol}_zscore"]
            orig = p[f"{fcol}_original"]
            z_mat[i, j] = z
            star = "*" if abs(z) >= 0.5 else ""
            annot_mat[i][j] = f"z = {z:+.2f}{star}\n({fmt_fn(orig)})"

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13.8, 9.0), gridspec_kw={"height_ratios": [1.15, 1.0]})

    im = ax1.imshow(z_mat, cmap="RdBu_r", vmin=-1.5, vmax=1.5, aspect="auto")
    for i in range(4):
        for j in range(len(feat_info)):
            z = z_mat[i, j]
            txt_color = "white" if abs(z) > 0.85 else "#111827"
            weight = "bold" if abs(z) >= 0.5 else "normal"
            ax1.text(j, i, annot_mat[i][j], ha="center", va="center", color=txt_color, fontsize=8.3, fontweight=weight)

    ax1.set_xticks(np.arange(len(feat_info)))
    ax1.set_xticklabels([lbl for _, lbl, _ in feat_info], fontsize=8.1, fontweight="bold")
    ax1.set_yticks(np.arange(4))
    ax1.set_yticklabels(
        [f"{p['codigo_cluster']}: {p['nombre_propuesto']}\n(n={p['n_secciones']:,} | {p['pct_secciones_panel']:.1f}%)" for p in perfiles],
        fontsize=8.5, fontweight="bold"
    )
    ax1.set_title(
        "A. Matriz de Centroides por Perfil: Puntaje Estandarizado (z-score) y Valor en Escala Original (* indica variable rectora |z| >= 0.50)",
        fontsize=10.5, fontweight="bold", pad=10
    )
    cbar = fig.colorbar(im, ax=ax1, orientation="vertical", fraction=0.02, pad=0.02)
    cbar.set_label("z-score vs Panel B", fontsize=8.5)

    # Panel B: Coordenadas paralelas de z-scores
    x = np.arange(len(feat_info))
    ax2.axhline(0, color="#111827", linewidth=1.1, linestyle="-", alpha=0.7)
    ax2.axhspan(-0.5, 0.5, color="#E5E7EB", alpha=0.45, label="Banda neutral (|z| < 0.50)")
    for p in perfiles:
        c = p["cluster_id"]
        zs = [p[f"{fcol}_zscore"] for fcol, _, _ in feat_info]
        ax2.plot(
            x, zs, marker="o", linewidth=2.4, markersize=7,
            color=CLUSTER_COLORS[c], label=f"{p['codigo_cluster']}: {p['nombre_propuesto']}"
        )

    ax2.set_xticks(x)
    ax2.set_xticklabels([lbl for _, lbl, _ in feat_info], fontsize=8.0, fontweight="bold")
    ax2.set_ylim(-1.45, 1.65)
    ax2.set_ylabel("Desviaciones Estándar (z-score)", fontsize=9.5, fontweight="bold")
    ax2.set_title("B. Firma Multivariada de los 4 Perfiles en las 7 Dimensiones del Modelo", fontsize=10.5, fontweight="bold")
    ax2.grid(True, alpha=0.6)
    ax2.legend(loc="upper left", ncol=3, fontsize=7.0, frameon=True)

    fig.suptitle("Caracterización de Centroides y Variables Rectoras del Modelo K-Means++ (k=4)", fontsize=12.5, fontweight="bold", y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(OUT_FIGURAS / "fig3_radar_centroides.png", dpi=300)
    plt.close(fig)


def generate_fig4_brechas_demograficas(data: dict) -> None:
    """Figura 4: Tasas de participación 18-29 vs 60+ y Mujeres vs Hombres por perfil y Media Panel B."""
    perfiles = data["perfiles"]
    pan_b = data["resumen_panel_b"]

    groups = [f"{p['codigo_cluster']}\n({p['pct_secciones_panel']:.1f}%)" for p in perfiles] + ["Media\nPanel B"]
    joven = [p["tasa_joven_18_29_original"] * 100 for p in perfiles] + [pan_b["tasa_joven_18_29_original"] * 100]
    mayor = [p["tasa_mayor_60_mas_original"] * 100 for p in perfiles] + [pan_b["tasa_mayor_60_mas_original"] * 100]
    mujer = [p["tasa_mujeres_original"] * 100 for p in perfiles] + [pan_b["tasa_mujeres_original"] * 100]
    hombre = [p["tasa_hombres_original"] * 100 for p in perfiles] + [pan_b["tasa_hombres_original"] * 100]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.8, 6.0), sharey=True)
    x = np.arange(len(groups))
    w = 0.35

    ax1.bar(x - w / 2, joven, width=w, color="#3B82F6", label="Jóvenes (18–29 años)")
    ax1.bar(x + w / 2, mayor, width=w, color="#1E3A8A", label="Adultos Mayores (60+ años)")
    for i in range(len(groups)):
        ax1.text(x[i] - w / 2, joven[i] + 0.7, f"{joven[i]:.1f}%", ha="center", va="bottom", fontsize=7.8, fontweight="bold", color="#1D4ED8")
        ax1.text(x[i] + w / 2, mayor[i] + 0.7, f"{mayor[i]:.1f}%", ha="center", va="bottom", fontsize=7.8, fontweight="bold", color="#1E3A8A")
        gap = mayor[i] - joven[i]
        ax1.annotate(
            f"Brecha:\n+{gap:.1f} pts", xy=(x[i], max(joven[i], mayor[i]) + 7.2),
            ha="center", va="center", fontsize=7.6, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.22", facecolor="#EFF6FF", edgecolor="#93C5FD")
        )

    ax1.set_xticks(x)
    ax1.set_xticklabels(groups, fontsize=9, fontweight="bold")
    ax1.set_ylim(0, 88)
    ax1.set_ylabel("Tasa de Participación Hexanual SV / (SV + NV) (%)", fontsize=9.5, fontweight="bold")
    ax1.set_title("A. Brecha Generacional: Jóvenes (18–29) vs Adultos Mayores (60+)", fontsize=10.5, fontweight="bold")
    ax1.grid(axis="y", alpha=0.6)
    ax1.legend(loc="upper right", fontsize=8.5, frameon=True)

    ax2.bar(x - w / 2, mujer, width=w, color="#8B5CF6", label="Mujeres")
    ax2.bar(x + w / 2, hombre, width=w, color="#10B981", label="Hombres")
    for i in range(len(groups)):
        ax2.text(x[i] - w / 2, mujer[i] + 0.7, f"{mujer[i]:.1f}%", ha="center", va="bottom", fontsize=7.8, fontweight="bold", color="#6D28D9")
        ax2.text(x[i] + w / 2, hombre[i] + 0.7, f"{hombre[i]:.1f}%", ha="center", va="bottom", fontsize=7.8, fontweight="bold", color="#047857")
        gap_g = mujer[i] - hombre[i]
        ax2.annotate(
            f"M - H:\n+{gap_g:.1f} pts", xy=(x[i], max(mujer[i], hombre[i]) + 7.2),
            ha="center", va="center", fontsize=7.6, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.22", facecolor="#F5F3FF", edgecolor="#C4B5FD")
        )

    ax2.set_xticks(x)
    ax2.set_xticklabels(groups, fontsize=9, fontweight="bold")
    ax2.set_title("B. Brecha de Género: Mujeres vs Hombres (Destaca C3: +11.15 pts)", fontsize=10.5, fontweight="bold")
    ax2.grid(axis="y", alpha=0.6)
    ax2.legend(loc="upper right", fontsize=8.5, frameon=True)

    fig.suptitle(
        "Estructura Demográfica de la Participación por Perfil (Promedio Hexanual 2009–2024 con SV / [SV + NV])",
        fontsize=12, fontweight="bold", y=0.98
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(OUT_FIGURAS / "fig4_brechas_demograficas.png", dpi=300)
    plt.close(fig)


def generate_fig5_urbano_rural_entidades(data: dict) -> None:
    """Figura 5: Tipología Urbana/Rural/Mixta por perfil (k=4), Media Panel B, e Incluidas vs Excluidas en 2024."""
    import textwrap
    perfiles = data["perfiles"]
    pan_b = data["resumen_panel_b"]
    inc_exc = data["incluidas_vs_excluidas_2024"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.4, 6.2), gridspec_kw={"width_ratios": [1.22, 1.15]})

    labels_1 = [
        textwrap.fill(f"{p['codigo_cluster']}: {p['nombre_propuesto']}", width=28)
        for p in perfiles
    ] + [
        "Media Nacional Panel B\n(por secciones: 53,644)"
    ]
    u_vals = [p["pct_secciones_urbanas"] for p in perfiles] + [pan_b["pct_secciones_urbanas_1d"]]
    r_vals = [p["pct_secciones_rurales"] for p in perfiles] + [pan_b["pct_secciones_rurales_1d"]]
    m_vals = [p["pct_secciones_mixtas"] for p in perfiles] + [pan_b["pct_secciones_mixtas_1d"]]

    y1 = np.arange(len(labels_1))[::-1]
    ax1.barh(y1, u_vals, height=0.58, color="#2563EB", label="Urbana (U)")
    ax1.barh(y1, r_vals, left=u_vals, height=0.58, color="#16A34A", label="Rural (R)")
    ax1.barh(y1, m_vals, left=np.array(u_vals) + np.array(r_vals), height=0.58, color="#F59E0B", label="Mixta (M)")

    for idx, (u, r, m) in enumerate(zip(u_vals, r_vals, m_vals)):
        yi = y1[idx]
        if u >= 12:
            ax1.text(u / 2, yi, f"U: {u:.1f}%", va="center", ha="center", color="white", fontsize=8, fontweight="bold")
        if r >= 12:
            ax1.text(u + r / 2, yi, f"R: {r:.1f}%", va="center", ha="center", color="white", fontsize=8, fontweight="bold")
        if m >= 7:
            ax1.text(u + r + m / 2, yi, f"M: {m:.1f}%", va="center", ha="center", color="#111827", fontsize=7.5, fontweight="bold")

    ax1.set_yticks(y1)
    ax1.set_yticklabels(labels_1, fontsize=8.0, fontweight="bold")
    ax1.set_xlim(0, 100)
    ax1.set_xlabel("Porcentaje de Secciones (%)", fontsize=9.5, fontweight="bold")
    ax1.set_title("A. Composición Urbana / Rural / Mixta por Perfil y Panel B", fontsize=10.5, fontweight="bold")
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=8.5, frameon=True)
    ax1.grid(axis="x", alpha=0.5)

    # Panel B: Comparación de Secciones Incluidas (53,644) vs Excluidas en 2024 (17,107 = 8,703 + 8,404)
    sub_ie = [inc_exc[0], inc_exc[1], inc_exc[2], inc_exc[3], inc_exc[5]]
    ie_labels = [
        f"Incluidas Panel B\n({sub_ie[0]['n_secciones']:,} secc.\n{sub_ie[0]['pct_ln_2024']:.1f}% LN)",
        f"Total Excl. 2024\n({sub_ie[1]['n_secciones']:,} secc.\n{sub_ie[1]['pct_ln_2024']:.1f}% LN)",
        f"Excl. Post-2009\n({sub_ie[2]['n_secciones']:,} secc.\n{sub_ie[2]['pct_ln_2024']:.1f}% LN)",
        f"Excl. Filtro Calidad\n({sub_ie[3]['n_secciones']:,} secc.\n{sub_ie[3]['pct_ln_2024']:.1f}% LN)",
        f"Total CCPC 2024\n({sub_ie[4]['n_secciones']:,} secc.\n100% LN)",
    ]
    x2 = np.arange(len(ie_labels))
    part_24 = [r["participacion_2024_ponderada_sv_svnv_pct"] for r in sub_ie]
    urb_24 = [r["pct_urbana_1d"] for r in sub_ie]
    urb_24[0] = pan_b["pct_secciones_urbanas_1d"]

    w2 = 0.35
    ax2.bar(x2 - w2 / 2, part_24, width=w2, color="#0D9488", label="Participación 2024 Pond. SV/(SV+NV) (%)")
    ax2.bar(x2 + w2 / 2, urb_24, width=w2, color="#6366F1", label="% Secciones Urbanas en 2024")
    for i in range(len(x2)):
        ax2.text(x2[i] - w2 / 2, part_24[i] + 1.0, f"{part_24[i]:.2f}%", ha="center", va="bottom", fontsize=7.5, fontweight="bold", color="#0F766E")
        ax2.text(x2[i] + w2 / 2, urb_24[i] + 1.0, f"{urb_24[i]:.1f}%", ha="center", va="bottom", fontsize=7.5, fontweight="bold", color="#4338CA")

    ax2.set_xticks(x2)
    ax2.set_xticklabels(ie_labels, fontsize=7.2, fontweight="bold")
    ax2.set_ylim(0, 96)
    ax2.set_ylabel("Porcentaje (%)", fontsize=9.5, fontweight="bold")
    ax2.set_title("B. Secciones Incluidas (53,644) vs Excluidas (17,107) en 2024", fontsize=10.5, fontweight="bold")
    ax2.legend(loc="upper right", fontsize=8.2, frameon=True)
    ax2.grid(axis="y", alpha=0.5)

    fig.suptitle(
        "Tipología Territorial por Perfil y Análisis de Cobertura de Secciones Incluidas vs Excluidas en 2024",
        fontsize=12, fontweight="bold", y=0.98
    )
    fig.tight_layout(rect=[0, 0.08, 1, 0.94])
    fig.savefig(OUT_FIGURAS / "fig5_urbano_rural_entidades.png", dpi=300)
    plt.close(fig)


def generate_fig6_benchmark_k(data: dict) -> None:
    """Figura 6: Benchmark de k=3..7 (Silhouette, Davies-Bouldin, Calinski-Harabasz y Bootstrap ARI con IC 95%)."""
    bench = data["benchmark_modelos"]
    km_rows = [r for r in bench if r["algoritmo"] == "K-Means++"]
    gmm_rows = [r for r in bench if r["algoritmo"] == "GMM (full)"]

    ks = [int(r["k"]) for r in km_rows]
    km_sil = [r["silhouette"] for r in km_rows]
    gmm_sil = [r["silhouette"] for r in gmm_rows]
    km_db = [r["davies_bouldin"] for r in km_rows]
    gmm_db = [r["davies_bouldin"] for r in gmm_rows]
    km_ch = [r["calinski_harabasz"] for r in km_rows]
    gmm_ch = [r["calinski_harabasz"] for r in gmm_rows]
    km_ari = [r["bootstrap_ari_media"] for r in km_rows]
    km_ari_low = [r["bootstrap_ari_media"] - r["bootstrap_ari_ic95_inf"] for r in km_rows]
    km_ari_high = [r["bootstrap_ari_ic95_sup"] - r["bootstrap_ari_media"] for r in km_rows]

    fig, axes = plt.subplots(2, 2, figsize=(13.2, 8.2))
    (ax1, ax2), (ax3, ax4) = axes

    for ax in [ax1, ax2, ax3, ax4]:
        ax.axvspan(3.8, 6.2, color="#FEF3C7", alpha=0.55, zorder=0, label="Rango convocatoria (k=4..6)")
        ax.axvline(4, color="#D97706", linestyle="--", linewidth=1.5, zorder=2)

    # Panel A: Silhouette
    ax1.plot(ks, km_sil, marker="o", linewidth=2.3, color="#1D4ED8", label="K-Means++")
    ax1.plot(ks, gmm_sil, marker="s", linestyle="--", linewidth=1.8, color="#6B7280", label="GMM (full)")
    for k_v, v in zip(ks, km_sil):
        ax1.annotate(f"{v:.4f}", (k_v, v), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8, fontweight="bold")
    ax1.set_title("A. Coeficiente de Silhouette (Mayor es mejor)", fontsize=10.5, fontweight="bold")
    ax1.set_xticks(ks)
    ax1.set_ylim(0.08, 0.235)
    ax1.grid(True, alpha=0.6)
    ax1.legend(loc="upper right", fontsize=8)

    # Panel B: Davies-Bouldin
    ax2.plot(ks, km_db, marker="o", linewidth=2.3, color="#047857", label="K-Means++")
    ax2.plot(ks, gmm_db, marker="s", linestyle="--", linewidth=1.8, color="#6B7280", label="GMM (full)")
    for k_v, v in zip(ks, km_db):
        ax2.annotate(f"{v:.4f}", (k_v, v), textcoords="offset points", xytext=(0, -13), ha="center", fontsize=8, fontweight="bold")
    ax2.set_title("B. Índice de Davies-Bouldin (Menor es mejor)", fontsize=10.5, fontweight="bold")
    ax2.set_xticks(ks)
    ax2.set_ylim(1.40, 2.35)
    ax2.grid(True, alpha=0.6)
    ax2.legend(loc="upper left", fontsize=8)

    # Panel C: Calinski-Harabasz
    ax3.plot(ks, km_ch, marker="o", linewidth=2.3, color="#7C3AED", label="K-Means++")
    ax3.plot(ks, gmm_ch, marker="s", linestyle="--", linewidth=1.8, color="#6B7280", label="GMM (full)")
    for k_v, v in zip(ks, km_ch):
        ax3.annotate(f"{v:,.0f}", (k_v, v), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8, fontweight="bold")
    ax3.set_title("C. Índice Calinski-Harabasz (Mayor es mejor)", fontsize=10.5, fontweight="bold")
    ax3.set_xticks(ks)
    ax3.set_xlabel("Número de Clusters (k)", fontsize=9.5, fontweight="bold")
    ax3.set_ylim(6000, 18500)
    ax3.grid(True, alpha=0.6)
    ax3.legend(loc="upper right", fontsize=8)

    # Panel D: Bootstrap ARI (100 réplicas al 80% + IC 95%)
    ax4.errorbar(
        ks, km_ari, yerr=[km_ari_low, km_ari_high], fmt="-o", linewidth=2.2,
         capsize=5, color="#B91C1C", label="ARI Bootstrap Media ± IC 95%"
    )
    ax4.axhline(0.85, color="#374151", linestyle=":", linewidth=1.2, label="Umbral de alta estabilidad (0.85)")
    for k_v, v in zip(ks, km_ari):
        ax4.annotate(f"{v:.4f}", (k_v, v), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8, fontweight="bold")
    ax4.set_title("D. Estabilidad Bootstrap ARI (100 Réplicas al 80%, IC 95%)", fontsize=10.5, fontweight="bold")
    ax4.set_xticks(ks)
    ax4.set_xlabel("Número de Clusters (k)", fontsize=9.5, fontweight="bold")
    ax4.set_ylim(0.78, 1.02)
    ax4.grid(True, alpha=0.6)
    ax4.legend(loc="lower left", fontsize=8)

    fig.suptitle(
        "Selección Empírica de k=4: Mejor Desempeño en Silhouette, Davies-Bouldin y Calinski-Harabasz dentro del Rango 4–6",
        fontsize=11.8, fontweight="bold", y=0.98
    )
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(OUT_FIGURAS / "fig6_benchmark_k.png", dpi=300)
    plt.close(fig)


def generate_fig7_proyeccion_pca_umap(data: dict, df_b: pd.DataFrame) -> None:
    """Figura 7: Proyección 2D de PCA y UMAP de las 53,644 secciones coloreadas por perfil (k=4)."""
    perfiles = {p["cluster_id"]: p for p in data["perfiles"]}
    pca_info = data["proyecciones_pca"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.2))

    # Muestreo determinista para graficación nítida + centroides exactos sobre las 53,644 secciones
    rng = np.random.default_rng(42)
    sample_idx = rng.choice(len(df_b), size=min(18000, len(df_b)), replace=False)
    sub_plot = df_b.iloc[sample_idx]

    for c in range(4):
        p = perfiles[c]
        mask_s = sub_plot["cluster"] == c
        mask_all = df_b["cluster"] == c
        lbl = f"{p['codigo_cluster']}: {p['nombre_propuesto']} ({p['pct_secciones_panel']:.1f}%)"

        ax1.scatter(
            sub_plot.loc[mask_s, "pca_1"], sub_plot.loc[mask_s, "pca_2"],
            s=3.5, alpha=0.32, color=CLUSTER_COLORS[c], label=lbl, rasterized=True
        )
        cx_pca = float(df_b.loc[mask_all, "pca_1"].mean())
        cy_pca = float(df_b.loc[mask_all, "pca_2"].mean())
        ax1.scatter([cx_pca], [cy_pca], s=150, color=CLUSTER_COLORS[c], edgecolor="black", linewidth=1.5, zorder=10)
        ax1.annotate(
            p["codigo_cluster"], (cx_pca, cy_pca), fontsize=9.5, fontweight="bold",
            xytext=(6, 6), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor=CLUSTER_COLORS[c], lw=1.2)
        )

        ax2.scatter(
            sub_plot.loc[mask_s, "umap_1"], sub_plot.loc[mask_s, "umap_2"],
            s=3.5, alpha=0.32, color=CLUSTER_COLORS[c], label=lbl, rasterized=True
        )
        cx_umap = float(df_b.loc[mask_all, "umap_1"].mean())
        cy_umap = float(df_b.loc[mask_all, "umap_2"].mean())
        ax2.scatter([cx_umap], [cy_umap], s=150, color=CLUSTER_COLORS[c], edgecolor="black", linewidth=1.5, zorder=10)
        ax2.annotate(
            p["codigo_cluster"], (cx_umap, cy_umap), fontsize=9.5, fontweight="bold",
            xytext=(6, 6), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor=CLUSTER_COLORS[c], lw=1.2)
        )

    ax1.set_xlabel(f"Componente Principal 1 ({pca_info['pca_var_exp_1']:.2f}% varianza)", fontsize=9.5, fontweight="bold")
    ax1.set_ylabel(f"Componente Principal 2 ({pca_info['pca_var_exp_2']:.2f}% varianza)", fontsize=9.5, fontweight="bold")
    ax1.set_title(
        f"A. Proyección Lineal PCA 2D ({pca_info['pca_var_exp_total_2d']:.2f}% Varianza Acumulada)",
        fontsize=10.8, fontweight="bold"
    )
    ax1.set_xlim(-4.5, 4.5)
    ax1.set_ylim(-4.0, 4.5)
    ax1.grid(True, alpha=0.5)

    ax2.set_xlabel("Dimensión UMAP 1 (n_neighbors=30, min_dist=0.1)", fontsize=9.5, fontweight="bold")
    ax2.set_ylabel("Dimensión UMAP 2", fontsize=9.5, fontweight="bold")
    ax2.set_title("B. Proyección No Lineal UMAP 2D (Únicamente para Visualización)", fontsize=10.8, fontweight="bold")
    ax2.grid(True, alpha=0.5)

    handles = [
        mpatches.Patch(color=CLUSTER_COLORS[c], label=f"{perfiles[c]['codigo_cluster']}: {perfiles[c]['nombre_propuesto']} (n={perfiles[c]['n_secciones']:,})")
        for c in range(4)
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.01), ncol=2, fontsize=8.8, frameon=True)

    fig.suptitle(
        "Geometría del Espacio Electoral 7D: Proyecciones PCA y UMAP de los 4 Perfiles Ciudadanos (N = 53,644 Secciones)",
        fontsize=12, fontweight="bold", y=0.98
    )
    fig.tight_layout(rect=[0, 0.08, 1, 0.94])
    fig.savefig(OUT_FIGURAS / "fig7_proyeccion_pca_umap.png", dpi=300)
    plt.close(fig)


def main() -> None:
    print("[Fase 6] Cargando metricas_finales.json y etiquetas_finales.parquet...")
    data, df_b = load_inputs()

    print("[Fase 6] 1/7 Generando fig1_mapa_clusters.png...")
    generate_fig1_mapa_clusters(data, df_b)

    print("[Fase 6] 2/7 Generando fig2_evolucion_temporal.png...")
    generate_fig2_evolucion_temporal(data)

    print("[Fase 6] 3/7 Generando fig3_radar_centroides.png...")
    generate_fig3_radar_centroides(data)

    print("[Fase 6] 4/7 Generando fig4_brechas_demograficas.png...")
    generate_fig4_brechas_demograficas(data)

    print("[Fase 6] 5/7 Generando fig5_urbano_rural_entidades.png...")
    generate_fig5_urbano_rural_entidades(data)

    print("[Fase 6] 6/7 Generando fig6_benchmark_k.png...")
    generate_fig6_benchmark_k(data)

    print("[Fase 6] 7/7 Generando fig7_proyeccion_pca_umap.png...")
    generate_fig7_proyeccion_pca_umap(data, df_b)

    print(f"[Fase 6] Completado. 7 figuras a 300 DPI guardadas en {OUT_FIGURAS}")


if __name__ == "__main__":
    main()
