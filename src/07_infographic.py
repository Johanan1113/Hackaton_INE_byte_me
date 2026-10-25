"""
Módulo 07: Generador de Fichas de Perfiles Ciudadanos (Infografía / Poster Técnico 300 DPI)
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
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D

# Configuración de Logging
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("07_infographic")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DATASETS = os.path.join(PROJECT_ROOT, "output", "datasets")
ENTREGABLES_DIR = os.path.join(PROJECT_ROOT, "entregables_finales")
OUTPUT_PNG = os.path.join(ENTREGABLES_DIR, "Fichas_Perfiles_Infografia_ByteMe.png")
OUTPUT_PDF = os.path.join(ENTREGABLES_DIR, "Fichas_Perfiles_Infografia_ByteMe.pdf")

# Paleta Institucional
HEX_PURPLE = "#582D73"   # Primario INE
HEX_MAGENTA = "#D1367E"  # Secundario Acción
HEX_TEAL = "#00A896"     # Terciario Cívico
HEX_AMBER = "#E67E22"    # Soporte Alerta
HEX_BLUE = "#2980B9"     # Juventud Dinámica
HEX_DARK = "#1E1E24"     # Texto principal
HEX_MUTED = "#5A6275"    # Texto secundario
HEX_BG = "#F4F6F9"       # Fondo general
HEX_CARD = "#FFFFFF"     # Tarjetas
HEX_BORDER = "#D0D7DE"   # Bordes

CLUSTER_COLORS = {
    0: HEX_MAGENTA,  # Voto Femenino Consistente
    1: HEX_PURPLE,   # Pivote Presidencial Volátil
    2: HEX_AMBER,    # Abstencionismo Estructural Urbano
    3: HEX_TEAL,     # Voto Tradicional Rural y Mayor
    4: HEX_BLUE      # Juventud Movilizada en Expansión
}

def load_data():
    """Carga metadatos de arquetipos y series temporales históricas."""
    fichas_path = os.path.join(OUTPUT_DATASETS, "arquetipos_fichas.json")
    with open(fichas_path, "r", encoding="utf-8") as f:
        arquetipos = json.load(f)
        
    df_clusters = pd.read_parquet(os.path.join(OUTPUT_DATASETS, "dataset_clusters_final.parquet"))
    df_armonizadas = pd.read_parquet(os.path.join(OUTPUT_DATASETS, "secciones_armonizadas_2009_2024.parquet"))
    
    # Calcular promedios longitudinales de participación por cluster y nacional
    cols_years = ['part_2009', 'part_2012', 'part_2015', 'part_2018', 'part_2021', 'part_2024']
    merged = df_clusters[['cve_seccion', 'cluster']].merge(
        df_armonizadas[['cve_seccion'] + cols_years], on='cve_seccion'
    )
    
    traj_cluster = merged.groupby('cluster')[cols_years].mean()
    traj_nacional = df_armonizadas[cols_years].mean()
    
    return arquetipos, traj_cluster, traj_nacional, df_clusters

def generate_infographic():
    """Genera el poster/infografía a 300 DPI en PNG y PDF."""
    logger.info("=== GENERACIÓN DE INFOGRAFÍA / POSTER DE FICHAS DE PERFILES ===")
    os.makedirs(ENTREGABLES_DIR, exist_ok=True)
    
    arquetipos, traj_cluster, traj_nacional, df_clusters = load_data()
    
    # Configuración de Matplotlib
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.size'] = 10
    
    # Dimensiones tipo póster panorámico editorial (32 x 22 pulgadas, 300 DPI)
    fig = plt.figure(figsize=(32, 22), facecolor=HEX_BG, dpi=300)
    
    # Grid principal: Cabecera (0.13), Contenido 2x3 (0.80), Footer (0.07)
    gs = gridspec.GridSpec(
        nrows=3, ncols=1,
        height_ratios=[0.11, 0.81, 0.08],
        left=0.02, right=0.98, top=0.98, bottom=0.02,
        hspace=0.04
    )
    
    # -------------------------------------------------------------
    # 1. CABECERA INSTITUCIONAL
    # -------------------------------------------------------------
    ax_head = fig.add_subplot(gs[0])
    ax_head.axis('off')
    
    # Fondo de la cabecera
    bg_head = patches.FancyBboxPatch(
        (0, 0), 1, 1, boxstyle="round,pad=0.01,rounding_size=0.02",
        transform=ax_head.transAxes, facecolor=HEX_PURPLE, edgecolor="none", zorder=1
    )
    ax_head.add_patch(bg_head)
    
    # Pleca decorativa magenta
    pleca = patches.Rectangle((0, 0), 1, 0.06, transform=ax_head.transAxes, facecolor=HEX_MAGENTA, edgecolor="none", zorder=2)
    ax_head.add_patch(pleca)
    
    # Textos de Cabecera
    ax_head.text(
        0.025, 0.72,
        "INSTITUTO NACIONAL ELECTORAL   |   ESTRATEGIA NACIONAL DE EDUCACIÓN CÍVICA (ENCÍVICA)",
        color="#F3E5F5", fontsize=13, weight='bold', zorder=3
    )
    ax_head.text(
        0.025, 0.42,
        "FICHAS SINTÉTICAS DE PERFILES CIUDADANOS DE PARTICIPACIÓN (CCPC 2009–2024)",
        color="white", fontsize=23, weight='heavy', zorder=3
    )
    ax_head.text(
        0.025, 0.20,
        "Concurso Oficial: \"Hackea la Participación: Datos que construyen democracia\"  •  Reto 1: Perfiles ciudadanos de participación",
        color="#E1BEE7", fontsize=12, zorder=3
    )
    
    # Caja de Metadatos de Equipo (Derecha)
    ax_head.text(
        0.66, 0.72,
        "EQUIPO: BYTE ME",
        color="#FFE082", fontsize=15, weight='bold', zorder=3
    )
    ax_head.text(
        0.66, 0.48,
        "Representante: Johanan Olivares Gutierrez (Científico de Datos Principal / MLOps)",
        color="white", fontsize=11, zorder=3
    )
    ax_head.text(
        0.66, 0.32,
        "Integrantes: Oscar Ariel Cuevas Martinez  •  Saul Alexis Arias Gonzales",
        color="white", fontsize=11, zorder=3
    )
    ax_head.text(
        0.66, 0.16,
        "Universo: 62,048 Secciones Longitudinales  |  85.9M Electores  |  6 Elecciones Federales",
        color="#E1BEE7", fontsize=10.5, weight='bold', zorder=3
    )

    # -------------------------------------------------------------
    # 2. GRID 2x3 DE FICHAS Y SÍNTESIS
    # -------------------------------------------------------------
    gs_cards = gridspec.GridSpecFromSubplotSpec(
        nrows=2, ncols=3,
        subplot_spec=gs[1],
        wspace=0.03, hspace=0.05
    )
    
    # Orden de las tarjetas:
    # Fila 1: Cluster 2 (Abstencionismo), Cluster 0 (Voto Femenino), Cluster 1 (Pivote Presidencial)
    # Fila 2: Cluster 4 (Juventud), Cluster 3 (Voto Tradicional Rural), Panel 6 (Síntesis Metodológica y Política)
    card_order = [2, 0, 1, 4, 3]
    
    years_labels = ['2009', '2012', '2015', '2018', '2021', '2024']
    
    for idx, c_id in enumerate(card_order):
        row = idx // 3
        col = idx % 3
        ax_card = fig.add_subplot(gs_cards[row, col])
        ax_card.axis('off')
        
        info = arquetipos[str(c_id)]
        color_c = CLUSTER_COLORS[c_id]
        
        # Fondo blanco de la tarjeta
        card_bg = patches.FancyBboxPatch(
            (0, 0), 1, 1, boxstyle="round,pad=0.01,rounding_size=0.025",
            transform=ax_card.transAxes, facecolor=HEX_CARD, edgecolor=HEX_BORDER, linewidth=1.5, zorder=1
        )
        ax_card.add_patch(card_bg)
        
        # Cabecera de la tarjeta con color del cluster
        header_patch = patches.Rectangle(
            (0, 0.86), 1, 0.14,
            transform=ax_card.transAxes, facecolor=color_c, edgecolor="none", zorder=2
        )
        ax_card.add_patch(header_patch)
        
        # Título y badges en la cabecera
        ax_card.text(
            0.04, 0.94,
            f"ARQUETIPO C{c_id}  |  {info['nombre'].upper()}",
            transform=ax_card.transAxes, color="white", fontsize=14, weight='bold', zorder=3
        )
        ax_card.text(
            0.04, 0.885,
            f"Volumen: {info['secciones']:,} secciones ({info['pct_secciones']}%)  •  Lista Nominal: {info['padron_2024']/1e6:.2f} M electores ({info['pct_padron']}%)",
            transform=ax_card.transAxes, color="#F9F9FB", fontsize=10, weight='semibold', zorder=3
        )
        
        # Lema Cívico destacado
        ax_card.text(
            0.04, 0.815,
            f"«{info['lema_civico']}»",
            transform=ax_card.transAxes, color=HEX_DARK, fontsize=10.5, style='italic', weight='bold',
            zorder=3, wrap=True
        )
        
        # Sub-cuadrícula de Métricas Clave (KPIs)
        # 6 cajas de métricas en dos filas de 3
        kpis = [
            ("Participación Media", f"{info['participacion_media']*100:.1f}%", color_c),
            ("Brecha Pres vs Int", f"{info['brecha_presidencial']*100:+.1f} pts", HEX_DARK),
            ("Brecha de Género (M-H)", f"{info['brecha_genero']*100:+.1f} pts", HEX_DARK),
            ("Votación 18–29 años", f"{info['tasa_jovenes']*100:.1f}%", HEX_DARK),
            ("Votación 60+ años", f"{info['tasa_mayores']*100:.1f}%", HEX_DARK),
            ("Entorno Territorial", f"{info['pct_urbana']:.0f}% Urb / {info['pct_rural']:.0f}% Rur", HEX_DARK),
        ]
        
        for k_i, (k_label, k_val, k_col) in enumerate(kpis):
            kx = 0.04 + (k_i % 3) * 0.315
            ky = 0.70 if (k_i < 3) else 0.59
            
            box_kpi = patches.FancyBboxPatch(
                (kx, ky), 0.29, 0.095, boxstyle="round,pad=0.005,rounding_size=0.015",
                transform=ax_card.transAxes, facecolor="#F8FAFC", edgecolor=HEX_BORDER, linewidth=0.8, zorder=2
            )
            ax_card.add_patch(box_kpi)
            
            ax_card.text(
                kx + 0.145, ky + 0.055, k_val,
                transform=ax_card.transAxes, color=k_col, fontsize=12, weight='bold',
                ha='center', va='center', zorder=3
            )
            ax_card.text(
                kx + 0.145, ky + 0.02, k_label,
                transform=ax_card.transAxes, color=HEX_MUTED, fontsize=7.5,
                ha='center', va='center', zorder=3
            )
            
        # Inserción de Mini-gráfico de Trayectoria Temporal (2009-2024)
        # Usamos un inset axes en matplotlib dentro de la tarjeta
        ax_inset = ax_card.inset_axes([0.04, 0.34, 0.92, 0.21])
        ax_inset.set_facecolor("#FFFFFF")
        
        c_traj = traj_cluster.loc[c_id].values * 100
        nat_traj = traj_nacional.values * 100
        
        # Graficar trayectorias
        ax_inset.plot(years_labels, nat_traj, color="#A0AAB5", linestyle="--", linewidth=1.5, label="Media Nacional", zorder=2)
        ax_inset.plot(years_labels, c_traj, color=color_c, marker='o', linewidth=2.5, markersize=5, label=f"Cluster {c_id}", zorder=3)
        
        # Relleno entre el cluster y la media nacional
        ax_inset.fill_between(years_labels, c_traj, nat_traj, color=color_c, alpha=0.15, zorder=1)
        
        # Anotar los valores extremos
        ax_inset.text(5, c_traj[5] + 1.2, f"{c_traj[5]:.1f}% (2024)", color=color_c, fontsize=8, weight='bold', ha='right')
        
        ax_inset.set_ylim(25, 75)
        ax_inset.set_ylabel("Participación (%)", fontsize=8, color=HEX_MUTED)
        ax_inset.tick_params(axis='both', which='major', labelsize=8)
        ax_inset.grid(True, linestyle=":", alpha=0.6, color="#CBD5E1")
        ax_inset.legend(loc='lower left', fontsize=7.5, frameon=True, facecolor='white', framealpha=0.9)
        
        # Diagnóstico y Estrategia INE (Bloque inferior de la tarjeta)
        est = info["estrategia"]
        
        ax_card.text(
            0.04, 0.30,
            "DIAGNÓSTICO & DINÁMICA DE PARTICIPACIÓN:",
            transform=ax_card.transAxes, color=HEX_PURPLE, fontsize=9, weight='bold', zorder=3
        )
        ax_card.text(
            0.04, 0.22,
            f"• Diagnóstico: {est['diagnostico']}\n• Factor Crítico de Abstención: {info['factor_abstencion']}",
            transform=ax_card.transAxes, color=HEX_DARK, fontsize=8.2, zorder=3
        )
        
        # Bloque de Intervención Estratégica INE
        rec_bg = patches.FancyBboxPatch(
            (0.04, 0.03), 0.92, 0.17, boxstyle="round,pad=0.005,rounding_size=0.015",
            transform=ax_card.transAxes, facecolor="#F1F5F9", edgecolor=color_c, linewidth=1.2, zorder=2
        )
        ax_card.add_patch(rec_bg)
        
        ax_card.text(
            0.06, 0.165,
            f"INTERVENCIÓN RECOMENDADA INE / ENCÍVICA:",
            transform=ax_card.transAxes, color=color_c, fontsize=8.5, weight='bold', zorder=3
        )
        ax_card.text(
            0.06, 0.045,
            f"► CANAL: {est['canal']}\n► NARRATIVA: {est['narrativa']}\n► ACCIÓN OPERATIVA: {est['accion_operativa']}",
            transform=ax_card.transAxes, color=HEX_DARK, fontsize=7.8, zorder=3
        )

    # -------------------------------------------------------------
    # TARJETA 6: SÍNTESIS METODOLÓGICA Y MATRIZ ESTRATÉGICA
    # -------------------------------------------------------------
    ax_card6 = fig.add_subplot(gs_cards[1, 2])
    ax_card6.axis('off')
    
    card6_bg = patches.FancyBboxPatch(
        (0, 0), 1, 1, boxstyle="round,pad=0.01,rounding_size=0.025",
        transform=ax_card6.transAxes, facecolor=HEX_CARD, edgecolor=HEX_BORDER, linewidth=1.5, zorder=1
    )
    ax_card6.add_patch(card6_bg)
    
    h6 = patches.Rectangle((0, 0.86), 1, 0.14, transform=ax_card6.transAxes, facecolor="#2C3E50", edgecolor="none", zorder=2)
    ax_card6.add_patch(h6)
    
    ax_card6.text(
        0.04, 0.94,
        "SÍNTESIS METODOLÓGICA Y MATRIZ ESTRATÉGICA",
        transform=ax_card6.transAxes, color="white", fontsize=14, weight='bold', zorder=3
    )
    ax_card6.text(
        0.04, 0.885,
        "Benchmark de Algoritmos, Explicabilidad y Prioridades de Política Pública",
        transform=ax_card6.transAxes, color="#CBD5E1", fontsize=10, weight='semibold', zorder=3
    )
    
    # 1. Benchmark de Clustering
    ax_card6.text(
        0.04, 0.81,
        "1. BENCHMARK DE ALGORITMOS NO SUPERVISADOS",
        transform=ax_card6.transAxes, color=HEX_PURPLE, fontsize=9.5, weight='bold', zorder=3
    )
    ax_card6.text(
        0.04, 0.69,
        "• Modelo Campeón: K-Means++ con k = 5 clusters.\n"
        "• Silhouette Score: 0.1805 (superó a GMM con 0.1481 y HDBSCAN).\n"
        "• Davies-Bouldin Index: 1.4233  •  Calinski-Harabasz: 18,742.6\n"
        "• Estabilidad de Remuestreo Bootstrap: ARI = 0.8411 (alta solidez).\n"
        "• Reducción Dimensional: PCA (60.1% varianza explicada) y UMAP 2D.",
        transform=ax_card6.transAxes, color=HEX_DARK, fontsize=8.5, zorder=3
    )
    
    # 2. Explicabilidad Multivariada
    ax_card6.text(
        0.04, 0.64,
        "2. EXPLICABILIDAD ESTADÍSTICA (ANOVA & RANDOM FOREST)",
        transform=ax_card6.transAxes, color=HEX_PURPLE, fontsize=9.5, weight='bold', zorder=3
    )
    ax_card6.text(
        0.04, 0.52,
        "• Random Forest Multiclase: 94.08% exactitud de clasificación.\n"
        "• Factores más determinantes (Importancia):\n"
        "  1. Brecha Presidencial vs Intermedia (Importancia = 0.324)\n"
        "  2. Estabilidad Longitudinal (1/CV) (Importancia = 0.241)\n"
        "  3. Participación Histórica Media (Importancia = 0.182)\n"
        "  4. Brecha de Género (Mujeres - Hombres) (Importancia = 0.138)\n"
        "• Pruebas ANOVA F-test: Significancia p < 1e-15 en todas las variables.",
        transform=ax_card6.transAxes, color=HEX_DARK, fontsize=8.5, zorder=3
    )
    
    # 3. Matriz de Prioridad Institucional para el INE
    ax_card6.text(
        0.04, 0.47,
        "3. MATRIZ DE PRIORIDADES OPERATIVAS INE / ENCÍVICA",
        transform=ax_card6.transAxes, color=HEX_PURPLE, fontsize=9.5, weight='bold', zorder=3
    )
    
    matriz_text = (
        "┌─────────┬──────────────────────────┬─────────────────────────────┐\n"
        "│ Cluster │ Arquetipo Ciudadano      │ Prioridad de Política INE   │\n"
        "├─────────┼──────────────────────────┼─────────────────────────────┤\n"
        "│   C2    │ Abstencionismo Urbano    │ Casillas nodos / Fac. empleo│\n"
        "│   C0    │ Voto Femenino Consist.   │ Redes de cuidado / Liderazgo│\n"
        "│   C1    │ Pivote Presidencial      │ Pedagogía elecciones interm.│\n"
        "│   C4    │ Juventud en Expansión    │ Credencialización en campus │\n"
        "│   C3    │ Voto Rural y Mayor       │ Accesibilidad física rural  │\n"
        "└─────────┴──────────────────────────┴─────────────────────────────┘"
    )
    ax_card6.text(
        0.04, 0.28,
        matriz_text,
        transform=ax_card6.transAxes, color="#1E293B", fontfamily="monospace", fontsize=7.5, weight='bold', zorder=3
    )
    
    # Caja de impacto de política
    impact_box = patches.FancyBboxPatch(
        (0.04, 0.03), 0.92, 0.21, boxstyle="round,pad=0.005,rounding_size=0.015",
        transform=ax_card6.transAxes, facecolor="#F8FAFC", edgecolor=HEX_PURPLE, linewidth=1.2, zorder=2
    )
    ax_card6.add_patch(impact_box)
    
    ax_card6.text(
        0.06, 0.20,
        "IMPACTO DIRECTO EN LA ENCÍVICA 2024–2030:",
        transform=ax_card6.transAxes, color=HEX_PURPLE, fontsize=8.8, weight='bold', zorder=3
    )
    ax_card6.text(
        0.06, 0.05,
        "Esta tipología trasciende las campañas genéricas homogeneizantes del INE.\n"
        "Al georreferenciar las 62,048 secciones del país en 5 perfiles nítidos, las 300 Juntas\n"
        "Distritales Ejecutivas pueden asignar presupuestos, módulos móviles y programas de\n"
        "educación cívica con micro-focalización territorial, optimizando recursos públicos\n"
        "y combatiendo el abstencionismo estructural en los 32.9 millones de electores del C2.",
        transform=ax_card6.transAxes, color=HEX_DARK, fontsize=8.0, zorder=3
    )

    # -------------------------------------------------------------
    # 3. PIE DE PÁGINA INSTITUCIONAL
    # -------------------------------------------------------------
    ax_foot = fig.add_subplot(gs[2])
    ax_foot.axis('off')
    
    bg_foot = patches.FancyBboxPatch(
        (0, 0), 1, 1, boxstyle="round,pad=0.01,rounding_size=0.015",
        transform=ax_foot.transAxes, facecolor="#1E1E24", edgecolor="none", zorder=1
    )
    ax_foot.add_patch(bg_foot)
    
    ax_foot.text(
        0.025, 0.65,
        "CONCURSO OFICIAL INE: \"HACKEA LA PARTICIPACIÓN: DATOS QUE CONSTRUYEN DEMOCRACIA\" (CCPC 2009–2024)",
        color="white", fontsize=11, weight='bold', zorder=2
    )
    ax_foot.text(
        0.025, 0.25,
        "Entregable 3: Fichas de Perfiles Ciudadanos  •  Resolución Editorial: 300 DPI  •  Pipeline 100% reproducible en código abierto",
        color="#CBD5E1", fontsize=9.5, zorder=2
    )
    ax_foot.text(
        0.65, 0.65,
        "EQUIPO \"BYTE ME\"  •  INSTITUTO NACIONAL ELECTORAL",
        color="#F59E0B", fontsize=11, weight='bold', zorder=2
    )
    ax_foot.text(
        0.65, 0.25,
        "Johanan Olivares Gutierrez (Rep.)  |  Oscar Ariel Cuevas Martinez  |  Saul Alexis Arias Gonzales",
        color="white", fontsize=9.5, zorder=2
    )

    # Guardar en PNG (300 DPI) y PDF
    logger.info(f"Guardando imagen PNG a 300 DPI en: {OUTPUT_PNG}")
    plt.savefig(OUTPUT_PNG, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    
    logger.info(f"Guardando versión vectorial PDF en: {OUTPUT_PDF}")
    plt.savefig(OUTPUT_PDF, format='pdf', facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    
    plt.close(fig)
    
    # Validaciones de archivo
    png_size = os.path.getsize(OUTPUT_PNG) / 1024
    pdf_size = os.path.getsize(OUTPUT_PDF) / 1024
    logger.info(f"✓ PNG generado exitosamente: {png_size:.1f} KB")
    logger.info(f"✓ PDF generado exitosamente: {pdf_size:.1f} KB")
    assert png_size > 100, f"Error: El PNG es demasiado pequeño ({png_size:.1f} KB)"
    assert pdf_size > 100, f"Error: El PDF es demasiado pequeño ({pdf_size:.1f} KB)"
    logger.info("✓ Infografía / Poster técnico completado con máxima calidad editorial.")

if __name__ == "__main__":
    generate_infographic()
