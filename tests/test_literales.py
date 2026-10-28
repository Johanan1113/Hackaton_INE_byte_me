"""Cifras escritas a mano en los generadores: valores por omisión en .get(), números
dentro de cargar_cifras() y cadenas con cifras en texto visible."""
import ast
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(os.environ.get("SCRIPTS_DIR", PROJECT_ROOT / "scripts" / "auditoria"))
GENERADORES = ["07_compilar_documento.py", "08_generar_fichas.py", "10_generar_presentacion.py"]
PATRON = re.compile(r"\d+\.\d+\s*(%|pts|millones|mil\b)|≈\s*\d|\b\d{1,3}(,\d{3})+\b")
# Únicas cadenas con cifras permitidas: títulos de referencias, dato del PREP y constantes de formato.
PERMITIDAS = ("Expansión Política", "PREP cerró en", "asigna 0.0% de participación", "(100.00%)")
EXACTAS = {"0.00 pts"}


def _es_numero(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _excluidos(tree):
    """Nodos dentro de assert/raise (mensajes de error) y docstrings."""
    fuera = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Assert, ast.Raise)):
            fuera.update(id(m) for m in ast.walk(n))
        if isinstance(n, (ast.FunctionDef, ast.Module, ast.ClassDef)) and n.body:
            primero = n.body[0]
            if isinstance(primero, ast.Expr) and isinstance(primero.value, ast.Constant):
                fuera.add(id(primero.value))
    return fuera


def problemas(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fuera = _excluidos(tree)
    out = []
    for n in ast.walk(tree):
        # 1) .get(clave, valor_por_omisión) con cifra
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get" and len(n.args) == 2:
            for m in ast.walk(n.args[1]):
                if isinstance(m, ast.Constant) and (
                    (_es_numero(m.value) and m.value not in (0, 1))
                    or (isinstance(m.value, str) and re.search(r"\d", m.value))
                ):
                    out.append(f"{path.name}:{n.lineno} valor por omisión con cifra en .get(): {ast.unparse(n)[:90]}")
                    break
        # 2) números escritos dentro de cargar_cifras()
        if isinstance(n, ast.FunctionDef) and n.name == "cargar_cifras":
            for m in ast.walk(n):
                if isinstance(m, ast.Dict):
                    for v in m.values:
                        if isinstance(v, ast.Constant) and _es_numero(v.value) and v.value not in (0, 1):
                            out.append(f"{path.name}:{v.lineno} número fijo en cargar_cifras(): {v.value}")
        # 3) cadenas visibles con cifras
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in fuera:
            if n.value in EXACTAS:
                continue
            if PATRON.search(n.value) and not any(p in n.value for p in PERMITIDAS):
                out.append(f"{path.name}:{n.lineno} cadena con cifra: {n.value[:80]!r}")
    return out


def test_sin_cifras_escritas_a_mano():
    todos = []
    for nombre in GENERADORES:
        todos += problemas(SCRIPTS / nombre)
    assert not todos, f"{len(todos)} cifras escritas a mano:\n" + "\n".join(todos[:80])
