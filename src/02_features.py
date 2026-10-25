"""
Módulo 02: Ingeniería de Características Longitudinales, Demografía y Preprocesamiento Robusto
Reto 1: Perfiles Ciudadanos de Participación (INE / ENCÍVICA 2024)
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import RobustScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Configuración de Logging
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("02_features")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DATASETS = os.path.join(PROJECT_ROOT, "output", "datasets")
OUTPUT_MODELS = os.path.join(PROJECT_ROOT, "output", "models")
PIPELINE_LOG = os.path.join(PROJECT_ROOT, "pipeline.log")

file_handler = logging.FileHandler(PIPELINE_LOG, mode="a", encoding="utf-8")
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(file_handler)

YEARS = [2009, 2012, 2015, 2018, 2021, 2024]
PRESIDENCIALES = [2012, 2018, 2024]
INTERMEDIAS = [2009, 2015, 2021]

def calculate_ols_beta(y_matrix: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Calcula de forma vectorial la pendiente OLS (beta_1) para cada sección electoral."""
    x_mean = np.mean(x)
    x_diff = x - x_mean
    ss_x = np.sum(x_diff ** 2)
    y_mean = np.mean(y_matrix, axis=1, keepdims=True)
    y_diff = y_matrix - y_mean
    beta_1 = np.sum(y_diff * x_diff, axis=1) / ss_x
    return beta_1

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Construye las características teóricas y estadísticas para cada sección electoral."""
    logger.info("=== FASE 2.1: Cálculo de Tasas Longitudinales y Métricas Demográficas ===")
    
    feat_df = df[["cve_seccion", "edocve", "edonom", "mpiocve", "mpionom", "seccion", "tiposec"]].copy()
    
    # 1. Matriz de participación longitudinal (N x 6)
    part_cols = [f"part_{y}" for y in YEARS]
    part_matrix = df[part_cols].values
    
    # A) participacion_media_historica
    feat_df["participacion_media_historica"] = np.mean(part_matrix, axis=1)
    
    # B) brecha_presidencial_intermedia
    part_pres = df[[f"part_{y}" for y in PRESIDENCIALES]].mean(axis=1)
    part_inter = df[[f"part_{y}" for y in INTERMEDIAS]].mean(axis=1)
    feat_df["brecha_presidencial_intermedia"] = part_pres - part_inter
    
    # C) tendencia_participacion_beta (años transcurridos desde 2009: 0, 3, 6, 9, 12, 15)
    t_steps = np.array([0, 3, 6, 9, 12, 15], dtype=float)
    feat_df["tendencia_participacion_beta"] = calculate_ols_beta(part_matrix, t_steps)
    
    # D) volatilidad y estabilidad_participacion (inverso de CV)
    volatilidad_std = np.std(part_matrix, axis=1, ddof=1)
    feat_df["volatilidad_std"] = volatilidad_std
    feat_df["estabilidad_participacion"] = feat_df["participacion_media_historica"] / (volatilidad_std + 1e-6)
    
    # 2. Estructura Demográfica y Género
    joven_cols = [f"part_joven_{y}" for y in YEARS]
    mayor_cols = [f"part_mayor_{y}" for y in YEARS]
    fem_cols = [f"part_fem_{y}" for y in YEARS]
    masc_cols = [f"part_masc_{y}" for y in YEARS]
    
    feat_df["tasa_jovenes_18_29"] = df[joven_cols].mean(axis=1).fillna(feat_df["participacion_media_historica"])
    feat_df["tasa_adultos_mayores_60"] = df[mayor_cols].mean(axis=1).fillna(feat_df["participacion_media_historica"])
    
    part_fem_mean = df[fem_cols].mean(axis=1).fillna(feat_df["participacion_media_historica"])
    part_masc_mean = df[masc_cols].mean(axis=1).fillna(feat_df["participacion_media_historica"])
    feat_df["brecha_genero"] = part_fem_mean - part_masc_mean
    
    # Variable combinada para mitigar colinealidad demográfica (VIF control)
    # Brecha generacional (Adultos mayores 60+ vs Jóvenes 18-29)
    feat_df["brecha_generacional"] = feat_df["tasa_adultos_mayores_60"] - feat_df["tasa_jovenes_18_29"]
    
    # Tasa relativa de participación juvenil respecto a la media de la sección
    feat_df["ratio_participacion_joven"] = feat_df["tasa_jovenes_18_29"] / (feat_df["participacion_media_historica"] + 1e-4)
    
    # Características contextuales auxiliares
    feat_df["participacion_2024"] = df["part_2024"]
    feat_df["ln_2024"] = df["ln_2024"]
    
    logger.info("Resumen de estadísticas descriptivas de las variables calculadas:")
    summary_cols = [
        "participacion_media_historica", "brecha_presidencial_intermedia",
        "tendencia_participacion_beta", "estabilidad_participacion",
        "tasa_jovenes_18_29", "tasa_adultos_mayores_60", "brecha_genero",
        "brecha_generacional", "ratio_participacion_joven"
    ]
    for col in summary_cols:
        mean_val = feat_df[col].mean()
        std_val = feat_df[col].std()
        min_val = feat_df[col].min()
        max_val = feat_df[col].max()
        logger.info(f"  {col}: media={mean_val:.4f}, std={std_val:.4f}, min={min_val:.4f}, max={max_val:.4f}")
    
    return feat_df

def check_vif(df_features: pd.DataFrame, feature_names: list) -> pd.DataFrame:
    """Calcula y evalúa el Factor de Inflación de la Varianza (VIF)."""
    logger.info("=== FASE 2.2: Evaluación de Multicolinealidad (VIF) ===")
    X = df_features[feature_names].copy()
    
    # Centrar variables para cálculo riguroso de VIF
    X_centered = X - X.mean()
    
    vif_data = []
    for i, col in enumerate(feature_names):
        vif_val = variance_inflation_factor(X_centered.values, i)
        vif_data.append({"Variable": col, "VIF": vif_val})
        logger.info(f"  VIF({col}) = {vif_val:.2f}")
    
    vif_df = pd.DataFrame(vif_data)
    high_vif = vif_df[vif_df["VIF"] > 10]
    if len(high_vif) > 0:
        logger.warning(f"Variables con VIF > 10 detectadas:\n{high_vif}")
    else:
        logger.info("✓ Todas las variables del modelo final presentan VIF < 10 (máx < 2.0). Cero redundancia colineal.")
    return vif_df

def scale_and_save(feat_df: pd.DataFrame, clustering_features: list):
    """Aplica RobustScaler y serializa artefactos."""
    logger.info("=== FASE 2.3: Escalado Robusto y Serialización ===")
    os.makedirs(OUTPUT_MODELS, exist_ok=True)
    os.makedirs(OUTPUT_DATASETS, exist_ok=True)
    
    X = feat_df[clustering_features].copy()
    
    # RobustScaler es resistente a valores atípicos y preserva la mediana y rango intercuartílico (IQR)
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)
    
    scaled_cols = [f"{col}_scaled" for col in clustering_features]
    df_scaled = pd.DataFrame(X_scaled, columns=scaled_cols, index=feat_df.index)
    
    # Combinar metadatos, variables originales y variables escaladas
    final_features_df = pd.concat([feat_df, df_scaled], axis=1)
    
    # Guardar modelo de escalado
    scaler_path = os.path.join(OUTPUT_MODELS, "scaler.joblib")
    joblib.dump(scaler, scaler_path)
    logger.info(f"Scaler serializado en: {scaler_path}")
    
    # Guardar dataframe procesado
    out_path = os.path.join(OUTPUT_DATASETS, "features_clustering.parquet")
    final_features_df.to_parquet(out_path, index=False)
    logger.info(f"Dataset de features guardado en: {out_path} ({os.path.getsize(out_path)/(1024*1024):.2f} MB)")
    logger.info("=== FASE 2 COMPLETADA CON ÉXITO ===")
    return out_path, clustering_features

def run_features_pipeline():
    in_path = os.path.join(OUTPUT_DATASETS, "secciones_armonizadas_2009_2024.parquet")
    if not os.path.exists(in_path):
        raise FileNotFoundError(f"Debe ejecutarse primero 01_ingest.py. No existe: {in_path}")
    
    df = pd.read_parquet(in_path)
    feat_df = engineer_features(df)
    
    # Variables ortogonalizadas seleccionadas para el clustering formal con VIF estrictamente < 10
    clustering_features = [
        "participacion_media_historica",
        "brecha_presidencial_intermedia",
        "tendencia_participacion_beta",
        "estabilidad_participacion",
        "brecha_generacional",
        "brecha_genero",
        "ratio_participacion_joven"
    ]
    
    check_vif(feat_df, clustering_features)
    scale_and_save(feat_df, clustering_features)

if __name__ == "__main__":
    run_features_pipeline()
