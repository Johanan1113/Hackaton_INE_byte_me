# Bitácora Técnica de Auditoría y Corrección · Equipo Byte me · Reto 1 INE

## 0. Entorno de Ejecución y Versiones Reales Instaladas (Regla 8)

- **Fecha de inicio de auditoría:** 2026-10-25
- **Rama de trabajo Git:** `auditoria-correcciones` (respaldo íntegro adicional en `../byteme_backup_20261025`)
- **Semilla global:** `random_state = 42`
- **Versiones reales instaladas en el entorno (`/opt/anaconda/bin/python`):**
  - `Python`: `3.14.6` (el documento original reportaba erróneamente `3.14.8`)
  - `duckdb`: `2.0.0`
  - `scikit-learn`: `1.9.0`
  - `scipy`: `1.18.0`
  - `umap-learn`: `0.5.12`
  - `hdbscan`: `Integrado en scikit-learn==1.9.0 (sklearn.cluster.HDBSCAN); paquete standalone no instalado`
  - `pandas`: `3.0.3`
  - `numpy`: `2.4.6`
  - `matplotlib`: `3.11.0`
  - `seaborn`: `0.13.2`
  - `statsmodels`: `0.14.6`
  - `pyarrow`: `23.0.1`
  - `joblib`: `1.5.3`
  - `reportlab`: `5.1.0` (el PDF exportado desde Google Docs en `Downloads/` reportaba `4.2.2`)
  - `pypdf`: `6.21.2`
  - `Jinja2`: `3.1.6`
  - `pytest`: `9.0.3`
  - `pillow`: `12.3.0`

---

## 1. Registro Cronológico de Hallazgos, Decisiones y Cambios (Regla 6)

Formato reglamentario:
`fecha · fase · archivo/ubicación · antes → después · motivo · evidencia (ruta del output)`

- `2026-10-25 · Fase 0 · Repositorio raíz (.git y ../byteme_backup_20261025) · Sin control de versiones Git → Repositorio Git inicializado con commit base en master, rama activa auditoria-correcciones y respaldo completo en ../byteme_backup_20261025 · Garantizar trazabilidad y reversibilidad total antes de modificar o auditar código · .git/refs/heads/auditoria-correcciones`
- `2026-10-25 · Fase 0 · requirements.txt · Archivo inexistente → Creado requirements.txt con versiones exactas fijadas · Cumplir Regla 8 de reproducibilidad estricta · requirements.txt`
- `2026-10-25 · Fase 0.1 · data/raw_zips/*.zip y src/01_ingest.py · Lectura uniforme con encoding='latin1' y eliminación sólo de '\ufeff' → Detectado que los 32 CSV de 2024 tienen BOM UTF-8 (\xef\xbb\xbf), lo que bajo latin1 produce la columna 'Ï»¿AELEC' y corrompe acentos (mojibake) en EDONOM y MPIONOM · Auditar diferencias de esquema entre 2009–2021 y 2024 · outputs/fase0/inventario.md`
- `2026-10-25 · Fase 0.1 · data/raw_zips/DatosAbiertos_DECEyEC_ConteosCensales2024.zip · SEXO en {0, 1} (2009–2021) → SEXO en {0, 1, 2} en 2024 (103 filas con SEXO=2 'No binario', LN=105, SV=60, NV=33, NS=12) y 20,912 nulos en DEL · Documentar cambio de esquema en 2024 y asimetría en 01_ingest.py (que incluyó SEXO=2 en LN/SV total pero lo excluyó de ln_fem y ln_masc) · outputs/fase0/inventario.md`
- `2026-10-25 · Fase 0.2 · src/01_ingest.py (líneas 127 y 203) · GROUP BY EDOCVE, SECCION sin ORDER BY y conteo de municipios por intersección de claves (2,455) → Identificado que la falta de ORDER BY en DuckDB genera orden de filas no determinista entre corridas, y que las 62,048 secciones del panel en 2024 pertenecen en realidad a 2,473 municipios (99.84%) debido a municipios de nueva creación · Explicar por qué la corrida 1 (16:48) y la corrida 2 (16:55) en pipeline.log dieron métricas ligeramente distintas · outputs/fase0/baseline_vs_reportado.csv`
- `2026-10-25 · Fase 0.2 · src/03_clustering.py y src/04_profiling.py · Valores reportados en prosa (ARI=0.8411, DB=1.4233, RF=94.08%) vs. Parquet/Tabla (ARI=0.8970, DB=1.4245, RF=94.06%) → Documentada la discrepancia exacta en baseline_vs_reportado.csv · La prosa copió a mano los resultados de la corrida 1 (pipeline.log línea 100), mientras que la tabla del PDF leyó el Parquet sobrescrito por la corrida 2 (pipeline.log línea 299) · outputs/fase0/baseline_vs_reportado.csv`
- `2026-10-25 · Fase 0.3 · src/07_infographic.py (líneas 334–354) · Infografía reporta DB=1.4233, CH=18,742.6, GMM Sil=0.1481 e importancias RF (0.324, 0.241, 0.182, 0.138) → Rastreado a cadenas de texto escritas a mano en src/07_infographic.py que no leen de ningún archivo de datos · CH=18,742.6 es matemáticamente imposible para la curva de inercia del modelo (exigiría inercia ~170.8k en k=5 en vez de 197.4k) y GMM k=5 tuvo Sil=0.0188 (máximo 0.1097 en k=3) · outputs/fase0/inventario.md`
- `2026-10-25 · Fase 1.1 · src/01_ingest.py (líneas 168–172) y src/05_report_pdf.py (línea 397) · Participación calculada como SV / LN y reportada como promedio simple seccional (2012=62.5%, 2018=58.6%, 2024=56.6%) → Verificado contra la fórmula oficial del Manual CCPC (pág. 17): SV / (SV + NV). Al excluir NS (cuadernillos no capturados: 0.22% en 2012, 6.83% en 2018 y 6.43% en 2024), la participación nacional ponderada reproduce exactamente el dato oficial del INE: 2012=62.08% (62.1%), 2018=62.37% (62.4%) y 2024=59.67% (59.7%) · Explicar la diferencia de -3.8 pts en 2018 y -3.1 pts en 2024 reportada en la auditoría · outputs/fase1/serie_nacional.csv`
- `2026-10-25 · Fase 1.2 · Cluster C4 (dataset_clusters_final.parquet) · C4 reportado como 'Juventud Movilizada en Expansión' con caída de 60.4% (2012) a 39.9% (2018) y 33.3% (2024) → Demostrado que la caída de C4 es un artefacto del error SV / LN: el 88.7% de las secciones sin cuadernillos capturados en 2018 (1,898 de 2,139 con SV+NV=0) y el 99.3% en 2024 (1,792 de 1,804 con SV+NV=0) fueron agrupadas en C4 porque 01_ingest.py les asignó 0.0% de participación. En las 50 secciones con mayor caída 2012–2024, el 100% tiene SV_2024=0, NV_2024=0 y NS_2024=LN_2024 · Diagnosticar la causa real del desplome en C4 · outputs/fase1/c4_diagnostico.md, outputs/fase1/c4_diagnostico.csv, outputs/fase1/c4_top50_caida.csv`
- `2026-10-25 · Fase 1.4 · src/01_ingest.py (líneas 159–166) y src/05_report_pdf.py (línea 464) · Afirmación de que se aplicó capping al 100% por 'casillas especiales con electores en tránsito' → Verificado que existen 0 filas y 0 secciones-año con SV > LN o SV > (SV + NV) en los 6 años, y que los diccionarios oficiales CCPC especifican que la base NO incluye casillas especiales · Corregir explicación metodológica falsa en el documento · outputs/fase1/c4_diagnostico.md`
- `2026-10-25 · Fase 1.5 · output/datasets/dataset_clusters_final.parquet · Sin tratamiento de valores extremos ni de secciones sin captura → Identificadas las secciones con participación media <15% o >90%, |brecha_genero|>25 pts o |brecha_pres|>40 pts, comprobando que la mayoría proviene de secciones con años sin captura (SV+NV=0) o con baja lista nominal capturada · Sustentar criterio de limpieza y winsorización · outputs/fase1/outliers.csv`
- `2026-10-25 · Fase 1.6 · Universo 2024 (70,751 secciones) · Sin análisis de sesgo de selección del panel → Comparadas las 62,048 secciones incluidas (87.70% de secciones 2024; 85.94 M de LN = 87.40%) contra las 8,703 excluidas (12.30% de secciones; 12.39 M de LN = 12.60%, predominantemente urbanas 83.2% en zonas de expansión como Edomex, Nuevo León, Jalisco, Puebla y Q. Roo) · Documentar sesgo del panel balanceado · outputs/fase1/incluidas_vs_excluidas.csv`

