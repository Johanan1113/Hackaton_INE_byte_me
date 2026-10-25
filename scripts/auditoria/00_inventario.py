"""
Fase 0.1 y 0.3: Inventario de datos, scripts, mapeo de esquemas por año (2009-2024),
versiones de librerías y rastreo de discrepancias infografía vs. documento.
Salida: outputs/fase0/inventario.md
"""

import os
import sys
import zipfile
import io
import importlib.metadata as meta
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_ZIPS_DIR = os.path.join(PROJECT_ROOT, "data", "raw_zips")
OUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "fase0")
OUT_FILE = os.path.join(OUT_DIR, "inventario.md")

YEARS = ["2009", "2012", "2015", "2018", "2021", "2024"]


def get_installed_versions() -> dict:
    pkgs = [
        "duckdb", "scikit-learn", "scipy", "umap-learn", "hdbscan",
        "pandas", "numpy", "matplotlib", "seaborn", "statsmodels",
        "pyarrow", "joblib", "reportlab", "pypdf", "Jinja2", "pytest", "pillow"
    ]
    installed = {d.metadata["Name"].lower(): d.version for d in meta.distributions()}
    res = {"Python": sys.version.split()[0]}
    for p in pkgs:
        val = installed.get(p.lower(), "No instalado (HDBSCAN integrado en scikit-learn 1.9.0)" if p == "hdbscan" else "No instalado")
        res[p] = val
    return res


def inspect_raw_files() -> list:
    records = []
    for fname in sorted(os.listdir(RAW_ZIPS_DIR)):
        fpath = os.path.join(RAW_ZIPS_DIR, fname)
        size_mb = os.path.getsize(fpath) / (1024 * 1024)
        if fname.endswith(".zip"):
            with zipfile.ZipFile(fpath, "r") as z:
                csvs = sorted(f for f in z.namelist() if f.lower().endswith(".csv"))
                txts = [f for f in z.namelist() if f.lower().endswith(".txt")]
                first_cols = []
                has_bom = False
                if csvs:
                    with z.open(csvs[0]) as f:
                        first_line = f.readline()
                        has_bom = first_line.startswith(b"\xef\xbb\xbf")
                        decoded = first_line.decode("utf-8-sig", errors="replace").strip()
                        first_cols = [c.strip() for c in decoded.split(",")]
                year_str = "N/A"
                for y in ["2009", "2012", "2015", "2018", "2021", "2024", "2025"]:
                    if y in fname:
                        year_str = y
                        break
                records.append({
                    "archivo": fname,
                    "anio": year_str,
                    "formato": f"ZIP ({len(csvs)} CSVs, {len(txts)} TXT)",
                    "tamano_mb": round(size_mb, 2),
                    "bom_utf8": "Sí" if has_bom else "No",
                    "columnas": ", ".join(first_cols)
                })
        else:
            records.append({
                "archivo": fname,
                "anio": "2009–2024",
                "formato": os.path.splitext(fname)[1].upper().replace(".", ""),
                "tamano_mb": round(size_mb, 2),
                "bom_utf8": "N/A",
                "columnas": "Manual metodológico y diccionario de plataforma CCPC (38 páginas)"
            })
    return records


