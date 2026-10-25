# Inventario Técnico y Diagnóstico de Línea Base (Fase 0)

## 1. Archivos de Datos Crudos (`data/raw_zips/`)

| Archivo | Año | Formato | Tamaño (MB) | BOM UTF-8 | Columnas / Contenido |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `DatosAbiertos_DECEyEC_ConteosCensales2009.zip` | 2009 | ZIP (32 CSVs, 1 TXT) | 38.34 | No | `AELEC, FELECCION, EDOCVE, EDONOM, MPIOCVE, MPIONOM, SECCION, TIPOSEC, DEF, DEL, SEXO, EDAD, LN, SV, NV, NS` |
| `DatosAbiertos_DECEyEC_ConteosCensales2012.zip` | 2012 | ZIP (32 CSVs, 1 TXT) | 37.69 | No | `AELEC, FELECCION, EDOCVE, EDONOM, MPIOCVE, MPIONOM, SECCION, TIPOSEC, DEF, DEL, SEXO, EDAD, LN, SV, NV, NS` |
| `DatosAbiertos_DECEyEC_ConteosCensales2015.zip` | 2015 | ZIP (32 CSVs, 1 TXT) | 40.62 | No | `AELEC, FELECCION, EDOCVE, EDONOM, MPIOCVE, MPIONOM, SECCION, TIPOSEC, DEF, DEL, SEXO, EDAD, LN, SV, NV, NS` |
| `DatosAbiertos_DECEyEC_ConteosCensales2018.zip` | 2018 | ZIP (32 CSVs, 1 TXT) | 41.38 | No | `AELEC, FELECCION, EDOCVE, EDONOM, MPIOCVE, MPIONOM, SECCION, TIPOSEC, DEF, DEL, SEXO, EDAD, LN, SV, NV, NS` |
| `DatosAbiertos_DECEyEC_ConteosCensales2021.zip` | 2021 | ZIP (32 CSVs, 1 TXT) | 42.30 | No | `AELEC, FELECCION, EDOCVE, EDONOM, MPIOCVE, MPIONOM, SECCION, TIPOSEC, DEF, DEL, SEXO, EDAD, LN, SV, NV, NS` |
| `DatosAbiertos_DECEyEC_ConteosCensales2024.zip` | 2024 | ZIP (32 CSVs, 1 TXT) | 78.60 | Sí | `AELEC, FELECCION, EDOCVE, EDONOM, MPIOCVE, MPIONOM, SECCION, TIPOSEC, DEF, DEL, SEXO, EDAD, LN, SV, NV, NS` |
| `DatosAbiertos_DECEyEC_ConteosCensalesPJ2025.zip` | 2025 | ZIP (31 CSVs, 1 TXT) | 85.04 | Sí | `AELEC, EDOCVE, EDONOM, MPIOCVE, MPIONOM, SECCION, TIPOSEC, DEF, CJ, DEJ, SEXO, EDAD, LN, SV, NV, NS` |
| `DatosAbiertos_DECEyEC_ConteosCensales_PrisionPreventiva2024.zip` | 2024 | ZIP (1 CSVs, 1 TXT) | 0.01 | Sí | `AELEC, ESTADO, EDONOM, DEF, SEXO` |
| `DatosAbiertos_DECEyEC_ConteosCensales_VotoAnticipado2024.zip` | 2024 | ZIP (1 CSVs, 1 TXT) | 0.02 | Sí | `AELEC, EDOCVE, EDONOM, MPIOCVE, MPIONOM, DEF, DEL, SEXO` |
| `Manual-Conteos-Censales-2009-2024.pdf` | 2009–2024 | PDF | 2.50 | N/A | `Manual metodológico y diccionario de plataforma CCPC (38 páginas)` |

## 2. Mapeo de Columnas y Esquema por Año (2009–2024)

Todos los archivos CSV de los seis procesos electorales federales (2009, 2012, 2015, 2018, 2021 y 2024) contienen exactamente **16 columnas** con los mismos identificadores nominales, pero presentan diferencias importantes de codificación, dominio de valores y proporción de registros no especificados (`NS`):

