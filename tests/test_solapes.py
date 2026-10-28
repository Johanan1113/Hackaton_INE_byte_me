"""Detecta texto encimado (a nivel de carácter) y texto que cruza el borde de recuadros
en los tres PDF entregables."""
import os
from pathlib import Path
import pdfplumber
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENTREGABLES_DIR = Path(os.environ.get("ENTREGABLES_DIR", PROJECT_ROOT / "outputs" / "entregables"))
PDFS = ["Documento_Tecnico_ByteMe.pdf", "Fichas_Perfiles_ByteMe.pdf", "Presentacion_Ejecutiva_ByteMe.pdf"]


def _inter(a, b):
    x0, x1 = max(a["x0"], b["x0"]), min(a["x1"], b["x1"])
    t, bt = max(a["top"], b["top"]), min(a["bottom"], b["bottom"])
    return max(0.0, x1 - x0) * max(0.0, bt - t)


def _area(a):
    return max(1e-6, (a["x1"] - a["x0"]) * (a["bottom"] - a["top"]))


def _contexto(chars, i, n=12):
    return "".join(c["text"] for c in chars[max(0, i - n): i + n]).replace("\n", " ")


def caracteres_encimados(page, umbral=0.30):
    """Pares de caracteres visibles cuyas cajas se traslapan más del umbral."""
    cs = [c for c in page.chars if c["text"].strip()]
    idx = sorted(range(len(cs)), key=lambda i: cs[i]["x0"])
    fallas, activos = [], []
    for i in idx:
        a = cs[i]
        activos = [j for j in activos if cs[j]["x1"] > a["x0"]]
        for j in activos:
            b = cs[j]
            if _inter(a, b) > umbral * min(_area(a), _area(b)):
                fallas.append((round(a["top"]), _contexto(cs, i), _contexto(cs, j)))
        activos.append(i)
    vistos, unicas = set(), []
    for f in fallas:
        k = (f[0], f[1][:8], f[2][:8])
        if k not in vistos:
            vistos.add(k)
            unicas.append(f)
    return unicas


def palabras_que_cruzan_bordes(page):
    """Palabras parcialmente dentro de un recuadro relleno grande (tarjeta, banda o celda).
    Se ignoran las líneas de las gráficas (trazos sin relleno) y el fondo de página."""
    W, H = float(page.width), float(page.height)
    ws = page.extract_words()
    fallas = []
    for r in list(page.rects) + list(page.curves):
        if not r.get("fill"):
            continue
        w, h = r["x1"] - r["x0"], r["bottom"] - r["top"]
        if w < 200 or h < 12 or (w > 0.8 * W and h > 0.8 * H):
            continue
        for wd in ws:
            ov = _inter(wd, r)
            if 0.10 * _area(wd) < ov < 0.90 * _area(wd):
                fallas.append((round(wd["top"]), wd["text"], round(r["top"]), round(r["bottom"])))
    return fallas


def revisar(pdf_path):
    salida = []
    with pdfplumber.open(pdf_path) as pdf:
        for pn, page in enumerate(pdf.pages, 1):
            for top, ca, cb in caracteres_encimados(page):
                salida.append(f"p{pn} y≈{top}: «{ca}» encimado con «{cb}»")
            for top, txt, rt, rb in palabras_que_cruzan_bordes(page):
                salida.append(f"p{pn} y≈{top}: '{txt}' cruza el borde de un recuadro ({rt}–{rb})")
    return salida


@pytest.mark.parametrize("nombre", PDFS)
def test_sin_texto_encimado(nombre):
    f = revisar(ENTREGABLES_DIR / nombre)
    assert not f, f"{len(f)} problemas en {nombre}:\n" + "\n".join(f[:60])
