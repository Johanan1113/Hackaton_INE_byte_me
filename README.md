# Reto 1: Perfiles Ciudadanos de Participación Electoral en México (2009–2024)
## Concurso "Hackea la participación: Datos que construyen democracia"
### CCPC 2009–2024 / ENCÍVICA — Instituto Nacional Electoral (INE)

---

## 1. Metadatos del Equipo

- **Convocatoria:** Concurso *"Hackea la participación: Datos que construyen democracia"* (CCPC 2009–2024 / ENCÍVICA).
- **Reto:** Reto 1 — Perfiles ciudadanos de participación.
- **Nombre del Equipo:** `Byte me`
- **Repositorio Público GitHub:** `https://github.com/Johanan1113/Hackaton_INE_byte_me`
- **Integrantes:**
  1. **Johanan Olivares Gutiérrez** (Representante) — *Ciencia de Datos y MLOps*
  2. **Oscar Ariel Cuevas Martínez** — *Modelación Social Computacional*
  3. **Saúl Alexis Arias González** — *Diseño de Información para Políticas Públicas*

---

## 2. Resumen Ejecutivo y Hallazgos Metodológicos

Este repositorio implementa el pipeline reproducible de auditoría, limpieza, modelado no supervisado y diseño de estrategias focalizadas de educación cívica a partir de los microdatos abiertos de los **Conteos Censales de Participación Ciudadana (CCPC)** de seis elecciones federales consecutivas (**2009, 2012, 2015, 2018, 2021 y 2024**).

### 2.1 Aporte Metodológico Central: Corrección por Registros `NS` y Fórmula Oficial `SV / (SV + NV)`
En los archivos abiertos del CCPC se cumple la identidad $\text{LN} = \text{SV} + \text{NV} + \text{NS}$, donde $\text{NS}$ corresponde a los electores cuyos cuadernillos de Lista Nominal no estuvieron disponibles para su captura por recuento distrital o contingencias operativas ($6{,}089{,}742$ registros = $6.83\%$ de la LN en 2018; $6{,}325{,}654$ registros = $6.43\%$ en 2024). Según la documentación técnica oficial del INE (*01_descripcioncampos_conteoscensales2024.txt*):

> *"Registros no especificados en participación, pues corresponden a:*
> *- Registro correspondiente a un cuadernillo sin marcas de votación.*
> *- Registro correspondiente a un cuadernillo no disponible para su captura.*
> *- Registro correspondiente a una página no disponible en el cuadernillo."*

Calcular $\text{SV}/\text{LN}$ en lugar de la fórmula oficial $\text{SV}/(\text{SV}+\text{NV})$ asigna $0.0\%$ de participación a las secciones sin captura ($\text{SV}+\text{NV}=0$), subestima la participación nacional en $4.26\text{ puntos}$ en 2018 y $3.84\text{ en }2024$, y genera grupos artificiales de baja participación en cualquier análisis de conglomerados.

Al aplicar $\text{SV}/(\text{SV}+\text{NV})$ en todas las tasas y construir el **Panel Principal (Opción B, cero imputación)** con las **53,644 secciones** que cuentan con captura válida ($\text{SV}+\text{NV} \ge 50$ en las seis elecciones) y sin saltos abruptos de Lista Nominal por reseccionamiento —cubriendo el **75.82% de las secciones** y el **79.53% de la Lista Nominal de 2024** ($78{,}199{,}518$ electores en **2,393 municipios**)—, la serie nacional reproduce los datos censales oficiales del INE (`2009: 44.06%`, `2012: 62.08%`, `2015: 47.07%`, `2018: 62.37% vs 62.4%`, `2021: 51.84% vs 51.8%`, `2024: 59.67% vs 59.7%`).

### 2.2 Los 4 Perfiles Ciudadanos de Participación (K-Means++, $k = 4$)
Dentro del rango de $4$ a $6$ perfiles de la convocatoria, **$k = 4$** alcanza el mejor desempeño en **Silhouette ($0.1789$)**, **Davies-Bouldin ($1.5380$)** y **Calinski-Harabasz ($14{,}435.43$)**, con alta estabilidad bootstrap ($\text{ARI} = 0.9572$, IC 95% $[0.9091, 0.9915]$):

