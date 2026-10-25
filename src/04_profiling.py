"""
Módulo 04: Explicabilidad (Random Forest/ANOVA), Narrativa de Arquetipos y Planes ENCÍVICA
Reto 1: Perfiles Ciudadanos de Participación (INE / ENCÍVICA 2024)
"""

import os
import sys
import logging
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from scipy.stats import f_oneway

# Configuración de Logging
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("04_profiling")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DATASETS = os.path.join(PROJECT_ROOT, "output", "datasets")
OUTPUT_MODELS = os.path.join(PROJECT_ROOT, "output", "models")
OUTPUT_FIGURES = os.path.join(PROJECT_ROOT, "output", "figures")
PIPELINE_LOG = os.path.join(PROJECT_ROOT, "pipeline.log")

file_handler = logging.FileHandler(PIPELINE_LOG, mode="a", encoding="utf-8")
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(file_handler)

INE_PURPLE = "#582D73"
INE_MAGENTA = "#D1367E"
INE_DARK = "#2B2B2B"
CLUSTER_PALETTE = ["#582D73", "#D1367E", "#2A9D8F", "#E76F51", "#264653"]

def explain_clusters_with_rf(df: pd.DataFrame, feature_names: list):
    """
    Entrena un RandomForestClassifier multiclase sobre las etiquetas de los clusters
    para calcular importancia Gini y de Permutación, además de ANOVA F-test.
    """
    logger.info("=== FASE 4.1: Explicabilidad y Feature Importance (Random Forest & ANOVA) ===")
    
    scaled_cols = [f"{col}_scaled" for col in feature_names]
    X = df[scaled_cols].values
    y = df["cluster"].values
    
    rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    train_acc = rf.score(X, y)
    logger.info(f"Random Forest Classifier entrenado con éxito. Exactitud de reconstrucción: {train_acc*100:.2f}%")
    joblib.dump(rf, os.path.join(OUTPUT_MODELS, "rf_explainer.joblib"))
    
    # Importancia Gini
    gini_imp = rf.feature_importances_
    
    # Importancia por Permutación (muestra de 5,000 registros para eficiencia)
    sample_idx = np.random.RandomState(42).choice(len(X), size=5000, replace=False)
    perm_res = permutation_importance(rf, X[sample_idx], y[sample_idx], n_repeats=5, random_state=42, n_jobs=-1)
    perm_imp = perm_res.importances_mean
    
    # ANOVA F-test por variable
    anova_results = []
    for col in feature_names:
        groups = [df[df["cluster"] == c][col].values for c in sorted(df["cluster"].unique())]
        f_stat, p_val = f_oneway(*groups)
        anova_results.append({"feature": col, "f_stat": f_stat, "p_val": p_val})
        logger.info(f"  ANOVA F-test ({col}): F={f_stat:.2f}, p-value={p_val:.2e}")
        
    feat_importance_df = pd.DataFrame({
        "feature": feature_names,
        "feature_label": [
            "Participación Histórica", "Brecha Presidencial", "Tendencia Beta",
            "Estabilidad (Inv CV)", "Brecha Generacional", "Brecha Género", "Ratio Joven"
        ],
        "gini_importance": gini_imp,
        "permutation_importance": perm_imp,
        "f_statistic": [r["f_stat"] for r in anova_results]
    }).sort_values("gini_importance", ascending=True)
    
    feat_importance_df.to_parquet(os.path.join(OUTPUT_DATASETS, "feature_importance.parquet"), index=False)
    
    # Gráfica de Importancia a 300 DPI
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)
    
    # Gini
    y_pos = np.arange(len(feat_importance_df))
    ax1.barh(y_pos, feat_importance_df["gini_importance"], color=INE_PURPLE, alpha=0.85)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(feat_importance_df["feature_label"], fontsize=10)
    ax1.set_title("A) Importancia Gini (Reducción de Impureza)", fontsize=11, fontweight="bold", color=INE_DARK)
    ax1.set_xlabel("Importancia Relativa", fontsize=10)
    ax1.grid(True, linestyle="--", alpha=0.4, axis="x")
    
    # Permutation
    ax2.barh(y_pos, feat_importance_df["permutation_importance"], color=INE_MAGENTA, alpha=0.85)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(feat_importance_df["feature_label"], fontsize=10)
    ax2.set_title("B) Importancia por Permutación (Impacto en Exactitud)", fontsize=11, fontweight="bold", color=INE_DARK)
    ax2.set_xlabel("Disminución en Score", fontsize=10)
    ax2.grid(True, linestyle="--", alpha=0.4, axis="x")
    
    plt.suptitle("Determinantes Cuantitativos de los Perfiles de Participación (INE / ENCÍVICA)", fontsize=13, fontweight="bold", color=INE_PURPLE, y=0.98)
    fig_path = os.path.join(OUTPUT_FIGURES, "05_feature_importance_rf.png")
    plt.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Gráfica de Feature Importance guardada en: {fig_path}")
    
    return feat_importance_df

