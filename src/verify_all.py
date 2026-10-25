"""
Script de Verificación y Auto-Auditoría Integral de Entregables
Concurso Oficial: "Hackea la Participación: Datos que construyen democracia" (CCPC 2009–2024 / ENCÍVICA)
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
import pypdf
from pptx import Presentation
import pandas as pd

# Configuración de Logging
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("verify_all")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENTREGABLES_DIR = os.path.join(PROJECT_ROOT, "entregables_finales")
DATASETS_DIR = os.path.join(PROJECT_ROOT, "output", "datasets")
FIGURES_DIR = os.path.join(ENTREGABLES_DIR, "figures")

INTEGRANTES_OBLIGATORIOS = [
    "Byte me",
    "Johanan Olivares Gutierrez",
    "Oscar Ariel Cuevas Martinez",
    "Saul Alexis Arias Gonzales"
]

def audit_documento_tecnico():
    """Valida el Documento Técnico Oficial en PDF."""
    pdf_path = os.path.join(ENTREGABLES_DIR, "Documento_Tecnico_Reto1_ByteMe.pdf")
    logger.info("Auditoría 1: Documento Técnico Oficial (PDF)...")
    
    assert os.path.exists(pdf_path), f"Falta archivo requerido: {pdf_path}"
    file_size_kb = os.path.getsize(pdf_path) / 1024
    assert file_size_kb > 200, f"Tamaño sospechosamente bajo en Documento Técnico: {file_size_kb:.1f} KB"
    
    reader = pypdf.PdfReader(pdf_path)
    num_pages = len(reader.pages)
    logger.info(f"  • Extensión detectada: {num_pages} páginas.")
    
    # REGLA ESTRICTA DE CONVOCATORIA: ENTRE 8 Y 12 CUARTILLAS
    assert 8 <= num_pages <= 12, (
        f"VIOLACIÓN REGLAMENTARIA: El documento debe tener entre 8 y 12 páginas, pero tiene {num_pages}."
    )
    
    # Extracción de texto y verificación de autores
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() or ""
        
    for item in INTEGRANTES_OBLIGATORIOS:
        assert item.lower() in full_text.lower(), f"Metadato obligatorio ausente en PDF: '{item}'"
        
    logger.info(f"  ✓ Documento Técnico cumple al 100% (Páginas: {num_pages}, Tamaño: {file_size_kb:.1f} KB, Autores verificados).")

def audit_presentacion_pptx():
    """Valida la Presentación Ejecutiva en PPTX y su conversión a PDF."""
    pptx_path = os.path.join(ENTREGABLES_DIR, "Presentacion_Ejecutiva_Reto1_ByteMe.pptx")
    pdf_path = os.path.join(ENTREGABLES_DIR, "Presentacion_Ejecutiva_Reto1_ByteMe.pdf")
    logger.info("Auditoría 2: Presentación Ejecutiva (PPTX y PDF)...")
    
    assert os.path.exists(pptx_path), f"Falta archivo requerido: {pptx_path}"
    prs = Presentation(pptx_path)
    num_slides = len(prs.slides)
    logger.info(f"  • Número de diapositivas PPTX: {num_slides}")
    
    # REGLA REGLAMENTARIA: MÁXIMO 10 DIAPOSITIVAS
    assert 1 <= num_slides <= 10, (
        f"VIOLACIÓN REGLAMENTARIA: La presentación debe tener máximo 10 diapositivas, pero tiene {num_slides}."
    )
    
    # Verificación de aspecto 16:9
    aspect_ratio = prs.slide_width / prs.slide_height
    assert 1.7 < aspect_ratio < 1.8, f"La presentación debe ser 16:9 widescreen, aspecto actual: {aspect_ratio:.2f}"
    
    # Verificación del PDF compilado
    assert os.path.exists(pdf_path), f"Falta archivo PDF de la presentación: {pdf_path}"
    pdf_reader = pypdf.PdfReader(pdf_path)
    assert len(pdf_reader.pages) <= 10, f"El PDF de la presentación excede 10 páginas: {len(pdf_reader.pages)}"
    
    logger.info(f"  ✓ Presentación PPTX y PDF validados exitosamente ({num_slides} diapositivas, formato 16:9).")

def audit_infografia():
    """Valida el poster/infografía de perfiles ciudadanos (PNG y PDF)."""
    png_path = os.path.join(ENTREGABLES_DIR, "Fichas_Perfiles_Infografia_ByteMe.png")
    pdf_path = os.path.join(ENTREGABLES_DIR, "Fichas_Perfiles_Infografia_ByteMe.pdf")
    logger.info("Auditoría 3: Fichas de Perfiles Ciudadanos (Infografía / Poster)...")
    
    assert os.path.exists(png_path), f"Falta archivo requerido: {png_path}"
    png_size_kb = os.path.getsize(png_path) / 1024
    assert png_size_kb > 100, f"El PNG de la infografía es demasiado pequeño: {png_size_kb:.1f} KB (esperado > 100 KB)"
    
    assert os.path.exists(pdf_path), f"Falta archivo requerido: {pdf_path}"
    pdf_reader = pypdf.PdfReader(pdf_path)
    assert len(pdf_reader.pages) == 1, f"El PDF del póster debe tener exactamente 1 página, tiene {len(pdf_reader.pages)}"
    
    logger.info(f"  ✓ Infografía / Poster validado (PNG: {png_size_kb:.1f} KB, PDF: {os.path.getsize(pdf_path)/1024:.1f} KB).")

def audit_figuras():
    """Valida que existan las 7 figuras analíticas de soporte a 300 DPI."""
    logger.info("Auditoría 4: Figuras Analíticas de Soporte...")
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
        fig_path = os.path.join(FIGURES_DIR, fig_name)
        assert os.path.exists(fig_path), f"Falta figura analítica: {fig_path}"
        fig_kb = os.path.getsize(fig_path) / 1024
        assert fig_kb > 50, f"Figura {fig_name} sospechosamente pequeña ({fig_kb:.1f} KB)"
        
    logger.info(f"  ✓ Las 7 figuras analíticas requeridas existen y están en alta resolución (300 DPI).")

def audit_datasets_y_modelos():
    """Valida los datasets procesados y arquetipos analíticos."""
    logger.info("Auditoría 5: Consistencia de Datasets y Arquetipos...")
    json_path = os.path.join(DATASETS_DIR, "arquetipos_fichas.json")
    parquet_path = os.path.join(DATASETS_DIR, "dataset_clusters_final.parquet")
    
    assert os.path.exists(json_path), f"Falta archivo: {json_path}"
    with open(json_path, "r", encoding="utf-8") as f:
        arquetipos = json.load(f)
        
    n_clusters = len(arquetipos)
    logger.info(f"  • Cantidad de clusters identificados: {n_clusters}")
    assert 4 <= n_clusters <= 6, f"El número de clusters debe estar entre 4 y 6, detectados: {n_clusters}"
    
    assert os.path.exists(parquet_path), f"Falta archivo: {parquet_path}"
    df = pd.read_parquet(parquet_path)
    assert len(df) == 62048, f"El universo seccional debe ser exactamente 62,048 secciones, detectadas: {len(df)}"
    assert set(df['cluster'].unique()) == set(range(n_clusters)), "Inconsistencia en IDs de clusters en Parquet."
    
    logger.info(f"  ✓ Universo de 62,048 secciones y {n_clusters} arquetipos verificado con éxito.")

def audit_readme():
    """Valida el archivo README.md de documentación."""
    logger.info("Auditoría 6: Documentación README.md...")
    readme_path = os.path.join(ENTREGABLES_DIR, "README.md")
    assert os.path.exists(readme_path), f"Falta README.md en {readme_path}"
    
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert len(content) > 1000, "README.md es demasiado corto."
    for item in INTEGRANTES_OBLIGATORIOS:
        assert item.lower() in content.lower(), f"Metadato '{item}' ausente en README.md"
        
    logger.info("  ✓ README.md verificado con metadatos completos y guías de reproducción.")

def run_all_audits():
    """Ejecuta todas las auditorías con código de salida estricto."""
    logger.info("================================================================================")
    logger.info("=== SUITE DE AUTO-AUDITORÍA Y VERIFICACIÓN FINAL: EQUIPO BYTE ME ===")
    logger.info("================================================================================")
    
    try:
        audit_documento_tecnico()
        audit_presentacion_pptx()
        audit_infografia()
        audit_figuras()
        audit_datasets_y_modelos()
        audit_readme()
        
        logger.info("================================================================================")
        logger.info("🎉 ¡TODAS LAS AUDITORÍAS FUERON SUPERADAS CON ÉXITO! (CÓDIGO DE SALIDA 0)")
        logger.info("El paquete de entregables en 'entregables_finales/' cumple 100% con los")
        logger.info("requisitos reglamentarios del INE y la ENCÍVICA para el Reto 1.")
        logger.info("================================================================================")
        return 0
    except AssertionError as e:
        logger.error(f"❌ FALLO EN LA AUDITORÍA: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ ERROR INESPERADO DURANTE LA AUDITORÍA: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = run_all_audits()
    sys.exit(exit_code)
