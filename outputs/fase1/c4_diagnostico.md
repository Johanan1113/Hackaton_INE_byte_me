# Diagnóstico de Datos, Auditoría de Cluster C4 y Errores de Carga (Fase 1)

## 1. Hallazgo Central: El Error de Denominador (`SV / LN` vs `SV / (SV + NV)`)

> [!IMPORTANT]
> **Causa raíz identificada con certeza matemática (100%):**
> En los archivos abiertos de los Conteos Censales de Participación Ciudadana (CCPC), cada fila cumple la identidad exacta `LN = SV + NV + NS`, donde:
> - `SV` = Sí votaron (registros con marca de voto en el cuadernillo).
> - `NV` = No votaron (registros sin marca de voto en cuadernillos capturados).
> - `NS` = **No especificados** (cuadernillos no disponibles para su captura o sin marcas de votación).
> 
> De acuerdo con el **Manual de la Plataforma CCPC 2009–2024 (pág. 17)**, la fórmula oficial de participación del INE es:
> $$\text{Participación CCPC} = \frac{\text{Sí votaron}}{\text{Sí votaron} + \text{No votaron}} = \frac{SV}{SV + NV}$$
> 
> Sin embargo, el script `src/01_ingest.py` (líneas 168–172) calculó erróneamente `SV / LN = SV / (SV + NV + NS)`. Cuando un cuadernillo no fue capturado (`NS = LN`, `SV = 0`, `NV = 0`), `01_ingest.py` le asignó **0.0% de participación** en vez de tratarlo como dato no capturado (`NaN` si toda la sección tiene `SV+NV=0`, o excluyendo la casilla no capturada si otras casillas de la sección sí se capturaron).

### 1.1 Verificación de la Serie Nacional (`outputs/fase1/serie_nacional.csv`)

Al usar la fórmula oficial del INE ($\Sigma SV / \Sigma (SV + NV)$), los datos crudos del repositorio reproducen **exactamente** las cifras oficiales del estudio censal del INE:

| Año | Tipo | Dato Oficial / Ref. | Total Ponderada `SV/(SV+NV)` | Total Simple `SV/(SV+NV)` | Panel Ponderada `SV/(SV+NV)` | Panel Simple `SV/(SV+NV)` | Total Simple Errónea `SV/LN` (Reportada en Doc) | `% NS / LN` (No capturados) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2009** | Intermedia | **44.1%** | **44.06%** | 44.97% | 44.39% | 45.05% | 43.81% | 2.41% |
| **2012** | Presidencial | **62.1%** | **62.08%** | 62.67% | 62.50% | 62.95% | 62.51% | 0.22% |
| **2015** | Intermedia | **47.1%** | **47.07%** | 48.58% | 47.76% | 49.23% | 45.58% | 6.13% |
| **2018** | Presidencial | **62.4%** | **62.37%** | 63.12% | 63.10% | 63.75% | 58.57% | 6.83% |
| **2021** | Intermedia | **51.8%** | **51.84%** | 54.04% | 52.81% | 54.83% | 51.44% | 4.32% |
| **2024** | Presidencial | **59.7%** | **59.67%** | 60.53% | 60.40% | 61.21% | 56.61% | 6.43% |

- **En 2012:** `NS` fue apenas `0.22%` de la Lista Nominal (`168,649` registros), por lo que `SV/(SV+NV)` ponderado (**62.08%**, redondeado **62.1%**) y el promedio simple de `SV/LN` (**62.51%**) quedaron muy cercanos.
- **En 2018:** `NS` subió a **6.83%** de la Lista Nominal (`6,089,742` registros; `2,517` secciones completas con `SV+NV=0`). Con la fórmula correcta `SV/(SV+NV)`, la participación nacional ponderada es **62.37%** (idéntica al **62.4%** oficial del INE), pero `SV/LN` la desplomó artificialmente a **58.10%** ponderada (**58.57%** promedio simple, que el documento reportó como `58.6%`).
- **En 2024:** `NS` fue **6.43%** de la Lista Nominal (`6,325,654` registros; `2,100` secciones completas con `SV+NV=0`). Con la fórmula correcta `SV/(SV+NV)`, la participación nacional ponderada es **59.67%** (idéntica al **59.7%** oficial del INE), pero `SV/LN` la redujo artificialmente a **55.83%** ponderada (**56.61%** promedio simple, que el documento reportó como `56.6%`).
- **Nota sobre el promedio simple vs. ponderado:** Al corregir la fórmula a `SV/(SV+NV)`, el promedio simple por sección queda efectivamente **arriba** del dato nacional ponderado en todos los años (`62.67%` vs `62.08%` en 2012; `63.12%` vs `62.37%` en 2018; `60.53%` vs `59.67%` en 2024), confirmando la regularidad empírica de que las secciones rurales pequeñas votan más.

