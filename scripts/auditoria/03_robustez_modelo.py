#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fase 2: Corrección del Pipeline y Pruebas de Robustez del Modelo (03_robustez_modelo.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

Implementa las decisiones metodológicas confirmadas tras el hallazgo de Fase 1:
1. Fórmula oficial CCPC: P = SV / (SV + NV) en todas las tasas (total, 18-29, 60+, mujeres, hombres).
   La brecha de género utiliza exclusivamente mujeres (SEXO=1) menos hombres (SEXO=0);
   el registro no binario (SEXO=2 en 2024) se incorpora en la tasa total.
2. Universo Principal = Opción B (Cero Imputación):
   - Secciones continuas 2009-2024 (62,048)
   - Año válido: SV + NV >= 50 en las 6 elecciones (54,804 secciones)
   - Sin saltos abruptos de LN por reseccionamiento (<0.5x o >2.5x entre elecciones consecutivas: 53,645)
   - Tasas demográficas hexanuales válidas sin imputación (53,644 secciones; 2,393 municipios)
3. Sensibilidad = Opción A (para sección de Limitaciones):
   - Sobre las 62,048 secciones continuas, años con SV + NV < 50 como NaN (sin imputar),
     exigiendo >= 2 elecciones presidenciales y >= 2 intermedias válidas.
   - Reporta el ARI entre Opción A y el Panel Principal (Opción B) en las secciones comunes.
4. Correcciones técnicas:
   - Lectura determinista con utf-8-sig en 2024 y ORDER BY edocve, seccion
   - Transformación de estabilidad: log1p(1/CV) winsorizada en p1-p99
   - Winsorización p1-p99 de las 7 variables previo a RobustScaler
   - Semillas fijas (random_state=42)
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.stats import f_oneway, kurtosis, skew
from sklearn.cluster import HDBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import RobustScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor
import umap

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_ZIPS_DIR = PROJECT_ROOT / "data" / "raw_zips"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUT_FASE2 = PROJECT_ROOT / "outputs" / "fase2"
OUT_FASE2.mkdir(parents=True, exist_ok=True)

import io

YEARS = [2009, 2012, 2015, 2018, 2021, 2024]
PRES_YEARS = [2012, 2018, 2024]
MID_YEARS = [2009, 2015, 2021]

ENTIDADES = {
    1: "Aguascalientes", 2: "Baja California", 3: "Baja California Sur", 4: "Campeche",
    5: "Coahuila", 6: "Colima", 7: "Chiapas", 8: "Chihuahua", 9: "Ciudad de México",
    10: "Durango", 11: "Guanajuato", 12: "Guerrero", 13: "Hidalgo", 14: "Jalisco",
    15: "Estado de México", 16: "Michoacán", 17: "Morelos", 18: "Nayarit", 19: "Nuevo León",
    20: "Oaxaca", 21: "Puebla", 22: "Querétaro", 23: "Quintana Roo", 24: "San Luis Potosí",
    25: "Sinaloa", 26: "Sonora", 27: "Tabasco", 28: "Tamaulipas", 29: "Tlaxcala",
    30: "Veracruz", 31: "Yucatán", 32: "Zacatecas",
}

FEATURE_COLS = [
    "participacion_media_historica",
    "brecha_presidencial_intermedia",
    "tendencia_participacion_beta",
    "estabilidad_participacion",
    "brecha_generacional",
    "brecha_genero",
    "ratio_participacion_joven",
]


