#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Maestro de Reproducibilidad Integral (run_all.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

Ejecuta secuencialmente todo el pipeline de auditoría, modelado (k=4),
exportación de tablas, generación de figuras a 300 DPI, compilación del
documento técnico (PDF), generación de fichas infográficas (PDF/PNG),
validación de consistencia y presentación ejecutiva (PPTX/PDF).
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

STEPS = [
    ("Fase 0.1: Inventario del repositorio y esquemas", "scripts/auditoria/00_inventario.py"),
    ("Fase 0.2: Reproducción de línea base del modelo", "scripts/auditoria/01_baseline_reproduccion.py"),
    ("Fase 1: Verificación profunda de datos CCPC 2009–2024", "scripts/auditoria/02_verificacion_datos.py"),
    ("Fase 2: Robustez del modelo y clustering k=4", "scripts/auditoria/03_robustez_modelo.py"),
    ("Fase 3: Perfiles, estrategias y metricas_finales.json", "scripts/auditoria/04_perfiles_y_nombres.py"),
    ("Fase 4: Exportación de tablas oficiales", "scripts/auditoria/05_exportar_tablas.py"),
    ("Fase 4.1: Análisis de auditoría externa y tablas complementarias", "scripts/auditoria/11_analisis_auditoria.py"),
    ("Fase 5: Generación de figuras a 300 DPI", "scripts/auditoria/06_generar_figuras.py"),
    ("Fase 6: Compilación del Documento Técnico PDF", "scripts/auditoria/07_compilar_documento.py"),
    ("Fase 7: Generación de Fichas de Perfiles (PDF/PNG)", "scripts/auditoria/08_generar_fichas.py"),
    ("Fase 8: Validación automatizada de consistencia y cifras", "scripts/auditoria/09_validacion_consistencia.py"),
    ("Fase 9: Generación de Presentación Ejecutiva (PPTX/PDF)", "scripts/auditoria/10_generar_presentacion.py"),
]


def main() -> None:
    t0 = time.time()
    for title, rel_script in STEPS:
        print(f"\n{'=' * 78}\n>>> {title} ({rel_script})\n{'=' * 78}")
        script_path = PROJECT_ROOT / rel_script
        subprocess.run([sys.executable, str(script_path)], cwd=str(PROJECT_ROOT), check=True)

    elapsed = time.time() - t0
    print(f"\n{'=' * 78}\nPIPELINE COMPLETO FINALIZADO CON ÉXITO EN {elapsed:.1f} SEGUNDOS\n{'=' * 78}")


if __name__ == "__main__":
    main()
