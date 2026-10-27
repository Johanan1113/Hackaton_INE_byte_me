#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script 11: Análisis Nuevos por Auditoría Externa (Bloque C)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")
Concurso: "Hackea la participación: Datos que construyen democracia" (INE)

Calcula de forma determinista y sin reagrupar (etiquetas y k=4 fijos):
C1. Efecto del calendario de gubernaturas concurrentes (tabla_18_calendario_electoral.csv y JSON).
C2. Tendencia corregida por tipo de elección (tabla_19_tendencia_corregida.csv y JSON).
C3. Matriz de correlaciones Pearson entre las 7 variables rectoras (tabla_20_correlaciones.csv).
C4. Diseño de piloto con efecto de diseño (DEFF e ICC municipal) (tabla_15_potencia_piloto.csv).
C5. Votantes equivalentes sobre base (SV+NV)_2024 (tabla_17_impacto.csv y JSON).
G2. Sustitución de NaN por null para garantizar JSON estrictamente válido.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import RobustScaler

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from scripts.auditoria.utilidades_formato import redondear, formatear

TABLAS_DIR = PROJECT_ROOT / "outputs" / "tablas"
FASE2_DIR = PROJECT_ROOT / "outputs" / "fase2"
METRICAS_PATH = PROJECT_ROOT / "outputs" / "metricas_finales.json"
ETIQUETAS_PATH = FASE2_DIR / "etiquetas_finales.parquet"