| Perfil | Nombre Oficial del Perfil | Secciones (% Panel / % 2024) | LN 2024 (% Panel / % 2024) | Part. Media ($z$) | Brecha Pres-Inter ($z$) | Tendencia Anual ($z$) | Base Inter. 2021 / Pres. 2024 | Tipo Secc. U/R/M |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **C0** | **Baja Participación Intermitente con Rezago Juvenil** | 17,622 (32.85% / 24.91%) | 28,070,662 (35.90% / 28.55%) | 50.37% (-0.65) | +17.31 pts (+0.60) | +0.86 pts/año (+0.26) | 46.1% / 56.9% | 79.0/13.5/7.5% |
| **C1** | **Alta Participación Estable e Intergeneracional** | 8,824 (16.45% / 12.47%) | 11,490,525 (14.69% / 11.69%) | 65.05% (+0.95) | +5.37 pts (-1.10) | +0.15 pts/año (-0.73) | 62.5% / 65.7% | 46.0/40.9/13.2% |
| **C2** | **Participación en Ascenso con Juventud Activa** | 14,624 (27.26% / 20.67%) | 18,796,916 (24.04% / 19.12%) | 58.93% (+0.29) | +16.81 pts (+0.53) | +1.28 pts/año (+0.84) | 60.4% / 68.0% | 68.6/22.3/9.1% |
| **C3** | **Participación a la Baja con Brecha de Género** | 12,574 (23.44% / 17.77%) | 19,841,415 (25.37% / 20.18%) | 55.42% (-0.10) | +8.20 pts (-0.69) | -0.63 pts/año (-0.83) | 49.5% / 55.6% | 48.8/41.2/10.0% |
| **Panel B** | **Media Nacional Panel B** | **53,644** (100% / 75.82%) | **78,199,518** (100% / 79.53%) | **56.30%** (0.00) | **+13.07 pts** (0.00) | **+0.68 pts/año** (0.00) | **52.8% / 60.6%** | **63.7/26.9/9.5%** |

> *Nota sobre tendencias:* La columna «Tendencia Anual» reporta la pendiente lineal simple 2009–2024 (variable rectora de la tipología). La tendencia corregida que controla por el ciclo presidencial–intermedio mediante regresión con efectos fijos temporales se reporta en `tabla_19_tendencia_corregida.csv` (C0: +0.40, C1: 0.00, C2: +0.88, C3: -0.17 pts/año).

---

## 3. Estructura de Entregables y Código

```text
reto1_perfiles_participacion/
├── BITACORA.md                                      # Bitácora técnica cronológica y trazabilidad de cambios
├── requirements.txt                                 # Dependencias fijadas del entorno de ejecución
├── run_all.py                                       # Orquestador maestro reproducible de punta a punta
├── entrega_ByteMe_Reto1/                            # Carpeta con el paquete de entrega formal del concurso
│   ├── Documento_Tecnico_ByteMe.pdf                 # Documento Técnico (12 págs, Arial 11 pt / interlineado 1.5)
│   ├── Fichas_Perfiles_ByteMe.pdf                   # Fichas de perfiles (5 págs horizontales, texto >= 10 pt)
│   ├── Presentacion_Ejecutiva_ByteMe.pdf            # Presentación Ejecutiva (10 diapositivas 16:9, Arial)
│   ├── Presentacion_Ejecutiva_ByteMe.pptx           # Presentación Ejecutiva PowerPoint nativa editable
│   ├── Fichas_Portada.png                           # Portada ejecutiva (300 DPI)
│   ├── Ficha_C0.png ... Ficha_C3.png                # Fichas individuales por perfil (300 DPI)
│   ├── crear_zip_entrega.sh                         # Script automatizado de validación y empaquetado ZIP
│   ├── agregar_cartas.sh                            # Script auxiliar para incorporar cartas firmadas al ZIP
│   ├── ENLACE_REPOSITORIO.txt                       # Enlace al repositorio y notas de reproducibilidad
│   └── LEEME.txt                                    # Manifiesto formal de entrega y reserva de espacios
├── plantillas/
│   └── documento_tecnico.md.j2                      # Plantilla Jinja2 del documento técnico
├── scripts/auditoria/
│   ├── 00_inventario.py                             # Fase 0.1: Inventario del repositorio y esquemas
│   ├── 01_baseline_reproduccion.py                  # Fase 0.2: Reproducción de línea base del modelo
│   ├── 02_verificacion_datos.py                     # Fase 1: Verificación profunda de datos CCPC 2009–2024
│   ├── 03_robustez_modelo.py                        # Fase 2: Robustez del modelo y clustering k=4
│   ├── 04_perfiles_y_nombres.py                     # Fase 3: Perfiles, estrategias y metricas_finales.json
│   ├── 05_exportar_tablas.py                        # Fase 4: Exportación de tablas oficiales en CSV (utf-8-sig)
│   ├── 06_generar_figuras.py                        # Fase 5: Generación de figuras analíticas a 300 DPI
│   ├── 07_compilar_documento.py                     # Fase 6: Compilación del Documento Técnico PDF (Arial 11/19)
│   ├── 08_generar_fichas.py                         # Fase 7: Generación de Fichas de Perfiles (PDF 5 págs y PNGs)
│   ├── 09_validacion_consistencia.py                # Fase 8: Validación automatizada de consistencia y cifras
│   ├── 10_generar_presentacion.py                   # Fase 9: Generación de Presentación Ejecutiva PPTX/PDF (10 slides)
│   ├── 11_analisis_auditoria.py                     # Fase 10: Análisis de auditoría externa (calendario, pendientes, ICC, impacto)
│   └── utilidades_formato.py                        # Módulo común de redondeo ROUND_HALF_UP con Decimal
├── tests/
│   ├── test_consistencia.py                         # Suite de 28 pruebas de consistencia técnica y cifras
│   └── test_presentacion.py                         # Suite de 14 pruebas automatizadas de la presentación
└── outputs/
    ├── metricas_finales.json                        # Diccionario estructurado con métricas, diagnósticos y parámetros que alimentan deterministamente el documento, fichas y presentación
    ├── reporte_validacion_consistencia.json         # Resultado de validación automatizada
    ├── perfil_por_seccion_2024.csv                  # Tipología seccional nacional (65,748 secciones, 91.5% LN)
    ├── juntas_prioritarias_por_perfil.csv           # Priorización territorial distrital (300 distritos)
    ├── tablas/                                      # 21 tablas CSV oficiales en utf-8-sig (tabla_01..tabla_20)
    ├── figuras/                                     # Figuras PNG a 300 DPI
    └── entregables/
        ├── Documento_Tecnico_ByteMe.pdf             # Documento Técnico Oficial (12 págs, Arial 11 pt / 19 pt leading)
        ├── Fichas_Perfiles_ByteMe.pdf               # Fichas de los 4 Perfiles (5 págs horizontales)
        ├── Presentacion_Ejecutiva_ByteMe.pdf        # Presentación Ejecutiva PDF (10 diapositivas 16:9)
        ├── Presentacion_Ejecutiva_ByteMe.pptx       # Presentación Ejecutiva PPTX (gráficas nativas editables)
        ├── iconos/                                  # Íconos vectoriales oficiales en PNG 300 DPI
        ├── Fichas_Portada.png                       # Ficha Portada en PNG a 300 DPI
        ├── Ficha_C0.png ... Ficha_C3.png            # Fichas C0 a C3 en PNG a 300 DPI
        └── Fichas_Perfiles_ByteMe.png               # Vista combinada de Fichas a 300 DPI
```