| Concepto Requerido | Columna en CSV (2009–2024) | Tipo / Dominio | Observaciones y Diferencias entre Años (2018 y 2024 vs. resto) |
| :--- | :---: | :--- | :--- |
| **Votaron** | `SV` | Entero (`>= 0`) | Personas con marca de voto en el cuadernillo de la Lista Nominal. |
| **No votaron** | `NV` | Entero (`>= 0`) | Personas sin marca de voto en cuadernillos efectivamente capturados. |
| **No especificados (Crítico)** | `NS` | Entero (`>= 0`) | Cuadernillos sin marcas, no disponibles para captura o requeridos por tribunal electoral. En **2012** `NS` es apenas **0.22%** de `LN`, pero en **2018** sube a **6.83%** (6,089,742 electores; 2,517 secciones con `SV+NV=0`) y en **2024** a **6.43%** (6,325,654 electores; 2,100 secciones con `SV+NV=0`). El script original `01_ingest.py` ignoró `NS` y dividió `SV / LN` en vez de la fórmula oficial del Manual CCPC `SV / (SV + NV)`. |
| **Lista nominal** | `LN` | Entero (`> 0`) | Cumple exactamente la identidad `LN = SV + NV + NS` en el 100% de las filas de los 6 años (0 violaciones). |
| **Sexo** | `SEXO` | Entero (`0, 1` / `0, 1, 2`) | De **2009 a 2021** sólo toma valores `0` (Hombre) y `1` (Mujer). En **2024** se incorpora el valor `2` (**No binario**, 103 registros / 105 personas en LN). En `01_ingest.py` se incluyó `SEXO=2` en `LN`/`SV` total pero se excluyó de `ln_fem` y `ln_masc`. |
| **Grupos de edad quinquenales** | `EDAD` | Entero (`18` a `140`) | Los CSV crudos no traen una columna pre-agrupada quinquenal, sino la edad individual en años cumplidos (`EDAD`). Los grupos quinquenales del Manual CCPC (`18-19`, `20-24`, `25-29`, ..., `100+`) y las etapas de vida (`Juventud` 18–24 en INE; o `18–29` y `60+` en el modelo) se construyen agregando por rangos de `EDAD`. |
| **Tipo de sección** | `TIPOSEC` | Texto (`U`, `M`, `R`) | Codificado como `U` (Urbana), `M` (Mixta), `R` (Rural) en los 6 años, sin valores nulos. |
| **Entidad** | `EDOCVE`, `EDONOM` | Entero (`1`–`32`), Texto | Clave INE de entidad (1 a 32) y nombre. En **2024** los archivos vienen en UTF-8 con BOM (`\xef\xbb\xbf`); al leerlos con `encoding='latin1'` en `01_ingest.py`, la primera columna quedó como `Ï»¿AELEC` y `EDONOM`/`MPIONOM` sufrieron corrupción de acentos (*mojibake*). |
| **Municipio** | `MPIOCVE`, `MPIONOM` | Entero, Texto | Clave de municipio por entidad y nombre. Sin nulos en los 6 años. |
| **Sección** | `SECCION` | Entero | Número de sección electoral dentro de la entidad (`EDOCVE`). Sin nulos en los 6 años. |
| **Distrito Federal / Local** | `DEF`, `DEL` | Entero / Texto / Float | En 2009 y 2012 contienen algunos valores alfanuméricos o guiones; en **2024** `DEL` presenta **20,912 filas nulas (`NaN`)**. |

### 2.1 Resumen Cuantitativo de Esquema e Integridad por Año