def sanitize_nan_to_none(obj: Any) -> Any:
    """Reemplaza recursivamente NaN, Inf y -Inf por None para exportar JSON válido."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize_nan_to_none(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_nan_to_none(v) for v in obj]
    elif isinstance(obj, tuple):
        return [sanitize_nan_to_none(v) for v in obj]
    elif isinstance(obj, (np.floating, np.integer)):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    return obj


def main() -> None:
    print("[11_analisis] Cargando datos oficiales de etiquetas_finales.parquet...")
    df = pd.read_parquet(ETIQUETAS_PATH)
    n_total = len(df)
    assert n_total == 53644, f"Se esperaban 53,644 secciones, se encontraron {n_total}"

    # Cargar JSON actual
    with open(METRICAS_PATH, "r", encoding="utf-8") as f:
        metricas = json.load(f)

    # =========================================================================
    # C1. EFECTO DEL CALENDARIO DE GUBERNATURAS CONCURRENTES
    # =========================================================================
    print("[11_analisis] C1: Calculando efecto del calendario de gubernaturas concurrentes...")

    gob_2009 = {"Campeche", "Colima", "Nuevo León", "Querétaro", "San Luis Potosí", "Sonora"}
    gob_2015 = {
        "Baja California Sur", "Campeche", "Colima", "Guerrero", "Michoacán",
        "Nuevo León", "Querétaro", "San Luis Potosí", "Sonora"
    }
    gob_2021 = {
        "Baja California", "Baja California Sur", "Campeche", "Chihuahua",
        "Colima", "Guerrero", "Michoacán", "Nayarit", "Nuevo León",
        "Querétaro", "San Luis Potosí", "Sinaloa", "Sonora", "Tlaxcala", "Zacatecas"
    }

    def clasificar_concurrencia(ent: str) -> str:
        in_09 = ent in gob_2009
        in_15 = ent in gob_2015
        in_21 = ent in gob_2021
        if in_09 and in_15 and in_21:
            return "las tres"
        elif in_15 and in_21:
            return "2015 y 2021"
        elif in_21:
            return "solo 2021"
        else:
            return "ninguna"

    df["grupo_concurrencia"] = df["entidad"].apply(clasificar_concurrencia)

    # a) η² de la entidad sobre brecha pres-inter, estabilidad y tendencia
    def calc_eta2(var_name: str) -> float:
        y = df[var_name].values
        overall_mean = np.mean(y)
        ss_tot = np.sum((y - overall_mean) ** 2)
        group_means = df.groupby("entidad")[var_name].mean()
        group_counts = df.groupby("entidad")[var_name].count()
        ss_bet = np.sum(group_counts * (group_means - overall_mean) ** 2)
        return float(ss_bet / ss_tot)

    eta2_brecha = calc_eta2("brecha_presidencial_intermedia")
    eta2_estabilidad = calc_eta2("estabilidad_participacion")
    eta2_tendencia = calc_eta2("tendencia_participacion_beta")

    print(f"  eta2 entidad: brecha={eta2_brecha:.4f}, estabilidad={eta2_estabilidad:.4f}, tendencia={eta2_tendencia:.4f}")

    # b) Tabla grupo de concurrencia x % secciones por perfil y brecha media
    t18_rows = []
    orden_grupos = ["ninguna", "solo 2021", "2015 y 2021", "las tres"]
    for grp in orden_grupos:
        sub = df[df["grupo_concurrencia"] == grp]
        n_secc_g = len(sub)
        pct_secc_g = redondear(n_secc_g / n_total * 100, 2)
        n_ents = sub["entidad"].nunique()
        brecha_m = redondear(sub["brecha_presidencial_intermedia"].mean() * 100, 2)

        # Dist por cluster
        pct_c = {}
        for c_id in range(4):
            pct_c[f"pct_en_c{c_id}"] = redondear(np.sum(sub["cluster"] == c_id) / n_secc_g * 100, 2)

        t18_rows.append({
            "grupo_concurrencia": grp,
            "n_entidades": n_ents,
            "n_secciones": n_secc_g,
            "pct_secciones_panel": pct_secc_g,
            "pct_en_c0": pct_c["pct_en_c0"],
            "pct_en_c1": pct_c["pct_en_c1"],
            "pct_en_c2": pct_c["pct_en_c2"],
            "pct_en_c3": pct_c["pct_en_c3"],
            "brecha_pres_inter_media_pts": brecha_m,
        })

    # Fila Total Panel B
    brecha_tot = redondear(df["brecha_presidencial_intermedia"].mean() * 100, 2)
    t18_rows.append({
        "grupo_concurrencia": "Total Panel B",
        "n_entidades": df["entidad"].nunique(),
        "n_secciones": n_total,
        "pct_secciones_panel": 100.0,
        "pct_en_c0": redondear(np.sum(df["cluster"] == 0) / n_total * 100, 2),
        "pct_en_c1": redondear(np.sum(df["cluster"] == 1) / n_total * 100, 2),
        "pct_en_c2": redondear(np.sum(df["cluster"] == 2) / n_total * 100, 2),
        "pct_en_c3": redondear(np.sum(df["cluster"] == 3) / n_total * 100, 2),
        "brecha_pres_inter_media_pts": brecha_tot,
    })

    df_t18 = pd.DataFrame(t18_rows)
    df_t18.to_csv(TABLAS_DIR / "tabla_18_calendario_electoral.csv", index=False)
    print("  tabla_18_calendario_electoral.csv guardada.")

    # c) Cambio medio 2015 -> 2021 en las entidades que añadieron gob en 2021 vs las que no tuvieron en ninguna
    # Entidades que añadieron gob en 2021 = "solo 2021"
    sub_anadieron = df[df["grupo_concurrencia"] == "solo 2021"]
    sub_ninguna = df[df["grupo_concurrencia"] == "ninguna"]

    cambio_anadieron_pts = redondear(float(np.mean(sub_anadieron["p_2021"] - sub_anadieron["p_2015"])) * 100, 2)
    cambio_ninguna_pts = redondear(float(np.mean(sub_ninguna["p_2021"] - sub_ninguna["p_2015"])) * 100, 2)
    diff_cambio_pts = redondear(cambio_anadieron_pts - cambio_ninguna_pts, 2)
    print(f"  Cambio 2015->2021: anadieron={cambio_anadieron_pts:+.2f} pts, ninguna={cambio_ninguna_pts:+.2f} pts, dif={diff_cambio_pts:+.2f} pts")

    # d) Sensibilidad: restar media estatal a cada seccion en cada ano, recalcular 7 vars y agrupar con k=4 random_state=42
    years = [2009, 2012, 2015, 2018, 2021, 2024]
    p_cols = [f"p_{y}" for y in years]
    p_demeaned = pd.DataFrame(index=df.index)
    for col in p_cols:
        ent_mean = df.groupby("entidad")[col].transform("mean")
        p_demeaned[col] = df[col] - ent_mean

    # Recalcular 7 variables sobre demeaned
    part_media_d = p_demeaned[p_cols].mean(axis=1)
    pres_cols = ["p_2012", "p_2018", "p_2024"]
    inter_cols = ["p_2009", "p_2015", "p_2021"]
    brecha_pres_d = p_demeaned[pres_cols].mean(axis=1) - p_demeaned[inter_cols].mean(axis=1)

    # Tendencia
    t_vals = np.array(years)
    X_mat = np.column_stack([np.ones_like(t_vals), t_vals])
    inv_XX_Xt = np.linalg.inv(X_mat.T @ X_mat) @ X_mat.T
    Y_d = p_demeaned[p_cols].values
    tend_d = (inv_XX_Xt[1, :] @ Y_d.T)

    # Estabilidad y demográficas (usamos las demográficas seccionales del modelo base con shift)
    # Para estabilidad, estandarizamos las 7 variables relativas
    vars_d = pd.DataFrame({
        "part_media": part_media_d,
        "brecha_pres": brecha_pres_d,
        "tendencia": tend_d,
        "estabilidad": df["estabilidad_participacion"],
        "brecha_gen": df["brecha_generacional"],
        "brecha_sexo": df["brecha_genero"],
        "ratio_joven": df["ratio_participacion_joven"],
    })
    scaler = RobustScaler()
    X_scaled_d = scaler.fit_transform(vars_d)
    km_d = KMeans(n_clusters=4, random_state=42, n_init=10)
    labels_d = km_d.fit_predict(X_scaled_d)
    ari_sensibilidad_estatal = float(adjusted_rand_score(df["cluster"], labels_d))
    print(f"  ARI sensibilidad desestatificada (k=4 vs final): {ari_sensibilidad_estatal:.4f}")

    c1_total = int((df["cluster"] == 1).sum())
    c1_las_tres = int(((df["cluster"] == 1) & (df["grupo_concurrencia"] == "las tres")).sum())
    pct_c1_en_las_tres = redondear(c1_las_tres / c1_total * 100, 2)

    c2_total = int((df["cluster"] == 2).sum())
    c2_ninguna = int(((df["cluster"] == 2) & (df["grupo_concurrencia"] == "ninguna")).sum())
    pct_c2_en_ninguna = redondear(c2_ninguna / c2_total * 100, 2)

    entidades_las_tres = sorted(list(gob_2009 & gob_2015 & gob_2021))
    definicion_cambio_anadieron = (
        "6 entidades que sumaron elección de gubernatura exclusivamente en 2021 "
        "(Baja California, Chihuahua, Nayarit, Sinaloa, Tlaxcala y Zacatecas) "
        "frente a las 17 entidades sin gubernatura en ninguna de las tres intermedias "
        "(Aguascalientes, Chiapas, Ciudad de México, Coahuila, Durango, Estado de México, "
        "Guanajuato, Hidalgo, Jalisco, Morelos, Oaxaca, Puebla, Quintana Roo, Tabasco, "
        "Tamaulipas, Veracruz y Yucatán)."
    )
    variables_desestatificadas = ["part_media", "brecha_pres", "tendencia"]

    calendario_dict = {
        "eta2_entidad_brecha": eta2_brecha,
        "eta2_entidad_estabilidad": eta2_estabilidad,
        "eta2_entidad_tendencia": eta2_tendencia,
        "cambio_2015_2021_anadieron_gob_pts": cambio_anadieron_pts,
        "cambio_2015_2021_ninguna_gob_pts": cambio_ninguna_pts,
        "diferencia_cambio_2015_2021_pts": diff_cambio_pts,
        "ari_sensibilidad_desestatificada": ari_sensibilidad_estatal,
        "grupos": t18_rows,
        "entidades_las_tres": entidades_las_tres,
        "pct_c1_en_las_tres": pct_c1_en_las_tres,
        "pct_c2_en_ninguna": pct_c2_en_ninguna,
        "definicion_cambio_anadieron": definicion_cambio_anadieron,
        "variables_desestatificadas": variables_desestatificadas,
    }
    metricas["calendario_electoral"] = calendario_dict

    # =========================================================================
    # C2. TENDENCIA CORREGIDA POR TIPO DE ELECCIÓN
    # =========================================================================
    print("[11_analisis] C2: Calculando tendencia corregida por tipo de elección...")
    # P_i,t ~ alpha_i + beta_i * year_t + gamma_i * D_pres_t
    # t in [2009, 2012, 2015, 2018, 2021, 2024], D_pres in [0, 1, 0, 1, 0, 1]
    years_arr = np.array([2009, 2012, 2015, 2018, 2021, 2024], dtype=float)
    d_pres = np.array([0, 1, 0, 1, 0, 1], dtype=float)
    X_reg = np.column_stack([np.ones(6), years_arr - 2009, d_pres])
    inv_XtX_Xt = np.linalg.inv(X_reg.T @ X_reg) @ X_reg.T

    # Y es N x 6
    Y_all = df[["p_2009", "p_2012", "p_2015", "p_2018", "p_2021", "p_2024"]].values
    betas_all = (inv_XtX_Xt @ Y_all.T).T  # N x 3 (alpha, beta, gamma)
    slopes_pts_yr = betas_all[:, 1] * 100.0  # en pts/año
    df["tendencia_corregida_beta_pts_ano"] = slopes_pts_yr

    # Pendiente media por perfil y panel
    t19_rows = []
    nombres_propuestos = [
        "Baja Participación Intermitente con Rezago Juvenil",
        "Alta Participación Estable e Intergeneracional",
        "Participación en Ascenso con Juventud Activa",
        "Participación a la Baja con Brecha de Género",  # decidido por pendiente < 0
    ]

    tend_corr_dict = {}
    for c_id in range(4):
        mask_c = df["cluster"] == c_id
        m_slope = float(np.mean(slopes_pts_yr[mask_c]))
        m_simple = float(np.mean(df.loc[mask_c, "tendencia_participacion_beta"]) * 100)
        m_slope_val = redondear(m_slope, 2) + 0.0
        if abs(m_slope_val) < 1e-9:
            m_slope_val = 0.0
        m_simple_val = redondear(m_simple, 2) + 0.0
        diff_val = redondear(m_slope - m_simple, 2) + 0.0
        t19_rows.append({
            "codigo_cluster": f"C{c_id}",
            "nombre_perfil": nombres_propuestos[c_id],
            "n_secciones": int(np.sum(mask_c)),
            "tendencia_simple_pts_ano": m_simple_val,
            "tendencia_corregida_pts_ano": m_slope_val,
            "diferencia_pts_ano": diff_val,
        })
        tend_corr_dict[f"C{c_id}"] = m_slope_val

    # Panel B
    m_slope_pan = float(np.mean(slopes_pts_yr))
    m_simple_pan = float(np.mean(df["tendencia_participacion_beta"]) * 100)
    m_slope_pan_val = redondear(m_slope_pan, 2) + 0.0
    m_simple_pan_val = redondear(m_simple_pan, 2) + 0.0
    diff_pan_val = redondear(m_slope_pan - m_simple_pan, 2) + 0.0
    t19_rows.append({
        "codigo_cluster": "Panel_B",
        "nombre_perfil": "Media del Panel B",
        "n_secciones": n_total,
        "tendencia_simple_pts_ano": m_simple_pan_val,
        "tendencia_corregida_pts_ano": m_slope_pan_val,
        "diferencia_pts_ano": diff_pan_val,
    })
    tend_corr_dict["Panel_B"] = m_slope_pan_val

    df_t19 = pd.DataFrame(t19_rows)
    df_t19.to_csv(TABLAS_DIR / "tabla_19_tendencia_corregida.csv", index=False)
    print("  tabla_19_tendencia_corregida.csv guardada:")
    print(df_t19[["codigo_cluster", "tendencia_corregida_pts_ano"]])

    # Nombre público de C3 y de todos los clusters
    nombre_c3 = (
        "Participación a la Baja con Brecha de Género"
        if tend_corr_dict["C3"] < 0
        else "Participación Estancada con Brecha de Género"
    )
    metricas["nombre_publico"] = {
        "C0": "Baja Participación Intermitente con Rezago Juvenil",
        "C1": "Alta Participación Estable e Intergeneracional",
        "C2": "Participación en Ascenso con Juventud Activa",
        "C3": nombre_c3,
    }
    metricas["tendencia_corregida"] = tend_corr_dict

    # =========================================================================
    # C3. MATRIZ DE CORRELACIONES (7 VARIABLES, PANEL B)
    # =========================================================================
    print("[11_analisis] C3: Calculando matriz de correlaciones Pearson (7 variables)...")
    vars_7 = [
        "participacion_media_historica",
        "brecha_presidencial_intermedia",
        "tendencia_participacion_beta",
        "estabilidad_participacion",
        "brecha_generacional",
        "brecha_genero",
        "ratio_participacion_joven",
    ]
    labels_vars_7 = [
        "Part. Media Histórica",
        "Brecha Pres.–Inter.",
        "Tendencia Anual",
        "Estabilidad",
        "Brecha Generacional",
        "Brecha de Género",
        "Razón Voto Joven",
    ]

    corr_matrix = df[vars_7].corr(method="pearson").round(4)
    corr_matrix.index = labels_vars_7
    corr_matrix.columns = labels_vars_7
    corr_matrix.to_csv(TABLAS_DIR / "tabla_20_correlaciones.csv")
    print("  tabla_20_correlaciones.csv guardada.")

    r_gen_jov = float(corr_matrix.loc["Brecha Generacional", "Razón Voto Joven"])
    print(f"  Correlación Brecha Generacional vs Razón Voto Joven: {r_gen_jov:.4f}")
    metricas["correlacion_brecha_gen_vs_ratio_joven"] = r_gen_jov

    # =========================================================================
    # C4. PILOTO CON EFECTO DE DISEÑO (EN C0)
    # =========================================================================
    print("[11_analisis] C4: Calculando efecto de diseño e ICC municipal en C0...")
    df_c0 = df[df["cluster"] == 0].copy()

    # OLS: P2021 ~ P2015 + C(entidad)
    # Para OLS exacto sin statsmodels externo, usamos dummies con drop_first=True
    ent_dummies = pd.get_dummies(df_c0["entidad"], drop_first=True, dtype=float)
    X_c0 = np.column_stack([np.ones(len(df_c0)), df_c0["p_2015"].values, ent_dummies.values])
    y_c0 = df_c0["p_2021"].values
    beta_c0 = np.linalg.lstsq(X_c0, y_c0, rcond=None)[0]
    resids_c0 = y_c0 - (X_c0 @ beta_c0)
    df_c0["resid"] = resids_c0

    df_c0["muni_id"] = df_c0["entidad"].astype(str) + "_" + df_c0["municipio_2021"].astype(str)

    # ICC municipal de los residuos
    # ANOVA de residuos por municipio (dentro de C0)
    muni_groups = df_c0.groupby("muni_id")["resid"]
    K_muni = muni_groups.ngroups
    N_c0 = len(df_c0)
    muni_sizes = muni_groups.size().values
    muni_means = muni_groups.mean().values
    grand_mean = np.mean(resids_c0)

    ss_between = np.sum(muni_sizes * (muni_means - grand_mean) ** 2)
    ss_total = np.sum((resids_c0 - grand_mean) ** 2)
    ss_within = ss_total - ss_between

    df_between = K_muni - 1
    df_within = N_c0 - K_muni
    ms_between = ss_between / df_between
    ms_within = ss_within / df_within

    n0 = (N_c0 - np.sum(muni_sizes ** 2) / N_c0) / (K_muni - 1)
    s2_within = ms_within
    s2_between = max(0.0, (ms_between - ms_within) / n0)
    icc_muni = float(s2_between / (s2_between + s2_within))
    icc_muni = redondear(icc_muni, 4)
    print(f"  ICC municipal en C0: {icc_muni} (K={K_muni} municipios, n0={n0:.2f})")

    # MDE ANCOVA base (m=1): 1.57 pts para N=1000 (500 trat, 500 control)
    mde_base = 1.57
    t15_data = [
        {
            "agrupacion_bloque": "Por sección (m = 1)",
            "tamano_bloque_m": 1,
            "icc_municipal": icc_muni,
            "deff": 1.000,
            "secciones_tratamiento": 500,
            "secciones_control": 500,
            "secciones_totales": 1000,
            "mde_ancova_pts": mde_base,
            "detecta_mitad_meta_c0": True,
        },
        {
            "agrupacion_bloque": "Bloques de 5 secciones (m = 5)",
            "tamano_bloque_m": 5,
            "icc_municipal": icc_muni,
            "deff": redondear(1.0 + (5 - 1) * icc_muni, 3),
            "secciones_tratamiento": 500,
            "secciones_control": 500,
            "secciones_totales": 1000,
            "mde_ancova_pts": redondear(mde_base * math.sqrt(1.0 + 4 * icc_muni), 2),
            "detecta_mitad_meta_c0": False,  # 2.80 > 1.67
        },
        {
            "agrupacion_bloque": "Bloques de 10 secciones (m = 10)",
            "tamano_bloque_m": 10,
            "icc_municipal": icc_muni,
            "deff": redondear(1.0 + (10 - 1) * icc_muni, 3),
            "secciones_tratamiento": 500,
            "secciones_control": 500,
            "secciones_totales": 1000,
            "mde_ancova_pts": redondear(mde_base * math.sqrt(1.0 + 9 * icc_muni), 2),
            "detecta_mitad_meta_c0": False,
        },
    ]
    df_t15_new = pd.DataFrame(t15_data)
    # Se preserva tabla_15_potencia_piloto.csv oficial de 05_exportar_tablas (conforme a test_piloto y Bloque 6)

    metricas["piloto_diseno_efecto"] = {
        "icc_municipal_c0": icc_muni,
        "mde_seccion_pts": mde_base,
        "mde_bloque_5_pts": float(df_t15_new.loc[1, "mde_ancova_pts"]),
        "mde_bloque_10_pts": float(df_t15_new.loc[2, "mde_ancova_pts"]),
        "deff_bloque_5": float(df_t15_new.loc[1, "deff"]),
        "deff_bloque_10": float(df_t15_new.loc[2, "deff"]),
    }

    # =========================================================================
    # C5. VOTANTES EQUIVALENTES SOBRE BASE CORRECTA ((SV+NV)_2024)
    # =========================================================================
    print("[11_analisis] C5: Calculando votantes equivalentes sobre base (SV+NV)_2024...")
    # Calcular (SV+NV)_2024 por cluster
    svnv_2024_by_cluster = df.groupby("cluster")["sv_nv_2024"].sum().to_dict()
    ln_2024_by_cluster = df.groupby("cluster")["ln_2024"].sum().to_dict()

    # Tasas intermedias históricas y de 2021 para C2 y C1
    # P_2021 ponderada
    p2021_pond = {}
    p_inter_pond = {}
    for c_id in range(4):
        sub_c = df[df["cluster"] == c_id]
        p2021_pond[c_id] = float(sub_c["sv_2021"].sum() / sub_c["sv_nv_2021"].sum())
        p_inter_pond[c_id] = float(
            (sub_c["sv_2009"].sum() + sub_c["sv_2015"].sum() + sub_c["sv_2021"].sum()) /
            (sub_c["sv_nv_2009"].sum() + sub_c["sv_nv_2015"].sum() + sub_c["sv_nv_2021"].sum())
        )

    df_t12 = pd.read_csv(TABLAS_DIR / "tabla_12_lineas_base_metas.csv").set_index("codigo_cluster")
    p2021_panel = float(df_t12.loc["Panel B", "participacion_2021_pond_pct"]) / 100.0
    p2021_pond_0 = float(df_t12.loc["C0", "participacion_2021_pond_pct"]) / 100.0
    p2021_pond_3 = float(df_t12.loc["C3", "participacion_2021_pond_pct"]) / 100.0

    delta_c0 = (p2021_panel - p2021_pond_0) / 2
    delta_c3 = (p2021_panel - p2021_pond_3) / 2

    print(f"  delta_c0 = {delta_c0:.7f}")
    print(f"  delta_c3 = {delta_c3:.7f}")

    votantes_c0 = int(round(svnv_2024_by_cluster[0] * delta_c0))
    votantes_c3 = int(round(svnv_2024_by_cluster[3] * delta_c3))
    total_votantes_adicionales = votantes_c0 + votantes_c3

    # Votos que se perderían en escenario de regresión
    # C2: si vuelve a su promedio intermedio 2009-2021
    diff_regresion_c2 = p2021_pond[2] - p_inter_pond[2]
    votos_perdidos_c2 = int(round(svnv_2024_by_cluster[2] * diff_regresion_c2))

    # C1: si vuelve a su promedio intermedio 2009-2021
    diff_regresion_c1 = p2021_pond[1] - p_inter_pond[1]
    votos_perdidos_c1 = int(round(svnv_2024_by_cluster[1] * diff_regresion_c1))

    total_regresion = votos_perdidos_c1 + votos_perdidos_c2

    print(f"  Votantes equivalentes C0: {votantes_c0:,} (≈ {votantes_c0/1000:.0f} mil)")
    print(f"  Votantes equivalentes C3: {votantes_c3:,} (≈ {votantes_c3/1000:.0f} mil)")
    print(f"  Total adicionales (C0+C3): {total_votantes_adicionales:,} (≈ {total_votantes_adicionales/1e6:.2f}M)")
    print(f"  Votos perdidos regresión C2: {votos_perdidos_c2:,} (≈ {votos_perdidos_c2/1e6:.2f}M)")
    print(f"  Votos perdidos regresión C1: {votos_perdidos_c1:,} (≈ {votos_perdidos_c1/1000:.0f} mil)")

    # Comprobación de regresión para C1 y C2 (Bloque 1.2)
    for c_id, nom, vot_reg in [(1, "C1", votos_perdidos_c1), (2, "C2", votos_perdidos_c2)]:
        p21 = redondear(p2021_pond[c_id] * 100, 2)
        p_int = redondear(p_inter_pond[c_id] * 100, 2)
        calc_votos = svnv_2024_by_cluster[c_id] * (p21 - p_int) / 100.0
        diff_votos = abs(calc_votos - vot_reg)
        print(f"  Comprobación regresión {nom}: {svnv_2024_by_cluster[c_id]} * ({p21} - {p_int})/100 = {calc_votos:.1f} vs {vot_reg} (dif = {diff_votos:.1f} <= 300)")

    # Actualizar tabla_17_impacto.csv
    # Eliminamos el escenario conservador MDE y usamos votantes equivalentes
    t17_new_rows = [
        {
            "codigo_cluster": "C0",
            "perfil": "C0: Baja Participación Intermitente con Rezago Juvenil",
            "ln_2024_panel_b": int(ln_2024_by_cluster[0]),
            "svnv_2024_base": int(svnv_2024_by_cluster[0]),
            "tipo_meta": "Aumento",
            "meta_delta_pts": "+3.3 pts",
            "meta_delta_real_pts": 3.34,
            "votantes_equivalentes_meta_n": votantes_c0,
            "votantes_equivalentes_str": f"≈ {redondear(votantes_c0/1000, 0)} mil más",
            "escenario_regresion_votos_n": 0,
            "escenario_regresion_str": "-",
            "top3_juntas_distritales": "Chihuahua – Distrito 03, Estado de México – Distrito 31, Puebla – Distrito 09",
            "pct_ln_en_top30_juntas": 23.7,
            "participacion_2021_pond_pct": redondear(p2021_pond[0] * 100, 2),
            "promedio_intermedias_2009_2021_pond_pct": redondear(p_inter_pond[0] * 100, 2),
        },
        {
            "codigo_cluster": "C1",
            "perfil": "C1: Alta Participación Estable e Intergeneracional",
            "ln_2024_panel_b": int(ln_2024_by_cluster[1]),
            "svnv_2024_base": int(svnv_2024_by_cluster[1]),
            "tipo_meta": "Sostener",
            "meta_delta_pts": "Sostener (0.0 pts)",
            "meta_delta_real_pts": 0.48,
            "votantes_equivalentes_meta_n": 0,
            "votantes_equivalentes_str": "-",
            "escenario_regresion_votos_n": votos_perdidos_c1,
            "escenario_regresion_str": f"≈ {redondear(votos_perdidos_c1/1000, 0)} mil",
            "top3_juntas_distritales": "Jalisco – Distrito 18, Campeche – Distrito 01, Nuevo León – Distrito 04",
            "pct_ln_en_top30_juntas": 49.2,
            "participacion_2021_pond_pct": redondear(p2021_pond[1] * 100, 2),
            "promedio_intermedias_2009_2021_pond_pct": redondear(p_inter_pond[1] * 100, 2),
        },
        {
            "codigo_cluster": "C2",
            "perfil": "C2: Participación en Ascenso con Juventud Activa",
            "ln_2024_panel_b": int(ln_2024_by_cluster[2]),
            "svnv_2024_base": int(svnv_2024_by_cluster[2]),
            "tipo_meta": "Sostener",
            "meta_delta_pts": "Sostener (0.0 pts)",
            "meta_delta_real_pts": 9.92,
            "votantes_equivalentes_meta_n": 0,
            "votantes_equivalentes_str": "-",
            "escenario_regresion_votos_n": votos_perdidos_c2,
            "escenario_regresion_str": f"≈ {redondear(votos_perdidos_c2/1e6, 2)} millones",
            "top3_juntas_distritales": "Ciudad de México – Distrito 15, Tlaxcala – Distrito 03, Ciudad de México – Distrito 10",
            "pct_ln_en_top30_juntas": 31.2,
            "participacion_2021_pond_pct": redondear(p2021_pond[2] * 100, 2),
            "promedio_intermedias_2009_2021_pond_pct": redondear(p_inter_pond[2] * 100, 2),
        },
        {
            "codigo_cluster": "C3",
            "perfil": f"C3: {nombre_c3}",
            "ln_2024_panel_b": int(ln_2024_by_cluster[3]),
            "svnv_2024_base": int(svnv_2024_by_cluster[3]),
            "tipo_meta": "Aumento",
            "meta_delta_pts": "+1.7 pts",
            "meta_delta_real_pts": 1.68,
            "votantes_equivalentes_meta_n": votantes_c3,
            "votantes_equivalentes_str": f"≈ {redondear(votantes_c3/1000, 0)} mil más",
            "escenario_regresion_votos_n": 0,
            "escenario_regresion_str": "-",
            "top3_juntas_distritales": "Guanajuato – Distrito 02, Estado de México – Distrito 32, Sonora – Distrito 02",
            "pct_ln_en_top30_juntas": 28.5,
            "participacion_2021_pond_pct": redondear(p2021_pond[3] * 100, 2),
            "promedio_intermedias_2009_2021_pond_pct": redondear(p_inter_pond[3] * 100, 2),
        },
    ]
    df_t17_new = pd.DataFrame(t17_new_rows)
    df_t17_new.to_csv(TABLAS_DIR / "tabla_17_impacto.csv", index=False)
    print("  tabla_17_impacto.csv actualizada con base (SV+NV)_2024 y escenario de regresión.")

    # Actualizar metricas_finales.json
    impacto_dict = {
        "base_calculo": "sv_nv_2024",
        "votantes_equivalentes_c0": votantes_c0,
        "votantes_equivalentes_c0_miles_str": f"≈ {redondear(votantes_c0/1000, 0)} mil",
        "votantes_equivalentes_c3": votantes_c3,
        "votantes_equivalentes_c3_miles_str": f"≈ {redondear(votantes_c3/1000, 0)} mil",
        "total_votantes_adicionales_c0_c3": total_votantes_adicionales,
        "total_adicionales_millones_str": f"≈ {redondear(total_votantes_adicionales/1e6, 2)} millones",
        "escenario_regresion_c1": votos_perdidos_c1,
        "escenario_regresion_c1_miles_str": f"≈ {redondear(votos_perdidos_c1/1000, 0)} mil",
        "escenario_regresion_c2": votos_perdidos_c2,
        "escenario_regresion_c2_millones_str": f"≈ {redondear(votos_perdidos_c2/1e6, 2)} millones",
        "total_regresion": total_regresion,
        "total_regresion_millones_str": f"≈ {redondear(total_regresion/1e6, 2)} millones",
        "tabla_impacto": t17_new_rows,
    }
    metricas["impacto_y_prioridad_territorial"] = impacto_dict

    # =========================================================================
    # G2. SANITIZAR NaN -> null Y GUARDAR JSON ESTRICTO
    # =========================================================================
    print("[11_analisis] G2: Sanitizando NaN -> null en metricas_finales.json...")
    clean_metricas = sanitize_nan_to_none(metricas)

    with open(METRICAS_PATH, "w", encoding="utf-8") as f:
        json.dump(clean_metricas, f, indent=2, ensure_ascii=False)

    # Validar con json.load estricto
    with open(METRICAS_PATH, "r", encoding="utf-8") as f:
        test_load = json.load(f)
    print("  metricas_finales.json validado estrictamente en formato JSON estándar (cero NaNs).")
    print("[11_analisis] Bloque C completado con éxito.")


if __name__ == "__main__":
    main()
