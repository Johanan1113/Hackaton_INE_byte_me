# Perfiles Ciudadanos de Participación Electoral en México (2009–2024): Auditoría de Microdatos Censales, Tipología Seccional Reproducible y Estrategias Focalizadas de Educación Cívica

**Equipo Byte me — Propuesta técnica para el Reto 1: Perfiles ciudadanos de participación (Concurso INE: Hackea la participación)**

---

## 1. Resumen Ejecutivo

El presente estudio desarrolla una tipología nacional de secciones electorales a partir de los microdatos abiertos de los Conteos Censales de Participación Ciudadana (CCPC) en las seis elecciones federales celebradas entre 2009 y 2024. Durante la auditoría de integridad de datos se identificó un hallazgo metodológico fundamental: en las bases de datos abiertas del CCPC, la Lista Nominal se descompone en la identidad exacta $\text{LN} = \text{SV} + \text{NV} + \text{NS}$, donde $\text{SV}$ representa a las personas que sí votaron, $\text{NV}$ a quienes no votaron y $\text{NS}$ a los registros no especificados (cuadernillos sin marcas de votación, no disponibles para captura o con páginas faltantes, según el catálogo de campos del INE) (6,089,742 electores equivalentes al 6.83% de la Lista Nominal en 2018, y 6,325,654 electores equivalentes al 6.43% en 2024).

Dividir $\text{SV} / \text{LN}$ en lugar de aplicar la definición oficial $\text{SV} / (\text{SV} + \text{NV})$ asigna artificialmente una participación de 0.0% a miles de secciones sin captura ($\text{SV} + \text{NV} = 0$), subestimando la media nacional en 4.27 puntos porcentuales en 2018 y en 3.84 puntos en 2024, además de fabricar un agrupamiento espurio de supuesto declive cívico. Al corregir la formulación a $\text{SV} / (\text{SV} + \text{NV})$ y depurar el panel sin recurrir a ninguna imputación sintética (**Panel Principal Opción B**: 53,644 secciones con cobertura continua, equivalentes al 75.82% de las secciones y al 79.53% de la Lista Nominal de 2024 en 2,393 municipios), se reproduce con exactitud la serie censal oficial publicada por el INE (44.06% en 2009, 62.08% en 2012, 47.07% en 2015, 62.37% en 2018, 51.84% en 2021 y 59.67% en 2024).

Dentro del rango de 4.0 a 6.0 perfiles establecido por la convocatoria, el modelo **K-Means++ con $k = 4$** domina empíricamente en las métricas de validación interna (Silhouette de 0.1789, Davies-Bouldin de 1.5380 y Calinski-Harabasz de 14,435.43) y alcanza una estabilidad bootstrap de $\text{ARI} = 0.9572$ (IC 95%: $[0.9091, 0.9915]$), identificando cuatro perfiles accionables para la Estrategia Nacional de Cultura Cívica (ENCÍVICA):

- **C0 — Baja Participación Intermitente con Rezago Juvenil** (17,622 secciones, 32.85% del panel / 35.90% de la LN del panel; participación media de 50.37%).

- **C1 — Alta Participación Estable e Intergeneracional** (8,824 secciones, 16.45% del panel / 14.69% de la LN del panel; participación media de 65.05%).

- **C2 — Participación en Ascenso con Juventud Activa** (14,624 secciones, 27.26% del panel / 24.04% de la LN del panel; participación media de 58.93%).

- **C3 — Liderazgo Femenino con Participación Estancada** (12,574 secciones, 23.44% del panel / 25.37% de la LN del panel; participación media de 55.42%).


---

## 2. Datos y Tratamiento: El Hallazgo de los Registros Sin Captura (`NS`) y el Universo de Estudio

### 2.1 Significado de `NS` y validación de la fórmula oficial $\text{SV} / (\text{SV} + \text{NV})$

En los microdatos abiertos de los Conteos Censales de Participación Ciudadana (CCPC), la Lista Nominal se desagrega en tres categorías: electores que sufragaron (`SV`), electores que no votaron (`NV`) y electores sin condición especificada de voto (`NS`, correspondientes a cuadernillos sin marcas de votación, no disponibles para captura o con páginas faltantes, según el catálogo de campos del INE). En todas las filas se cumple que $\text{LN} = \text{SV} + \text{NV} + \text{NS}$. Cuando una sección carece por completo de cuadernillos capturados en un proceso electoral, la base registra $\text{SV} = 0$, $\text{NV} = 0$ y $\text{NS} = \text{LN}$.

Calcular la tasa de participación como $\text{SV} / \text{LN}$ confunde la ausencia administrativa del cuadernillo ($\text{NS}$) con abstencionismo ciudadano ($\text{NV}$). En cambio, la definición censal correcta calcula todas las tasas sobre el universo con condición de voto efectivamente verificada en cuadernillo:

$$P_{i,t} = \frac{\text{SV}_{i,t}}{\text{SV}_{i,t} + \text{NV}_{i,t}}$$

Esta misma formulación $\text{SV}_g / (\text{SV}_g + \text{NV}_g)$ se aplica de manera uniforme a las tasas por grupo etario (18–29 años y 60+ años) y por sexo. En 2024, los registros con marcador no binario (`SEXO = 2`) se integran en el numerador y denominador de la tasa total seccional, mientras que la brecha de género se calcula exclusivamente entre mujeres (`SEXO = 1`) y hombres (`SEXO = 0`).

La Tabla 1 demuestra que la fórmula $\text{SV} / (\text{SV} + \text{NV})$ ponderada sobre el total de secciones del CCPC reproduce con exactitud los datos publicados en los Estudios Censales de la DECEyEC (`DECEYEC_Comparativo_VF.pdf`, p. 7, Figura 3.1, para 2009, 2012 y 2015; Estudios Censales 2018 y 2024; y `Manual-Conteos-Censales-2009-2024.pdf`, p. 21). Para la elección intermedia de 2021, la referencia censal oficial de 51.8% proviene de la imagen del tablero interactivo oficial del INE incluida en la página 21 del *Manual de Conteos Censales 2009–2024* (sección *"Participación por año"*), cuyo valor sin redondear en los microdatos es 51.84% (como referencia externa no censal, el cierre del PREP 2021 reportó 52.67%).

**Tabla 1. Serie Nacional de Participación 2009–2024: Validación Censal y Sesgo por Registros `NS`**