### Archivos de la versión preliminar

`src/`, `main.py` y `pipeline.log` corresponden al pipeline preliminar, que calculaba la participación como SV/LN. Se conservan solo por trazabilidad: el pipeline vigente está en `scripts/auditoria/` y se ejecuta con `python run_all.py`. `output/datasets/dataset_clusters_final.parquet` es la salida de esa versión preliminar y se usa únicamente para compararla con la tipología corregida.

---

## 4. Obtención de Datos Crudos del INE (CCPC 2009–2024)

Los datos abiertos de los Conteos Censales de Participación Ciudadana corresponden a los microdatos seccionales publicados por el INE en la **Plataforma de Conteos Censales del INE** (https://www.ine.mx/conteos-censales-participacion-ciudadana/):
- **2009:** `data/raw_zips/DatosAbiertos_DECEyEC_ConteosCensales2009.zip`
- **2012:** `data/raw_zips/DatosAbiertos_DECEyEC_ConteosCensales2012.zip`
- **2015:** `data/raw_zips/DatosAbiertos_DECEyEC_ConteosCensales2015.zip`
- **2018:** `data/raw_zips/DatosAbiertos_DECEyEC_ConteosCensales2018.zip`
- **2021:** `data/raw_zips/DatosAbiertos_DECEyEC_ConteosCensales2021.zip`
- **2024:** `data/raw_zips/DatosAbiertos_DECEyEC_ConteosCensales2024.zip`

Sintaxis contraída: `data/raw_zips/DatosAbiertos_DECEyEC_ConteosCensales{2009,2012,2015,2018,2021,2024}.zip`

Para la reproducción completa desde datos crudos, dichos archivos descargados de la Plataforma de Conteos Censales del INE deben residir en `data/raw_zips/`.

Los pasos 01–03 del pipeline auditan la versión preliminar con `output/datasets/dataset_clusters_final.parquet`, incluido en el repositorio para permitir la auditoría inmediata sin necesidad de re-descargar los paquetes crudos.

---

## 5. Entorno de Software y Reproducción Completa

### Versiones Reales Verificadas
- `Python 3.14.6`, `duckdb 2.0.0`, `scikit-learn 1.9.0`, `scipy 1.18.0`, `umap-learn 0.5.12`, `pandas 3.0.3`, `numpy 2.4.6`, `statsmodels 0.14.6`, `pyarrow 23.0.1`, `matplotlib 3.11.0`, `seaborn 0.13.2`, `reportlab 5.1.0`, `pypdf 6.21.2`, `Jinja2 3.1.6`, `pytest 9.0.3`, `pillow 12.3.0`, `pdfplumber 0.11.10`, `python-pptx 1.0.2`.

### Comandos de Ejecución y Verificación
```bash
# 1. Instalar dependencias exactas
pip install -r requirements.txt

# 2. Ejecutar todo el pipeline desde cero (determinista, random_state=42)
python run_all.py

# 3. Ejecutar la suite completa de 42 pruebas automatizadas de consistencia y presentación
pytest -v
```

> **Nota de reproducibilidad:** Las pruebas automatizadas (`pytest -v`) y la ejecución del pipeline completo (`python run_all.py`) requieren el repositorio completo clonado desde GitHub (incluyendo los scripts, modelos intermedios y tablas analíticas).
>
> **Convención de redondeo:** Las cifras a 1 decimal se obtienen redondeando (`ROUND_HALF_UP`) el valor publicado a 2 decimales en `outputs/tablas`, para que cualquier lector las reproduzca desde las tablas publicadas.


