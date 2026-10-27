"""Detecta texto encimado o cortado por recuadros de color en los tres PDF entregables."""
import os
from pathlib import Path
import pdfplumber
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENTREGABLES_DIR = Path(os.environ.get("ENTREGABLES_DIR", PROJECT_ROOT / "outputs" / "entregables"))
PDFS = [
    "Documento_Tecnico_ByteMe.pdf",
    "Fichas_Perfiles_ByteMe.pdf",
    "Presentacion_Ejecutiva_ByteMe.pdf",
]


def _inter(a, b):
    x0, x1 = max(a["x0"], b["x0"]), min(a["x1"], b["x1"])
    t, bt = max(a["top"], b["top"]), min(a["bottom"], b["bottom"])
    return max(0.0, x1 - x0) * max(0.0, bt - t)


def _area(a):
    return max(1e-6, (a["x1"] - a["x0"]) * (a["bottom"] - a["top"]))


def _es_claro(c):
    if c is None:
        return True
    if isinstance(c, (int, float)):
        return c > 0.85
    c = list(c)
    if len(c) == 1:
        return c[0] > 0.85
    if len(c) == 3:
        return min(c) > 0.85
    if len(c) == 4:
        return max(c) < 0.15
    return False


def solapes(pdf_path, umbral=0.15):
    fallas = []
    with pdfplumber.open(pdf_path) as pdf:
        for pn, page in enumerate(pdf.pages, 1):
            W, H = float(page.width), float(page.height)
            ws = page.extract_words()
            for i in range(len(ws)):
                for j in range(i + 1, len(ws)):
                    a, b = ws[i], ws[j]
                    if abs(a["top"] - b["top"]) < 0.5:
                        continue
                    if _inter(a, b) > umbral * min(_area(a), _area(b)):
                        fallas.append(f"p{pn}: '{a['text']}' encimado con '{b['text']}'")
            for r in list(page.rects) + list(page.curves):
                if not r.get("fill") or _es_claro(r.get("non_stroking_color")):
                    continue
                w, h = r["x1"] - r["x0"], r["bottom"] - r["top"]
                if w < 200 or h < 12 or (w > 0.8 * W and h > 0.8 * H):
                    continue
                for wd in ws:
                    ov = _inter(wd, r)
                    if 0.10 * _area(wd) < ov < 0.90 * _area(wd):
                        fallas.append(f"p{pn}: '{wd['text']}' cortado por recuadro de color")
    return fallas


@pytest.mark.parametrize("nombre", PDFS)
def test_sin_texto_encimado(nombre):
    f = solapes(ENTREGABLES_DIR / nombre)
    assert not f, f"{len(f)} solapes en {nombre}:\n" + "\n".join(f[:40])
