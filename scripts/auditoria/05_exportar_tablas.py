#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fase 5: Exportación de Tablas Oficiales desde la Fuente Única de Verdad (05_exportar_tablas.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

Lee outputs/metricas_finales.json y genera todas las tablas CSV en outputs/tablas/
para alimentar de forma 100% programática el documento técnico, las fichas infográficas
y las pruebas automatizadas de consistencia (tests/test_consistencia.py).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
METRICAS_PATH = PROJECT_ROOT / "outputs" / "metricas_finales.json"
OUT_TABLAS = PROJECT_ROOT / "outputs" / "tablas"
OUT_TABLAS.mkdir(parents=True, exist_ok=True)


def main() -> None:
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))

    # 1. Cascada de filtrado del universo
    df_cascada = pd.DataFrame(data["universo_y_cobertura"]["cascada_filtrado"])
    df_cascada.to_csv(OUT_TABLAS / "tabla_01_cascada_universo.csv", index=False)

    # 2. Serie nacional 2009-2024
    df_serie = pd.DataFrame(data["serie_nacional_2009_2024"])
    df_serie.to_csv(OUT_TABLAS / "tabla_02_serie_nacional_2009_2024.csv", index=False)

    # 3. Secciones incluidas vs excluidas en 2024
    df_inc_exc = pd.DataFrame(data["incluidas_vs_excluidas_2024"])
    df_inc_exc.to_csv(OUT_TABLAS / "tabla_03_incluidas_vs_excluidas_2024.csv", index=False)

    # 4. Benchmark de modelos (K-Means++, GMM, HDBSCAN)
    df_bench = pd.DataFrame(data["benchmark_modelos"])
    df_bench.to_csv(OUT_TABLAS / "tabla_04_benchmark_modelos.csv", index=False)

    # 5. Pruebas de robustez (estabilidad, VIF, ventanas temporales)
    df_est = pd.DataFrame(data["estabilidad_comparacion"])
    df_est.to_csv(OUT_TABLAS / "tabla_05a_estabilidad_comparacion.csv", index=False)
    df_vif = pd.DataFrame(data["vif_colinealidad"])
    df_vif.to_csv(OUT_TABLAS / "tabla_05b_vif_colinealidad.csv", index=False)
    df_win = pd.DataFrame(data["ventanas_temporales"])
    df_win.to_csv(OUT_TABLAS / "tabla_05c_ventanas_temporales.csv", index=False)

    # 6. Perfiles k=4 con fila de Media Nacional Panel B
    perfiles = data["perfiles"]
    pan_b = data["resumen_panel_b"]
    rows_p = []
    for p in perfiles:
        rows_p.append({
            "codigo_cluster": p["codigo_cluster"],
            "nombre_perfil": p["nombre_propuesto"],
            "n_secciones": p["n_secciones"],
            "pct_secciones_panel": p["pct_secciones_panel"],
            "pct_secciones_2024_total": p["pct_secciones_2024_total"],
            "ln_2024": p["ln_2024"],
            "pct_ln_panel": p["pct_ln_panel"],
            "pct_ln_2024_total": p["pct_ln_2024_total"],
            "n_municipios": p["n_municipios_con_presencia"],
            "part_media_pct": round(p["participacion_media_historica_original"] * 100, 2),
            "part_media_z": round(p["participacion_media_historica_zscore"], 2),
            "brecha_pres_inter_pts": round(p["brecha_presidencial_intermedia_original"] * 100, 2),
            "brecha_pres_inter_z": round(p["brecha_presidencial_intermedia_zscore"], 2),
            "tendencia_beta_pts_anio": round(p["tendencia_participacion_beta_original"] * 100, 2),
            "tendencia_beta_z": round(p["tendencia_participacion_beta_zscore"], 2),
            "estabilidad_log1p": round(p["estabilidad_participacion_original"], 4),
            "estabilidad_z": round(p["estabilidad_participacion_zscore"], 2),
            "brecha_gen_pts": round(p["brecha_generacional_original"] * 100, 2),
            "brecha_gen_z": round(p["brecha_generacional_zscore"], 2),
            "brecha_genero_pts": round(p["brecha_genero_original"] * 100, 2),
            "brecha_genero_z": round(p["brecha_genero_zscore"], 2),
            "ratio_joven": round(p["ratio_participacion_joven_original"], 4),
            "ratio_joven_z": round(p["ratio_participacion_joven_zscore"], 2),
            "pct_urbana_sec": round(p["pct_secciones_urbanas"], 1),
            "pct_rural_sec": round(p["pct_secciones_rurales"], 1),
            "pct_mixta_sec": round(p["pct_secciones_mixtas"], 1),
            "pct_urbana_ln": round(p["pct_ln_urbana"], 1),
            "pct_rural_ln": round(p["pct_ln_rural"], 1),
            "pct_mixta_ln": round(p["pct_ln_mixta"], 1),
        })

    rows_p.append({
        "codigo_cluster": "Panel_B",
        "nombre_perfil": "Media Nacional Panel Principal (Opción B)",
        "n_secciones": pan_b["n_secciones"],
        "pct_secciones_panel": 100.00,
        "pct_secciones_2024_total": data["universo_y_cobertura"]["panel_principal_pct_secciones_2024"],
        "ln_2024": pan_b["ln_2024"],
        "pct_ln_panel": 100.00,
        "pct_ln_2024_total": data["universo_y_cobertura"]["panel_principal_pct_ln_2024"],
        "n_municipios": data["universo_y_cobertura"]["panel_principal_municipios"],
        "part_media_pct": round(pan_b["participacion_media_historica_media"] * 100, 2),
        "part_media_z": 0.00,
        "brecha_pres_inter_pts": round(pan_b["brecha_presidencial_intermedia_media"] * 100, 2),
        "brecha_pres_inter_z": 0.00,
        "tendencia_beta_pts_anio": round(pan_b["tendencia_participacion_beta_media"] * 100, 2),
        "tendencia_beta_z": 0.00,
        "estabilidad_log1p": round(pan_b["estabilidad_participacion_media"], 4),
        "estabilidad_z": 0.00,
        "brecha_gen_pts": round(pan_b["brecha_generacional_media"] * 100, 2),
        "brecha_gen_z": 0.00,
        "brecha_genero_pts": round(pan_b["brecha_genero_media"] * 100, 2),
        "brecha_genero_z": 0.00,
        "ratio_joven": round(pan_b["ratio_participacion_joven_media"], 4),
        "ratio_joven_z": 0.00,
        "pct_urbana_sec": pan_b["pct_secciones_urbanas_1d"],
        "pct_rural_sec": pan_b["pct_secciones_rurales_1d"],
        "pct_mixta_sec": pan_b["pct_secciones_mixtas_1d"],
        "pct_urbana_ln": round(pan_b["pct_ln_urbana"], 1),
        "pct_rural_ln": round(pan_b["pct_ln_rural"], 1),
        "pct_mixta_ln": round(pan_b["pct_ln_mixta"], 1),
    })
    df_p_res = pd.DataFrame(rows_p)
    df_p_res.to_csv(OUT_TABLAS / "tabla_06_perfiles_k4_resumen.csv", index=False)

    # 7. Series 2009-2024 y tasas demográficas por perfil (incluyendo Media Nacional Panel B)
    rows_sd = []
    for p in perfiles:
        rows_sd.append({
            "codigo_cluster": p["codigo_cluster"],
            "nombre_perfil": p["nombre_propuesto"],
            "p_2009_pond_pct": round(p["p_2009_ponderada"] * 100, 2),
            "p_2012_pond_pct": round(p["p_2012_ponderada"] * 100, 2),
            "p_2015_pond_pct": round(p["p_2015_ponderada"] * 100, 2),
            "p_2018_pond_pct": round(p["p_2018_ponderada"] * 100, 2),
            "p_2021_pond_pct": round(p["p_2021_ponderada"] * 100, 2),
            "p_2024_pond_pct": round(p["p_2024_ponderada"] * 100, 2),
            "p_2009_simple_pct": round(p["p_2009_simple"] * 100, 2),
            "p_2012_simple_pct": round(p["p_2012_simple"] * 100, 2),
            "p_2015_simple_pct": round(p["p_2015_simple"] * 100, 2),
            "p_2018_simple_pct": round(p["p_2018_simple"] * 100, 2),
            "p_2021_simple_pct": round(p["p_2021_simple"] * 100, 2),
            "p_2024_simple_pct": round(p["p_2024_simple"] * 100, 2),
            "media_presidencial_pct": round(p["media_presidencial_original"] * 100, 2),
            "media_intermedia_pct": round(p["media_intermedia_original"] * 100, 2),
            "tasa_joven_18_29_pct": round(p["tasa_joven_18_29_original"] * 100, 2),
            "tasa_mayor_60_mas_pct": round(p["tasa_mayor_60_mas_original"] * 100, 2),
            "tasa_mujeres_pct": round(p["tasa_mujeres_original"] * 100, 2),
            "tasa_hombres_pct": round(p["tasa_hombres_original"] * 100, 2),
            "ratio_joven_cociente_medias": round(p["ratio_joven_ratio_de_medias_usado_en_modelo"], 4),
            "ratio_joven_media_ratios_anuales": round(p["ratio_joven_media_de_ratios_anuales"], 4),
            "top5_entidades_secciones": p["top5_entidades_por_pct_secciones"],
            "top5_entidades_ln_2024": p["top5_entidades_por_pct_ln_2024"],
        })
    rows_sd.append({
        "codigo_cluster": "Panel_B",
        "nombre_perfil": "Media Nacional Panel Principal (Opción B)",
        "p_2009_pond_pct": round(pan_b["p_2009_ponderada"] * 100, 2),
        "p_2012_pond_pct": round(pan_b["p_2012_ponderada"] * 100, 2),
        "p_2015_pond_pct": round(pan_b["p_2015_ponderada"] * 100, 2),
        "p_2018_pond_pct": round(pan_b["p_2018_ponderada"] * 100, 2),
        "p_2021_pond_pct": round(pan_b["p_2021_ponderada"] * 100, 2),
        "p_2024_pond_pct": round(pan_b["p_2024_ponderada"] * 100, 2),
        "p_2009_simple_pct": round(pan_b["p_2009_simple"] * 100, 2),
        "p_2012_simple_pct": round(pan_b["p_2012_simple"] * 100, 2),
        "p_2015_simple_pct": round(pan_b["p_2015_simple"] * 100, 2),
        "p_2018_simple_pct": round(pan_b["p_2018_simple"] * 100, 2),
        "p_2021_simple_pct": round(pan_b["p_2021_simple"] * 100, 2),
        "p_2024_simple_pct": round(pan_b["p_2024_simple"] * 100, 2),
        "media_presidencial_pct": round(pan_b["media_presidencial_original"] * 100, 2),
        "media_intermedia_pct": round(pan_b["media_intermedia_original"] * 100, 2),
        "tasa_joven_18_29_pct": round(pan_b["tasa_joven_18_29_original"] * 100, 2),
        "tasa_mayor_60_mas_pct": round(pan_b["tasa_mayor_60_mas_original"] * 100, 2),
        "tasa_mujeres_pct": round(pan_b["tasa_mujeres_original"] * 100, 2),
        "tasa_hombres_pct": round(pan_b["tasa_hombres_original"] * 100, 2),
        "ratio_joven_cociente_medias": round(pan_b["ratio_joven_ratio_de_medias_usado_en_modelo"], 4),
        "ratio_joven_media_ratios_anuales": round(pan_b["ratio_joven_media_de_ratios_anuales"], 4),
        "top5_entidades_secciones": "Total Nacional (32 entidades)",
        "top5_entidades_ln_2024": "Total Nacional (32 entidades)",
    })
    pd.DataFrame(rows_sd).to_csv(OUT_TABLAS / "tabla_07_perfiles_k4_series_demografia.csv", index=False)

    # 8. Estrategias k=4
    pd.DataFrame(data["estrategias"]).to_csv(OUT_TABLAS / "tabla_08_estrategias_k4.csv", index=False)

    # 9. Matriz de transición (clusters viejos -> nuevos k=4)
    pd.DataFrame(data["transicion_clusters"]).to_csv(OUT_TABLAS / "tabla_09_transicion_clusters.csv", index=False)

    # 10. Sensibilidad Opción A
    pd.DataFrame(data["sensibilidad_opcion_a"]).to_csv(OUT_TABLAS / "tabla_10_sensibilidad_opcion_a.csv", index=False)

    # 11. Interpretabilidad RF / ANOVA
    pd.DataFrame(data["interpretabilidad_rf_anova"]).to_csv(OUT_TABLAS / "tabla_11_interpretabilidad_rf_anova.csv", index=False)

    # 12. Líneas base y metas cuantitativas (Bloque D)
    if "lineas_base_metas" in data:
        pd.DataFrame(data["lineas_base_metas"]).to_csv(OUT_TABLAS / "tabla_12_lineas_base_metas.csv", index=False)

    # 13. Validación fuera de tiempo (Bloque B)
    if "validacion_fuera_de_tiempo" in data and "tabla_13" in data["validacion_fuera_de_tiempo"]:
        pd.DataFrame(data["validacion_fuera_de_tiempo"]["tabla_13"]).to_csv(
            OUT_TABLAS / "tabla_13_validacion_temporal.csv", index=False
        )

    # 14. Cobertura ampliada (Bloque C)
    if "cobertura_ampliada_2024" in data and "tabla_14" in data["cobertura_ampliada_2024"]:
        pd.DataFrame(data["cobertura_ampliada_2024"]["tabla_14"]).to_csv(
            OUT_TABLAS / "tabla_14_cobertura_ampliada.csv", index=False
        )

    # 15. Potencia de piloto (Bloque E)
    if "potencia_piloto_c0" in data and "tabla_15" in data["potencia_piloto_c0"]:
        pd.DataFrame(data["potencia_piloto_c0"]["tabla_15"]).to_csv(
            OUT_TABLAS / "tabla_15_potencia_piloto.csv", index=False
        )

    sha_m = hashlib.sha256(METRICAS_PATH.read_bytes()).hexdigest()
    n_tabs = len(list(OUT_TABLAS.glob("tabla_*.csv")))
    print(f"[Fase 5] {n_tabs} tablas exportadas en {OUT_TABLAS} desde metricas_finales.json (SHA256={sha_m})")


if __name__ == "__main__":
    main()
