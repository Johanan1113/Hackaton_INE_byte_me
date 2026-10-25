# Evaluación Comparativa de $k \in \{4, 5, 6\}$ dentro del Rango de la Convocatoria (4 a 6 Perfiles)

## 1. Métricas de Validación Interna y Estabilidad Bootstrap (100 réplicas al 80%)

- **$k=4$**: Silhouette = `0.1789`, Davies-Bouldin = `1.5380`, Calinski-Harabasz = `14,435.43`, ARI Bootstrap = `0.9572 ± 0.0253` (IC 95%: `[0.9091, 0.9915]`).
- **$k=5$**: Silhouette = `0.1625`, Davies-Bouldin = `1.6109`, Calinski-Harabasz = `12,676.61`, ARI Bootstrap = `0.9327 ± 0.0330` (IC 95%: `[0.8728, 0.9854]`).
- **$k=6$**: Silhouette = `0.1639`, Davies-Bouldin = `1.5709`, Calinski-Harabasz = `11,550.69`, ARI Bootstrap = `0.9675 ± 0.0162` (IC 95%: `[0.9375, 0.9887]`).

## 2. Interpretabilidad Sustantiva y Diferenciación de Política Pública

1. **¿Qué ocurre en $k=4$?**
   - En $k=4$, las secciones de *Alta Participación Consolidada y Estable* (`C2` en $k=5$, con $z=+1.64$ en estabilidad y $66.08\%$ de participación) se fusionan parcialmente con las secciones de *Participación en Ascenso con Juventud Activa* (`C4` en $k=5$, con $\beta=+1.20$ pts/año) y con las de liderazgo femenino rural (`C3` en $k=5$).
   - Esto oculta la distinción operativa crítica entre: (a) comunidades donde la participación ya es alta y estable desde 2009 (`66.08\%`), que sólo requieren mantenimiento y relevo de funcionariado de casilla, y (b) secciones donde la participación creció `+23.93 pts` entre 2009 y 2024 impulsada por votantes jóvenes (`C4`), que requieren consolidar el hábito en elecciones intermedias.

2. **¿Qué aporta $k=5$?**
   - Los 5 clusters tienen tamaños equilibrados (entre `12.95%` y `30.28%` de las secciones; ningún cluster marginal ni residual), alta estabilidad bootstrap (`ARI = 0.9327`) y cada uno posee al menos **3 variables rectoras con $|z| \ge 0.50$ sin traslape conceptual**:
     - **C0 (`17.77%`)**: Abstencionismo crónico (`48.55%`, $z=-0.84$) con rezago juvenil severo (`ratio_joven = 0.758`, $z=-1.19$; `brecha_generacional = +22.71 pts`, $z=+0.87$).
     - **C1 (`30.28%`)**: Participación intermitente de ciclo presidencial (`brecha_pres_inter = +19.42 pts`, $z=+0.90$; `estabilidad` $z=-0.72$; `tendencia = +1.14 pts/año`, $z=+0.63$; `83.20%` urbano).
     - **C2 (`12.95%`)**: Alta participación consolidada y estable (`66.08%`, $z=+1.06$; `estabilidad` $z=+1.64$; `brecha_pres_inter = +4.67 pts`, $z=-1.20$; `ratio_joven = 0.910`, $z=+1.06$).
     - **C3 (`19.93%`)**: Constancia de ciclo con liderazgo femenino y estancamiento secular (`brecha_genero = +11.96 pts`, $z=+0.97$; `tendencia` $z=-0.79$; `brecha_pres_inter = +7.96 pts`, $z=-0.73$; `estabilidad` $z=+0.65$; `41.75%` rural).
     - **C4 (`19.07%`)**: Participación en ascenso con juventud activa (`brecha_generacional = +9.62 pts`, $z=-0.95$; `ratio_joven = 0.898`, $z=+0.87$; `tendencia = +1.20 pts/año`, $z=+0.72$; `brecha_genero = +5.35 pts`, $z=-0.57$).

3. **¿Qué ocurre en $k=6$?**
   - En $k=6$, el cluster de *Participación Intermitente de Ciclo Presidencial* (`C1` en $k=5$) se subdivide en dos subgrupos urbanos con el mismo diagnóstico operativo (alta brecha presidencial-intermedia en zonas metropolitanas), diferenciados principalmente por la pendiente histórica (`beta`), lo que generaría dos estrategias redundantes orientadas al mismo canal metropolitano en elecciones intermedias.

## 3. Conclusión Metodológica

Se recomienda mantener **$k=5$** como solución principal porque maximiza la utilidad accionable para la DECEyEC y las Juntas Distritales Ejecutivas: produce 5 perfiles con diagnósticos causales hipotéticos y canales de intervención mutuamente excluyentes, cumple con holgura el criterio de estabilidad (`ARI = 0.9327 > 0.85`), evita fusionar la participación consolidada con la participación emergente (como hace $k=4$) y evita fragmentar el perfil urbano intermitente en dos subperfiles con la misma intervención operativa (como hace $k=6$).