def plot_radar_chart(df: pd.DataFrame, cluster_names: dict, feature_names: list):
    """Genera gráfico de radar multivariable para comparar la huella dactilar de cada perfil a 300 DPI."""
    logger.info("=== FASE 4.2: Construcción del Radar Chart Multivariable ===")
    
    categories = [
        "Part. Histórica", "Brecha Presid.", "Tendencia Beta",
        "Estabilidad", "Brecha Generacional", "Brecha Género", "Ratio Joven"
    ]
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    # Normalizar medias entre 0 y 1 para visualización radial homogénea
    means_by_cluster = df.groupby("cluster")[feature_names].mean()
    min_vals = df[feature_names].min()
    max_vals = df[feature_names].max()
    norm_means = (means_by_cluster - min_vals) / (max_vals - min_vals)
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True), dpi=300)
    plt.xticks(angles[:-1], categories, color="#2B2B2B", size=10, fontweight="bold")
    ax.set_rlabel_position(30)
    plt.yticks([0.2, 0.4, 0.6, 0.8], ["20%", "40%", "60%", "80%"], color="grey", size=8)
    plt.ylim(0, 1)
    
    for i, c in enumerate(sorted(cluster_names.keys())):
        values = norm_means.loc[c].values.flatten().tolist()
        values += values[:1]
        ax.plot(angles, values, linewidth=2, linestyle='solid', label=f"C{c}: {cluster_names[c]}", color=CLUSTER_PALETTE[i])
        ax.fill(angles, values, color=CLUSTER_PALETTE[i], alpha=0.15)
        
    plt.title("Huella Cívica Comparativa por Arquetipo Ciudadano (INE)", size=14, color=INE_PURPLE, y=1.08, fontweight="bold")
    plt.legend(loc='upper right', bbox_to_anchor=(1.25, 1.1), frameon=True, fontsize=9)
    
    radar_path = os.path.join(OUTPUT_FIGURES, "04_radar_clusters_profiles.png")
    plt.savefig(radar_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Radar chart guardado en: {radar_path}")

def plot_demographic_boxplots(df: pd.DataFrame, cluster_names: dict):
    """Genera distribuciones estadísticas en boxplots para los 5 perfiles a 300 DPI."""
    logger.info("=== FASE 4.3: Gráfica de Distribuciones y Boxplots Demográficos ===")
    
    plot_df = df.copy()
    plot_df["Arquetipo"] = plot_df["cluster"].map(lambda c: f"C{c}: {cluster_names[c]}")
    order = [f"C{c}: {cluster_names[c]}" for c in sorted(cluster_names.keys())]
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 11), dpi=300)
    plt.subplots_adjust(hspace=0.35, wspace=0.25)
    
    # 1. Participación Media Histórica
    sns.boxplot(data=plot_df, x="Arquetipo", y="participacion_media_historica", ax=axes[0, 0], palette=CLUSTER_PALETTE, order=order)
    axes[0, 0].set_title("A) Participación Media Histórica (2009-2024)", fontsize=11, fontweight="bold", color=INE_DARK)
    axes[0, 0].set_ylabel("Tasa de Participación", fontsize=10)
    axes[0, 0].set_xticklabels(axes[0, 0].get_xticklabels(), rotation=20, ha="right", fontsize=8)
    axes[0, 0].grid(True, linestyle="--", alpha=0.3)
    
    # 2. Brecha Presidencial vs Intermedia
    sns.boxplot(data=plot_df, x="Arquetipo", y="brecha_presidencial_intermedia", ax=axes[0, 1], palette=CLUSTER_PALETTE, order=order)
    axes[0, 1].set_title("B) Brecha Presidencial vs. Intermedia (Volatilidad)", fontsize=11, fontweight="bold", color=INE_DARK)
    axes[0, 1].set_ylabel("Diferencia de Participación (Pres - Int)", fontsize=10)
    axes[0, 1].set_xticklabels(axes[0, 1].get_xticklabels(), rotation=20, ha="right", fontsize=8)
    axes[0, 1].grid(True, linestyle="--", alpha=0.3)
    
    # 3. Tasa de Participación Jóvenes (18 a 29 años)
    sns.boxplot(data=plot_df, x="Arquetipo", y="tasa_jovenes_18_29", ax=axes[1, 0], palette=CLUSTER_PALETTE, order=order)
    axes[1, 0].set_title("C) Tasa de Participación Juvenil (18 a 29 años)", fontsize=11, fontweight="bold", color=INE_DARK)
    axes[1, 0].set_ylabel("Tasa de Participación Juvenil", fontsize=10)
    axes[1, 0].set_xticklabels(axes[1, 0].get_xticklabels(), rotation=20, ha="right", fontsize=8)
    axes[1, 0].grid(True, linestyle="--", alpha=0.3)
    
    # 4. Brecha de Género (Mujeres - Hombres)
    sns.boxplot(data=plot_df, x="Arquetipo", y="brecha_genero", ax=axes[1, 1], palette=CLUSTER_PALETTE, order=order)
    axes[1, 1].set_title("D) Brecha de Género (% Mujeres - % Hombres)", fontsize=11, fontweight="bold", color=INE_DARK)
    axes[1, 1].set_ylabel("Diferencia Pro-Femenina", fontsize=10)
    axes[1, 1].set_xticklabels(axes[1, 1].get_xticklabels(), rotation=20, ha="right", fontsize=8)
    axes[1, 1].grid(True, linestyle="--", alpha=0.3)
    
    plt.suptitle("Distribución de Métricas Clave por Arquetipo Ciudadano", fontsize=14, fontweight="bold", color=INE_PURPLE, y=0.98)
    bp_path = os.path.join(OUTPUT_FIGURES, "06_demographic_boxplots.png")
    plt.savefig(bp_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Boxplots guardados en: {bp_path}")

def plot_geographic_distribution(df: pd.DataFrame, cluster_names: dict):
    """Analiza y gráfica la distribución territorial y tipología urbana/rural por cluster a 300 DPI."""
    logger.info("=== FASE 4.4: Análisis Territorial y Tipología Seccional ===")
    
    # 1. Distribución Urbano / Rural / Mixta
    tipo_mapping = {"U": "Urbana", "R": "Rural", "M": "Mixta"}
    df["tipo_nombre"] = df["tiposec"].map(tipo_mapping).fillna("Urbana")
    
    ct_tipo = pd.crosstab(df["cluster"], df["tipo_nombre"], normalize="index") * 100
    ct_tipo.index = [f"C{c}: {cluster_names[c]}" for c in ct_tipo.index]
    
    # 2. Entidades federativas con mayor peso en cada cluster
    top_states_per_cluster = {}
    for c in sorted(cluster_names.keys()):
        top_s = df[df["cluster"] == c]["edonom"].value_counts().head(3)
        top_states_per_cluster[c] = ", ".join([f"{s} ({n:,})" for s, n in top_s.items()])
        logger.info(f"  Cluster {c} ({cluster_names[c]}): Principales estados -> {top_states_per_cluster[c]}")
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=300)
    
    # Gráfica de barras apiladas Tipo de Sección
    colors_tipo = ["#457B9D", "#E76F51", "#2A9D8F"]
    ct_tipo.plot(kind="barh", stacked=True, color=colors_tipo, ax=ax1, alpha=0.85)
    ax1.set_title("A) Composición Territorial (Urbana / Rural / Mixta)", fontsize=11, fontweight="bold", color=INE_DARK)
    ax1.set_xlabel("Porcentaje (%) de Secciones del Cluster", fontsize=10)
    ax1.legend(loc="lower right", frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.3, axis="x")
    
    # Gráfica de Padrón Electoral (Lista Nominal 2024 acumulada en millones)
    ln_by_cluster = df.groupby("cluster")["ln_2024"].sum() / 1e6
    c_labels = [f"C{c}:\n{cluster_names[c]}" for c in ln_by_cluster.index]
    ax2.bar(c_labels, ln_by_cluster.values, color=CLUSTER_PALETTE, alpha=0.85)
    ax2.set_title("B) Tamaño del Padrón Electoral Representado (Millones)", fontsize=11, fontweight="bold", color=INE_DARK)
    ax2.set_ylabel("Millones de Electores (LN 2024)", fontsize=10)
    ax2.set_xticklabels(c_labels, rotation=15, ha="right", fontsize=8)
    for i, v in enumerate(ln_by_cluster.values):
        ax2.text(i, v + 0.5, f"{v:.1f} M", ha="center", fontsize=9, fontweight="bold")
    ax2.grid(True, linestyle="--", alpha=0.3, axis="y")
    
    plt.suptitle("Distribución Territorial y Dimensión del Padrón por Arquetipo", fontsize=13, fontweight="bold", color=INE_PURPLE, y=0.98)
    geo_path = os.path.join(OUTPUT_FIGURES, "07_geographic_distribution.png")
    plt.savefig(geo_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Gráfica geográfica guardada en: {geo_path}")

def generate_archetype_fichas(df: pd.DataFrame, cluster_names: dict) -> dict:
    """Genera las fichas técnicas detalladas y matrices estratégicas para ENCÍVICA."""
    logger.info("=== FASE 4.5: Fichas Técnicas Institucionales y Planes de Acción ===")
    
    total_sections = len(df)
    total_padron = df["ln_2024"].sum()
    
    fichas = {}
    
    strategy_matrix = {
        0: {
            "nombre": "Voto Femenino Consistente",
            "diagnostico": "Secciones con alta participación y la brecha de género más alta del país a favor de las mujeres (+13%). Fuerte arraigo de liderazgos comunitarios femeninos.",
            "canal": "Redes comunitarias, centros de salud, escuelas públicas y grupos organizados de mujeres.",
            "narrativa": "Reconocimiento del liderazgo cívico femenino como motor de la democracia local; empoderamiento institucional.",
            "accion_operativa": "Talleres de formación cívica con enfoque de género y capacitación para funcionarias de casilla."
        },
        1: {
            "nombre": "Pivote Presidencial Volátil",
            "diagnostico": "Alta brecha de participación entre elecciones presidenciales e intermedias (+24%). Movilización coyuntural dependiente de la polarización ejecutiva.",
            "canal": "Medios masivos digitales (TikTok, Instagram, YouTube), espacios públicos universitarios.",
            "narrativa": "La importancia del Congreso y los gobiernos locales en la vida cotidiana; 'Tu voto cuenta en cada elección'.",
            "accion_operativa": "Campañas de pedagogía legislativa y sensibilización previa a procesos electorales intermedios."
        },
        2: {
            "nombre": "Abstencionismo Estructural Urbano",
            "diagnostico": "Representa el 36% de las secciones. Participación históricamente baja (<45%), alta densidad urbana y fuerte apatía ciudadana.",
            "canal": "Centros laborales, plataformas corporativas, transporte público y difusión digital geolocalizada.",
            "narrativa": "Costo del abstencionismo e impacto de las decisiones públicas en servicios urbanos y movilidad.",
            "accion_operativa": "Instalación de casillas en nodos de alto tránsito urbano y facilidades de permiso laboral para votar."
        },
        3: {
            "nombre": "Voto Tradicional Rural y Mayor",
            "diagnostico": "Participación muy alta y estable (>72%), con predominio rural y masiva afluencia de adultos mayores de 60 años.",
            "canal": "Radio comunitaria, asambleas ejidales y perifoneo en lenguas originarias.",
            "narrativa": "Preservación de la tradición cívica y corresponsabilidad con las futuras generaciones de la comunidad.",
            "accion_operativa": "Garantizar accesibilidad universal física en casillas rurales y material bilingüe adaptado."
        },
        4: {
            "nombre": "Juventud Movilizada en Expansión",
            "diagnostico": "Secciones periurbanas y universitarias con el ratio de votación juvenil más dinámico, pero con tendencia oscilante según la agenda pública.",
            "canal": "Universidades, eventos culturales, influencers cívicos y formatos interactivos digitales.",
            "narrativa": "Incidencia de las juventudes en la agenda climática, educativa y de derechos laborales.",
            "accion_operativa": "Convenios con instituciones de educación superior para credencialización en campus y debates cívicos."
        }
    }
    
    for c in sorted(cluster_names.keys()):
        sub = df[df["cluster"] == c]
        n_sec = int(len(sub))
        pct_sec = float((n_sec / total_sections) * 100)
        padron_c = int(sub["ln_2024"].sum())
        pct_padron = float((padron_c / total_padron) * 100)
        
        ficha = {
            "id": int(c),
            "nombre": cluster_names[c],
            "secciones": n_sec,
            "pct_secciones": round(pct_sec, 2),
            "padron_2024": padron_c,
            "pct_padron": round(pct_padron, 2),
            "participacion_media": round(float(sub["participacion_media_historica"].mean()), 4),
            "brecha_presidencial": round(float(sub["brecha_presidencial_intermedia"].mean()), 4),
            "tendencia_beta": round(float(sub["tendencia_participacion_beta"].mean()), 5),
            "estabilidad": round(float(sub["estabilidad_participacion"].mean()), 2),
            "tasa_jovenes": round(float(sub["tasa_jovenes_18_29"].mean()), 4),
            "tasa_mayores": round(float(sub["tasa_adultos_mayores_60"].mean()), 4),
            "brecha_genero": round(float(sub["brecha_genero"].mean()), 4),
            "pct_urbana": round(float((sub["tiposec"] == "U").mean() * 100), 2),
            "pct_rural": round(float((sub["tiposec"] == "R").mean() * 100), 2),
            "pct_mixta": round(float((sub["tiposec"] == "M").mean() * 100), 2),
            "estrategia": strategy_matrix[c]
        }
        fichas[int(c)] = ficha
        logger.info(f"Ficha C{c} ({cluster_names[c]}): {n_sec:,} secciones ({pct_sec:.1f}%), Padrón: {padron_c/1e6:.2f}M ({pct_padron:.1f}%), Part Media: {ficha['participacion_media']*100:.1f}%")
        
    fichas_path = os.path.join(OUTPUT_DATASETS, "arquetipos_fichas.json")
    with open(fichas_path, "w", encoding="utf-8") as f:
        json.dump(fichas, f, indent=4, ensure_ascii=False)
    logger.info(f"Fichas técnicas exportadas en: {fichas_path}")
    logger.info("=== FASE 4 COMPLETADA CON ÉXITO ===")
    return fichas

def run_profiling_pipeline():
    in_path = os.path.join(OUTPUT_DATASETS, "dataset_clusters_final.parquet")
    if not os.path.exists(in_path):
        raise FileNotFoundError(f"Debe ejecutarse primero 03_clustering.py: {in_path}")
        
    df = pd.read_parquet(in_path)
    
    clustering_features = [
        "participacion_media_historica",
        "brecha_presidencial_intermedia",
        "tendencia_participacion_beta",
        "estabilidad_participacion",
        "brecha_generacional",
        "brecha_genero",
        "ratio_participacion_joven"
    ]
    
    cluster_names = {
        0: "Voto Femenino Consistente",
        1: "Pivote Presidencial Volátil",
        2: "Abstencionismo Estructural Urbano",
        3: "Voto Tradicional Rural y Mayor",
        4: "Juventud Movilizada en Expansión"
    }
    
    explain_clusters_with_rf(df, clustering_features)
    plot_radar_chart(df, cluster_names, clustering_features)
    plot_demographic_boxplots(df, cluster_names)
    plot_geographic_distribution(df, cluster_names)
    generate_archetype_fichas(df, cluster_names)

if __name__ == "__main__":
    run_profiling_pipeline()