def load_year_raw(year: int) -> pd.DataFrame:
    """Lee de forma determinista los 32 CSV estatales de un año desde data/raw_zips."""
    zip_path = RAW_ZIPS_DIR / f"DatosAbiertos_DECEyEC_ConteosCensales{year}.zip"
    dfs = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        csv_files = sorted(f for f in zf.namelist() if f.lower().endswith(".csv"))
        for cname in csv_files:
            raw_bytes = zf.read(cname)
            enc = "utf-8-sig" if (year == 2024 or raw_bytes.startswith(b"\xef\xbb\xbf")) else "latin1"
            df_st = pd.read_csv(io.BytesIO(raw_bytes), encoding=enc, low_memory=False)
            df_st.columns = [c.replace("\ufeff", "").replace("ï»¿", "").strip().upper() for c in df_st.columns]
            dfs.append(df_st)

    df = pd.concat(dfs, ignore_index=True)
    df["EDOCVE"] = pd.to_numeric(df["EDOCVE"], errors="coerce").fillna(0).astype(int)
    df["SECCION"] = pd.to_numeric(df["SECCION"], errors="coerce").fillna(0).astype(int)
    df["MPIOCVE"] = pd.to_numeric(df["MPIOCVE"], errors="coerce").fillna(0).astype(int)
    df["EDAD"] = pd.to_numeric(df["EDAD"], errors="coerce").fillna(-1).astype(int)
    df["SEXO"] = pd.to_numeric(df["SEXO"], errors="coerce").fillna(-1).astype(int)
    for col in ["LN", "SV", "NV", "NS"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(np.int64)

    df["TIPO_CLEAN"] = df["TIPOSEC"].astype(str).str.strip().str.upper().str[0]
    df = df[(df["EDOCVE"] > 0) & (df["SECCION"] > 0)].copy()
    return df


def aggregate_sections_all_years() -> tuple[pd.DataFrame, dict]:
    """
    Agrega cada año a nivel sección electoral con DuckDB (ORDER BY edocve, seccion)
    y calcula las tasas con la fórmula oficial SV / (SV + NV).
    Devuelve el panel continuo de 62,048 secciones y estadísticas de reconciliación de universos.
    """
    con = duckdb.connect()
    yearly_dfs = {}
    section_sets = {}

    for y in YEARS:
        df_raw = load_year_raw(y)
        con.register("df_raw", df_raw)
        # EDAD: 18 a 29 años (joven), >= 60 años (adulto mayor)
        # SEXO: 0 -> Hombres, 1 -> Mujeres, 2 -> No binario (2024)
        q = f"""
        SELECT
            EDOCVE AS edocve,
            SECCION AS seccion,
            CAST(EDOCVE AS VARCHAR) || '_' || CAST(SECCION AS VARCHAR) AS seccion_id,
            FIRST(MPIOCVE ORDER BY MPIOCVE) AS municipio_{y},
            FIRST(MPIONOM ORDER BY MPIONOM) AS mpionom_{y},
            FIRST(TIPO_CLEAN ORDER BY TIPO_CLEAN) AS tipo_{y},
            SUM(LN) AS ln_{y},
            SUM(SV) AS sv_{y},
            SUM(NV) AS nv_{y},
            SUM(NS) AS ns_{y},
            SUM(SV + NV) AS sv_nv_{y},
            SUM(CASE WHEN EDAD BETWEEN 18 AND 29 THEN SV ELSE 0 END) AS sv_joven_{y},
            SUM(CASE WHEN EDAD BETWEEN 18 AND 29 THEN SV + NV ELSE 0 END) AS sv_nv_joven_{y},
            SUM(CASE WHEN EDAD >= 60 THEN SV ELSE 0 END) AS sv_mayor_{y},
            SUM(CASE WHEN EDAD >= 60 THEN SV + NV ELSE 0 END) AS sv_nv_mayor_{y},
            SUM(CASE WHEN SEXO = 1 THEN SV ELSE 0 END) AS sv_mujer_{y},
            SUM(CASE WHEN SEXO = 1 THEN SV + NV ELSE 0 END) AS sv_nv_mujer_{y},
            SUM(CASE WHEN SEXO = 0 THEN SV ELSE 0 END) AS sv_hombre_{y},
            SUM(CASE WHEN SEXO = 0 THEN SV + NV ELSE 0 END) AS sv_nv_hombre_{y}
        FROM df_raw
        GROUP BY EDOCVE, SECCION
        ORDER BY EDOCVE, SECCION
        """
        agg = con.execute(q).df()
        con.unregister("df_raw")

        # Tasas anuales con SV / (SV + NV)
        for prefix, num, den in [
            ("p", f"sv_{y}", f"sv_nv_{y}"),
            ("p_joven", f"sv_joven_{y}", f"sv_nv_joven_{y}"),
            ("p_mayor", f"sv_mayor_{y}", f"sv_nv_mayor_{y}"),
            ("p_mujer", f"sv_mujer_{y}", f"sv_nv_mujer_{y}"),
            ("p_hombre", f"sv_hombre_{y}", f"sv_nv_hombre_{y}"),
        ]:
            agg[f"{prefix}_{y}"] = np.where(agg[den] > 0, agg[num] / agg[den], np.nan)

        yearly_dfs[y] = agg
        section_sets[y] = set(agg["seccion_id"])

    # Reconciliación de universos seccionales
    union_all = set.union(*[section_sets[y] for y in YEARS])
    inter_all = set.intersection(*[section_sets[y] for y in YEARS])
    sec_2024 = section_sets[2024]
    new_in_2024_not_continuous = sec_2024 - inter_all
    disappeared_before_2024 = union_all - sec_2024

    df_2024 = yearly_dfs[2024]
    total_ln_2024_csv = int(df_2024["ln_2024"].sum())
    total_muns_2024 = int(
        (df_2024["edocve"].astype(str) + "_" + df_2024["municipio_2024"].astype(str)).nunique()
    )
    all_muns_union = set()
    for y in YEARS:
        d = yearly_dfs[y]
        all_muns_union |= set(d["edocve"].astype(str) + "_" + d[f"municipio_{y}"].astype(str))

    # Construir panel continuo de 62,048 secciones ordenado deterministamente
    panel = yearly_dfs[2009][["edocve", "seccion", "seccion_id"]].copy()
    panel = panel[panel["seccion_id"].isin(inter_all)].sort_values(["edocve", "seccion"]).reset_index(drop=True)

    for y in YEARS:
        cols_y = [c for c in yearly_dfs[y].columns if c not in ("edocve", "seccion")]
        panel = panel.merge(yearly_dfs[y][cols_y], on="seccion_id", how="inner")

    panel = panel.sort_values(["edocve", "seccion"]).reset_index(drop=True)
    panel["entidad"] = panel["edocve"].map(ENTIDADES)
    panel["municipio"] = panel["municipio_2024"]
    panel["tipo_2024"] = panel["tipo_2024"].fillna("U")

    reconciliacion = {
        "union_historica_2009_2024": len(union_all),
        "secciones_2024_total": len(sec_2024),
        "secciones_continuas_2009_2024": len(inter_all),
        "secciones_2024_no_continuas_creadas_post2009": len(new_in_2024_not_continuous),
        "secciones_2009_2021_baja_antes_2024": len(disappeared_before_2024),
        "ln_2024_total_csv": total_ln_2024_csv,
        "ln_2024_oficial_ine": 98329591,
        "ln_2024_continuas_62048": int(panel["ln_2024"].sum()),
        "municipios_historicos_union": len(all_muns_union),
        "municipios_2024_total": total_muns_2024,
        "municipios_continuas_62048": int(
            (panel["edocve"].astype(str) + "_" + panel["municipio_2024"].astype(str)).nunique()
        ),
    }
    return panel, reconciliacion


def compute_features_and_universes(panel: pd.DataFrame, reconciliacion: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Aplica las reglas de filtrado del Universo Principal (Opción B, cero imputación)
    y calcula las variables electorales y demográficas en el Panel Principal (Opción B)
    y en el Universo de Sensibilidad (Opción A).
    """
    sv_nv_cols = [f"sv_nv_{y}" for y in YEARS]
    sv_nv_mat = panel[sv_nv_cols].to_numpy()

    min_sv_nv = sv_nv_mat.min(axis=1)
    n_zero_years = (sv_nv_mat == 0).sum(axis=1)
    n_lt50_years = (sv_nv_mat < 50).sum(axis=1)
    valid_6_years = min_sv_nv >= 50

    # Saltos abruptos de LN entre elecciones consecutivas (<0.5x o >2.5x)
    consec_jump = np.zeros(len(panel), dtype=bool)
    for y1, y2 in zip(YEARS[:-1], YEARS[1:]):
        r = panel[f"ln_{y2}"].to_numpy() / np.maximum(panel[f"ln_{y1}"].to_numpy(), 1)
        consec_jump |= (r < 0.5) | (r > 2.5)

    panel["min_sv_nv"] = min_sv_nv
    panel["n_zero_years"] = n_zero_years
    panel["n_lt50_years"] = n_lt50_years
    panel["valid_6_years"] = valid_6_years
    panel["consec_ln_jump"] = consec_jump

    # Tasas demográficas hexanuales (promedio simple sobre los 6 años)
    p_cols = [f"p_{y}" for y in YEARS]
    p_pres_cols = [f"p_{y}" for y in PRES_YEARS]
    p_mid_cols = [f"p_{y}" for y in MID_YEARS]
    pj_cols = [f"p_joven_{y}" for y in YEARS]
    pm_cols = [f"p_mayor_{y}" for y in YEARS]
    pf_cols = [f"p_mujer_{y}" for y in YEARS]
    ph_cols = [f"p_hombre_{y}" for y in YEARS]

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        p_mat = panel[p_cols].to_numpy(dtype=float)
        panel["participacion_media_historica"] = np.nanmean(p_mat, axis=1)
        panel["media_presidencial"] = np.nanmean(panel[p_pres_cols].to_numpy(dtype=float), axis=1)
        panel["media_intermedia"] = np.nanmean(panel[p_mid_cols].to_numpy(dtype=float), axis=1)
        panel["brecha_presidencial_intermedia"] = panel["media_presidencial"] - panel["media_intermedia"]

        # Tendencia OLS (beta anual con t_steps = 0, 3, 6, 9, 12, 15 años desde 2009, igual que src/02_features.py)
        x = np.array([0.0, 3.0, 6.0, 9.0, 12.0, 15.0], dtype=float)
        x_centered = x - x.mean()
        denom_x = np.sum(x_centered ** 2)
        p_centered = p_mat - np.nanmean(p_mat, axis=1, keepdims=True)
        panel["tendencia_participacion_beta"] = np.sum(p_centered * x_centered, axis=1) / denom_x

        # Desviación estándar muestral (ddof=1, igual que en src/02_features.py)
        std_p = np.nanstd(p_mat, axis=1, ddof=1)
        mean_p = panel["participacion_media_historica"].to_numpy()
        panel["std_participacion"] = std_p
        panel["estabilidad_inv_cv_raw"] = mean_p / (std_p + 1e-4)
        panel["estabilidad_cv_raw"] = std_p / np.maximum(mean_p, 1e-4)
        panel["estabilidad_log1p_raw"] = np.log1p(panel["estabilidad_inv_cv_raw"])

        # Demográficas 2009-2024 sin imputación
        panel["tasa_joven_18_29"] = np.nanmean(panel[pj_cols].to_numpy(dtype=float), axis=1)
        panel["tasa_mayor_60_mas"] = np.nanmean(panel[pm_cols].to_numpy(dtype=float), axis=1)
        panel["tasa_mujeres"] = np.nanmean(panel[pf_cols].to_numpy(dtype=float), axis=1)
        panel["tasa_hombres"] = np.nanmean(panel[ph_cols].to_numpy(dtype=float), axis=1)

        panel["brecha_generacional"] = panel["tasa_mayor_60_mas"] - panel["tasa_joven_18_29"]
        panel["brecha_genero"] = panel["tasa_mujeres"] - panel["tasa_hombres"]
        # Ratio de medias hexanuales: tasa_joven_18_29 / participacion_media_historica
        panel["ratio_participacion_joven"] = panel["tasa_joven_18_29"] / panel["participacion_media_historica"]
        # También calculamos el promedio de ratios anuales para reportar ambos en Fase 3
        ratios_anuales = panel[pj_cols].to_numpy(dtype=float) / panel[p_cols].to_numpy(dtype=float)
        panel["ratio_participacion_joven_media_de_ratios"] = np.nanmean(ratios_anuales, axis=1)

    # Demográficas solo 2024 (para prueba 2.3 de ventana temporal)
    panel["brecha_generacional_2024"] = panel["p_mayor_2024"] - panel["p_joven_2024"]
    panel["brecha_genero_2024"] = panel["p_mujer_2024"] - panel["p_hombre_2024"]
    panel["ratio_participacion_joven_2024"] = panel["p_joven_2024"] / panel["p_2024"]

    # Verificar que no haya NaN en ninguna tasa demográfica ni electoral (cero imputación)
    non_null_demog = (
        panel["participacion_media_historica"].notna()
        & panel["brecha_presidencial_intermedia"].notna()
        & panel["tendencia_participacion_beta"].notna()
        & panel["estabilidad_log1p_raw"].notna()
        & panel["brecha_generacional"].notna()
        & panel["brecha_genero"].notna()
        & panel["ratio_participacion_joven"].notna()
    )
    panel["in_main_panel_B"] = panel["valid_6_years"] & (~panel["consec_ln_jump"]) & non_null_demog

    # Guardar el panel de 62,048 corregido completo
    panel.to_parquet(OUT_FASE2 / "panel_62048_corregido.parquet", index=False)

    # Construir tabla de cascada de filtrado (universo_filtrado.csv)
    c_62048 = panel
    c_54804 = panel[panel["valid_6_years"]]
    c_53645 = panel[panel["valid_6_years"] & (~panel["consec_ln_jump"])]
    c_53644 = panel[panel["in_main_panel_B"]].copy().reset_index(drop=True)

    def _muns(df_sub: pd.DataFrame) -> int:
        return int((df_sub["edocve"].astype(str) + "_" + df_sub["municipio_2024"].astype(str)).nunique())

    rows_univ = [
        {
            "etapa": "0_union_historica_2009_2024",
            "descripcion": "Unión histórica de secciones registradas en al menos una elección (2009-2024)",
            "secciones": reconciliacion["union_historica_2009_2024"],
            "secciones_excluidas_paso": 0,
            "pct_secciones_2024": round(reconciliacion["union_historica_2009_2024"] / reconciliacion["secciones_2024_total"] * 100, 2),
            "ln_2024": reconciliacion["ln_2024_total_csv"],
            "pct_ln_2024": 100.00,
            "municipios": reconciliacion["municipios_historicos_union"],
        },
        {
            "etapa": "1_universo_2024",
            "descripcion": "Secciones activas en el CCPC 2024 (excluye 1,930 secciones dadas de baja entre 2009 y 2021)",
            "secciones": reconciliacion["secciones_2024_total"],
            "secciones_excluidas_paso": reconciliacion["secciones_2009_2021_baja_antes_2024"],
            "pct_secciones_2024": 100.00,
            "ln_2024": reconciliacion["ln_2024_total_csv"],
            "pct_ln_2024": 100.00,
            "municipios": reconciliacion["municipios_2024_total"],
        },
        {
            "etapa": "2_panel_continuo_2009_2024",
            "descripcion": "Secciones presentes en las 6 elecciones 2009-2024 (excluye 8,703 secciones creadas post-2009)",
            "secciones": len(c_62048),
            "secciones_excluidas_paso": reconciliacion["secciones_2024_no_continuas_creadas_post2009"],
            "pct_secciones_2024": round(len(c_62048) / reconciliacion["secciones_2024_total"] * 100, 2),
            "ln_2024": int(c_62048["ln_2024"].sum()),
            "pct_ln_2024": round(c_62048["ln_2024"].sum() / reconciliacion["ln_2024_total_csv"] * 100, 2),
            "municipios": _muns(c_62048),
        },
        {
            "etapa": "3_captura_valida_6_elecciones",
            "descripcion": "Secciones con captura válida SV + NV >= 50 en las 6 elecciones (excluye 7,156 con SV+NV=0 en al menos una elección y 88 con 1<=SV+NV<50)",
            "secciones": len(c_54804),
            "secciones_excluidas_paso": len(c_62048) - len(c_54804),
            "pct_secciones_2024": round(len(c_54804) / reconciliacion["secciones_2024_total"] * 100, 2),
            "ln_2024": int(c_54804["ln_2024"].sum()),
            "pct_ln_2024": round(c_54804["ln_2024"].sum() / reconciliacion["ln_2024_total_csv"] * 100, 2),
            "municipios": _muns(c_54804),
        },
        {
            "etapa": "4_sin_saltos_abruptos_ln_consecutivos",
            "descripcion": "Excluye secciones con cambio abrupto de LN (<0.5x o >2.5x entre elecciones consecutivas; 1,311 en las 62,048 y 1,159 entre las 54,804)",
            "secciones": len(c_53645),
            "secciones_excluidas_paso": len(c_54804) - len(c_53645),
            "pct_secciones_2024": round(len(c_53645) / reconciliacion["secciones_2024_total"] * 100, 2),
            "ln_2024": int(c_53645["ln_2024"].sum()),
            "pct_ln_2024": round(c_53645["ln_2024"].sum() / reconciliacion["ln_2024_total_csv"] * 100, 2),
            "municipios": _muns(c_53645),
        },
        {
            "etapa": "5_panel_principal_opcion_b_cero_imputacion",
            "descripcion": "Excluye secciones sin electores en algún grupo etario en los 6 años (1 sección: 14_1645 sin 60+) para garantizar cero imputación",
            "secciones": len(c_53644),
            "secciones_excluidas_paso": len(c_53645) - len(c_53644),
            "pct_secciones_2024": round(len(c_53644) / reconciliacion["secciones_2024_total"] * 100, 2),
            "ln_2024": int(c_53644["ln_2024"].sum()),
            "pct_ln_2024": round(c_53644["ln_2024"].sum() / reconciliacion["ln_2024_total_csv"] * 100, 2),
            "municipios": _muns(c_53644),
        },
    ]
    df_univ = pd.DataFrame(rows_univ)
    df_univ.to_csv(OUT_FASE2 / "universo_filtrado.csv", index=False)

    return panel, c_53644, df_univ


def winsorize_series(s: pd.Series, p_low: float = 0.01, p_high: float = 0.99) -> pd.Series:
    q_low, q_high = s.quantile([p_low, p_high])
    return s.clip(lower=q_low, upper=q_high)


def test_2_1_stability(df_b: pd.DataFrame) -> pd.DataFrame:
    """
    2.1 Compara las tres definiciones de estabilidad sobre el Panel Principal (N=53,644) con k=4:
      (a) 1/CV = P_bar / (sigma + 1e-4) sin acotar (definición original)
      (b) CV = sigma / P_bar winsorizado p1-p99
      (c) log1p(1/CV) winsorizado p1-p99 (definición seleccionada)
    """
    base_6 = [
        "participacion_media_historica",
        "brecha_presidencial_intermedia",
        "tendencia_participacion_beta",
        "brecha_generacional",
        "brecha_genero",
        "ratio_participacion_joven",
    ]
    X_base = pd.DataFrame({c: winsorize_series(df_b[c]) for c in base_6})

    versions = {
        "a_inv_cv_sin_acotar": df_b["estabilidad_inv_cv_raw"].copy(),
        "b_cv_directo_winsor_p1_p99": winsorize_series(df_b["estabilidad_cv_raw"]),
        "c_log1p_inv_cv_winsor_p1_p99": winsorize_series(df_b["estabilidad_log1p_raw"]),
    }

    labels_dict = {}
    rows = []
    for name, s_est in versions.items():
        X_df = X_base.copy()
        X_df["estabilidad_participacion"] = s_est
        X_df = X_df[FEATURE_COLS]
        X_scaled = RobustScaler().fit_transform(X_df)

        km = KMeans(n_clusters=4, init="k-means++", n_init=50, random_state=42)
        lbl = km.fit_predict(X_scaled)
        labels_dict[name] = lbl

        sil = silhouette_score(X_scaled, lbl, sample_size=20000, random_state=42)
        db = davies_bouldin_score(X_scaled, lbl)
        ch = calinski_harabasz_score(X_scaled, lbl)

        rows.append({
            "version": name,
            "media": round(float(s_est.mean()), 6),
            "std": round(float(s_est.std()), 6),
            "min": round(float(s_est.min()), 6),
            "p01": round(float(s_est.quantile(0.01)), 6),
            "mediana": round(float(s_est.median()), 6),
            "p99": round(float(s_est.quantile(0.99)), 6),
            "max": round(float(s_est.max()), 6),
            "asimetria_skew": round(float(skew(s_est)), 4),
            "curtosis_kurt": round(float(kurtosis(s_est)), 4),
            "silhouette_k4": round(float(sil), 4),
            "davies_bouldin_k4": round(float(db), 4),
            "calinski_harabasz_k4": round(float(ch), 2),
        })

    df_est = pd.DataFrame(rows)
    ari_ab = adjusted_rand_score(labels_dict["a_inv_cv_sin_acotar"], labels_dict["b_cv_directo_winsor_p1_p99"])
    ari_ac = adjusted_rand_score(labels_dict["a_inv_cv_sin_acotar"], labels_dict["c_log1p_inv_cv_winsor_p1_p99"])
    ari_bc = adjusted_rand_score(labels_dict["b_cv_directo_winsor_p1_p99"], labels_dict["c_log1p_inv_cv_winsor_p1_p99"])

    df_est["ari_vs_a"] = [1.0, round(float(ari_ab), 4), round(float(ari_ac), 4)]
    df_est["ari_vs_b"] = [round(float(ari_ab), 4), 1.0, round(float(ari_bc), 4)]
    df_est["ari_vs_c"] = [round(float(ari_ac), 4), round(float(ari_bc), 4), 1.0]
    df_est["seleccionada"] = [False, False, True]
    df_est.to_csv(OUT_FASE2 / "estabilidad_comparacion.csv", index=False)
    return df_est


def prepare_scaled_features(df_b: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """Aplica winsorización p1-p99 a las 7 variables (con estabilidad (c)) y RobustScaler."""
    df_b["estabilidad_participacion"] = df_b["estabilidad_log1p_raw"]
    X_winsor = pd.DataFrame(index=df_b.index)
    for col in FEATURE_COLS:
        X_winsor[col] = winsorize_series(df_b[col], 0.01, 0.99)
        df_b[f"{col}_winsor"] = X_winsor[col]

    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X_winsor[FEATURE_COLS])
    for i, col in enumerate(FEATURE_COLS):
        df_b[f"{col}_scaled"] = X_scaled[:, i]
    return X_winsor, X_scaled


def test_2_2_collinearity(X_winsor: pd.DataFrame, X_scaled: np.ndarray, labels_7: np.ndarray) -> pd.DataFrame:
    """
    2.2 Calcula el VIF de las 7 variables y compara el clustering K-Means (k=4)
    con 7 variables, sin ratio_participacion_joven, y sin brecha_generacional.
    """
    X_std = (X_winsor - X_winsor.mean()) / X_winsor.std()
    vifs = {
        col: float(variance_inflation_factor(X_std.values, i))
        for i, col in enumerate(FEATURE_COLS)
    }

    # Sin ratio_participacion_joven (índice 6)
    idx_no_ratio = [i for i, c in enumerate(FEATURE_COLS) if c != "ratio_participacion_joven"]
    X_no_ratio = X_scaled[:, idx_no_ratio]
    X_std_no_ratio = X_std.iloc[:, idx_no_ratio]
    vifs_no_ratio = {
        c: float(variance_inflation_factor(X_std_no_ratio.values, j))
        for j, c in enumerate(X_std_no_ratio.columns)
    }
    lbl_no_ratio = KMeans(n_clusters=4, init="k-means++", n_init=50, random_state=42).fit_predict(X_no_ratio)

    # Sin brecha_generacional (índice 4)
    idx_no_bgen = [i for i, c in enumerate(FEATURE_COLS) if c != "brecha_generacional"]
    X_no_bgen = X_scaled[:, idx_no_bgen]
    X_std_no_bgen = X_std.iloc[:, idx_no_bgen]
    vifs_no_bgen = {
        c: float(variance_inflation_factor(X_std_no_bgen.values, j))
        for j, c in enumerate(X_std_no_bgen.columns)
    }
    lbl_no_bgen = KMeans(n_clusters=4, init="k-means++", n_init=50, random_state=42).fit_predict(X_no_bgen)

    sil_7 = silhouette_score(X_scaled, labels_7, sample_size=20000, random_state=42)
    db_7 = davies_bouldin_score(X_scaled, labels_7)
    ch_7 = calinski_harabasz_score(X_scaled, labels_7)

    sil_nr = silhouette_score(X_no_ratio, lbl_no_ratio, sample_size=20000, random_state=42)
    db_nr = davies_bouldin_score(X_no_ratio, lbl_no_ratio)
    ch_nr = calinski_harabasz_score(X_no_ratio, lbl_no_ratio)
    ari_nr = adjusted_rand_score(labels_7, lbl_no_ratio)

    sil_nb = silhouette_score(X_no_bgen, lbl_no_bgen, sample_size=20000, random_state=42)
    db_nb = davies_bouldin_score(X_no_bgen, lbl_no_bgen)
    ch_nb = calinski_harabasz_score(X_no_bgen, lbl_no_bgen)
    ari_nb = adjusted_rand_score(labels_7, lbl_no_bgen)

    rows = []
    for col in FEATURE_COLS:
        rows.append({
            "variable": col,
            "vif_7_variables": round(vifs[col], 4),
            "vif_sin_ratio_joven": round(vifs_no_ratio.get(col, np.nan), 4) if col in vifs_no_ratio else np.nan,
            "vif_sin_brecha_gen": round(vifs_no_bgen.get(col, np.nan), 4) if col in vifs_no_bgen else np.nan,
            "modelo_7_vars_silhouette": round(float(sil_7), 4),
            "modelo_7_vars_db": round(float(db_7), 4),
            "modelo_7_vars_ch": round(float(ch_7), 2),
            "sin_ratio_joven_silhouette": round(float(sil_nr), 4),
            "sin_ratio_joven_db": round(float(db_nr), 4),
            "sin_ratio_joven_ari_vs_7vars": round(float(ari_nr), 4),
            "sin_brecha_gen_silhouette": round(float(sil_nb), 4),
            "sin_brecha_gen_db": round(float(db_nb), 4),
            "sin_brecha_gen_ari_vs_7vars": round(float(ari_nb), 4),
        })
    df_vif = pd.DataFrame(rows)
    df_vif.to_csv(OUT_FASE2 / "vif_colinealidad.csv", index=False)
    return df_vif


def test_2_3_temporal_windows(df_b: pd.DataFrame, labels_7: np.ndarray) -> pd.DataFrame:
    """
    2.3 Compara la ventana temporal de las variables demográficas:
    promedio de las 6 elecciones (2009-2024) vs solo 2024 (con k=4).
    """
    X_2024_demog = pd.DataFrame(index=df_b.index)
    X_2024_demog["participacion_media_historica"] = winsorize_series(df_b["participacion_media_historica"])
    X_2024_demog["brecha_presidencial_intermedia"] = winsorize_series(df_b["brecha_presidencial_intermedia"])
    X_2024_demog["tendencia_participacion_beta"] = winsorize_series(df_b["tendencia_participacion_beta"])
    X_2024_demog["estabilidad_participacion"] = winsorize_series(df_b["estabilidad_log1p_raw"])
    X_2024_demog["brecha_generacional"] = winsorize_series(df_b["brecha_generacional_2024"].fillna(df_b["brecha_generacional"]))
    X_2024_demog["brecha_genero"] = winsorize_series(df_b["brecha_genero_2024"].fillna(df_b["brecha_genero"]))
    X_2024_demog["ratio_participacion_joven"] = winsorize_series(df_b["ratio_participacion_joven_2024"].fillna(df_b["ratio_participacion_joven"]))

    X_2024_scaled = RobustScaler().fit_transform(X_2024_demog[FEATURE_COLS])
    lbl_2024 = KMeans(n_clusters=4, init="k-means++", n_init=50, random_state=42).fit_predict(X_2024_scaled)
    ari_window = adjusted_rand_score(labels_7, lbl_2024)

    pairs = [
        ("tasa_joven_18_29", "tasa_joven_18_29", "p_joven_2024"),
        ("tasa_mayor_60_mas", "tasa_mayor_60_mas", "p_mayor_2024"),
        ("brecha_generacional", "brecha_generacional", "brecha_generacional_2024"),
        ("brecha_genero", "brecha_genero", "brecha_genero_2024"),
        ("ratio_participacion_joven", "ratio_participacion_joven", "ratio_participacion_joven_2024"),
    ]
    rows = []
    for name, col_6y, col_24 in pairs:
        s6 = df_b[col_6y]
        s24 = df_b[col_24]
        corr = s6.corr(s24)
        rows.append({
            "variable": name,
            "media_2009_2024": round(float(s6.mean()), 6),
            "std_2009_2024": round(float(s6.std()), 6),
            "media_solo_2024": round(float(s24.mean()), 6),
            "std_solo_2024": round(float(s24.std()), 6),
            "diferencia_medias": round(float(s24.mean() - s6.mean()), 6),
            "correlacion_pearson": round(float(corr), 4),
            "ari_clustering_6y_vs_2024": round(float(ari_window), 4),
        })
    df_win = pd.DataFrame(rows)
    df_win.to_csv(OUT_FASE2 / "ventanas_temporales.csv", index=False)
    return df_win


def test_2_4_benchmark(X_scaled: np.ndarray) -> tuple[pd.DataFrame, dict[int, np.ndarray]]:
    """
    2.4 Ejecuta el benchmark completo:
      - K-Means++ para k in {3, 4, 5, 6, 7} con 100 bootstraps al 80% (media, DE e IC 95%)
      - GMM (covariance_type='full') para k in {3, 4, 5, 6, 7} (Silhouette, DB, CH, BIC, AIC)
      - HDBSCAN en 3 configuraciones: (100, 10), (250, 20), (500, 30)
    """
    rows = []
    km_labels_by_k: dict[int, np.ndarray] = {}
    n = len(X_scaled)
    sub_n = int(0.8 * n)

    for k in [3, 4, 5, 6, 7]:
        km = KMeans(n_clusters=k, init="k-means++", n_init=50, random_state=42)
        labels = km.fit_predict(X_scaled)
        km_labels_by_k[k] = labels

        sil = silhouette_score(X_scaled, labels, sample_size=20000, random_state=42)
        db = davies_bouldin_score(X_scaled, labels)
        ch = calinski_harabasz_score(X_scaled, labels)
        inercia = km.inertia_

        # 100 bootstraps al 80% sin reemplazo
        rng = np.random.default_rng(42)
        aris = []
        for _ in range(100):
            idx = rng.choice(n, size=sub_n, replace=False)
            km_b = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=int(rng.integers(0, 1_000_000)))
            lbl_b = km_b.fit_predict(X_scaled[idx])
            aris.append(adjusted_rand_score(labels[idx], lbl_b))

        ari_mean = float(np.mean(aris))
        ari_std = float(np.std(aris))
        ari_p2_5, ari_p97_5 = np.percentile(aris, [2.5, 97.5])

        counts = np.bincount(labels)
        rows.append({
            "algoritmo": "K-Means++",
            "configuracion": f"k={k}",
            "k": k,
            "n_clusters_efectivos": k,
            "pct_ruido": 0.0,
            "inercia": round(float(inercia), 2),
            "silhouette": round(float(sil), 4),
            "davies_bouldin": round(float(db), 4),
            "calinski_harabasz": round(float(ch), 2),
            "bic": np.nan,
            "aic": np.nan,
            "bootstrap_ari_media": round(ari_mean, 4),
            "bootstrap_ari_std": round(ari_std, 4),
            "bootstrap_ari_ic95_inf": round(float(ari_p2_5), 4),
            "bootstrap_ari_ic95_sup": round(float(ari_p97_5), 4),
            "ari_vs_kmeans_mismo_k": 1.0,
            "cluster_min_pct": round(float(counts.min() / n * 100), 2),
            "cluster_max_pct": round(float(counts.max() / n * 100), 2),
        })

    # GMM para k in {3, 4, 5, 6, 7}
    for k in [3, 4, 5, 6, 7]:
        gmm = GaussianMixture(n_components=k, covariance_type="full", n_init=3, random_state=42)
        g_labels = gmm.fit_predict(X_scaled)
        sil = silhouette_score(X_scaled, g_labels, sample_size=20000, random_state=42)
        db = davies_bouldin_score(X_scaled, g_labels)
        ch = calinski_harabasz_score(X_scaled, g_labels)
        bic = gmm.bic(X_scaled)
        aic = gmm.aic(X_scaled)
        ari_km = adjusted_rand_score(km_labels_by_k[k], g_labels)
        counts = np.bincount(g_labels)

        rows.append({
            "algoritmo": "GMM (full)",
            "configuracion": f"k={k}",
            "k": k,
            "n_clusters_efectivos": k,
            "pct_ruido": 0.0,
            "inercia": np.nan,
            "silhouette": round(float(sil), 4),
            "davies_bouldin": round(float(db), 4),
            "calinski_harabasz": round(float(ch), 2),
            "bic": round(float(bic), 2),
            "aic": round(float(aic), 2),
            "bootstrap_ari_media": np.nan,
            "bootstrap_ari_std": np.nan,
            "bootstrap_ari_ic95_inf": np.nan,
            "bootstrap_ari_ic95_sup": np.nan,
            "ari_vs_kmeans_mismo_k": round(float(ari_km), 4),
            "cluster_min_pct": round(float(counts.min() / n * 100), 2),
            "cluster_max_pct": round(float(counts.max() / n * 100), 2),
        })

    # HDBSCAN en 3 configuraciones sobre el espacio 7D escalado
    for mcs, ms in [(100, 10), (250, 20), (500, 30)]:
        hdb = HDBSCAN(min_cluster_size=mcs, min_samples=ms, copy=True)
        h_labels = hdb.fit_predict(X_scaled)
        valid_mask = h_labels >= 0
        n_clusters_h = int(len(set(h_labels[valid_mask])))
        pct_noise = float((~valid_mask).mean() * 100)
        if n_clusters_h >= 2 and valid_mask.sum() > n_clusters_h:
            sil_h = float(silhouette_score(
                X_scaled[valid_mask],
                h_labels[valid_mask],
                sample_size=min(20000, int(valid_mask.sum())),
                random_state=42,
            ))
            db_h = float(davies_bouldin_score(X_scaled[valid_mask], h_labels[valid_mask]))
            ch_h = float(calinski_harabasz_score(X_scaled[valid_mask], h_labels[valid_mask]))
        else:
            sil_h, db_h, ch_h = np.nan, np.nan, np.nan

        rows.append({
            "algoritmo": "HDBSCAN (7D)",
            "configuracion": f"min_cluster_size={mcs}, min_samples={ms}",
            "k": np.nan,
            "n_clusters_efectivos": n_clusters_h,
            "pct_ruido": round(pct_noise, 2),
            "inercia": np.nan,
            "silhouette": round(sil_h, 4) if not np.isnan(sil_h) else np.nan,
            "davies_bouldin": round(db_h, 4) if not np.isnan(db_h) else np.nan,
            "calinski_harabasz": round(ch_h, 2) if not np.isnan(ch_h) else np.nan,
            "bic": np.nan,
            "aic": np.nan,
            "bootstrap_ari_media": np.nan,
            "bootstrap_ari_std": np.nan,
            "bootstrap_ari_ic95_inf": np.nan,
            "bootstrap_ari_ic95_sup": np.nan,
            "ari_vs_kmeans_mismo_k": np.nan,
            "cluster_min_pct": np.nan,
            "cluster_max_pct": np.nan,
        })

    df_bench = pd.DataFrame(rows)
    df_bench.to_csv(OUT_FASE2 / "benchmark.csv", index=False)
    return df_bench, km_labels_by_k


def test_2_6_sensitivity_option_a(panel_62048: pd.DataFrame, df_b: pd.DataFrame) -> pd.DataFrame:
    """
    2.6 Análisis de Sensibilidad = Opción A (para Limitaciones):
    Sobre las 62,048 secciones continuas, años con SV + NV < 50 se tratan como NaN (sin imputar),
    exigiendo al menos 2 elecciones presidenciales válidas y 2 elecciones intermedias válidas.
    Evalúa el ARI contra el Panel Principal (Opción B, N=53,644) en las secciones comunes:
      - Variante A1: sobre las 62,048 secciones con >=2 pres y >=2 inter válidas (sin filtro de salto LN)
      - Variante A2: sobre las 62,048 secciones con >=2 pres y >=2 inter válidas y sin salto abrupto de LN
    """
    df_a = panel_62048.copy()

    # Enmascarar como NaN cualquier sección-año con SV + NV < 50
    for y in YEARS:
        invalid_y = df_a[f"sv_nv_{y}"] < 50
        for prefix in ["p", "p_joven", "p_mayor", "p_mujer", "p_hombre"]:
            df_a.loc[invalid_y, f"{prefix}_{y}"] = np.nan

    pres_mat = df_a[[f"p_{y}" for y in PRES_YEARS]].to_numpy(dtype=float)
    mid_mat = df_a[[f"p_{y}" for y in MID_YEARS]].to_numpy(dtype=float)
    all_mat = df_a[[f"p_{y}" for y in YEARS]].to_numpy(dtype=float)

    n_pres_valid = np.sum(~np.isnan(pres_mat), axis=1)
    n_mid_valid = np.sum(~np.isnan(mid_mat), axis=1)

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        df_a["participacion_media_historica"] = np.nanmean(all_mat, axis=1)
        df_a["brecha_presidencial_intermedia"] = np.nanmean(pres_mat, axis=1) - np.nanmean(mid_mat, axis=1)

        # Tendencia OLS anual sobre los años válidos de cada sección (t_steps = 0, 3, 6, 9, 12, 15)
        x = np.array([0.0, 3.0, 6.0, 9.0, 12.0, 15.0], dtype=float)
        valid_mask = ~np.isnan(all_mat)
        n_valid = valid_mask.sum(axis=1)
        x_bar = np.where(n_valid > 0, (valid_mask * x).sum(axis=1) / np.maximum(n_valid, 1), np.nan)
        y_bar = df_a["participacion_media_historica"].to_numpy()
        x_diff = np.where(valid_mask, x - x_bar[:, None], 0.0)
        y_diff = np.where(valid_mask, all_mat - y_bar[:, None], 0.0)
        denom = (x_diff ** 2).sum(axis=1)
        df_a["tendencia_participacion_beta"] = np.where(denom > 0, (x_diff * y_diff).sum(axis=1) / np.maximum(denom, 1e-12), np.nan)

        std_a = np.nanstd(all_mat, axis=1, ddof=1)
        inv_cv_a = df_a["participacion_media_historica"].to_numpy() / (std_a + 1e-4)
        df_a["estabilidad_participacion"] = np.log1p(inv_cv_a)

        pj_mat = df_a[[f"p_joven_{y}" for y in YEARS]].to_numpy(dtype=float)
        pm_mat = df_a[[f"p_mayor_{y}" for y in YEARS]].to_numpy(dtype=float)
        pf_mat = df_a[[f"p_mujer_{y}" for y in YEARS]].to_numpy(dtype=float)
        ph_mat = df_a[[f"p_hombre_{y}" for y in YEARS]].to_numpy(dtype=float)

        tasa_j = np.nanmean(pj_mat, axis=1)
        tasa_m = np.nanmean(pm_mat, axis=1)
        tasa_f = np.nanmean(pf_mat, axis=1)
        tasa_h = np.nanmean(ph_mat, axis=1)

        df_a["brecha_generacional"] = tasa_m - tasa_j
        df_a["brecha_genero"] = tasa_f - tasa_h
        df_a["ratio_participacion_joven"] = tasa_j / df_a["participacion_media_historica"].to_numpy()

    non_null_a = df_a[FEATURE_COLS].notna().all(axis=1)
    cond_2pres_2mid = (n_pres_valid >= 2) & (n_mid_valid >= 2) & non_null_a

    results = []
    b_map = df_b.set_index("seccion_id")["cluster"]

    for variant_name, mask_a in [
        ("Opcion_A_62048_con_2pres_2inter_sin_filtro_LN", cond_2pres_2mid),
        ("Opcion_A_con_2pres_2inter_y_sin_salto_abrupto_LN", cond_2pres_2mid & (~df_a["consec_ln_jump"])),
    ]:
        sub_a = df_a[mask_a].copy().reset_index(drop=True)
        X_w = pd.DataFrame({c: winsorize_series(sub_a[c], 0.01, 0.99) for c in FEATURE_COLS})
        X_s = RobustScaler().fit_transform(X_w[FEATURE_COLS])
        km_a = KMeans(n_clusters=4, init="k-means++", n_init=50, random_state=42)
        sub_a["cluster_a"] = km_a.fit_predict(X_s)

        sil_a = silhouette_score(X_s, sub_a["cluster_a"], sample_size=20000, random_state=42)
        db_a = davies_bouldin_score(X_s, sub_a["cluster_a"])
        ch_a = calinski_harabasz_score(X_s, sub_a["cluster_a"])

        common = sub_a[sub_a["seccion_id"].isin(b_map.index)].copy()
        common["cluster_b"] = common["seccion_id"].map(b_map)
        ari_common = adjusted_rand_score(common["cluster_b"], common["cluster_a"])

        # Alinear etiquetas mediante algoritmo húngaro para calcular % de coincidencia exacta
        cm = pd.crosstab(common["cluster_b"], common["cluster_a"]).values
        row_ind, col_ind = linear_sum_assignment(-cm)
        exact_match_pct = float(cm[row_ind, col_ind].sum() / len(common) * 100)

        results.append({
            "variante": variant_name,
            "secciones_incluidas": len(sub_a),
            "secciones_adicionales_vs_panel_B": len(sub_a) - len(common),
            "secciones_comunes_con_panel_B": len(common),
            "ari_vs_panel_principal_B": round(float(ari_common), 4),
            "coincidencia_exacta_alineada_pct": round(exact_match_pct, 2),
            "silhouette_k4": round(float(sil_a), 4),
            "davies_bouldin_k4": round(float(db_a), 4),
            "calinski_harabasz_k4": round(float(ch_a), 2),
        })

    df_sens = pd.DataFrame(results)
    df_sens.to_csv(OUT_FASE2 / "sensibilidad_opcion_a.csv", index=False)
    return df_sens


def test_2_7_transition_matrix(panel_62048: pd.DataFrame, df_b: pd.DataFrame) -> pd.DataFrame:
    """
    Genera la matriz de transición entre los clusters originales (k=5 con el bug SV/LN y el artefacto C4)
    y los nuevos clusters seleccionados (k=4 con la fórmula oficial SV/(SV+NV) y el Panel Principal Opción B),
    incluyendo también la columna de secciones excluidas del Panel Principal.
    """
    orig_path = PROJECT_ROOT / "output" / "datasets" / "dataset_clusters_final.parquet"
    orig = pd.read_parquet(orig_path)[["edocve", "seccion", "cluster", "cluster_name"]].rename(
        columns={"cluster": "cluster_viejo", "cluster_name": "nombre_viejo"}
    )
    merged = panel_62048[["seccion_id", "edocve", "seccion"]].merge(
        orig, on=["edocve", "seccion"], how="left"
    )
    b_map = df_b.set_index("seccion_id")["cluster"]
    merged["cluster_nuevo"] = merged["seccion_id"].map(b_map).fillna(-1).astype(int)

    in_b = merged[merged["cluster_nuevo"] >= 0]
    ari_old_new = adjusted_rand_score(in_b["cluster_viejo"], in_b["cluster_nuevo"])

    rows = []
    for c_old in sorted(merged["cluster_viejo"].dropna().unique()):
        c_old_int = int(c_old)
        sub = merged[merged["cluster_viejo"] == c_old_int]
        old_name = str(sub["nombre_viejo"].iloc[0])
        total_old = len(sub)
        in_b_sub = sub[sub["cluster_nuevo"] >= 0]
        excl_sub = sub[sub["cluster_nuevo"] == -1]

        row = {
            "cluster_viejo": f"C{c_old_int}_viejo",
            "nombre_viejo": old_name,
            "total_secciones_62048": total_old,
            "excluidas_panel_B_n": len(excl_sub),
            "excluidas_panel_B_pct": round(len(excl_sub) / total_old * 100, 2),
            "en_panel_B_n": len(in_b_sub),
        }
        for c_new in range(4):
            cnt = int((in_b_sub["cluster_nuevo"] == c_new).sum())
            row[f"a_C{c_new}_nuevo_n"] = cnt
            row[f"a_C{c_new}_nuevo_pct_del_viejo_en_B"] = round(cnt / max(len(in_b_sub), 1) * 100, 2)
            row[f"a_C{c_new}_nuevo_pct_del_total_viejo"] = round(cnt / max(total_old, 1) * 100, 2)
        row["ari_global_viejo_vs_nuevo_en_B"] = round(float(ari_old_new), 4)
        rows.append(row)

    df_trans = pd.DataFrame(rows)
    df_trans.to_csv(OUT_FASE2 / "transicion_clusters.csv", index=False)
    return df_trans


def test_2_8_interpretability(X_scaled: np.ndarray, labels_4: np.ndarray) -> pd.DataFrame:
    """
    2.8 Interpretabilidad (no validación externa):
    Calcula importancia Gini de Random Forest, importancia por permutación y estadístico F de ANOVA para k=4.
    """
    rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(rf, X_scaled, labels_4, cv=cv, scoring="accuracy", n_jobs=-1)
    rf.fit(X_scaled, labels_4)

    perm = permutation_importance(
        rf, X_scaled, labels_4, n_repeats=10, random_state=42, n_jobs=-1
    )

    rows = []
    for i, col in enumerate(FEATURE_COLS):
        groups = [X_scaled[labels_4 == c, i] for c in range(4)]
        f_stat, p_val = f_oneway(*groups)
        rows.append({
            "variable": col,
            "rf_gini_importance": round(float(rf.feature_importances_[i]), 4),
            "rf_permutation_importance_mean": round(float(perm.importances_mean[i]), 4),
            "rf_permutation_importance_std": round(float(perm.importances_std[i]), 4),
            "anova_f_stat": round(float(f_stat), 2),
            "anova_p_value": float(p_val),
            "rf_cv5_accuracy_media": round(float(cv_scores.mean()), 4),
            "rf_cv5_accuracy_std": round(float(cv_scores.std()), 4),
            "nota_metodologica": "Medida de interpretabilidad interna sobre las mismas 7 variables del clustering (no validación externa)",
        })

    df_interp = pd.DataFrame(rows).sort_values("rf_gini_importance", ascending=False).reset_index(drop=True)
    df_interp["rango_importancia"] = np.arange(1, len(df_interp) + 1)
    df_interp.to_csv(OUT_FASE2 / "interpretabilidad_rf_anova.csv", index=False)
    return df_interp


def compute_projections_and_save_labels(
    df_b: pd.DataFrame,
    X_scaled: np.ndarray,
    km_labels_by_k: dict[int, np.ndarray],
) -> tuple[pd.DataFrame, dict]:
    """
    Calcula PCA (2D) y UMAP (2D, random_state=42) únicamente para visualización,
    y guarda outputs/fase2/etiquetas_finales.parquet de manera determinista con k=4 como cluster principal.
    """
    df_b["cluster"] = km_labels_by_k[4]
    df_b["cluster_k4"] = km_labels_by_k[4]
    df_b["cluster_k5"] = km_labels_by_k[5]
    df_b["cluster_k6"] = km_labels_by_k[6]

    pca = PCA(n_components=2, random_state=42)
    coords_pca = pca.fit_transform(X_scaled)
    df_b["pca_1"] = coords_pca[:, 0]
    df_b["pca_2"] = coords_pca[:, 1]

    reducer = umap.UMAP(
        n_neighbors=30,
        min_dist=0.1,
        n_components=2,
        metric="euclidean",
        random_state=42,
        n_jobs=1,
    )
    coords_umap = reducer.fit_transform(X_scaled)
    df_b["umap_1"] = coords_umap[:, 0]
    df_b["umap_2"] = coords_umap[:, 1]

    # Orden determinista por edocve, seccion
    df_b = df_b.sort_values(["edocve", "seccion"]).reset_index(drop=True)
    out_path = OUT_FASE2 / "etiquetas_finales.parquet"
    df_b.to_parquet(out_path, index=False)

    pca_info = {
        "k_seleccionado": 4,
        "pca_var_exp_1": round(float(pca.explained_variance_ratio_[0] * 100), 2),
        "pca_var_exp_2": round(float(pca.explained_variance_ratio_[1] * 100), 2),
        "pca_var_exp_total_2d": round(float(pca.explained_variance_ratio_.sum() * 100), 2),
        "sha256_etiquetas_finales": hashlib.sha256(out_path.read_bytes()).hexdigest(),
    }
    with open(OUT_FASE2 / "resumen_fase2.json", "w", encoding="utf-8") as f:
        json.dump(pca_info, f, indent=2, ensure_ascii=False)

    return df_b, pca_info


def main() -> None:
    print("[Fase 2] 1/8 Ingesta determinista desde raw_zips y reconciliación de universos...")
    panel_62048, reconciliacion = aggregate_sections_all_years()

    print("[Fase 2] 2/8 Aplicando reglas de Universo Principal (Opción B, cero imputación)...")
    panel_62048, df_b, df_univ = compute_features_and_universes(panel_62048, reconciliacion)
    print(f"  -> Panel Principal Opción B: {len(df_b):,} secciones | LN 2024: {df_b['ln_2024'].sum():,}")

    print("[Fase 2] 3/8 Prueba 2.1: Comparación de formulaciones de estabilidad (a, b, c) con k=4...")
    df_est = test_2_1_stability(df_b)

    print("[Fase 2] 4/8 Preparando variables winsorizadas (p1-p99) y escaladas (RobustScaler)...")
    X_winsor, X_scaled = prepare_scaled_features(df_b)

    print("[Fase 2] 5/8 Prueba 2.4: Benchmark K-Means++ (k=3..7, 100 bootstraps), GMM y HDBSCAN...")
    df_bench, km_labels_by_k = test_2_4_benchmark(X_scaled)
    labels_4 = km_labels_by_k[4]

    print("[Fase 2] 6/8 Pruebas 2.2 (VIF colinealidad) y 2.3 (Ventanas temporales) con k=4...")
    test_2_2_collinearity(X_winsor, X_scaled, labels_4)
    test_2_3_temporal_windows(df_b, labels_4)

    print("[Fase 2] 7/8 Pruebas 2.6 (Sensibilidad Opción A), 2.7 (Matriz transición) y 2.8 (RF/ANOVA) con k=4...")
    df_b["cluster"] = labels_4
    df_sens = test_2_6_sensitivity_option_a(panel_62048, df_b)
    df_trans = test_2_7_transition_matrix(panel_62048, df_b)
    df_interp = test_2_8_interpretability(X_scaled, labels_4)

    print("[Fase 2] 8/8 Calculando proyecciones PCA/UMAP deterministas y guardando etiquetas_finales.parquet...")
    df_b, pca_info = compute_projections_and_save_labels(df_b, X_scaled, km_labels_by_k)
    print(f"[Fase 2] Completado. SHA256(etiquetas_finales.parquet) = {pca_info['sha256_etiquetas_finales']}")


if __name__ == "__main__":
    main()