| Año | Filas en CSV | CSVs con BOM UTF-8 | Valores `SEXO` | Rango `EDAD` | Nulos `DEL` | `LN` Total | `SV` Total | `NV` Total | `NS` Total | `% NS / LN` | Violaciones `LN=SV+NV+NS` |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2009** | 8,706,843 | 0/32 | `[0, 1]` | 18–130 | 0 | 77,481,831 | 33,316,974 | 42,298,963 | 1,865,894 | **2.41%** | 0 |
| **2012** | 8,604,456 | 0/32 | `[0, 1]` | 18–132 | 0 | 76,490,962 | 47,383,154 | 28,939,159 | 168,649 | **0.22%** | 0 |
| **2015** | 9,106,059 | 0/32 | `[0, 1]` | 18–117 | 0 | 83,563,462 | 36,926,612 | 41,517,874 | 5,118,976 | **6.13%** | 0 |
| **2018** | 9,251,122 | 0/32 | `[0, 1]` | 18–137 | 0 | 89,123,997 | 51,784,399 | 31,249,856 | 6,089,742 | **6.83%** | 0 |
| **2021** | 9,430,502 | 0/32 | `[0, 1]` | 18–139 | 0 | 93,532,133 | 46,389,189 | 43,099,624 | 4,043,320 | **4.32%** | 0 |
| **2024** | 9,773,730 | 32/32 | `[0, 1, 2]` | 18–140 | 20,912 | 98,330,348 | 54,899,228 | 37,105,466 | 6,325,654 | **6.43%** | 0 |

## 3. Scripts Existentes, su Función y Equivalencia con la Estructura de Auditoría

| Script Original | Función en el Pipeline Original | Equivalencia en `scripts/auditoria/` |
| :--- | :--- | :--- |
| `main.py` | Orquestador secuencial de `src/01_ingest.py` a `src/verify_all.py`. | `scripts/auditoria/run_all.py` |
| `src/01_ingest.py` | Ingesta de ZIPs CCPC vía DuckDB, agregación por `EDOCVE, SECCION` (sin `ORDER BY`), cálculo `SV/LN`, capping `>100%` e inner join de 62,048 secciones. | `00_inventario.py`, `02_verificacion_datos.py` |
| `src/02_features.py` | Cálculo de 7 variables longitudinales/demográficas, prueba VIF y escalado con `RobustScaler`. | `03_robustez_modelo.py`, `05_tablas_nuevas.py` |
| `src/03_clustering.py` | Benchmark K-Means++ (`k=3..7`), GMM y HDBSCAN (`min_cluster_size=250`), PCA 2D y UMAP 2D. | `03_robustez_modelo.py`, `06_figuras.py` |
| `src/03_clustering_refinement.py` | Agrega lemas cívicos, íconos Unicode y factores de abstención a `arquetipos_fichas.json`. | `04_perfiles_y_nombres.py` |
| `src/04_profiling.py` | Entrena Random Forest y ANOVA F-test (reportados como validación), genera figuras 04–07 y `arquetipos_fichas.json`. | `03_robustez_modelo.py`, `04_perfiles_y_nombres.py`, `06_figuras.py` |
| `src/05_report_pdf.py` | Compila el Documento Técnico de 10 páginas usando ReportLab (`NumberedCanvas`) con texto y cifras parcialmente escritas a mano. | `08_documento.py` + `plantillas/documento_tecnico.md.j2` |
| `src/06_presentation.py` | Genera presentación ejecutiva PPTX/PDF (fuera del alcance de esta corrección). | *Fuera de alcance* |
| `src/07_infographic.py` | Genera el póster/infografía en Matplotlib (`32x22 in`, 300 DPI) mezclando lectura de `arquetipos_fichas.json` con métricas escritas a mano en el bloque metodológico. | `07_infografia.py` + `plantillas/infografia_textos.json.j2` |
| `src/verify_all.py` / `src/verify_pipeline.py` | Verificaciones básicas de existencia de archivos, conteo de páginas y ausencia de `NaN`. | `09_validacion_consistencia.py` + `tests/test_consistencia.py` |

## 4. Cómo se Generaron la Infografía, las Figuras y el Documento (Fase 0.3)