| Año | Elección | Secc. CCPC | Secc. `SV+NV=0` | `NS` (% LN) | Erróneo `SV/LN` Pond. | Oficial CCPC `SV/(SV+NV)` Pond. | Oficial CCPC Simple | Dato Censal INE Publicado | Panel B (53,644) Pond. | Panel B Simple | Sesgo Panel B Pond. vs CCPC |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 2009 | Intermedia | 64,934 | 1,004 | 2.41% | 43.00% | **44.06%** | 44.97% | **44.06%** | 44.50% | 45.17% | +0.44 pts |
| 2012 | Presidencial | 65,599 | 82 | 0.22% | 61.95% | **62.08%** | 62.67% | **62.08%** | 62.59% | 63.13% | +0.51 pts |
| 2015 | Intermedia | 68,362 | 2,042 | 6.13% | 44.19% | **47.07%** | 48.58% | **47.07%** | 47.75% | 49.29% | +0.68 pts |
| 2018 | Presidencial | 68,408 | 2,517 | 6.83% | 58.10% | **62.37%** | 63.12% | **62.4%** | 63.21% | 63.93% | +0.84 pts |
| 2021 | Intermedia | 68,812 | 1,693 | 4.32% | 49.60% | **51.84%** | 54.04% | **51.8%** | 52.81% | 54.83% | +0.97 pts |
| 2024 | Presidencial | 70,751 | 2,100 | 6.43% | 55.83% | **59.67%** | 60.53% | **59.7%** | 60.55% | 61.45% | +0.88 pts |


### 2.2 Reconciliación del universo seccional y cascada de filtrado (Opción B, cero imputación)

A lo largo del periodo 2009–2024 existieron 72,681 claves seccionales distintas en la unión histórica de los seis conteos censales. De ellas, 1,930 fueron dadas de baja por reseccionamiento antes de 2024, resultando en 70,751 secciones activas en 2024 (con una Lista Nominal de 98,330,348 electores en el CSV abierto frente a 98,329,591 del informe ejecutivo INE). Esas 70,751 secciones se dividen exactamente en 62,048 secciones con presencia continua en las seis elecciones y 8,703 secciones creadas con posterioridad a 2009.

Para construir indicadores longitudinales sin recurrir a ninguna imputación sintética (**Universo Principal — Opción B**), se aplican tres filtros de calidad sobre el panel continuo: (1) contar con captura válida $\text{SV} + \text{NV} \ge 50$ en las seis elecciones (lo cual excluye 7,244 secciones: 7,156 con $\text{SV}+\text{NV}=0$ en al menos un comicio y 88 con $1 \le \text{SV}+\text{NV} < 50$); (2) excluir secciones con cambios abruptos de Lista Nominal entre elecciones consecutivas ($<0.5\times$ o $>2.5\times$) atribuibles a subdivisiones o fusiones que conservaron el código de sección madre (1,159 secciones excluidas de las 1,311 detectadas en el panel continuo); y (3) contar con electores en todos los grupos etarios en el hexenio (1 sección excluida).

**Tabla 2. Cascada de Filtrado del Universo Seccional y Cobertura sobre 2024**

| Etapa de Filtrado | Secciones | Excluidas en el Paso | % Secciones 2024 | Lista Nominal 2024 | % LN 2024 | Municipios |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 0_union_historica_2009_2024 | 72,681 | 0 | 102.73% | 98,330,348 | 100.00% | 2,477 |
| 1_universo_2024 | 70,751 | 1,930 | 100.00% | 98,330,348 | 100.00% | 2,477 |
| 2_panel_continuo_2009_2024 | 62,048 | 8,703 | 87.70% | 85,936,860 | 87.40% | 2,473 |
| 3_captura_valida_6_elecciones | 54,804 | 7,244 | 77.46% | 79,932,810 | 81.29% | 2,396 |
| 4_sin_saltos_abruptos_ln_consecutivos | 53,645 | 1,159 | 75.82% | 78,199,727 | 79.53% | 2,393 |
| 5_panel_principal_opcion_b_cero_imputacion | 53,644 | 1 | 75.82% | 78,199,518 | 79.53% | 2,393 |


---

## 3. Metodología, Pruebas de Robustez y Justificación de $k = 4$

### 3.1 Definición de las 7 variables, transformación de estabilidad y colinealidad

El modelo caracteriza cada una de las 53,644 secciones mediante siete variables calculadas sobre las tasas $\text{SV} / (\text{SV} + \text{NV})$ de las seis elecciones:
1. **`participacion_media_historica`**: promedio simple de las seis tasas de participación seccional ($\mu = 56.30\%$, $\sigma = 9.18\%$).
2. **`brecha_presidencial_intermedia`**: diferencia entre la participación media en elecciones presidenciales (2012, 2018, 2024) y en elecciones intermedias (2009, 2015, 2021) ($\mu = +13.07\text{ pts}$, $\sigma = 7.02\text{ pts}$).
3. **`tendencia_participacion_beta`**: pendiente anual de regresión lineal ordinaria ($\text{OLS}$) sobre los años transcurridos desde 2009 ($\mu = +0.68\text{ pts/año}$, $\sigma = 0.72\text{ pts/año}$).
4. **`estabilidad_participacion`**: transformación logarítmica $\log(1 + 1/\text{CV})$, donde $\text{CV} = \sigma_i / (\mu_i + 10^{-4})$ ($\mu = 1.9811$, $\sigma = 0.4278$).
5. **`brecha_generacional`**: diferencia entre la tasa media hexanual de adultos mayores (60+ años, 63.91%) y la de jóvenes (18–29 años, 47.45%) ($\mu = +16.46\text{ pts}$, $\sigma = 7.20\text{ pts}$).
6. **`brecha_genero`**: diferencia entre la tasa media hexanual de mujeres (60.07%) y la de hombres (52.28%) ($\mu = +7.79\text{ pts}$, $\sigma = 4.28\text{ pts}$).
7. **`ratio_participacion_joven`**: cociente entre las medias hexanuales $\text{tasa\_joven\_18\_29} / \text{participacion\_media\_historica}$ ($\mu = 0.8385$, $\sigma = 0.0681$; el promedio de cocientes anuales es 0.8309).

Previo al escalamiento con `RobustScaler`, las siete variables se winsorizan en los percentiles 1 y 99. El pipeline se ejecutó en un entorno reproducible verificado con doble corrida determinista (`Python 3.14.6`, `DuckDB 2.0.0`, `scikit-learn 1.9.0`, `SciPy 1.18.0`, `umap-learn 0.5.12`, `pandas 3.0.3`, `numpy 2.4.6`, `statsmodels 0.14.6`).

**Estabilidad y colinealidad:** La versión original sin acotar $1/\text{CV}$ presentaba asimetría extrema ($\text{skewness} = 3.78$, $\text{kurtosis} = 31.25$), mientras que $\log(1 + 1/\text{CV})$ winsorizada reduce la asimetría a 0.99 y la curtosis a 0.57, manteniendo alta concordancia con el coeficiente de variación directo ($\text{ARI} = 0.7451$). En el análisis del Factor de Inflación de la Varianza ($\text{VIF}$), las variables presentan valores entre 1.21 (`brecha_genero`) y 3.99 (`ratio_participacion_joven`, con 3.97 en `brecha_generacional`). Se conservan simultáneamente `ratio_participacion_joven` y `brecha_generacional` por su complementariedad conceptual sustantiva: la primera mide la propensión de voto juvenil relativa al nivel cívico general de su propia sección, mientras que la segunda mide la distancia absoluta en puntos porcentuales entre el grupo de 60+ años y el de 18–29 años (por ejemplo, en C0 y C3 la brecha generacional es similar, de 20.64 y 20.94 puntos, pero operan en estructuras demográficas y de género distintas).