---

## 2. Regla de Decisión de la Fase 1.7 (CHECKPOINT A)

> [!CAUTION]
> **DECISIÓN: SÍ HAY ERROR DE DATOS EN EL PIPELINE ORIGINAL (`src/01_ingest.py`).**
> Conforme a la regla 1.7 del prompt, **nos detenemos en el CHECKPOINT A sin volver a correr el modelo** hasta recibir confirmación explícita sobre la corrección propuesta.

### Propuesta de Corrección Técnica para Aplicar al Iniciar la Fase 2:
1. **Fórmula oficial de participación CCPC (`SV / (SV + NV)`):**
   - Calcular todas las tasas de participación (total seccional, jóvenes 18–29, adultos mayores 60+, mujeres y hombres) dividiendo entre los registros efectivamente capturados en cuadernillos (`SV + NV = LN - NS`), **nunca** entre `LN` bruto cuando `NS > 0`.
2. **Tratamiento de secciones-año con captura nula o parcial (`SV + NV == 0`):**
   - En el panel de 62,048 secciones existen 4,769 secciones que en algún año (principalmente 2015, 2018, 2021 o 2024) tuvieron `SV + NV == 0` (`NS = LN`, cuadernillo no disponible/en recuento).
   - **Opción A (Recomendada — conserva las 62,048 secciones del panel):** Cuando `SV + NV == 0` en un año para una sección (o subgrupo demográfico), tratar la tasa de ese año específico como dato faltante (`NaN`) —no como `0.0%`— y calcular las métricas longitudinales de la sección (media histórica, brecha presidencial-intermedia, pendiente OLS $\beta_1$, desviación estándar y promedios demográficos) sobre los años con captura válida (`SV + NV >= 50`), exigiendo al menos 4 años válidos (de 6) con al menos 2 presidenciales y 2 intermedias (o imputando el año faltante con la media de la sección ajustada por el efecto año nacional si una sección tiene menos).
   - **Opción B (Alternativa estricta — reduce tamaño del panel):** Excluir del panel las secciones que tengan `SV + NV < 50` en cualquiera de los 6 procesos electorales (lo cual reduciría el panel de 62,048 a ~57,180 secciones con cuadernillos capturados en los 6 comicios).
3. **Ordenamiento determinista y codificación limpia:**
   - Leer los CSV de 2024 con `utf-8-sig` (eliminando BOM y *mojibake*) y agregar `ORDER BY edocve, seccion` en DuckDB para garantizar reproducibilidad bit a bit.
4. **Control de valores extremos (Fase 1.5):**
   - Winsorizar las variables continuas de entrada al clustering en los percentiles `p1–p99` (además de la transformación de estabilidad que se evaluará en la Fase 2.1).