## 2. Diagnóstico del Cluster C4 (`outputs/fase1/c4_diagnostico.csv`)

El supuesto desplome de participación en el Cluster C4 (`Juventud Movilizada en Expansión`, $n = 8,421$ secciones: de `60.4%` en 2012 a `39.9%` en 2018 y `33.3%` en 2024) **NO es un fenómeno real de abstencionismo ciudadano**, sino un **artefacto de datos** creado por agrupar en C4 a las secciones cuyos cuadernillos no fueron capturados (`NS > 0`) en 2018 y 2024:

- De las **2,139 secciones** del panel que tienen `SV + NV = 0` (`NS = LN`, 0% de captura) en **2018**, **1,898 (88.7%) fueron asignadas a C4**.
- De las **1,804 secciones** del panel que tienen `SV + NV = 0` (`NS = LN`, 0% de captura) en **2024**, **1,792 (99.3%) fueron asignadas a C4**.
- En total, **3,489 de las 8,421 secciones de C4 (41.4%)** tienen el 100% de sus cuadernillos no capturados (`SV + NV = 0`) en al menos uno de los seis años, y **6,558 secciones de C4 (77.9%)** tienen más de 20% de sus registros como `NS` en 2018 o 2024.

### 2.1 Distribución de Participación en C4: Serie Errónea (`SV/LN`) vs. Serie Corregida (`SV/(SV+NV)`)

| Año | Fórmula | Secciones con captura (`SV+NV>0`) | Secciones sin captura (`SV+NV=0`) | Media (%) | P1 | P5 | P25 | Mediana (P50) | P75 | P95 | P99 | Secciones `< 30%` (%) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2009** | Original erronea: SV / LN | 8,421 | 51 | **44.87%** | 12.9 | 24.8 | 36.7 | 45.0 | 52.8 | 65.5 | 74.9 | 964 (11.4%) |
| **2009** | Corregida CCPC: SV / (SV + NV) | 8,370 | 51 | **45.37%** | 19.8 | 26.0 | 37.2 | 45.2 | 53.0 | 65.6 | 75.0 | 851 (10.2%) |
| **2012** | Original erronea: SV / LN | 8,421 | 15 | **60.38%** | 29.2 | 42.6 | 54.4 | 61.2 | 67.3 | 75.6 | 82.3 | 94 (1.1%) |
| **2012** | Corregida CCPC: SV / (SV + NV) | 8,406 | 15 | **60.58%** | 32.3 | 43.1 | 54.5 | 61.2 | 67.4 | 75.6 | 82.3 | 65 (0.8%) |
| **2015** | Original erronea: SV / LN | 8,421 | 168 | **45.85%** | 0.0 | 21.8 | 36.2 | 46.2 | 56.0 | 70.5 | 80.3 | 1,161 (13.8%) |
| **2015** | Corregida CCPC: SV / (SV + NV) | 8,253 | 168 | **48.43%** | 19.9 | 27.5 | 39.4 | 48.1 | 57.2 | 71.3 | 80.9 | 653 (7.9%) |
| **2018** | Original erronea: SV / LN | 8,421 | 1,897 | **39.91%** | 0.0 | 0.0 | 20.6 | 46.8 | 61.3 | 73.4 | 81.0 | 2,744 (32.6%) |
| **2018** | Corregida CCPC: SV / (SV + NV) | 6,524 | 1,897 | **58.25%** | 29.3 | 39.1 | 50.4 | 58.8 | 66.5 | 75.9 | 83.5 | 72 (1.1%) |
| **2021** | Original erronea: SV / LN | 8,421 | 648 | **44.46%** | 0.0 | 0.0 | 33.9 | 46.9 | 57.9 | 72.6 | 81.2 | 1,658 (19.7%) |
| **2021** | Corregida CCPC: SV / (SV + NV) | 7,773 | 648 | **50.67%** | 20.8 | 29.0 | 41.2 | 50.4 | 60.0 | 73.7 | 82.3 | 472 (6.1%) |
| **2024** | Original erronea: SV / LN | 8,421 | 1,786 | **33.31%** | 0.0 | 0.0 | 20.0 | 34.5 | 51.0 | 66.1 | 73.6 | 3,370 (40.0%) |
| **2024** | Corregida CCPC: SV / (SV + NV) | 6,635 | 1,786 | **54.28%** | 22.7 | 35.0 | 47.1 | 54.8 | 62.2 | 71.9 | 78.3 | 160 (2.4%) |

