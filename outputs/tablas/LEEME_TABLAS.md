# Catálogo de Tablas Analíticas Oficiales (outputs/tablas/)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

1. `tabla_01_cascada_universo.csv`: Cascada metodológica de conformación del universo de análisis y panel principal de secciones (2009–2024).
2. `tabla_02_serie_nacional_2009_2024.csv`: Serie temporal de participación nacional oficial CCPC vs. panel y subestimación por SV/LN (la columna `dif_reportada_doc_erronea_vs_oficial_pts` es histórico de la versión preliminar).
3. `tabla_03_incluidas_vs_excluidas_2024.csv`: Comparativa de balance y cobertura entre secciones incluidas en el Panel B y secciones excluidas en 2024.
4. `tabla_04_benchmark_modelos.csv`: Benchmark de algoritmos de agrupamiento y métricas de validación interna para k=4, 5 y 6.
5. `tabla_05a_estabilidad_comparacion.csv`: Comparación de estabilidad y consistencia de clústeres mediante remuestreo bootstrap (ARI).
6. `tabla_05b_vif_colinealidad.csv`: Diagnóstico de multicolinealidad (VIF) entre variables rectoras e impacto de exclusión etaria en ARI.
7. `tabla_05c_ventanas_temporales.csv`: Análisis de sensibilidad temporal y estabilidad de la tipología ante ventanas sub-periódicas.
8. `tabla_06_perfiles_k4_resumen.csv`: Resumen cuantitativo de los 4 perfiles ciudadanos (secciones, Lista Nominal, medias z y tipo seccional).
9. `tabla_07_perfiles_k4_series_demografia.csv`: Trayectoria histórica hexanual y desglose sociodemográfico por perfil ciudadano (2009–2024).
10. `tabla_08_estrategias_k4.csv`: Matriz de estrategias focalizadas de educación cívica, metas e hipótesis por perfil ciudadano.
11. `tabla_09_transicion_clusters.csv`: Matriz de transición y reasignación de secciones entre k=3 preliminar y k=4 auditado (histórico de la versión preliminar).
12. `tabla_10_sensibilidad_opcion_a.csv`: Análisis de sensibilidad comparativo frente a imputación de secciones atípicas (Opción A vs. Opción B).
13. `tabla_11_interpretabilidad_rf_anova.csv`: Diagnóstico de interpretabilidad y relevancia de características mediante Random Forest y ANOVA.
14. `tabla_12_lineas_base_metas.csv`: Líneas base observadas (2021/2024) y metas cuantitativas verificables generales y secundarias por perfil rumbo a 2027 y 2030.
15. `tabla_13_validacion_temporal.csv`: Validación fuera de tiempo (calibración 2009–2021 y evaluación predictiva sobre comicios de 2024).
16. `tabla_14_cobertura_ampliada.csv`: Cobertura ampliada nacional y asignación por proximidad euclidiana de secciones no panelizadas en 2024.
17. `tabla_15_potencia_piloto.csv`: Diseño experimental y cálculo de potencia estadística (MDE ANCOVA) para piloto seccional en C0 en 2027.
18. `tabla_17_impacto.csv`: Impacto electoral estimado en electores adicionales y votantes en riesgo de regresión por perfil ciudadano hacia 2027.
19. `tabla_18_calendario_electoral.csv`: Evaluación del impacto del calendario electoral concurrente en la participación intermedia (2015–2021).
20. `tabla_19_tendencia_corregida.csv`: Estimación de tendencia secular corregida por ciclo presidencial–intermedio por perfil ciudadano.
21. `tabla_20_correlaciones.csv`: Matriz de correlaciones de Pearson entre las 7 variables rectoras del modelo sobre el Panel Principal.

Nota sobre numeración: No existe `tabla_16` debido a la reestructuración metodológica que unificó el análisis de potencia del piloto (Bloque E, Tabla 15) y el análisis de impacto territorial (Bloque D, Tabla 17) sin requerir una tabla intermedia.
