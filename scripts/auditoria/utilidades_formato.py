#!/usr/bin/env bash
# -*- coding: utf-8 -*-
"""
Módulo de Utilidades de Formato y Redondeo Unificado
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")
Ubicación: scripts/auditoria/utilidades_formato.py

Implementa la política única de redondeo aritmético simétrico (ROUND_HALF_UP)
mediante la biblioteca Decimal de Python, garantizando consistencia absoluta
en todos los entregables impresos y reportados:
- 60.85 -> 60.9
- 11.15 -> 11.2
- 47.75 -> 47.8
- 60.55 -> 60.6
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Union


def redondear(x: Any, nd: int = 1) -> Union[float, int, None]:
    """
    Aplica redondeo aritmético ROUND_HALF_UP con Decimal a x con nd decimales.
    Soporta float, int, str, Decimal o None.
    Si nd == 0, devuelve int.
    Si nd > 0, devuelve float.
    Si x es None o no es numérico convertible, lo devuelve tal cual.
    """
    if x is None:
        return None
    try:
        # Convertir a string para evitar inexactitudes binarias de float
        d = Decimal(str(x))
    except Exception:
        return x

    if nd == 0:
        return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    else:
        fmt = "0." + "0" * nd
        return float(d.quantize(Decimal(fmt), rounding=ROUND_HALF_UP))


def formatear(x: Any, nd: int = 1, coma_miles: bool = False) -> str:
    """
    Redondea x con ROUND_HALF_UP y formatea como cadena con exactamente nd decimales.
    Si coma_miles es True, incluye separador de miles con comas.
    """
    r = redondear(x, nd)
    if r is None:
        return ""
    if nd == 0:
        if coma_miles:
            return f"{r:,}"
        return f"{r}"
    else:
        if coma_miles:
            return f"{r:,.{nd}f}"
        return f"{r:.{nd}f}"


def formatear_pct(x: Any, nd: int = 1) -> str:
    """
    Redondea x y devuelve cadena con sufijo '%'.
    """
    return f"{formatear(x, nd)}%"
