# Justificación de la Elección de $k=4$ dentro del Rango de la Convocatoria (4 a 6 Perfiles)

## 1. Métricas de Validación Interna y Estabilidad Bootstrap (100 réplicas al 80%)

- **$k=3$ (fuera del rango 4–6 de la convocatoria)**: Silhouette = `0.2099`, Davies-Bouldin = `1.4875`, Calinski-Harabasz = `16,402.41`, ARI Bootstrap = `0.9734 ± 0.0258` (IC 95%: `[0.9163, 0.9927]`). Aunque obtiene las mejores métricas internas al agregar el espacio en tres macro-estratos, queda fuera del rango de 4 a 6 perfiles requerido por la convocatoria.
- **$k=4$ (seleccionado)**: Silhouette = `0.1789`, Davies-Bouldin = `1.5380`, Calinski-Harabasz = `14,435.43`, ARI Bootstrap = `0.9572 ± 0.0253` (IC 95%: `[0.9091, 0.9915]`).
- **$k=5$ (dominado)**: Silhouette = `0.1625`, Davies-Bouldin = `1.6109`, Calinski-Harabasz = `12,676.61`, ARI Bootstrap = `0.9327 ± 0.0330` (IC 95%: `[0.8728, 0.9854]`).
- **$k=6$**: Silhouette = `0.1639`, Davies-Bouldin = `1.5709`, Calinski-Harabasz = `11,550.69`, ARI Bootstrap = `0.9675 ± 0.0162` (IC 95%: `[0.9375, 0.9887]`).

## 2. Criterios de Selección de $k=4$

1. **Dominancia empírica en el rango 4–6:** Dentro del intervalo de 4 a 6 perfiles establecido por la convocatoria, **$k=4$ obtiene el mejor Silhouette (`0.1789`), el menor índice Davies-Bouldin (`1.5380`) y el mayor Calinski-Harabasz (`14,435.43`)**, superando a $k=5$ en las cuatro métricas y a $k=6$ en las tres métricas de separación y compacidad interna.
2. **Estabilidad bootstrap estadísticamente indistinguible del máximo:** La estabilidad por remuestreo de $k=4$ (`ARI = 0.9572`, IC 95% `[0.9091, 0.9915]`) es comparable a la de $k=6$ (`ARI = 0.9675`, IC 95% `[0.9375, 0.9887]`), cuyos intervalos de confianza al 95% se traslapan ampliamente.
3. **Diferenciación sustantiva completa frente a $k=6$:** En $k=4$, los cuatro perfiles cuentan con al menos **5 variables rectoras con $|z| \ge 0.50$**. En contraste, $k=6$ produce un grupo sin diferenciación clara (`C1` en $k=6$, con `17.77%` del panel), el cual presenta una sola variable con $|z| \ge 0.50$ (`tendencia_participacion_beta` con $z=-0.51$) y valores cercanos al promedio nacional en las seis dimensiones restantes ($|z| \le 0.43$).
4. **Utilidad de $k=6$ como sub-segmentación auxiliar:** Con $k=6$, el perfil de baja participación (`C0` en $k=4$) se divide en un subgrupo de rezago juvenil y otro de ciclo presidencial urbano, distinción útil cuando se requiere focalización territorial fina a nivel subdistrital.