1. **Figuras (`output/figures/01_*.png` a `07_*.png`):** Se generaron con `matplotlib` y `seaborn` a 300 DPI desde `src/03_clustering.py` (figuras 01, 02 y 03) y `src/04_profiling.py` (figuras 04, 05, 06 y 07). Sin embargo, los colores entre figuras no estaban unificados por ID de cluster: en `03_clustering.py` se asignó color por orden de iteración `CLUSTER_PALETTE[i]`, mientras que en `07_infographic.py` se usó un diccionario distinto `CLUSTER_COLORS`.
2. **Infografía (`entregables_finales/Fichas_Perfiles_Infografia_ByteMe.png` y `.pdf`):** Se generó mediante `src/07_infographic.py` con `matplotlib` (`figsize=(32, 22)`, `dpi=300`). Aunque las 5 tarjetas de perfiles leen de `output/datasets/arquetipos_fichas.json`, la **Tarjeta 6 (Síntesis Metodológica)** tiene texto estático escrito a mano en las líneas 331–403 de `src/07_infographic.py`.
3. **Origen de las discrepancias entre Infografía y Documento (Fase 0.3):**
   - **No determinismo en `01_ingest.py`:** La consulta DuckDB `GROUP BY EDOCVE, SECCION` carece de `ORDER BY`. En `pipeline.log` quedaron registradas dos corridas completas el 24 de octubre de 2026: una a las `16:48:16` (línea 100) y otra a las `16:56:03` (línea 299).
   - **`Davies-Bouldin = 1.4233` y `ARI = 0.8411` vs `1.4245` y `0.8970`:** En la primera corrida (`16:48:16`), K-Means (`k=5`) obtuvo `Sil=0.1805`, `DB=1.4233`, `CH=14062.4` y `ARI=0.8411`. Esos valores se copiaron a mano en el texto de `src/05_report_pdf.py` (líneas 594–595) y `src/07_infographic.py` (líneas 334–336). Minutos después (`16:56:03`), una segunda corrida sobrescribió `clustering_benchmark_metrics.parquet` con `Sil=0.1788`, `DB=1.4245`, `CH=14,062.0` y `ARI=0.8970`. Como la tabla del documento lee del Parquet pero el párrafo lee texto fijo, el propio documento se contradice entre su tabla (`1.4245`, `0.8970`) y su texto (`1.4233`, `0.8411`).
   - **`Calinski-Harabasz = 18,742.6` y `GMM = 0.1481`:** Están escritos como cadenas literales fijas en `src/07_infographic.py` (líneas 334–335). No provienen de ninguna corrida real del repositorio (en `clustering_benchmark_metrics.parquet`, CH para `k=5` es `14,062.0` y el Silhouette de GMM para `k=5` es `0.0188`, con máximo `0.1097` en `k=3`). Matemáticamente, dado que la suma total de cuadrados $TSS = \text{Inercia} \times \left(1 + \frac{CH \times (k-1)}{N-k}\right)$ es constante (~377,518 en los datos escalados), un $CH = 18,742.6$ en $k=5$ exigiría una inercia de ~170.8 mil, incompatible con la inercia real de `k=5` (197.4 mil).
   - **Documento PDF en `entregables_finales/` vs `Downloads/`:** El PDF en `entregables_finales/Documento_Tecnico_Reto1_ByteMe.pdf` tiene productor `ReportLab PDF Library`, mientras que la copia en `/home/johan/Downloads/Documento_Tecnico_Reto1_ByteMe.pdf` fue exportada desde Google Docs (`Skia/PDF m158 Google Docs Renderer`) a partir de `Documento_Tecnico_Reto1_ByteMe.docx` conservando el texto que afirma haber sido compilado con ReportLab.

## 5. Versiones Reales Instaladas en el Entorno

| Librería / Componente | Versión Instalada |
| :--- | :--- |
| `Python` | `3.14.6` |
| `duckdb` | `2.0.0` |
| `scikit-learn` | `1.9.0` |
| `scipy` | `1.18.0` |
| `umap-learn` | `0.5.12` |
| `hdbscan` | `No instalado (HDBSCAN integrado en scikit-learn 1.9.0)` |
| `pandas` | `3.0.3` |
| `numpy` | `2.4.6` |
| `matplotlib` | `3.11.0` |
| `seaborn` | `0.13.2` |
| `statsmodels` | `0.14.6` |
| `pyarrow` | `23.0.1` |
| `joblib` | `1.5.3` |
| `reportlab` | `5.1.0` |
| `pypdf` | `6.21.2` |
| `Jinja2` | `3.1.6` |
| `pytest` | `9.0.3` |
| `pillow` | `12.3.0` |