Obsérvese que al evaluar las secciones de C4 con cuadernillos efectivamente capturados (`SV/(SV+NV)`), su participación media es **60.53% en 2012**, **58.65% en 2018** y **54.15% en 2024**, y las secciones con participación `< 30%` caen de **2,744 (32.6%) a solo 66 (1.0%) en 2018**, y de **3,370 (40.0%) a solo 99 (1.5%) en 2024**.

### 2.2 Crecimiento de Lista Nominal por Sección (2012–2018–2024): C4 vs. Resto del Panel

| Grupo | Secciones | LN Media 2012 | LN Media 2018 | LN Media 2024 | Crecimiento Medio 2012–2018 (%) | Crecimiento Medio 2018–2024 (%) | Crecimiento Medio 2012–2024 (%) | Mediana Crec. 2012–2024 (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cluster C4** | 8,421 | 1,039 | 1,197 | 1,318 | +13.36% | +6.20% | +23.21% | +9.14% |
| **Resto del panel (C0, C1, C2, C3)** | 53,627 | 1,154 | 1,293 | 1,395 | +10.87% | +5.54% | +18.03% | +9.17% |
| **Total Panel** | 62,048 | 1,138 | 1,280 | 1,385 | +11.21% | +5.63% | +18.73% | +9.16% |

- El crecimiento de la Lista Nominal no explica la caída aparente de C4; la explica la proporción de cuadernillos `NS` no capturados.

### 2.3 Concentración Geográfica de C4 (`outputs/fase1/c4_entidades.csv`) y Top 50 Caídas (`outputs/fase1/c4_top50_caida.csv`)

Las 10 entidades con mayor número de secciones en C4 concentran el **61.1%** del cluster, encabezadas por entidades donde hubo alto volumen de paquetes/cuadernillos en recuento o no capturados (`NS`) en 2018 y 2024:

| Clave | Entidad | Secciones en C4 | % de C4 | Secciones con `SV+NV=0` (2018) | Secciones con `SV+NV=0` (2024) | Media 2018 `SV/LN` | Media 2018 `SV/(SV+NV)` | Media 2024 `SV/LN` | Media 2024 `SV/(SV+NV)` |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 25 | SINALOA | 1,004 | 11.92% | 527 | 325 | 27.4% | **60.5%** | 34.1% | **53.4%** |
| 08 | CHIHUAHUA | 677 | 8.04% | 166 | 226 | 35.7% | **52.3%** | 23.9% | **50.0%** |
| 26 | SONORA | 596 | 7.08% | 96 | 73 | 34.8% | **49.3%** | 37.5% | **48.4%** |
| 14 | JALISCO | 566 | 6.72% | 39 | 40 | 45.2% | **55.4%** | 38.5% | **53.6%** |
| 30 | VERACRUZ | 555 | 6.59% | 190 | 70 | 36.4% | **64.1%** | 39.0% | **57.0%** |
| 19 | NUEVO LEON | 493 | 5.85% | 59 | 58 | 39.5% | **52.5%** | 38.9% | **53.8%** |
| 16 | MICHOACAN | 417 | 4.95% | 51 | 92 | 42.5% | **53.6%** | 27.4% | **46.2%** |
| 11 | GUANAJUATO | 416 | 4.94% | 62 | 24 | 33.5% | **47.6%** | 39.5% | **50.8%** |
| 15 | MEXICO | 358 | 4.25% | 67 | 69 | 46.7% | **67.7%** | 36.7% | **64.5%** |
| 07 | CHIAPAS | 305 | 3.62% | 42 | 72 | 46.9% | **67.2%** | 28.4% | **54.9%** |

- En `outputs/fase1/c4_top50_caida.csv` se documentan las 50 secciones con mayor caída entre 2012 y 2024: **las 50 secciones tienen `SV_2024 = 0`, `NV_2024 = 0` y `NS_2024 = LN_2024`**, es decir, cayeron de ~90% en 2012 a `0.0%` en 2024 únicamente porque sus cuadernillos de 2024 están clasificados como `NS` (no disponibles para captura).

## 3. Verificación de Errores de Carga en 2018 y 2024 (Fase 1.3)

| Punto de Verificación | Estado | Evidencia Cuantitativa |
| :--- | :---: | :--- |
| **1. Nombres de columnas distintos o BOM** | **Revisado / Encontrado (BOM en 2024)** | Los 6 años tienen las mismas 16 columnas (`AELEC, FELECCION, EDOCVE, EDONOM, MPIOCVE, MPIONOM, SECCION, TIPOSEC, DEF, DEL, SEXO, EDAD, LN, SV, NV, NS`). Sin embargo, en **2024 los 32 CSV tienen BOM UTF-8 (`\xef\xbb\xbf`)**. Al leer con `encoding='latin1'` en `01_ingest.py`, el encabezado quedó como `Ï»¿AELEC` y los nombres de estados/municipios sufrieron corrupción de caracteres (*mojibake*, ej. `MÃ‰XICO`). |
| **2. Casillas contiguas o extraordinarias no sumadas a nivel sección** | **Revisado / No encontrado** | Los archivos CSV del CCPC ya vienen agregados por `EDOCVE + SECCION + SEXO + EDAD` (0 filas con la misma tupla `EDOCVE, SECCION, SEXO, EDAD` en los 6 años). Sin embargo, **cuando una casilla básica, contigua o extraordinaria de la sección no tuvo cuadernillo disponible, sus electores quedaron en `NS`**, y al dividir `SV / LN` en lugar de `SV / (SV + NV)` se trató a esas casillas no capturadas como 0% de votación. |
| **3. Filas duplicadas** | **Revisado / No encontrado** | `0` filas duplicadas exactas y `0` filas duplicadas en la llave `(EDOCVE, SECCION, SEXO, EDAD)` en los 6 años (`2009` a `2024`). |
| **4. Claves `EDOCVE_SECCION` con ceros a la izquierda perdidos o tipo numérico vs. texto** | **Revisado / No encontrado** | `01_ingest.py` formateó `f"{int(r['edocve']):02d}_{int(r['seccion']):04d}"` de forma consistente en todos los años. No obstante, la consulta `GROUP BY EDOCVE, SECCION` en DuckDB carecía de `ORDER BY`, produciendo un orden de filas no determinista entre corridas. |
| **5. Registros de 'no binario' (`SEXO=2` en 2024) excluidos del total pero incluidos en LN o al revés** | **Revisado / Encontrado (asimetría en género)** | En 2024 existen **105 filas con `SEXO = 2`** (`LN = 105`, `SV = 79`, `NV = 23`, `NS = 3`). `01_ingest.py` los incluyó en `ln` y `sv` totales, pero los excluyó de `ln_fem` (`SEXO=1`) y `ln_masc` (`SEXO=0`). Por su volumen (105 personas de 98.3 millones = 0.0001%), el impacto numérico es despreciable, pero debe documentarse explícitamente. |
| **6. Secciones reseccionadas que conservan la misma clave** | **Revisado / Encontrado** | Aunque el inner join conserva 62,048 claves `EDOCVE_SECCION`, existen secciones que sufrieron reseccionamiento (subdivisión por crecimiento demográfico o fusión) conservando el número de sección madre: **121 secciones** redujeron su LN a menos de la mitad (`LN_2024 / LN_2009 < 0.50`) y **634 secciones** más que duplicaron y medio su LN (`LN_2024 / LN_2009 > 2.50`). |
| **7. Omisión de `NS` y división por `LN` en vez de `(SV + NV)`** | **Revisado / ENCONTRADO (Error Crítico)** | `01_ingest.py` calculó `part = SV / LN` y `part_grupo = SV_grupo / LN_grupo` en lugar de `SV / (SV + NV)`. Esto convirtió `6,089,742` registros `NS` en 2018 y `6,325,654` en 2024 en falsos abstencionistas, reduciendo la media nacional en ~3.8 pts en 2018 y ~3.1 pts en 2024 y creando artificialmente la caída del cluster C4. |

## 4. Tasas Mayores a 100% antes del Capping (Fase 1.4)

| Año | Filas crudas con `SV > LN` | Filas crudas con `SV > (SV+NV)` | Secciones con `SV > LN` | Secciones con `SV > (SV+NV)` |
| :---: | :---: | :---: | :---: | :---: |
| **2009** | 0 | 0 | 0 | 0 |
| **2012** | 0 | 0 | 0 | 0 |
| **2015** | 0 | 0 | 0 | 0 |
| **2018** | 0 | 0 | 0 | 0 |
| **2021** | 0 | 0 | 0 | 0 |
| **2024** | 0 | 0 | 0 | 0 |

- **Resultado:** Existen **0 secciones-año** y **0 filas** en los 6 procesos electorales donde `SV > LN` o `SV > (SV + NV)` antes del capping.
- **Explicación:** En la base CCPC, la fuente son exclusivamente los cuadernillos de Lista Nominal de casillas básicas, contiguas y extraordinarias (`LN = SV + NV + NS`, con $SV, NV, NS \ge 0$), por lo que es matemáticamente imposible que `SV` supere a `SV + NV` o a `LN`. Además, los diccionarios oficiales (`01_descripcioncampos_conteoscensales*.txt`) especifican explícitamente que **los Conteos Censales NO incluyen casillas especiales**. La mención en el documento original a un *capping al 100% por casillas especiales con electores en tránsito* era incorrecta y debe eliminarse.