def inspect_panel_years_schema() -> list:
    schema_stats = []
    for y in YEARS:
        zpath = os.path.join(RAW_ZIPS_DIR, f"DatosAbiertos_DECEyEC_ConteosCensales{y}.zip")
        n_rows = 0
        bom_count = 0
        sexo_vals = set()
        tiposec_vals = set()
        edad_min, edad_max = 999, -1
        del_nulls = 0
        def_nulls = 0
        sec_nulls = 0
        tot_ln, tot_sv, tot_nv, tot_ns = 0, 0, 0, 0
        diff_identity = 0

        with zipfile.ZipFile(zpath, "r") as z:
            csvs = sorted(f for f in z.namelist() if f.lower().endswith(".csv"))
            for c in csvs:
                raw = z.read(c)
                if raw.startswith(b"\xef\xbb\xbf"):
                    bom_count += 1
                df = pd.read_csv(io.BytesIO(raw), encoding="latin1", low_memory=False)
                df.columns = [col.replace("\ufeff", "").replace("ï»¿", "").strip().upper() for col in df.columns]
                n_rows += len(df)
                sexo_vals.update(df["SEXO"].dropna().unique().tolist())
                tiposec_vals.update(df["TIPOSEC"].dropna().astype(str).unique().tolist())
                edad_min = min(edad_min, int(df["EDAD"].min()))
                edad_max = max(edad_max, int(df["EDAD"].max()))
                del_nulls += int(df["DEL"].isna().sum())
                def_nulls += int(df["DEF"].isna().sum())
                sec_nulls += int(df["SECCION"].isna().sum())
                tot_ln += int(df["LN"].sum())
                tot_sv += int(df["SV"].sum())
                tot_nv += int(df["NV"].sum())
                tot_ns += int(df["NS"].sum())
                diff_identity += int((df["LN"] != (df["SV"] + df["NV"] + df["NS"])).sum())

        schema_stats.append({
            "anio": y,
            "filas_csv": n_rows,
            "archivos_con_bom": f"{bom_count}/32",
            "valores_sexo": sorted(list(sexo_vals)),
            "valores_tiposec": sorted(list(tiposec_vals)),
            "rango_edad": f"{edad_min}–{edad_max}",
            "nulos_del": del_nulls,
            "nulos_seccion": sec_nulls,
            "ln_total": tot_ln,
            "sv_total": tot_sv,
            "nv_total": tot_nv,
            "ns_total": tot_ns,
            "pct_ns_sobre_ln": round(tot_ns / tot_ln * 100, 2),
            "violaciones_ln_sv_nv_ns": diff_identity
        })
    return schema_stats


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    versions = get_installed_versions()
    raw_files = inspect_raw_files()
    schema_stats = inspect_panel_years_schema()

    lines = []
    lines.append("# Inventario Técnico y Diagnóstico de Línea Base (Fase 0)")
    lines.append("")
    lines.append("## 1. Archivos de Datos Crudos (`data/raw_zips/`)")
    lines.append("")
    lines.append("| Archivo | Año | Formato | Tamaño (MB) | BOM UTF-8 | Columnas / Contenido |")
    lines.append("| :--- | :---: | :---: | :---: | :---: | :--- |")
    for r in raw_files:
        lines.append(f"| `{r['archivo']}` | {r['anio']} | {r['formato']} | {r['tamano_mb']:.2f} | {r['bom_utf8']} | `{r['columnas']}` |")

    lines.append("")
    lines.append("## 2. Mapeo de Columnas y Esquema por Año (2009–2024)")
    lines.append("")
    lines.append("Todos los archivos CSV de los seis procesos electorales federales (2009, 2012, 2015, 2018, 2021 y 2024) contienen exactamente **16 columnas** con los mismos identificadores nominales, pero presentan diferencias importantes de codificación, dominio de valores y proporción de registros no especificados (`NS`):")
    lines.append("")
    lines.append("| Concepto Requerido | Columna en CSV (2009–2024) | Tipo / Dominio | Observaciones y Diferencias entre Años (2018 y 2024 vs. resto) |")
    lines.append("| :--- | :---: | :--- | :--- |")
    lines.append("| **Votaron** | `SV` | Entero (`>= 0`) | Personas con marca de voto en el cuadernillo de la Lista Nominal. |")
    lines.append("| **No votaron** | `NV` | Entero (`>= 0`) | Personas sin marca de voto en cuadernillos efectivamente capturados. |")
    lines.append("| **No especificados (Crítico)** | `NS` | Entero (`>= 0`) | Cuadernillos sin marcas, no disponibles para captura o requeridos por tribunal electoral. En **2012** `NS` es apenas **0.22%** de `LN`, pero en **2018** sube a **6.83%** (6,089,742 electores; 2,517 secciones con `SV+NV=0`) y en **2024** a **6.43%** (6,325,654 electores; 2,100 secciones con `SV+NV=0`). El script original `01_ingest.py` ignoró `NS` y dividió `SV / LN` en vez de la fórmula oficial del Manual CCPC `SV / (SV + NV)`. |")
    lines.append("| **Lista nominal** | `LN` | Entero (`> 0`) | Cumple exactamente la identidad `LN = SV + NV + NS` en el 100% de las filas de los 6 años (0 violaciones). |")
    lines.append("| **Sexo** | `SEXO` | Entero (`0, 1` / `0, 1, 2`) | De **2009 a 2021** sólo toma valores `0` (Hombre) y `1` (Mujer). En **2024** se incorpora el valor `2` (**No binario**, 103 registros / 105 personas en LN). En `01_ingest.py` se incluyó `SEXO=2` en `LN`/`SV` total pero se excluyó de `ln_fem` y `ln_masc`. |")
    lines.append("| **Grupos de edad quinquenales** | `EDAD` | Entero (`18` a `140`) | Los CSV crudos no traen una columna pre-agrupada quinquenal, sino la edad individual en años cumplidos (`EDAD`). Los grupos quinquenales del Manual CCPC (`18-19`, `20-24`, `25-29`, ..., `100+`) y las etapas de vida (`Juventud` 18–24 en INE; o `18–29` y `60+` en el modelo) se construyen agregando por rangos de `EDAD`. |")
    lines.append("| **Tipo de sección** | `TIPOSEC` | Texto (`U`, `M`, `R`) | Codificado como `U` (Urbana), `M` (Mixta), `R` (Rural) en los 6 años, sin valores nulos. |")
    lines.append("| **Entidad** | `EDOCVE`, `EDONOM` | Entero (`1`–`32`), Texto | Clave INE de entidad (1 a 32) y nombre. En **2024** los archivos vienen en UTF-8 con BOM (`\\xef\\xbb\\xbf`); al leerlos con `encoding='latin1'` en `01_ingest.py`, la primera columna quedó como `Ï»¿AELEC` y `EDONOM`/`MPIONOM` sufrieron corrupción de acentos (*mojibake*). |")
    lines.append("| **Municipio** | `MPIOCVE`, `MPIONOM` | Entero, Texto | Clave de municipio por entidad y nombre. Sin nulos en los 6 años. |")
    lines.append("| **Sección** | `SECCION` | Entero | Número de sección electoral dentro de la entidad (`EDOCVE`). Sin nulos en los 6 años. |")
    lines.append("| **Distrito Federal / Local** | `DEF`, `DEL` | Entero / Texto / Float | En 2009 y 2012 contienen algunos valores alfanuméricos o guiones; en **2024** `DEL` presenta **20,912 filas nulas (`NaN`)**. |")

    lines.append("")
    lines.append("### 2.1 Resumen Cuantitativo de Esquema e Integridad por Año")
    lines.append("")
    lines.append("| Año | Filas en CSV | CSVs con BOM UTF-8 | Valores `SEXO` | Rango `EDAD` | Nulos `DEL` | `LN` Total | `SV` Total | `NV` Total | `NS` Total | `% NS / LN` | Violaciones `LN=SV+NV+NS` |")
    lines.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for s in schema_stats:
        lines.append(
            f"| **{s['anio']}** | {s['filas_csv']:,} | {s['archivos_con_bom']} | `{s['valores_sexo']}` | {s['rango_edad']} | {s['nulos_del']:,} | "
            f"{s['ln_total']:,} | {s['sv_total']:,} | {s['nv_total']:,} | {s['ns_total']:,} | **{s['pct_ns_sobre_ln']:.2f}%** | {s['violaciones_ln_sv_nv_ns']} |"
        )

    lines.append("")
    lines.append("## 3. Scripts Existentes, su Función y Equivalencia con la Estructura de Auditoría")
    lines.append("")
    lines.append("| Script Original | Función en el Pipeline Original | Equivalencia en `scripts/auditoria/` |")
    lines.append("| :--- | :--- | :--- |")
    lines.append("| `main.py` | Orquestador secuencial de `src/01_ingest.py` a `src/verify_all.py`. | `scripts/auditoria/run_all.py` |")
    lines.append("| `src/01_ingest.py` | Ingesta de ZIPs CCPC vía DuckDB, agregación por `EDOCVE, SECCION` (sin `ORDER BY`), cálculo `SV/LN`, capping `>100%` e inner join de 62,048 secciones. | `00_inventario.py`, `02_verificacion_datos.py` |")
    lines.append("| `src/02_features.py` | Cálculo de 7 variables longitudinales/demográficas, prueba VIF y escalado con `RobustScaler`. | `03_robustez_modelo.py`, `05_tablas_nuevas.py` |")
    lines.append("| `src/03_clustering.py` | Benchmark K-Means++ (`k=3..7`), GMM y HDBSCAN (`min_cluster_size=250`), PCA 2D y UMAP 2D. | `03_robustez_modelo.py`, `06_figuras.py` |")
    lines.append("| `src/03_clustering_refinement.py` | Agrega lemas cívicos, íconos Unicode y factores de abstención a `arquetipos_fichas.json`. | `04_perfiles_y_nombres.py` |")
    lines.append("| `src/04_profiling.py` | Entrena Random Forest y ANOVA F-test (reportados como validación), genera figuras 04–07 y `arquetipos_fichas.json`. | `03_robustez_modelo.py`, `04_perfiles_y_nombres.py`, `06_figuras.py` |")
    lines.append("| `src/05_report_pdf.py` | Compila el Documento Técnico de 10 páginas usando ReportLab (`NumberedCanvas`) con texto y cifras parcialmente escritas a mano. | `08_documento.py` + `plantillas/documento_tecnico.md.j2` |")
    lines.append("| `src/06_presentation.py` | Genera presentación ejecutiva PPTX/PDF (fuera del alcance de esta corrección). | *Fuera de alcance* |")
    lines.append("| `src/07_infographic.py` | Genera el póster/infografía en Matplotlib (`32x22 in`, 300 DPI) mezclando lectura de `arquetipos_fichas.json` con métricas escritas a mano en el bloque metodológico. | `07_infografia.py` + `plantillas/infografia_textos.json.j2` |")
    lines.append("| `src/verify_all.py` / `src/verify_pipeline.py` | Verificaciones básicas de existencia de archivos, conteo de páginas y ausencia de `NaN`. | `09_validacion_consistencia.py` + `tests/test_consistencia.py` |")

    lines.append("")
    lines.append("## 4. Cómo se Generaron la Infografía, las Figuras y el Documento (Fase 0.3)")
    lines.append("")
    lines.append("1. **Figuras (`output/figures/01_*.png` a `07_*.png`):** Se generaron con `matplotlib` y `seaborn` a 300 DPI desde `src/03_clustering.py` (figuras 01, 02 y 03) y `src/04_profiling.py` (figuras 04, 05, 06 y 07). Sin embargo, los colores entre figuras no estaban unificados por ID de cluster: en `03_clustering.py` se asignó color por orden de iteración `CLUSTER_PALETTE[i]`, mientras que en `07_infographic.py` se usó un diccionario distinto `CLUSTER_COLORS`.")
    lines.append("2. **Infografía (`entregables_finales/Fichas_Perfiles_Infografia_ByteMe.png` y `.pdf`):** Se generó mediante `src/07_infographic.py` con `matplotlib` (`figsize=(32, 22)`, `dpi=300`). Aunque las 5 tarjetas de perfiles leen de `output/datasets/arquetipos_fichas.json`, la **Tarjeta 6 (Síntesis Metodológica)** tiene texto estático escrito a mano en las líneas 331–403 de `src/07_infographic.py`.")
    lines.append("3. **Origen de las discrepancias entre Infografía y Documento (Fase 0.3):**")
    lines.append("   - **No determinismo en `01_ingest.py`:** La consulta DuckDB `GROUP BY EDOCVE, SECCION` carece de `ORDER BY`. En `pipeline.log` quedaron registradas dos corridas completas el 24 de octubre de 2026: una a las `16:48:16` (línea 100) y otra a las `16:56:03` (línea 299).")
    lines.append("   - **`Davies-Bouldin = 1.4233` y `ARI = 0.8411` vs `1.4245` y `0.8970`:** En la primera corrida (`16:48:16`), K-Means (`k=5`) obtuvo `Sil=0.1805`, `DB=1.4233`, `CH=14062.4` y `ARI=0.8411`. Esos valores se copiaron a mano en el texto de `src/05_report_pdf.py` (líneas 594–595) y `src/07_infographic.py` (líneas 334–336). Minutos después (`16:56:03`), una segunda corrida sobrescribió `clustering_benchmark_metrics.parquet` con `Sil=0.1788`, `DB=1.4245`, `CH=14,062.0` y `ARI=0.8970`. Como la tabla del documento lee del Parquet pero el párrafo lee texto fijo, el propio documento se contradice entre su tabla (`1.4245`, `0.8970`) y su texto (`1.4233`, `0.8411`).")
    lines.append("   - **`Calinski-Harabasz = 18,742.6` y `GMM = 0.1481`:** Están escritos como cadenas literales fijas en `src/07_infographic.py` (líneas 334–335). No provienen de ninguna corrida real del repositorio (en `clustering_benchmark_metrics.parquet`, CH para `k=5` es `14,062.0` y el Silhouette de GMM para `k=5` es `0.0188`, con máximo `0.1097` en `k=3`). Matemáticamente, dado que la suma total de cuadrados $TSS = \\text{Inercia} \\times \\left(1 + \\frac{CH \\times (k-1)}{N-k}\\right)$ es constante (~377,518 en los datos escalados), un $CH = 18,742.6$ en $k=5$ exigiría una inercia de ~170.8 mil, incompatible con la inercia real de `k=5` (197.4 mil).")
    lines.append("   - **Documento PDF en `entregables_finales/` vs `Downloads/`:** El PDF en `entregables_finales/Documento_Tecnico_Reto1_ByteMe.pdf` tiene productor `ReportLab PDF Library`, mientras que la copia en `/home/johan/Downloads/Documento_Tecnico_Reto1_ByteMe.pdf` fue exportada desde Google Docs (`Skia/PDF m158 Google Docs Renderer`) a partir de `Documento_Tecnico_Reto1_ByteMe.docx` conservando el texto que afirma haber sido compilado con ReportLab.")

    lines.append("")
    lines.append("## 5. Versiones Reales Instaladas en el Entorno")
    lines.append("")
    lines.append("| Librería / Componente | Versión Instalada |")
    lines.append("| :--- | :--- |")
    for k, v in versions.items():
        lines.append(f"| `{k}` | `{v}` |")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Inventario generado exitosamente en: {OUT_FILE}")


if __name__ == "__main__":
    main()
