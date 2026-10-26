# Reto 1: Perfiles Ciudadanos de Participación Electoral en México (2009–2024)
## Concurso "Hackea la participación: Datos que construyen democracia"
### CCPC 2009–2024 / ENCÍVICA — Instituto Nacional Electoral (INE)

---

## 1. Metadatos del Equipo

- **Convocatoria:** Concurso *"Hackea la participación: Datos que construyen democracia"* (CCPC 2009–2024 / ENCÍVICA).
- **Reto:** Reto 1 — Perfiles ciudadanos de participación.
- **Nombre del Equipo:** `Byte me`
- **Integrantes:**
  1. **Johanan Olivares Gutierrez** (Representante) — *Ciencia de Datos y MLOps*
  2. **Oscar Ariel Cuevas Martinez** — *Modelación Social Computacional*
  3. **Saul Alexis Arias Gonzales** — *Diseño de Información para Políticas Públicas*

---

## 2. Resumen Ejecutivo y Hallazgos Metodológicos

Este repositorio implementa el pipeline reproducible de auditoría, limpieza, modelado no supervisado y diseño de estrategias focalizadas de educación cívica a partir de los microdatos abiertos de los **Conteos Censales de Participación Ciudadana (CCPC)** de seis elecciones federales consecutivas (**2009, 2012, 2015, 2018, 2021 y 2024**).

### 2.1 Aporte Metodológico Central: Corrección por Registros `NS` y Fórmula Oficial `SV / (SV + NV)`
En los archivos abiertos del CCPC se cumple la identidad $\text{LN} = \text{SV} + \text{NV} + \text{NS}$, donde $\text{NS}$ corresponde a los electores cuyos cuadernillos de Lista Nominal no estuvieron disponibles para su captura por recuento distrital o contingencias operativas ($6{,}089{,}742$ registros = $6.83\%$ de la LN en 2018; $6{,}325{,}654$ registros = $6.43\%$ en 2024). Calcular $\text{SV}/\text{LN}$ en lugar de la fórmula oficial $\text{SV}/(\text{SV}+\text{NV})$ asignaba $0.0\%$ de participación a las secciones sin cuadernillos capturados ($\text{SV}+\text{NV}=0$), subestimando la participación nacional en $-4.27\text{ pts}$ (2018) y $-3.84\text{ pts}$ (2024) y fabricando un cluster artificial de supuesto declive cívico.

Al aplicar $\text{SV}/(\text{SV}+\text{NV})$ en todas las tasas y construir el **Panel Principal (Opción B, cero imputación)** con las **53,644 secciones** que cuentan con captura válida ($\text{SV}+\text{NV} \ge 50$ en las seis elecciones) y sin saltos abruptos de Lista Nominal por reseccionamiento —cubriendo el **75.82% de las secciones** y el **79.53% de la Lista Nominal de 2024** ($78{,}199{,}518$ electores en **2,393 municipios**)—, la serie nacional reproduce los datos censales oficiales del INE (`2009: 44.06%`, `2012: 62.08%`, `2015: 47.07%`, `2018: 62.37% vs 62.4%`, `2021: 51.84% vs 51.8%`, `2024: 59.67% vs 59.7%`).

### 2.2 Los 4 Perfiles Ciudadanos de Participación (K-Means++, $k = 4$)
Dentro del rango de $4$ a $6$ perfiles de la convocatoria, **$k = 4$** alcanza el mejor desempeño en **Silhouette ($0.1789$)**, **Davies-Bouldin ($1.5380$)** y **Calinski-Harabasz ($14{,}435.43$)**, con alta estabilidad bootstrap ($\text{ARI} = 0.9572$, IC 95% $[0.9091, 0.9915]$):

| Perfil | Nombre Oficial del Perfil | Secciones (% Panel / % 2024) | LN 2024 (% Panel / % 2024) | Part. Media ($z$) | Brecha Pres-Inter ($z$) | Tendencia OLS ($z$) | Base Inter. 2021 / Pres. 2024 | Tipo Secc. U/R/M |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **C0** | **Baja Participación Intermitente con Rezago Juvenil** | 17,622 (32.85% / 24.91%) | 28,070,662 (35.90% / 28.55%) | 50.37% (-0.65) | +17.31 pts (+0.60) | +0.86 pts/a (+0.26) | 46.1% / 56.9% | 79.0/13.5/7.5% |
| **C1** | **Alta Participación Estable e Intergeneracional** | 8,824 (16.45% / 12.47%) | 11,490,525 (14.69% / 11.69%) | 65.05% (+0.95) | +5.37 pts (-1.10) | +0.15 pts/a (-0.73) | 62.5% / 65.7% | 46.0/40.9/13.2% |
| **C2** | **Participación en Ascenso con Juventud Activa** | 14,624 (27.26% / 20.67%) | 18,796,916 (24.04% / 19.12%) | 58.93% (+0.29) | +16.81 pts (+0.53) | +1.28 pts/a (+0.84) | 60.4% / 68.0% | 68.6/22.3/9.1% |
| **C3** | **Liderazgo Femenino con Participación Estancada** | 12,574 (23.44% / 17.77%) | 19,841,415 (25.37% / 20.18%) | 55.42% (-0.10) | +8.20 pts (-0.69) | +0.08 pts/a (-0.83) | 49.5% / 55.6% | 48.8/41.2/10.0% |
| **Panel B** | **Media Nacional Panel B** | **53,644** (100% / 75.82%) | **78,199,518** (100% / 79.53%) | **56.30%** (0.00) | **+13.07 pts** (0.00) | **+0.68 pts/a** (0.00) | **52.8% / 60.6%** | **63.7/26.9/9.5%** |

