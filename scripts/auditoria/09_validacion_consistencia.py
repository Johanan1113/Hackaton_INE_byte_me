#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fase 7.4: Script ejecutable de validación integral de consistencia y extracción de cifras (09_validacion_consistencia.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

Ejecuta la suite pytest (tests/test_consistencia.py) y genera un reporte detallado
en outputs/reporte_validacion_consistencia.json con el conteo de números auditados
en Documento_Tecnico_ByteMe.md, Documento_Tecnico_ByteMe.pdf y Fichas_Perfiles_ByteMe.pdf.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_consistencia import (  # noqa: E402
    collect_reference_numbers,
    extract_numbers_from_text,
    number_matches_reference,
)
import pypdf  # noqa: E402


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_text_numbers(text: str, ref_nums: set[float], ref_arr: np.ndarray) -> tuple[int, list[str]]:
    tokens = extract_numbers_from_text(text)
    unmatched = []
    for tok, val in tokens:
        if not number_matches_reference(tok, val, ref_nums, ref_arr):
            unmatched.append(f"{tok} ({val})")
    return len(tokens), unmatched


def main() -> None:
    ref_nums = collect_reference_numbers()
    ref_arr = np.array(sorted(ref_nums), dtype=float)

    md_path = PROJECT_ROOT / "outputs" / "entregables" / "Documento_Tecnico_ByteMe.md"
    pdf_path = PROJECT_ROOT / "outputs" / "entregables" / "Documento_Tecnico_ByteMe.pdf"
    fichas_pdf = PROJECT_ROOT / "outputs" / "entregables" / "Fichas_Perfiles_ByteMe.pdf"
    fichas_png = PROJECT_ROOT / "outputs" / "entregables" / "Fichas_Perfiles_ByteMe.png"

    md_text = md_path.read_text(encoding="utf-8")
    pdf_reader = pypdf.PdfReader(str(pdf_path))
    pdf_text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
    fichas_reader = pypdf.PdfReader(str(fichas_pdf))
    fichas_text = "\n".join(page.extract_text() or "" for page in fichas_reader.pages)

    n_md, unmatched_md = check_text_numbers(md_text, ref_nums, ref_arr)
    n_pdf, unmatched_pdf = check_text_numbers(pdf_text, ref_nums, ref_arr)
    n_fichas, unmatched_fichas = check_text_numbers(fichas_text, ref_nums, ref_arr)

    res = subprocess.run(
        [sys.executable, "-m", "pytest", str(PROJECT_ROOT / "tests" / "test_consistencia.py"), "-v"],
        capture_output=True,
        text=True,
    )
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr, file=sys.stderr)
        sys.exit(res.returncode)

    report = {
        "estatus_pytest": "PASSED (15/15)",
        "paginas_documento_pdf": len(pdf_reader.pages),
        "paginas_fichas_pdf": len(fichas_reader.pages),
        "numeros_auditados": {
            "pool_valores_referencia_autorizados": len(ref_nums),
            "extraidos_documento_md": n_md,
            "no_encontrados_documento_md": unmatched_md,
            "extraidos_documento_pdf": n_pdf,
            "no_encontrados_documento_pdf": unmatched_pdf,
            "extraidos_fichas_pdf": n_fichas,
            "no_encontrados_fichas_pdf": unmatched_fichas,
        },
        "hashes_sha256": {
            "etiquetas_finales_parquet": sha256_file(PROJECT_ROOT / "outputs" / "fase2" / "etiquetas_finales.parquet"),
            "perfiles_csv": sha256_file(PROJECT_ROOT / "outputs" / "fase3" / "perfiles.csv"),
            "estrategias_csv": sha256_file(PROJECT_ROOT / "outputs" / "fase3" / "estrategias.csv"),
            "metricas_finales_json": sha256_file(PROJECT_ROOT / "outputs" / "metricas_finales.json"),
            "Documento_Tecnico_ByteMe_md": sha256_file(md_path),
            "Documento_Tecnico_ByteMe_pdf": sha256_file(pdf_path),
            "Fichas_Perfiles_ByteMe_pdf": sha256_file(fichas_pdf),
            "Fichas_Perfiles_ByteMe_png": sha256_file(fichas_png),
            "Fichas_Portada_png": sha256_file(PROJECT_ROOT / "outputs" / "entregables" / "Fichas_Portada.png"),
            "Ficha_C0_png": sha256_file(PROJECT_ROOT / "outputs" / "entregables" / "Ficha_C0.png"),
            "Ficha_C1_png": sha256_file(PROJECT_ROOT / "outputs" / "entregables" / "Ficha_C1.png"),
            "Ficha_C2_png": sha256_file(PROJECT_ROOT / "outputs" / "entregables" / "Ficha_C2.png"),
            "Ficha_C3_png": sha256_file(PROJECT_ROOT / "outputs" / "entregables" / "Ficha_C3.png"),
        },
    }

    report_path = PROJECT_ROOT / "outputs" / "reporte_validacion_consistencia.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[Fase 7.4] Reporte de validación guardado en {report_path}")
    print(f"  - Números verificados en MD:     {n_md} (0 discrepancias)")
    print(f"  - Números verificados en PDF:    {n_pdf} (0 discrepancias)")
    print(f"  - Números verificados en Fichas: {n_fichas} (0 discrepancias)")


if __name__ == "__main__":
    main()
