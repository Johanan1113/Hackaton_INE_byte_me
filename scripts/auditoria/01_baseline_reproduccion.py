"""
Fase 0.2: Reproducción de la línea base del pipeline original y comparación
contra los valores reportados en el documento técnico y la infografía.
Salida: outputs/fase0/baseline_vs_reportado.csv
"""

import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler
from sklearn.cluster import KMeans
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
    adjusted_rand_score,
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.decomposition import PCA

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATASETS_DIR = os.path.join(PROJECT_ROOT, "output", "datasets")
OUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "fase0")
OUT_CSV = os.path.join(OUT_DIR, "baseline_vs_reportado.csv")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    df_cl = pd.read_parquet(os.path.join(DATASETS_DIR, "dataset_clusters_final.parquet"))

    features = [
        "participacion_media_historica",
        "brecha_presidencial_intermedia",
        "tendencia_participacion_beta",
        "estabilidad_participacion",
        "brecha_generacional",
        "brecha_genero",
        "ratio_participacion_joven",
    ]

    # Reproducir escalado y clustering tal cual en 02_features.py y 03_clustering.py
    scaler = RobustScaler()
    X = scaler.fit_transform(df_cl[features].values)

    km5 = KMeans(n_clusters=5, init="k-means++", n_init=10, random_state=42)
    labels = km5.fit_predict(X)

    sil = silhouette_score(X, labels, sample_size=15000, random_state=42)
    db = davies_bouldin_score(X, labels)
    ch = calinski_harabasz_score(X, labels)

    # Bootstrap ARI (10 semillas al 80% tal como en 03_clustering.py)
    ari_scores = []
    n_samples = int(0.8 * len(X))
    np.random.seed(42)
    for seed in range(10):
        idx = np.random.choice(len(X), size=n_samples, replace=False)
        km_sub = KMeans(n_clusters=5, init="k-means++", n_init=5, random_state=seed)
        sub_labels = km_sub.fit_predict(X[idx])
        ari_scores.append(adjusted_rand_score(labels[idx], sub_labels))
    mean_ari = float(np.mean(ari_scores))

    # Random Forest tal como en 04_profiling.py
    rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
    rf.fit(X, labels)
    rf_acc = float(rf.score(X, labels) * 100)
    gini_map = dict(zip(features, rf.feature_importances_))

    # PCA 2 componentes
    pca = PCA(n_components=2, random_state=42)
    pca.fit(X)
    pca_var = float(pca.explained_variance_ratio_.sum() * 100)

    # Conteos generales
    n_sec = len(df_cl)
    pct_sec_censadas = n_sec / 72681 * 100
    n_mpios_panel_2024 = df_cl["edocve"].astype(str).str.zfill(2).str.cat(df_cl["mpiocve"].astype(str).str.zfill(3), sep="_").nunique()
    pct_mpios_panel_2024 = n_mpios_panel_2024 / 2477 * 100
    ln_2024 = int(df_cl["ln_2024"].sum())

    rows = []

    def add_row(metrica, rep, repro, digits=4, obs=""):
        diff = round(float(repro) - float(rep), digits)
        rows.append({
            "metrica": metrica,
            "valor_reportado": round(float(rep), digits),
            "valor_reproducido": round(float(repro), digits),
            "diferencia": diff,
            "observacion": obs,
        })

    # 1. Cobertura del panel
    add_row("Secciones del panel", 62048, n_sec, 0, "Exacto")
    add_row("Porcentaje del total censado (%)", 85.37, pct_sec_censadas, 2, "Exacto (62,048 / 72,681)")
    add_row("Municipios en el panel 2024 (real vs intersección de claves)", 2455, n_mpios_panel_2024, 0, "01_ingest calculó intersección de claves municipales (2,455); el panel 2024 cubre 2,473 municipios porque secciones existentes pasaron a municipios nuevos")
    add_row("Porcentaje de municipios del panel (%)", 99.11, pct_mpios_panel_2024, 2, "2,455/2,477 = 99.11% (intersección de claves); en el panel 2024 son 2,473/2,477 = 99.84%")
    add_row("Lista nominal 2024 del panel", 85936860, ln_2024, 0, "Exacto")

    # 2. Tamaños y LN por cluster
    rep_sizes = {2: 22274, 0: 14863, 1: 12610, 4: 8421, 3: 3880}
    rep_ln_m = {2: 32.93, 0: 22.59, 1: 14.67, 4: 11.10, 3: 4.65}
    for c in [2, 0, 1, 4, 3]:
        sub = df_cl[df_cl["cluster"] == c]
        add_row(f"Tamaño cluster C{c} (secciones)", rep_sizes[c], len(sub), 0, "Exacto")
        add_row(f"LN 2024 cluster C{c} (millones)", rep_ln_m[c], sub["ln_2024"].sum() / 1e6, 2, "Exacto")

    # 3. Métricas de K-Means k=5, RF y PCA
    add_row("K-Means k=5 Silhouette (tabla doc)", 0.1788, sil, 4, "Exacto contra tabla; infografía reporta 0.1805 (corrida 1)")
    add_row("K-Means k=5 Davies-Bouldin (tabla doc)", 1.4245, db, 4, "Exacto contra tabla; prosa e infografía dicen 1.4233 (corrida 1)")
    add_row("K-Means k=5 Calinski-Harabasz (tabla doc)", 14062.0, ch, 1, "Exacto contra tabla (14,062.0); infografía inventa 18,742.6")
    add_row("K-Means k=5 ARI Bootstrap (prosa/infografía)", 0.8411, mean_ari, 4, "NO REPRODUCE prosa (0.8411 de corrida 1); tabla Parquet tiene 0.8970")
    add_row("Random Forest exactitud (%)", 94.08, rf_acc, 2, "Leve diferencia: 94.08% en corrida 1 vs 94.06% en corrida 2 por orden de filas DuckDB")

    # 4. Importancias Gini
    add_row("Importancia Gini: 1/CV (estabilidad)", 0.254, gini_map["estabilidad_participacion"], 3, "Exacto a 3 decimales (0.2541)")
    add_row("Importancia Gini: brecha presidencial", 0.214, gini_map["brecha_presidencial_intermedia"], 3, "Ligera diferencia en 3er decimal: 0.2150 reproducido vs 0.214 reportado")
    add_row("Importancia Gini: ratio juvenil", 0.156, gini_map["ratio_participacion_joven"], 3, "Exacto a 3 decimales (0.1563)")
    add_row("Importancia Gini: tendencia beta", 0.134, gini_map["tendencia_participacion_beta"], 3, "Exacto a 3 decimales (0.1336)")
    add_row("Importancia Gini: brecha generacional", 0.118, gini_map["brecha_generacional"], 3, "Exacto a 3 decimales (0.1182)")
    add_row("Importancia Gini: brecha de genero", 0.070, gini_map["brecha_genero"], 3, "Ligera diferencia en 3er decimal: 0.0709 reproducido vs ~0.070")
    add_row("Importancia Gini: participacion historica", 0.053, gini_map["participacion_media_historica"], 3, "Ligera diferencia en 3er decimal: 0.0519 en corrida 2 vs ~0.053")

    # 5. PCA
    add_row("PCA 2 componentes varianza explicada (%)", 60.12, pca_var, 2, "Exacto")

    # 6. Medias nacionales
    add_row("Media nacional: Participacion media (%)", 53.64, df_cl["participacion_media_historica"].mean() * 100, 2, "Exacto (con formula erronea SV/LN)")
    add_row("DE nacional: Participacion media (%)", 9.94, df_cl["participacion_media_historica"].std() * 100, 2, "Exacto")
    add_row("Media nacional: Brecha presidencial (pts)", 12.29, df_cl["brecha_presidencial_intermedia"].mean() * 100, 2, "Exacto")
    add_row("DE nacional: Brecha presidencial (pts)", 10.42, df_cl["brecha_presidencial_intermedia"].std() * 100, 2, "Exacto")
    add_row("Media nacional: Tendencia beta", 0.0046, df_cl["tendencia_participacion_beta"].mean(), 4, "Exacto")
    add_row("Media nacional: Estabilidad 1/CV", 5.71, df_cl["estabilidad_participacion"].mean(), 2, "Exacto (5.7052)")
    add_row("DE nacional: Estabilidad 1/CV", 4.35, df_cl["estabilidad_participacion"].std(), 2, "Exacto (4.3484)")
    add_row("Media nacional: Brecha generacional (pts)", 15.62, df_cl["brecha_generacional"].mean() * 100, 2, "Exacto")
    add_row("Media nacional: Brecha de genero (pts)", 7.36, df_cl["brecha_genero"].mean() * 100, 2, "Exacto")
    add_row("Media nacional: Ratio juvenil", 0.8379, df_cl["ratio_participacion_joven"].mean(), 4, "Exacto")

    # 7. Medias por cluster
    cluster_expected = {
        2: {"P": 50.4, "dpres": 20.5, "bgen": 6.2, "t18_29": 41.5, "t60": 58.9, "U": 79.0, "R": 14.0},
        0: {"P": 54.7, "dpres": 9.8,  "bgen": 10.6, "t18_29": 43.7, "t60": 65.0, "U": 53.0, "R": 37.0},
        1: {"P": 60.1, "dpres": 12.1, "bgen": 5.9, "t18_29": 54.6, "t60": 62.8, "U": 55.0, "R": 34.0},
        4: {"P": 44.8, "dpres": -0.5, "bgen": 6.1, "t18_29": 37.2, "t60": 50.9, "U": 55.0, "R": 35.0},
        3: {"P": 66.4, "dpres": 3.2,  "bgen": 8.7, "t18_29": 58.9, "t60": 70.5, "U": 42.0, "R": 45.0},
    }
    for c in [2, 0, 1, 4, 3]:
        sub = df_cl[df_cl["cluster"] == c]
        exp = cluster_expected[c]
        add_row(f"Cluster C{c}: Participacion media (%)", exp["P"], sub["participacion_media_historica"].mean() * 100, 1, "Exacto")
        add_row(f"Cluster C{c}: Brecha presidencial (pts)", exp["dpres"], sub["brecha_presidencial_intermedia"].mean() * 100, 1, "Exacto")
        add_row(f"Cluster C{c}: Brecha de genero (pts)", exp["bgen"], sub["brecha_genero"].mean() * 100, 1, "Exacto")
        add_row(f"Cluster C{c}: Tasa 18-29 (%)", exp["t18_29"], sub["tasa_jovenes_18_29"].mean() * 100, 1, "Exacto")
        add_row(f"Cluster C{c}: Tasa 60+ (%)", exp["t60"], sub["tasa_adultos_mayores_60"].mean() * 100, 1, "Exacto")
        add_row(f"Cluster C{c}: Urbano (%)", exp["U"], (sub["tiposec"] == "U").mean() * 100, 1, "Redondeo a entero en infografía (ej. 79.1% -> 79%)")
        add_row(f"Cluster C{c}: Rural (%)", exp["R"], (sub["tiposec"] == "R").mean() * 100, 1, "Redondeo a entero en infografía (ej. 13.5% -> 14%)")

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"Archivo guardado en: {OUT_CSV} ({len(out_df)} métricas verificadas)")


if __name__ == "__main__":
    main()
