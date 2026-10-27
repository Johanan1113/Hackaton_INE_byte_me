"""
Orquestador Maestro del Pipeline de Ciencia de Datos, MLOps y Entregables Finales
Concurso Oficial: "Hackea la Participación: Datos que construyen democracia" (CCPC 2009–2024 / ENCÍVICA)
Reto 1: Perfiles ciudadanos de participación
Equipo: Byte me
Integrantes:
  - Johanan Olivares Gutiérrez (Representante)
  - Oscar Ariel Cuevas Martínez
  - Saúl Alexis Arias González
"""

import os
import sys
import time
import logging
import argparse
import subprocess

# Configuración de Logging
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("main_orchestrator")

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
PIPELINE_LOG = os.path.join(PROJECT_ROOT, "pipeline.log")
ENTREGABLES_DIR = os.path.join(PROJECT_ROOT, "entregables_finales")

file_handler = logging.FileHandler(PIPELINE_LOG, mode="a", encoding="utf-8")
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(file_handler)

ALL_MODULES = [
    ("src/01_ingest.py", "FASE 1: Ingesta In-Memory DuckDB y Armonización Cartográfica (62,048 secciones)"),
    ("src/02_features.py", "FASE 2: Ingeniería de Características Longitudinales, Demografía y VIF"),
    ("src/03_clustering.py", "FASE 3: Benchmarking de Clustering (K-Means/GMM/HDBSCAN), PCA y UMAP"),
    ("src/03_clustering_refinement.py", "FASE 3b: Enriquecimiento Semántico y Consolidación de 5 Arquetipos"),
    ("src/04_profiling.py", "FASE 4: Explicabilidad (Random Forest/ANOVA) y Generación de 7 Figuras 300 DPI"),
    ("src/05_report_pdf.py", "FASE 5: Compilación del Documento Técnico Oficial (Exactamente 10 Páginas)"),
    ("src/06_presentation.py", "FASE 6: Generación de la Presentación Ejecutiva en PPTX (10 Slides) y PDF"),
    ("src/07_infographic.py", "FASE 7: Generación de Infografía / Poster Técnico a 300 DPI (PNG y PDF)"),
    ("src/verify_all.py", "FASE 8: Suite de Auto-Auditoría Integral y Verificación Reglamentaria")
]

REPORTS_ONLY_MODULES = [
    ("src/05_report_pdf.py", "FASE 5: Compilación del Documento Técnico Oficial (Exactamente 10 Páginas)"),
    ("src/06_presentation.py", "FASE 6: Generación de la Presentación Ejecutiva en PPTX (10 Slides) y PDF"),
    ("src/07_infographic.py", "FASE 7: Generación de Infografía / Poster Técnico a 300 DPI (PNG y PDF)"),
    ("src/verify_all.py", "FASE 8: Suite de Auto-Auditoría Integral y Verificación Reglamentaria")
]

def run_pipeline(reports_only=False):
    """Ejecuta el pipeline de forma secuencial y audita cada módulo."""
    logger.info("================================================================================")
    logger.info("=== INICIANDO PIPELINE MAESTRO: RETO 1 PERFILES DE PARTICIPACIÓN (INE)       ===")
    logger.info("=== EQUIPO: BYTE ME  |  CONCURSO CCPC 2009–2024 / ENCÍVICA                   ===")
    logger.info("================================================================================")
    
    total_start_time = time.time()
    python_bin = sys.executable
    
    modules_to_run = REPORTS_ONLY_MODULES if reports_only else ALL_MODULES
    
    for script_rel, desc in modules_to_run:
        script_path = os.path.join(PROJECT_ROOT, script_rel)
        logger.info(f"\n>>> INICIANDO: {desc} ({script_rel})")
        t0 = time.time()
        
        proc = subprocess.run([python_bin, script_path], cwd=PROJECT_ROOT, capture_output=True, text=True)
        elapsed = time.time() - t0
        
        if proc.returncode != 0:
            logger.error(f"❌ ERROR CRÍTICO EN {script_rel} (código {proc.returncode}):\n{proc.stderr}")
            print(f"\n❌ Error en {script_rel}:\n{proc.stderr}")
            sys.exit(proc.returncode)
            
        logger.info(f"✓ COMPLETADO EXITOSAMENTE: {desc} en {elapsed:.2f}s")
        if proc.stdout:
            lines = [l for l in proc.stdout.splitlines() if l.strip()]
            for line in lines[-4:]:
                logger.info(f"   [out] {line}")
                
    total_elapsed = time.time() - total_start_time
    logger.info("================================================================================")
    logger.info(f"=== PIPELINE COMPLETO EJECUTADO CON ÉXITO EN {total_elapsed:.2f}s ({total_elapsed/60:.2f} MIN) ===")
    logger.info("================================================================================")
    
    print("\n" + "="*80)
    print("🎉 PIPELINE Y AUDITORÍA FINALIZADOS CON ÉXITO (CÓDIGO DE SALIDA 0)")
    print("="*80)
    print("Directorio oficial de entregables: 'entregables_finales/'")
    print("  1. Documento Técnico Oficial (PDF, 10 páginas):")
    print(f"     -> {os.path.join(ENTREGABLES_DIR, 'Documento_Tecnico_Reto1_ByteMe.pdf')}")
    print("  2. Presentación Ejecutiva (PPTX 16:9, 10 diapositivas):")
    print(f"     -> {os.path.join(ENTREGABLES_DIR, 'Presentacion_Ejecutiva_Reto1_ByteMe.pptx')}")
    print("  3. Presentación Ejecutiva (PDF compilado):")
    print(f"     -> {os.path.join(ENTREGABLES_DIR, 'Presentacion_Ejecutiva_Reto1_ByteMe.pdf')}")
    print("  4. Fichas de Perfiles / Infografía (Poster 300 DPI PNG & PDF):")
    print(f"     -> {os.path.join(ENTREGABLES_DIR, 'Fichas_Perfiles_Infografia_ByteMe.png')}")
    print(f"     -> {os.path.join(ENTREGABLES_DIR, 'Fichas_Perfiles_Infografia_ByteMe.pdf')}")
    print("  5. Figuras Analíticas de Soporte (300 DPI):")
    print(f"     -> {os.path.join(ENTREGABLES_DIR, 'figures')}")
    print("  6. Documentación Técnica y Reproducción:")
    print(f"     -> {os.path.join(ENTREGABLES_DIR, 'README.md')}")
    print("="*80 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestador Maestro del Reto 1 (INE/ENCÍVICA) - Equipo Byte me")
    parser.add_argument("--reports-only", action="store_true", help="Compilar únicamente los reportes finales sin re-entrenar modelos")
    args = parser.parse_args()
    
    run_pipeline(reports_only=args.reports_only)