### 3.2 Benchmark de algoritmos y justificación de la elección de $k = 4$

Se evaluaron tres familias de algoritmos sobre el espacio 7D escalado: **K-Means++** ($k \in \{3, 4, 5, 6, 7\}$, `n_init=50, random_state=42`, con 100 réplicas bootstrap al 80% sin reemplazo), **Modelos de Mezclas Gaussianas (GMM)** con covarianza completa (`n_init=3, random_state=42`) y **HDBSCAN** en tres configuraciones de densidad (`min_cluster_size` $\in \{100, 250, 500\}$).

**Tabla 3. Benchmark Comparativo de Modelos de Clustering sobre el Panel Principal ($N = 53,644$)**

| Algoritmo | Configuración | Clusters Efectivos | % Ruido | Silhouette | Davies-Bouldin | Calinski-Harabasz | BIC | ARI Bootstrap Media (IC 95%) | Cluster Mín–Máx (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| K-Means++ | `k=3` | 3 | 0.00% | 0.2099 | 1.4875 | 16,402.41 | — | 0.9734 [0.9174, 0.9963] | 23.48%–42.59% |
| K-Means++ | `k=4` | 4 | 0.00% | 0.1789 | 1.5380 | 14,435.43 | — | 0.9572 [0.9091, 0.9915] | 16.45%–32.85% |
| K-Means++ | `k=5` | 5 | 0.00% | 0.1625 | 1.6109 | 12,676.61 | — | 0.9327 [0.8728, 0.9854] | 12.95%–30.28% |
| K-Means++ | `k=6` | 6 | 0.00% | 0.1639 | 1.5709 | 11,550.69 | — | 0.9675 [0.9375, 0.9887] | 11.02%–28.27% |
| K-Means++ | `k=7` | 7 | 0.00% | 0.1539 | 1.5736 | 10,673.24 | — | 0.9496 [0.5652, 0.9837] | 9.95%–22.65% |
| GMM (full) | `k=3` | 3 | 0.00% | 0.1054 | 3.2024 | 7,602.68 | 586,328 | — | 26.56%–40.37% |
| GMM (full) | `k=4` | 4 | 0.00% | 0.0692 | 4.3384 | 5,369.72 | 573,941 | — | 17.80%–34.77% |
| GMM (full) | `k=5` | 5 | 0.00% | 0.0326 | 3.7745 | 5,030.32 | 561,305 | — | 14.96%–22.69% |
| GMM (full) | `k=6` | 6 | 0.00% | 0.0242 | 2.8994 | 5,065.10 | 554,519 | — | 13.18%–18.99% |
| GMM (full) | `k=7` | 7 | 0.00% | 0.0191 | 3.2265 | 4,577.63 | 549,822 | — | 10.64%–19.12% |
| HDBSCAN (7D) | `min_cluster_size=100, min_samples=10` | 2 | 50.73% | 0.4140 | 0.6564 | 620.21 | — | — | — |
| HDBSCAN (7D) | `min_cluster_size=250, min_samples=20` | 0 | 100.00% | — | — | — | — | — | — |
| HDBSCAN (7D) | `min_cluster_size=500, min_samples=30` | 0 | 100.00% | — | — | — | — | — | — |


**Justificación de la elección de $k = 4$:**
1. **Mejor desempeño empírico dentro del rango de la convocatoria (4–6):** Aunque $k = 3$ alcanza métricas globales superiores (Silhouette 0.2099, Davies-Bouldin 1.4875, Calinski-Harabasz 16,402.41 y $\text{ARI} = 0.9734$), queda fuera del rango de 4 a 6 perfiles requerido por la convocatoria. Dentro del rango válido 4–6, **$k = 4$ tiene el mejor Silhouette (0.1789), el mejor Davies-Bouldin (1.5380) y el mejor Calinski-Harabasz (14,435.43)**, dominando a $k = 5$ en las cuatro métricas (Silhouette 0.1625, DB 1.6109, CH 12,676.61, ARI 0.9327).
2. **Estabilidad bootstrap comparable al máximo:** La estabilidad de $k = 4$ ($\text{ARI} = 0.9572$, IC 95% $[0.9091, 0.9915]$) es estadísticamente comparable a la de $k = 6$ ($\text{ARI} = 0.9675$, IC 95% $[0.9375, 0.9887]$), dado que sus intervalos de confianza se traslapan ampliamente.
3. **Diferenciación sustantiva frente a $k = 6$:** En $k = 4$, los cuatro perfiles cuentan con al menos cinco variables rectoras con $|z| \ge 0.50$. En cambio, $k = 6$ genera un grupo sin diferenciación sustantiva (17.77% del panel) que posee una sola variable con $|z| \ge 0.50$ (`tendencia_participacion_beta` con $z = -0.51$). Cabe señalar que, con $k = 6$, el perfil de baja participación se divide en un subgrupo de rezago juvenil y otro de ciclo presidencial urbano, lo cual resulta útil como sub-segmentación auxiliar para focalización territorial fina.
4. **Descarte de HDBSCAN y GMM:** En el espacio continuo de las secciones electorales, HDBSCAN colapsa la distribución en 2 macro-clusters (50.73% a 100.00% de ruido), mientras que GMM presenta menor separación esférica (Silhouette de 0.0692 en $k=4$).

### 3.3 Matriz de transición (clusters previos $\to$ nuevos $k = 4$) e interpretabilidad interna

La Tabla 4 muestra cómo se redistribuyen las 62,048 secciones de la partición original (contaminada por el cálculo $\text{SV}/\text{LN}$) hacia los cuatro nuevos perfiles de $k = 4$ ($\text{ARI}$ global entre particiones en el Panel B = 0.3351). Destaca que el **48.85% del antiguo cluster `C4_viejo`** (4,114 de 8,421 secciones) sale del Panel Principal por tratarse de secciones con $\text{SV}+\text{NV} < 50$ (principalmente $\text{SV}+\text{NV}=0$ en 2018 o 2024), confirmando que dicho agrupamiento era un artefacto de datos faltantes.

**Tabla 4. Matriz de Transición: Clusters Originales (`SV/LN`, $k=5$) hacia Nuevos Perfiles (`SV/[SV+NV]`, $k=4$)**

| Cluster Original (`SV/LN`) | Total (62,048) | Excluidas Panel B ($n$ / %) | En Panel B | $\to$ `C0` Nuevo ($n$ / %) | $\to$ `C1` Nuevo ($n$ / %) | $\to$ `C2` Nuevo ($n$ / %) | $\to$ `C3` Nuevo ($n$ / %) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `C0_viejo` (Voto Femenino Consistente) | 14,863 | 328 (2.21%) | 14,535 | 3,852 (26.5%) | 620 (4.3%) | 557 (3.8%) | 9,506 (65.4%) |
| `C1_viejo` (Pivote Presidencial Volátil) | 12,610 | 766 (6.07%) | 11,844 | 19 (0.2%) | 4,233 (35.7%) | 7,485 (63.2%) | 107 (0.9%) |
| `C2_viejo` (Abstencionismo Estructural Urbano) | 22,274 | 3,123 (14.02%) | 19,151 | 12,406 (64.8%) | 104 (0.5%) | 5,971 (31.2%) | 670 (3.5%) |
| `C3_viejo` (Voto Tradicional Rural y Mayor) | 3,880 | 73 (1.88%) | 3,807 | 0 (0.0%) | 3,109 (81.7%) | 0 (0.0%) | 698 (18.3%) |
| `C4_viejo` (Juventud Movilizada en Expansión) | 8,421 | 4,114 (48.85%) | 4,307 | 1,345 (31.2%) | 758 (17.6%) | 611 (14.2%) | 1,593 (37.0%) |


Como medida de **interpretabilidad interna** sobre las mismas siete variables empleadas en el agrupamiento (y no como validación externa), un clasificador Random Forest con validación cruzada estratificada de 5 pliegues alcanza una exactitud de 96.29% ($\pm 0.09\%$). El ranking de importancia Gini e importancia por permutación (Tabla 5) muestra que `estabilidad_participacion` ($F = 18,684.13$), `brecha_presidencial_intermedia` ($F = 29,701.07$) y `tendencia_participacion_beta` ($F = 17,943.97$) encabezan la capacidad discriminante entre los cuatro perfiles.

**Tabla 5. Interpretabilidad Interna de las 7 Variables para $k = 4$ (Random Forest y ANOVA Unidireccional)**

| Rango | Variable del Modelo | Importancia Gini (RF) | Importancia por Permutación (Media $\pm$ DE) | Estadístico $F$ de ANOVA | Valor $p$ |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | `ratio_participacion_joven` | 0.2167 | 0.1937 $\pm$ 0.0011 | 18,684.13 | $< 10^{-300}$ |
| 2 | `estabilidad_participacion` | 0.1998 | 0.2116 $\pm$ 0.0010 | 29,701.07 | $< 10^{-300}$ |
| 3 | `brecha_generacional` | 0.1556 | 0.1642 $\pm$ 0.0012 | 17,943.97 | $< 10^{-300}$ |
| 4 | `brecha_presidencial_intermedia` | 0.1246 | 0.0763 $\pm$ 0.0011 | 18,966.11 | $< 10^{-300}$ |
| 5 | `tendencia_participacion_beta` | 0.1220 | 0.1107 $\pm$ 0.0013 | 16,107.30 | $< 10^{-300}$ |
| 6 | `participacion_media_historica` | 0.0951 | 0.1115 $\pm$ 0.0007 | 8,279.66 | $< 10^{-300}$ |
| 7 | `brecha_genero` | 0.0861 | 0.1035 $\pm$ 0.0012 | 4,661.80 | $< 10^{-300}$ |


---

## 4. Caracterización de los 4 Perfiles Ciudadanos de Participación ($k = 4$)

Los nombres de los cuatro perfiles se derivaron aplicando estrictamente el umbral de $|z| \ge 0.50$ respecto a la media y desviación estándar del Panel Principal ($N = 53,644$). Las Tablas 6 y 7 presentan los centroides en unidades originales, puntajes estandarizados ($z$-scores), series históricas 2009–2024 (ponderadas y simples), tasas demográficas y composición territorial por secciones y por Lista Nominal, incluyendo la fila de la **Media Nacional del Panel Principal (Opción B)** (63.7% urbanas, 26.9% rurales y 9.5% mixtas al ponderar los perfiles por secciones; 64.0% / 26.7% / 9.4% al ponderar los perfiles por LN 2024, y 68.5% / 18.0% / 13.5% del total de electores en secciones U/R/M).

**Tabla 6. Centroides de las 7 Variables (Unidades Originales y $z$-scores) y Composición Territorial ($k = 4$)**

| Perfil | Nombre del Perfil | Secciones (% Panel / % 2024) | LN 2024 (% Panel / % 2024) | Part. Media ($z$) | Brecha Pres-Inter ($z$) | Tendencia OLS ($z$) | Estabilidad ($z$) | Brecha Gen. ($z$) | Brecha Género ($z$) | Ratio Joven ($z$) | Tipo Secc. U/R/M (por LN) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **C0** | Baja Participación Intermitente con Rezago Juvenil | 17,622 (32.85% / 24.91%) | 28,070,662 (35.90% / 28.55%) | 50.37% (-0.65) | +17.31 (+0.60) | +0.86 (+0.26) | 1.7036 (-0.65) | +20.64 (+0.58) | +6.90 (-0.21) | 0.7963 (-0.62) | 79.0/13.5/7.5% (79.9/8.8/11.3%) |
| **C1** | Alta Participación Estable e Intergeneracional | 8,824 (16.45% / 12.47%) | 11,490,525 (14.69% / 11.69%) | 65.05% (+0.95) | +5.37 (-1.10) | +0.15 (-0.73) | 2.5897 (+1.42) | +8.78 (-1.07) | +7.63 (-0.04) | 0.9090 (+1.04) | 46.0/40.9/13.2% (53.5/28.1/18.3%) |
| **C2** | Participación en Ascenso con Juventud Activa | 14,624 (27.26% / 20.67%) | 18,796,916 (24.04% / 19.12%) | 58.93% (+0.29) | +16.81 (+0.53) | +1.28 (+0.84) | 1.7561 (-0.53) | +12.20 (-0.59) | +6.08 (-0.40) | 0.8793 (+0.60) | 68.6/22.3/9.1% (72.2/15.9/11.9%) |
| **C3** | Liderazgo Femenino con Participación Estancada | 12,574 (23.44% / 17.77%) | 19,841,415 (25.37% / 20.18%) | 55.42% (-0.10) | +8.20 (-0.69) | +0.08 (-0.83) | 2.2047 (+0.52) | +20.94 (+0.62) | +11.15 (+0.78) | 0.8007 (-0.56) | 48.8/41.2/10.0% (57.7/27.1/15.2%) |
| **Panel B** | **Media Nacional Panel B** | **53,644** (100% / 75.82%) | **78,199,518** (100% / 79.53%) | **56.30%** (0.00) | **+13.07** (0.00) | **+0.68** (0.00) | **1.9811** (0.00) | **+16.46** (0.00) | **+7.79** (0.00) | **0.8385** (0.00) | **63.7/26.9/9.5%** (68.5/18.0/13.5%) |

**Tabla 7. Series Históricas 2009–2024 (Ponderada y Simple) y Tasas Demográficas por Perfil ($k = 4$)**

| Perfil | 2009 Pond (Simp) | 2012 Pond (Simp) | 2015 Pond (Simp) | 2018 Pond (Simp) | 2021 Pond (Simp) | 2024 Pond (Simp) | Media Pres / Inter | Jóvenes 18–29 / Mayores 60+ | Mujeres / Hombres | Ratio Joven (Medias / Anual) | Principales Entidades (% de secciones del cluster) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **C0** | 36.91% (37.24%) | 58.50% (58.85%) | 38.82% (39.89%) | 59.96% (60.41%) | **46.13%** (48.01%) | 56.94% (57.80%) | 59.02% / 41.71% | 40.17% / 60.81% | 53.70% / 46.79% | 0.7963 / 0.7848 | Ciudad de México (13.0%, 2,288 sec); Veracruz (10.7%, 1,892 sec); Estado de México (9.0%, 1,580 sec); Sinaloa (6.5%, 1,152 sec); Chihuahua (6.2%, 1,095 sec) |
| **C1** | 59.17% (59.30%) | 69.24% (69.39%) | 64.21% (64.64%) | 68.21% (68.37%) | **62.45%** (63.18%) | 65.70% (65.45%) | 67.74% / 62.37% | 59.10% / 67.88% | 68.78% / 61.14% | 0.9090 / 0.9075 | Jalisco (16.3%, 1,437 sec); Estado de México (13.2%, 1,165 sec); Nuevo León (12.3%, 1,081 sec); San Luis Potosí (8.8%, 779 sec); Yucatán (5.9%, 521 sec) |
| **C2** | 41.83% (41.87%) | 65.84% (65.39%) | 48.33% (49.05%) | 69.28% (68.89%) | **60.37%** (60.66%) | 68.04% (67.72%) | 67.33% / 50.53% | 51.81% / 64.01% | 61.83% / 55.75% | 0.8793 / 0.8700 | Ciudad de México (20.5%, 2,997 sec); Estado de México (8.1%, 1,183 sec); Puebla (7.6%, 1,106 sec); Michoacán (6.4%, 929 sec); Guerrero (5.5%, 807 sec) |
| **C3** | 49.62% (50.22%) | 61.24% (62.09%) | 50.38% (51.96%) | 58.99% (59.96%) | **49.45%** (51.77%) | 55.57% (56.49%) | 59.51% / 51.32% | 44.41% / 65.35% | 60.85% / 49.70% | 0.8007 / 0.7962 | Estado de México (13.3%, 1,678 sec); Veracruz (11.2%, 1,407 sec); Guanajuato (10.3%, 1,296 sec); Jalisco (7.8%, 977 sec); San Luis Potosí (5.1%, 641 sec) |
| **Panel B** | **44.50%** (45.17%) | **62.59%** (63.13%) | **47.75%** (49.29%) | **63.21%** (63.92%) | **52.81%** (54.83%) | **60.55%** (61.45%) | **62.84% / 49.76%** | **47.45% / 63.91%** | **60.07% / 52.28%** | **0.8385 / 0.8309** | Total Nacional (32 entidades; 2,393 municipios) |

### Diagnóstico analítico por perfil

- **C0 — Baja Participación Intermitente con Rezago Juvenil (17,622 secciones, 32.85% del panel; 28,070,662 electores, 35.90% de la LN del panel):** Sus 5 variables con |z| ≥ 0.5 son estabilidad (log(1 + 1/CV)) (-0.65, la más baja de los cuatro perfiles: 1.7036), participación media (-0.65, la más baja de los cuatro perfiles: 50.37%), razón de participación juvenil (-0.62, la más baja de los cuatro perfiles: 0.7963 con 40.17% de votación juvenil), brecha presidencial–intermedia (+0.60, la más alta de los cuatro perfiles: +17.31 pts entre presidenciales 59.02% e intermedias 41.71%) y brecha generacional (+0.58: +20.64 pts entre 60+ con 60.81% y 18–29 con 40.17%). Concentra el 32.85% de las secciones del panel y es predominantemente urbano (78.99% de secciones urbanas).

- **C1 — Alta Participación Estable e Intergeneracional (8,824 secciones, 16.45% del panel; 11,490,525 electores, 14.69% de la LN del panel):** Presenta los niveles más altos de los cuatro perfiles en estabilidad (log(1 + 1/CV)) (+1.42: 2.5897), razón de participación juvenil (+1.04: 0.9090, con 59.10% de votación juvenil) y participación media (+0.95: 65.05%, con 67.74% en presidenciales y 62.37% en intermedias), así como las menores brechas presidencial–intermedia (-1.10: +5.37 pts) y generacional (-1.07: +8.78 pts). Su pendiente anual es ligeramente positiva (+0.15 pts/año, z=-0.73 respecto a la media nacional de +0.68 pts/año) porque ya partía de un nivel alto en 2009 (59.17% ponderado / 59.30% simple).

- **C2 — Participación en Ascenso con Juventud Activa (14,624 secciones, 27.26% del panel; 18,796,916 electores, 24.04% de la LN del panel):** Sus 5 variables con |z| ≥ 0.5 son tendencia anual (+0.84, la más alta de los cuatro perfiles: +1.28 pts/año, pasando de 41.83% ponderado en 2009 a 60.37% en la intermedia de 2021 y 68.04% en la presidencial de 2024), razón de participación juvenil (+0.60: 0.8793 con 51.81% de votación juvenil), brecha generacional (-0.59: +12.20 pts), brecha presidencial–intermedia (+0.53: +16.81 pts porque partió de intermedias bajas en 2009 y 2015) y estabilidad (log(1 + 1/CV)) (-0.53 por ese mismo ascenso).

- **C3 — Liderazgo Femenino con Participación Estancada (12,574 secciones, 23.44% del panel; 19,841,415 electores, 25.37% de la LN del panel):** Sus 6 variables con |z| ≥ 0.5 son tendencia anual (z=-0.83 respecto a la media nacional: su pendiente global es +0.08 pts/año, positiva pero estancada porque las intermedias se mantuvieron en 49.6% [2009], 50.4% [2015] y 49.5% [2021], mientras que la participación presidencial cayó de 61.2% ponderado en 2012 a 59.0% en 2018 y 55.6% en 2024), brecha de género (+0.78, la más alta de los cuatro perfiles: +11.15 pts a favor de las mujeres con 60.85% vs 49.70% en hombres), brecha presidencial–intermedia (-0.69: +8.20 pts), brecha generacional (+0.62: +20.94 pts, 60+ con 65.35% vs 18–29 con 44.41%), razón de participación juvenil (-0.56: 0.8007) y estabilidad (log(1 + 1/CV)) (+0.52: 2.2047). Su composición es 48.8% urbana, 41.2% rural y 10.0% mixta (pluralidad urbana con sobrerrepresentación rural frente al 26.9% del panel).


---

## 5. Estrategias Focalizadas de Promoción e Intervención Institucional (ENCÍVICA)

Las estrategias operativas (Tabla 8) se diseñaron dentro de las atribuciones legales de la DECEyEC, la DERFE, la DEOE y las 300 Juntas Distritales Ejecutivas, garantizando neutralidad partidista, trazabilidad hacia la línea base observada en la elección intermedia de 2021 y en la presidencial de 2024 de cada perfil, y niveles de costo indicativos sin cifras monetarias arbitrarias.

En particular:
- En **C0 (Baja Participación Intermitente con Rezago Juvenil, 32.85% del panel, 79.0% urbano)**, dado que convergen una alta brecha presidencial-intermedia (+17.31 pts) y el menor ratio de participación juvenil (0.7963), la estrategia articula **dos líneas de acción**: (1) pedagogía sobre el papel legislativo de las elecciones intermedias mediante canales urbanos y metropolitanos, y (2) incorporación juvenil que atiende tanto a estudiantes universitarios y de nivel medio superior como a **jóvenes que no estudian** (en centros laborales, parques industriales, tianguis, centros comunitarios y deportivos barriales).
- En **C3 (Liderazgo Femenino con Participación Estancada, 23.44% del panel, 48.8% urbano y 41.2% rural)**, cuya pendiente global es ligeramente positiva (+0.08 pts/año) pero presenta una caída sostenida en elecciones presidenciales (de 61.2% ponderado en 2012 a 55.6% en 2024), la **acción principal** se enfoca en elevar la participación masculina (49.70% frente a 60.85% en mujeres) y revertir el descenso presidencial en centros de trabajo y radio regional, mientras que la accesibilidad rural opera como **acción secundaria** acorde con su sobrerrepresentación rural (41.2% frente a 26.9% en el panel).

**Tabla 8. Matriz de Estrategias Focalizadas, Líneas Base Observadas (2021/2024), Metas Cuantitativas y Viabilidad ($k = 4$)**

| Perfil | Línea Base Intermedia 2021 / Pres. 2024 (Pond.) | Hipótesis Causal y Objetivo Específico | Canales y Acción Operativa del INE | Meta Cuantitativa (con Línea Base) e Indicador | Unidad Responsable y Nivel de Costo Indicativo | Lema Institucional Neutral |
| :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **C0**<br>Baja Participación Intermitente con Rezago Juvenil | **46.1%** (2021)<br>**56.9%** (2024) | Hipótesis: asimetría de visibilidad informativa entre elecciones presidenciales e intermedias en zonas urbanas y metropolitanas, combinada con barreras de incorporación al primer sufragio y movilidad residencial o laboral en jóvenes de 18 a 29 años (tanto escolarizados como fuera del sistema educativo).<br><br>**Objetivo:** Reducir la caída de participación en elecciones intermedias (línea base ponderada de 46.1% en 2021 frente a 56.9% en la presidencial de 2024) e incrementar la tasa de votación del grupo de 18 a 29 años (línea base 2021 de 35.2%) en las 17,622 secciones del perfil. | **Canales:** Doble línea de intervención: (1) Ciclo intermedio urbano: transporte público masivo, corredores metropolitanos, medios públicos/digitales y plataforma 'Conóceles'; (2) Juventudes escolarizadas y no escolarizadas: universidades y planteles de educación media superior, más centros de trabajo, parques industriales, tianguis, centros comunitarios, deportivos barriales y mensajería digital geolocalizada ('Ubica tu Casilla').<br><br>**Acción INE:** Línea 1: campaña cívica metropolitana pre-intermedia (2027) de la DECEyEC y Juntas Locales/Distritales con despliegue de códigos QR hacia 'Conóceles'. Línea 2: brigadas móviles de actualización registral (DERFE) y promoción cívica (DECEyEC) tanto en campus educativos como en centros laborales, parques industriales, tianguis y espacios deportivos barriales de las 17,622 secciones. | **Meta:** Elevar la participación ponderada a 49.5% en la intermedia de 2027 (línea base 2021: 46.1%, cerrando la mitad de la brecha frente al 52.8% del panel) y la participación juvenil (18–29 años) a 39.1% en 2027 (línea base 2021: 35.2%, cerrando la mitad frente al 43.1% del panel).<br><br>**Indicador:** Tasa de participación ponderada SV/(SV+NV) del perfil en la intermedia de 2027 (vs. 46.1% en 2021) y tasa seccional SV/(SV+NV) del grupo 18–29 años en el CCPC 2027. | **Unidad:** DECEyEC en coordinación con las Juntas Locales y Distritales Ejecutivas y la DERFE<br><br>**Costo:** Nivel Medio — Estimación indicativa de orden operativo (sujeta a presupuestación de DECEyEC, DERFE y Juntas Distritales Ejecutivas; aprovecha tiempos oficiales del Estado, módulos itinerantes existentes y convenios con instituciones educativas y centros de trabajo). | *"Cada elección define tu entorno: infórmate, ubica tu casilla y participa en 2027"* |
| **C1**<br>Alta Participación Estable e Intergeneracional | **62.5%** (2021)<br>**65.7%** (2024) | Hipótesis: cohesión comunitaria e intergeneracional consolidada en contextos urbanos (46.0%), rurales (40.9%) y mixtos (13.1%) que sostiene altos niveles de sufragio en ambos tipos de elección; su principal reto operativo es asegurar el relevo generacional en la integración de Mesas Directivas de Casilla y la observación electoral.<br><br>**Objetivo:** Sostener los niveles históricos de participación en elecciones intermedias (62.5% ponderado en 2021; media histórica intermedia de 62.4%) y presidenciales (65.7% ponderado en 2024; media histórica presidencial de 67.7%), fortaleciendo el voluntariado cívico en las 8,824 secciones del perfil. | **Canales:** Redes comunitarias, planteles educativos locales, centros culturales y sesiones distritales de reconocimiento cívico y reclutamiento de funcionariado de casilla.<br><br>**Acción INE:** Talleres distritales de educación cívica intercultural y relevo generacional (DECEyEC), programas de reconocimiento a la participación comunitaria continua y reclutamiento temprano de CAE y sensibilización de la ciudadanía insaculada para asegurar la instalación completa de casillas con funcionariado propietario. | **Meta:** Sostener una participación ponderada ≥ 62.5% en la elección intermedia de 2027 (preservando el 62.5% observado en la intermedia de 2021) y sostener al menos el nivel de 2024 (65.7%) en la elección presidencial de 2030, aumentando la proporción de casillas instaladas con funcionariado propietario.<br><br>**Indicador:** Tasa de participación ponderada SV/(SV+NV) en la intermedia de 2027 (vs. 62.5% en 2021), en la presidencial de 2030 (vs. 65.7% en 2024), y porcentaje de casillas instaladas con funcionariado propietario el día de la jornada (dato de la DEOE). | **Unidad:** DECEyEC en coordinación con las Juntas Distritales Ejecutivas (Vocalías de Capacitación Electoral y Educación Cívica y Vocalías de Organización Electoral)<br><br>**Costo:** Nivel Bajo — Estimación indicativa de orden operativo (sujeta a presupuestación de DECEyEC y Juntas Distritales Ejecutivas; absorbible dentro de los programas ordinarios de educación cívica y capacitación electoral distrital). | *"Si te visitan para integrar una casilla, participa: tu comunidad cuenta contigo"* |
| **C2**<br>Participación en Ascenso con Juventud Activa | **60.4%** (2021)<br>**68.0%** (2024) | Hipótesis: creciente movilización cívica y dinamismo demográfico juvenil en secciones urbanas (68.6%) y rurales (22.3%) y mixtas (9.1%) que elevó la participación intermedia de 41.8% (2009) y 48.3% (2015) a 60.4% (2021); el riesgo principal es la regresión hacia su media intermedia histórica (50.5%) si no se institucionaliza el hábito del voto legislativo.<br><br>**Objetivo:** Consolidar en la elección intermedia de 2027 el nivel de participación alcanzado en 2021 (60.4% ponderado), evitando un retroceso hacia su promedio intermedio histórico (50.5% simple / 50.2% ponderado) en las 14,624 secciones del perfil. | **Canales:** Colectivos juveniles y estudiantiles, redes comunitarias y vecinales, plataformas digitales interactivas ('Conóceles') y espacios de diálogo distrital convocados por las Juntas Distritales Ejecutivas.<br><br>**Acción INE:** Despliegue de foros distritales 'Diálogos por la Democracia' de la DECEyEC, alianzas con redes juveniles y vecinales para promoción del voto informado rumbo a 2027 y monitoreo de capacidad instalada de casillas por la DEOE en secciones en crecimiento. | **Meta:** Consolidar en la elección intermedia de 2027 una participación ponderada ≥ 60.4% (sosteniendo la línea base observada en la intermedia de 2021 de 60.4% e impidiendo una regresión hacia su media intermedia histórica de 50.5%) y mantener la razón de participación juvenil ≥ 0.88.<br><br>**Indicador:** Tasa de participación ponderada SV/(SV+NV) en la intermedia de 2027 (vs. 60.4% en 2021 y vs. 48.3% en 2015) y razón de participación juvenil en el CCPC 2027. | **Unidad:** DECEyEC en coordinación con las Juntas Distritales Ejecutivas y la DEOE<br><br>**Costo:** Nivel Bajo-Medio — Estimación indicativa de orden operativo (sujeta a presupuestación de DECEyEC y Juntas Distritales Ejecutivas; basada en foros distritales, vinculación comunitaria y comunicación digital institucional). | *"Tu participación ya transforma tu comunidad: consolidemos el voto en cada elección"* |
| **C3**<br>Liderazgo Femenino con Participación Estancada | **49.5%** (2021)<br>**55.6%** (2024) | Hipótesis: rezago persistente en la participación masculina (49.70% vs 60.85% femenina) y juvenil (44.41% vs 65.35% en adultos mayores) asociado a dinámicas laborales, movilidad ocupacional masculina y desvinculación en elecciones presidenciales (donde la votación bajó de 61.2% en 2012 a 55.6% en 2024), aunado en su segmento rural (41.2% de las secciones) a costos de traslado físico a la casilla.<br><br>**Objetivo:** Elevar la participación masculina (línea base 2021 de 43.94% frente a 48.66% nacional) y revertir la caída en elecciones presidenciales (de 61.2% en 2012 a 55.6% en 2024) y el estancamiento en intermedias (49.5% en 2021) en las 12,574 secciones del perfil, atendiendo como acción secundaria la accesibilidad en sus localidades con sobrerrepresentación rural. | **Canales:** Acción principal: centros de trabajo con alta presencia masculina (agropecuarios, industriales, construcción, transporte y comercio), perifoneo y radiodifusoras regionales y comunitarias en tiempos oficiales. Acción secundaria (sobrerrepresentación rural 41.2%): módulos itinerantes de las Juntas Distritales Ejecutivas y asambleas comunitarias.<br><br>**Acción INE:** Acción principal: campañas de promoción del voto masculino y juvenil de la DECEyEC y Juntas Distritales en centros laborales, gremios de transporte/construcción/agroindustria y radio regional en tiempos oficiales. Acción secundaria: brigadas móviles de educación cívica y revisión de accesibilidad geográfica de domicilios de casilla (DEOE) en el 41.2% de secciones rurales y 10.0% mixtas del perfil. | **Meta:** Elevar la participación ponderada en la elección intermedia de 2027 a 51.1% (línea base 2021: 49.5%, cerrando la mitad de la brecha frente al 52.8% del panel), recuperar en la presidencial de 2030 a 58.1% (línea base 2024: 55.6%, cerrando la mitad frente al 60.6% del panel), y elevar la participación masculina a 46.3% en 2027 (línea base 2021: 43.9%, cerrando la mitad frente al 48.7% del panel).<br><br>**Indicador:** Tasa de participación masculina SV/(SV+NV) (vs. 43.9% en 2021), participación ponderada en la intermedia de 2027 (vs. 49.5% en 2021) y participación ponderada en la presidencial de 2030 (vs. 55.6% en 2024) en el CCPC. | **Unidad:** Juntas Distritales Ejecutivas, DECEyEC y Dirección Ejecutiva de Organización Electoral (DEOE)<br><br>**Costo:** Nivel Medio — Estimación indicativa de orden operativo (sujeta a presupuestación de DECEyEC, DEOE y Juntas Distritales Ejecutivas; combina vinculación en centros laborales, pauta en tiempos oficiales de radio regional y rutas de campo distritales). | *"La participación de todas y todos cuenta: sumemos la voz de hombres y jóvenes en cada comunidad"* |


---

## 6. Limitaciones Metodológicas, Análisis de Sensibilidad y Recomendaciones al INE

1. **Sesgo de cobertura y caracterización de las secciones excluidas en 2024:**
   La Tabla 9 compara las **53,644 secciones incluidas en el Panel Principal (Opción B)** frente a las **17,107 secciones activas en 2024 excluidas del Panel B** (24.18% de las secciones y 20.47% de la Lista Nominal de 2024):
   - Las **8,703 secciones creadas o reseccionadas con posterioridad a 2009** (12,393,488 electores, 12.60% de la LN 2024) son predominantemente urbanas (79.31% de las secciones y 80.8% de su Lista Nominal) y registraron en 2024 una participación ponderada de **54.57% frente al 60.40% del panel continuo (60.55% del Panel B)**, concentrándose en entidades de alta expansión periférica como Estado de México, Nuevo León, Jalisco, Puebla y Quintana Roo.
   - Las **8,404 secciones continuas excluidas por filtros de calidad** ($\text{SV}+\text{NV} < 50$ en algún año, salto abrupto de LN o ausencia de grupo etario; 7,737,342 electores, 7.87% de la LN 2024) presentan 54.28% de composición urbana, incluyen 1,798 secciones sin captura en 2024 y votaron 58.50% en las secciones con captura.
   - Como consecuencia de excluir estas zonas de reciente creación y menor participación, **el Panel Principal (Opción B) sobreestima la participación nacional ponderada del CCPC entre +0.44 y +0.97 puntos porcentuales**: +0.44 pts en 2009 (44.50% vs 44.06%), +0.51 pts en 2012 (62.59% vs 62.08%), +0.68 pts en 2015 (47.75% vs 47.07%), +0.84 pts en 2018 (63.21% vs 62.37%), +0.97 pts en 2021 (52.81% vs 51.84%) y +0.88 pts en 2024 (60.55% vs 59.67%).

**Tabla 9. Comparación de Secciones Incluidas vs Excluidas en el CCPC 2024**

| Subuniverso en 2024 | Secciones | % Secc. 2024 | Lista Nominal 2024 | % LN 2024 | % U / % R / % M | Secc. `SV+NV=0` en 2024 | Part. 2024 Pond. `SV/(SV+NV)` | Part. 2024 Simple | Principales Entidades en el Grupo |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| Incluidas en el Panel Principal Opción B (53,644) | 53,644 | 75.82% | 78,199,518 | 79.53% | 63.7/26.9/9.5% | 0 | **60.55%** | 61.45% | MEXICO: 5,606 (10.5%); CIUDAD DE MEXICO: 5,300 (9.9%); VERACRUZ: 4,202 (7.8%) |
| Excluidas totales del Panel Principal Opción B en 2024 (17,107) | 17,107 | 24.18% | 20,130,830 | 20.47% | 67.0/25.3/7.7% | 2,100 | **55.93%** | 57.25% | SINALOA: 1,694 (9.9%); CHIHUAHUA: 1,351 (7.9%); NUEVO LEON: 1,191 (7.0%) |
| Excluidas del panel continuo (creadas/reseccionadas post-2009: 8,703) | 8,703 | 12.30% | 12,393,488 | 12.60% | 79.3/13.8/6.9% | 302 | **54.57%** | 55.69% | NUEVO LEON: 891 (10.2%); MEXICO: 737 (8.5%); BAJA CALIFORNIA: 645 (7.4%) |
| Excluidas continuas por filtros de calidad (SV+NV<50, salto LN o sin 60+: 8,404) | 8,404 | 11.88% | 7,737,342 | 7.87% | 54.3/37.1/8.6% | 1,798 | **58.50%** | 59.23% | SINALOA: 1,257 (15.0%); CHIHUAHUA: 770 (9.2%); GUERRERO: 534 (6.4%) |
| Incluidas en el panel continuo 2009-2024 (62,048) | 62,048 | 87.70% | 85,936,860 | 87.40% | 62.4/28.3/9.3% | 1,798 | **60.40%** | 61.21% | MEXICO: 6,011 (9.7%); CIUDAD DE MEXICO: 5,479 (8.8%); VERACRUZ: 4,661 (7.5%) |
| Total Nacional CCPC 2024 (70,751) | 70,751 | 100.00% | 98,330,348 | 100.00% | 64.5/26.5/9.0% | 2,100 | **59.67%** | 60.53% | MEXICO: 6,748 (9.5%); CIUDAD DE MEXICO: 5,575 (7.9%); VERACRUZ: 4,938 (7.0%) |


2. **Análisis de sensibilidad con el Universo Opción A (sin imputar años faltantes):**
   Como prueba de sensibilidad, se evaluó la **Opción A** sobre el panel continuo tratando los años con $\text{SV}+\text{NV} < 50$ como `NaN` (sin imputar) y exigiendo al menos 2 elecciones presidenciales y 2 intermedias válidas (61,739 secciones sin filtro de salto de LN y 60,433 secciones excluyendo saltos de LN). Al reentrenar K-Means++ ($k = 4$) sobre este universo ampliado y comparar las etiquetas en las 53,644 secciones comunes con el Panel Principal (Opción B), se obtiene un **$\text{ARI} = 0.9729$** (98.98% de coincidencia exacta alineada) en la primera variante y **$\text{ARI} = 0.9707$** (98.93% de coincidencia exacta) en la segunda, indicando que la segmentación es robusta a la depuración del panel.
3. **Sensibilidad a la ventana de agregación temporal de variables demográficas:**
   Al comparar el agrupamiento obtenido con promedios demográficos hexanuales (2009–2024) frente al que resulta de utilizar únicamente el corte transversal de 2024, la concordancia con la tipología base baja a **$\text{ARI} = 0.4021$** (las correlaciones entre el promedio hexanual y el dato de 2024 son $r = 0.7361$ en `brecha_generacional`, $r = 0.8096$ en `brecha_genero` y $r = 0.7329$ en `ratio_participacion_joven`). Esto constituye una **limitación metodológica relevante**: las brechas demográficas de una sola elección presentan fluctuaciones coyunturales respecto al promedio estructural de seis comicios, por lo que las tipologías de largo plazo deben actualizarse tras cada ciclo federal.
4. **Ausencia del indicador de sección indígena o afromexicana en los CSV abiertos:**
   Los CSV abiertos del CCPC no incluyen el indicador de población indígena o afromexicana que sí muestra el tablero del INE; por ello no se incorporó al modelo. Se recomienda publicar dicho indicador en formato abierto junto con las bases del CCPC.
5. **Recomendación técnica al INE sobre la captura censal en 2018 y 2024:**
   Se recomienda a la DECEyEC: (a) incorporar en los archivos CSV de datos abiertos una bandera explícita de estatus de captura seccional (`CAPTURA_COMPLETA`, `RECUENTO_PARCIAL`, `SIN_CUADERNILLO_DISPONIBLE`) para evitar que personas usuarias externas confundan `NS` con abstencionismo; (b) publicar la llave de correspondencia histórica de secciones reseccionadas junto con el catálogo de secciones indígenas/afromexicanas en formato CSV abierto; y (c) reforzar la captura de cuadernillos para reducir el porcentaje de registros `NS` observado en 2018 (6.83%) y 2024 (6.43%) hacia los niveles alcanzados en 2012 (0.22%).