---

## 3. Estructura de Entregables y Código

```text
reto1_perfiles_participacion/
├── BITACORA.md                                      # Bitácora técnica cronológica y trazabilidad de cambios
├── requirements.txt                                 # Versiones reales fijadas del entorno de ejecución
├── run_all.py                                       # Orquestador maestro reproducible de punta a punta
├── plantillas/
│   └── documento_tecnico.md.j2                      # Plantilla Jinja2 del documento técnico (cero cifras fijas)
├── scripts/auditoria/
│   ├── 01_inventario_repo.py                        # Fase 0: Inventario del repositorio y auditoría de esquema
│   ├── 02_verificacion_datos.py                     # Fase 1: Serie nacional SV/(SV+NV), diagnóstico C4 e incluidas vs excluidas
│   ├── 03_robustez_modelo.py                        # Fase 2: Filtrado Opción B (53,644), VIF, benchmark k=3..7, sensibilidad Opción A
│   ├── 04_perfiles_y_nombres.py                     # Fase 3-4: Perfiles k=4, estrategias ENCÍVICA y metricas_finales.json
│   ├── 05_exportar_tablas.py                        # Fase 5: Exportación de las 11 tablas oficiales en CSV
│   ├── 06_generar_figuras.py                        # Fase 6: Generación de las 7 figuras analíticas a 300 DPI
│   ├── 07_compilar_documento.py                     # Fase 7.1-7.2: Compilación del Documento Técnico (MD, PDF de 12 págs y DOCX)
│   ├── 08_generar_fichas.py                         # Fase 7.3: Generación de las Fichas de Perfiles (PDF y PNG a 300 DPI)
│   └── 09_validacion_consistencia.py                # Fase 7.4: Ejecución de pytest y auditoría de extracción de números
├── tests/
│   └── test_consistencia.py                         # 8 tests automatizados (incluye extracción exhaustiva de números)
└── outputs/
    ├── metricas_finales.json                        # Fuente única de verdad (SHA-256 verificado en doble corrida)
    ├── reporte_validacion_consistencia.json         # Resultado de validación (0 discrepancias en MD, PDF y Fichas)
    ├── tablas/                                      # 11 tablas CSV oficiales (tabla_01..tabla_11)
    ├── figuras/                                     # 7 figuras PNG a 300 DPI (fig1..fig7)
    └── entregables/
        ├── Documento_Tecnico_ByteMe.pdf             # Documento Técnico Oficial (12 páginas)
        ├── Documento_Tecnico_ByteMe.md              # Fuente Markdown renderizada desde plantilla
        ├── Documento_Tecnico_ByteMe.docx            # Versión editable Word (.docx)
        ├── Fichas_Perfiles_ByteMe.pdf               # Infografía / Fichas de los 4 Perfiles en PDF
        ├── Fichas_Perfiles_ByteMe.png               # Infografía / Fichas de los 4 Perfiles en PNG a 300 DPI
        └── paginas_png/                             # Páginas convertidas a PNG para inspección visual
```

---

## 4. Entorno de Software y Reproducción Completa

### Versiones Reales Verificadas
- `Python 3.14.6`, `duckdb 2.0.0`, `scikit-learn 1.9.0`, `scipy 1.18.0`, `umap-learn 0.5.12`, `pandas 3.0.3`, `numpy 2.4.6`, `statsmodels 0.14.6`, `pyarrow 23.0.1`, `matplotlib 3.11.0`, `seaborn 0.13.2`, `reportlab 5.1.0`, `pypdf 6.21.2`, `Jinja2 3.1.6`, `pytest 9.0.3`, `pillow 12.3.0`.

### Comandos de Ejecución y Verificación
```bash
# 1. Instalar dependencias exactas
pip install -r requirements.txt

# 2. Ejecutar todo el pipeline desde cero (Fases 0 a 8)
python run_all.py

# 3. Ejecutar únicamente la suite de pruebas de consistencia y control de cifras
pytest tests/test_consistencia.py -v
```
