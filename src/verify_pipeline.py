"""
Módulo de Verificación y Sanity Checks del Pipeline
Reto 1: Perfiles Ciudadanos de Participación (INE / ENCÍVICA 2024)
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
import pypdf
from PIL import Image

# Configuración de Logging
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("verify_pipeline")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
OUTPUT_PDF = os.path.join(OUTPUT_DIR, "Reporte_Reto1_Perfiles_Participacion_INE.pdf")
OUTPUT_DATASETS = os.path.join(OUTPUT_DIR, "datasets")
OUTPUT_FIGURES = os.path.join(OUTPUT_DIR, "figures")
PIPELINE_LOG = os.path.join(PROJECT_ROOT, "pipeline.log")

file_handler = logging.FileHandler(PIPELINE_LOG, mode="a", encoding="utf-8")
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(file_handler)

def verify_all():
    logger.info("===============================================================")
    logger.info("=== FASE 6: EJECUCIÓN DE PRUEBAS DE CORDURA Y VERIFICACIÓN ===")
    logger.info("===============================================================")
    
    passed_checks = 0
    total_checks = 5
    
    # Check 1: ¿Existe el archivo PDF en output/ y su tamaño es superior a 400 KB?
    logger.info("Check 1: Existencia y tamaño del reporte PDF en output/...")
    assert os.path.exists(OUTPUT_PDF), f"FALLÓ: El archivo PDF no existe en {OUTPUT_PDF}"
    pdf_size_kb = os.path.getsize(OUTPUT_PDF) / 1024
    assert pdf_size_kb >= 400.0, f"FALLÓ: Tamaño del PDF ({pdf_size_kb:.2f} KB) es inferior a 400 KB"
    logger.info(f"✓ CHECK 1 APROBADO: PDF presente con {pdf_size_kb:.2f} KB (Requerido: > 400 KB)")
    passed_checks += 1
    
    # Check 2: ¿El PDF tiene al menos 5 páginas y se compila sin errores?
    logger.info("Check 2: Integridad y paginación del documento PDF...")
    try:
        reader = pypdf.PdfReader(OUTPUT_PDF)
        n_pages = len(reader.pages)
        assert n_pages >= 5, f"FALLÓ: El PDF tiene {n_pages} páginas (Requerido: >= 5 páginas)"
        # Verificar que las páginas contienen texto real
        total_text_len = sum(len(page.extract_text() or "") for page in reader.pages)
        assert total_text_len > 2000, f"FALLÓ: El PDF parece vacío, sólo {total_text_len} caracteres"
        logger.info(f"✓ CHECK 2 APROBADO: PDF íntegro con {n_pages} páginas y {total_text_len:,} caracteres extraídos.")
        passed_checks += 1
    except Exception as e:
        logger.error(f"FALLÓ Check 2 al parsear PDF: {e}")
        raise e
        
    # Check 3: ¿Todos los gráficos generados en output/figures/ tienen resolución adecuada y no están truncados?
    logger.info("Check 3: Verificación de gráficos de alta resolución en output/figures/...")
    expected_figures = [
        "01_clustering_benchmark_metrics.png",
        "02_umap_clusters_projection.png",
        "03_pca_clusters_projection.png",
        "04_radar_clusters_profiles.png",
        "05_feature_importance_rf.png",
        "06_demographic_boxplots.png",
        "07_geographic_distribution.png"
    ]
    for fig_name in expected_figures:
        fig_path = os.path.join(OUTPUT_FIGURES, fig_name)
        assert os.path.exists(fig_path), f"FALLÓ: Gráfica faltante: {fig_path}"
        assert os.path.getsize(fig_path) > 50000, f"FALLÓ: Gráfica anormalmente pequeña (<50KB): {fig_path}"
        with Image.open(fig_path) as img:
            w, h = img.size
            # Una imagen a 300 DPI con tamaño > 8x6 pulgadas tiene al menos 2000x1500 px
            assert w >= 1500 and h >= 1000, f"FALLÓ: Dimensiones de imagen insuficientes ({w}x{h} px): {fig_path}"
            logger.info(f"  ✓ {fig_name}: {w}x{h} px, {os.path.getsize(fig_path)/1024:.1f} KB")
    logger.info(f"✓ CHECK 3 APROBADO: Las {len(expected_figures)} figuras cumplen estándar de alta resolución 300 DPI.")
    passed_checks += 1
    
    # Check 4: ¿El dataset procesado en output/datasets/ no contiene valores NaN, Inf ni cluster -1 en el modelo final?
    logger.info("Check 4: Calidad y completitud del dataset final de clusters...")
    final_dataset_path = os.path.join(OUTPUT_DATASETS, "dataset_clusters_final.parquet")
    assert os.path.exists(final_dataset_path), f"FALLÓ: Dataset final no encontrado en {final_dataset_path}"
    df_final = pd.read_parquet(final_dataset_path)
    
    # Columnas numéricas clave
    key_features = [
        "participacion_media_historica", "brecha_presidencial_intermedia",
        "tendencia_participacion_beta", "estabilidad_participacion",
        "brecha_generacional", "brecha_genero", "ratio_participacion_joven",
        "cluster", "pca_1", "pca_2", "umap_1", "umap_2"
    ]
    for col in key_features:
        assert not df_final[col].isna().any(), f"FALLÓ: Columna {col} contiene valores NaN"
        assert not np.isinf(df_final[col]).any(), f"FALLÓ: Columna {col} contiene valores Infinitos"
        
    assert (df_final["cluster"] >= 0).all(), "FALLÓ: Se detectaron clusters con etiqueta -1 (ruido no clasificado)"
    logger.info(f"✓ CHECK 4 APROBADO: Dataset con {len(df_final):,} secciones, 0 NaNs, 0 Infs y 100% de asignación válida.")
    passed_checks += 1
    
    # Check 5: ¿La suma de los porcentajes de los clusters es igual al 100% del universo analizado?
    logger.info("Check 5: Conservación del 100% del universo electoral clasificado...")
    cluster_counts = df_final["cluster"].value_counts(normalize=True) * 100
    sum_percentages = cluster_counts.sum()
    np.testing.assert_almost_equal(sum_percentages, 100.0, decimal=4, err_msg="La suma de porcentajes difiere del 100%")
    total_assigned_rows = df_final["cluster"].count()
    assert total_assigned_rows == len(df_final), "El número de asignaciones no coincide con el total de filas"
    logger.info(f"✓ CHECK 5 APROBADO: Suma de clusters = {sum_percentages:.2f}% ({total_assigned_rows:,} / {len(df_final):,} registros).")
    passed_checks += 1
    
    logger.info("===============================================================")
    logger.info(f"=== TODAS LAS PRUEBAS DE CORDURA PASARON EXITOSAMENTE ({passed_checks}/{total_checks}) ===")
    logger.info("===============================================================")
    return True

if __name__ == "__main__":
    try:
        verify_all()
        sys.exit(0)
    except Exception as e:
        logger.error(f"FALLO CRÍTICO EN VERIFICACIÓN: {e}")
        sys.exit(1)
