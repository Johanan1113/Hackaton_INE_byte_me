#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fase 3 y 4: Reconstrucción de Perfiles (k=4), Nombres Objetivos, Estrategias y Viabilidad (04_perfiles_y_nombres.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

Genera a partir de outputs/fase2/etiquetas_finales.parquet (con k=4 como solución principal):
- outputs/fase3/perfiles.csv: Caracterización integral de los 4 perfiles en escala original y z-scores,
  series 2009-2024 (simples y ponderadas), métricas demográficas (incluyendo ambos cálculos del ratio joven),
  composición U/R/M (por secciones y por LN), campo indígena/afromexicano marcado como [PENDIENTE] y Top 5 entidades.
- outputs/fase3/estrategias.csv: Estrategias para los 4 perfiles con líneas base observadas en 2021/2024,
  costos cualitativos indicativos (cero cifras monetarias inventadas), lemas neutrales y factores causales como hipótesis.
- outputs/fase3/comparacion_k4_k5_k6.csv y comparacion_k4_k5_k6.md: Evaluación comparativa de k=4, 5 y 6.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_FASE2 = PROJECT_ROOT / "outputs" / "fase2"
OUT_FASE3 = PROJECT_ROOT / "outputs" / "fase3"
OUT_FASE3.mkdir(parents=True, exist_ok=True)

YEARS = [2009, 2012, 2015, 2018, 2021, 2024]
FEATURE_COLS = [
    "participacion_media_historica",
    "brecha_presidencial_intermedia",
    "tendencia_participacion_beta",
    "estabilidad_participacion",
    "brecha_generacional",
    "brecha_genero",
    "ratio_participacion_joven",
]

# Nombres finales aprobados (idénticos en tablas, estrategias, documento e infografía)
CLUSTER_META = {
    0: {
        "codigo": "C0",
        "nombre": "Baja Participación Intermitente con Rezago Juvenil",
        "variables_rectoras_z": (
            "estabilidad_participacion (z=-0.65), participacion_media_historica (z=-0.65), "
            "ratio_participacion_joven (z=-0.62), brecha_presidencial_intermedia (z=+0.60), "
            "brecha_generacional (z=+0.58)"
        ),
        "justificacion_regla_3_2": (
            "Sus 5 variables con |z|>=0.5 son estabilidad_participacion (-0.65, mínima nacional: 1.7036), "
            "participacion_media_historica (-0.65, mínima nacional: 50.37%), ratio_participacion_joven "
            "(-0.62, mínimo nacional: 0.7963 con 40.17% de votación juvenil), brecha_presidencial_intermedia "
            "(+0.60, máxima nacional: +17.31 pts entre presidenciales 59.02% e intermedias 41.71%) y "
            "brecha_generacional (+0.58: +20.64 pts entre 60+ con 60.81% y 18-29 con 40.17%). Concentra el "
            "32.85% de las secciones del panel y es predominantemente urbano (78.99% de secciones urbanas)."
        ),
        "lema_neutral": "Cada elección define tu entorno: infórmate, ubica tu casilla y participa en 2027",
        "hipotesis_abstencionismo": (
            "Hipótesis: asimetría de visibilidad informativa entre elecciones presidenciales e intermedias "
            "en zonas urbanas y metropolitanas, combinada con barreras de incorporación al primer sufragio "
            "y movilidad residencial o laboral en jóvenes de 18 a 29 años (tanto escolarizados como fuera del sistema educativo)."
        ),
        "objetivo_especifico": (
            "Reducir la caída de participación en elecciones intermedias (línea base ponderada de 46.1% en 2021 "
            "frente a 56.9% en la presidencial de 2024) e incrementar la tasa de votación del grupo de 18 a 29 años "
            "(línea base hexanual de 40.2%) en las 17,622 secciones del perfil."
        ),
        "canal_principal": (
            "Doble línea de intervención: (1) Ciclo intermedio urbano: transporte público masivo, corredores "
            "metropolitanos, medios públicos/digitales y plataforma 'Conóceles'; (2) Juventudes escolarizadas y "
            "no escolarizadas: universidades y planteles de educación media superior, más centros de trabajo, "
            "parques industriales, tianguis, centros comunitarios, deportivos barriales y mensajería digital "
            "geolocalizada ('Ubica tu Casilla')."
        ),
        "narrativa_mensaje": (
            "En la Línea 1, pedagogía institucional sobre las atribuciones de la Cámara de Diputados (presupuesto "
            "federal, fiscalización y legislación cotidiana); en la Línea 2, guía práctica para el primer voto, "
            "actualización de domicilio en el Padrón Electoral y localización exacta de casilla para jóvenes que "
            "estudian y jóvenes en centros laborales o comunitarios."
        ),
        "accion_operativa_ine": (
            "Línea 1: campaña cívica metropolitana pre-intermedia (2027) de la DECEyEC y Juntas Locales/Distritales "
            "con despliegue de códigos QR hacia 'Conóceles'. Línea 2: brigadas móviles de actualización registral "
            "(DERFE) y promoción cívica (DECEyEC) tanto en campus educativos como en centros laborales, parques "
            "industriales, tianguis y espacios deportivos barriales de las 17,622 secciones."
        ),
        "unidad_responsable": "DECEyEC en coordinación con las Juntas Locales y Distritales Ejecutivas y la DERFE",
        "costo_estimado_orden_magnitud": (
            "Nivel Medio — Estimación indicativa de orden operativo (sujeta a presupuestación de DECEyEC, DERFE y "
            "Juntas Distritales Ejecutivas; aprovecha tiempos oficiales del Estado, módulos itinerantes existentes "
            "y convenios con instituciones educativas y centros de trabajo)."
        ),
        "meta_cuantitativa": (
            "Elevar la participación ponderada del cluster en la elección intermedia de 2027 a 49.5% (+3.4 puntos "
            "porcentuales respecto al 46.1% observado en la intermedia de 2021, cerrando la mitad de la diferencia "
            "frente al 52.8% del Panel B en 2021) e incrementar la tasa de votación juvenil (18-29 años) de su "
            "línea base hexanual de 40.2% a 43.5% (+3.3 pts)."
        ),
        "indicador_seguimiento": (
            "Tasa de participación ponderada SV/(SV+NV) del cluster en la intermedia de 2027 (vs 46.1% en 2021) y "
            "tasa seccional SV/(SV+NV) del grupo 18-29 años en el CCPC 2027."
        ),
        "horizonte_temporal": "Permanente con intensificación preelectoral rumbo a la intermedia 2026-2027",
    },
    1: {
        "codigo": "C1",
        "nombre": "Alta Participación Estable e Intergeneracional",
        "variables_rectoras_z": (
            "estabilidad_participacion (z=+1.42), brecha_presidencial_intermedia (z=-1.10), "
            "brecha_generacional (z=-1.07), ratio_participacion_joven (z=+1.04), "
            "participacion_media_historica (z=+0.95), tendencia_participacion_beta (z=-0.73)"
        ),
        "justificacion_regla_3_2": (
            "Presenta los niveles más altos de estabilidad_participacion (+1.42: 2.5897), ratio_participacion_joven "
            "(+1.04: 0.9090, con 59.10% de votación juvenil) y participacion_media_historica (+0.95: 65.05%, con "
            "67.74% en presidenciales y 62.37% en intermedias), así como las menores brechas presidencial-intermedia "
            "(-1.10: +5.37 pts) y generacional (-1.07: +8.78 pts). Su pendiente anual es ligeramente positiva "
            "(+0.15 pts/año, z=-0.73 respecto a la media nacional de +0.68 pts/año) porque ya partía de un nivel "
            "alto en 2009 (59.17% ponderado / 59.30% simple)."
        ),
        "lema_neutral": "La constancia cívica fortalece a tu comunidad: intégrate como funcionaria o funcionario de casilla",
        "hipotesis_abstencionismo": (
            "Hipótesis: cohesión comunitaria e intergeneracional consolidada en contextos urbanos (46.0%), rurales "
            "(40.9%) y mixtos (13.1%) que sostiene altos niveles de sufragio en ambos tipos de elección; su principal "
            "reto operativo es asegurar el relevo generacional en la integración de Mesas Directivas de Casilla y la observación electoral."
        ),
        "objetivo_especifico": (
            "Sostener los niveles históricos de participación en elecciones intermedias (62.5% ponderado en 2021; "
            "media histórica intermedia de 62.4%) y presidenciales (65.7% ponderado en 2024; media histórica "
            "presidencial de 67.7%), fortaleciendo el voluntariado cívico en las 8,824 secciones del perfil."
        ),
        "canal_principal": (
            "Redes comunitarias, planteles educativos locales, centros culturales y sesiones distritales de "
            "reconocimiento cívico y reclutamiento de funcionariado de casilla."
        ),
        "narrativa_mensaje": (
            "Reconocimiento institucional a la constancia cívica comunitaria e invitación a participar como "
            "funcionariado de Mesa Directiva de Casilla, personas observadoras electorales y promotoras de educación cívica intergeneracional."
        ),
        "accion_operativa_ine": (
            "Sistematización de buenas prácticas comunitarias por la DECEyEC en el marco de ENCÍVICA, talleres de "
            "liderazgo cívico juvenil para el relevo generacional y reclutamiento temprano de Capacitadores-Asistentes "
            "Electorales (CAE) y funcionariado de casilla por las Juntas Distritales Ejecutivas."
        ),
        "unidad_responsable": "DECEyEC y Dirección Ejecutiva de Capacitación Electoral y Educación Cívica en las Juntas Distritales Ejecutivas",
        "costo_estimado_orden_magnitud": (
            "Nivel Bajo — Estimación indicativa de orden operativo (sujeta a presupuestación de DECEyEC y Juntas "
            "Distritales Ejecutivas; absorbible dentro de los programas ordinarios de educación cívica y capacitación electoral distrital)."
        ),
        "meta_cuantitativa": (
            "Sostener una participación ponderada >= 62.5% en la elección intermedia de 2027 (preservando el 62.5% "
            "observado en la intermedia de 2021) y >= 67.5% en la elección presidencial de 2030 (acorde con su media "
            "presidencial de 67.7%), logrando el 100% de integración de Mesas Directivas de Casilla con funcionariado propietario capacitado."
        ),
        "indicador_seguimiento": (
            "Tasa de participación ponderada SV/(SV+NV) en la intermedia de 2027 (vs 62.5% en 2021), en la "
            "presidencial de 2030 (vs 65.7% en 2024), y porcentaje de casillas integradas con propietarios en primera insaculación."
        ),
        "horizonte_temporal": "Continuo de mantenimiento y relevo generacional (2025-2030)",
    },
    2: {
        "codigo": "C2",
        "nombre": "Participación en Ascenso con Juventud Activa",
        "variables_rectoras_z": (
            "tendencia_participacion_beta (z=+0.84), ratio_participacion_joven (z=+0.60), "
            "brecha_generacional (z=-0.59), brecha_presidencial_intermedia (z=+0.53), "
            "estabilidad_participacion (z=-0.53)"
        ),
        "justificacion_regla_3_2": (
            "Sus 5 variables con |z|>=0.5 son tendencia_participacion_beta (+0.84, máxima nacional: +1.28 pts/año, "
            "pasando de 41.83% ponderado en 2009 a 60.37% en la intermedia de 2021 y 68.04% en la presidencial de 2024), "
            "ratio_participacion_joven (+0.60: 0.8793 con 51.81% de votación juvenil), brecha_generacional (-0.59: +12.20 pts), "
            "brecha_presidencial_intermedia (+0.53: +16.81 pts porque partió de intermedias bajas en 2009 y 2015) y "
            "estabilidad_participacion (-0.53 por ese mismo ascenso)."
        ),
        "lema_neutral": "Tu participación ya transforma tu comunidad: consolidemos el voto en cada elección",
        "hipotesis_abstencionismo": (
            "Hipótesis: creciente movilización cívica y dinamismo demográfico juvenil en secciones urbanas (68.6%) y "
            "periurbanas/rurales (31.4%) que elevó la participación intermedia de 41.8% (2009) y 48.3% (2015) a 60.4% "
            "(2021); el riesgo principal es la regresión hacia su media intermedia histórica (50.5%) si no se "
            "institucionaliza el hábito del voto legislativo."
        ),
        "objetivo_especifico": (
            "Consolidar en la elección intermedia de 2027 el nivel de participación alcanzado en 2021 (60.4% ponderado), "
            "evitando un retroceso hacia su promedio intermedio histórico (50.5% simple / 50.2% ponderado) en las "
            "14,624 secciones del perfil."
        ),
        "canal_principal": (
            "Colectivos juveniles y estudiantiles, redes comunitarias y vecinales, plataformas digitales interactivas "
            "('Conóceles') y espacios de diálogo distrital convocados por las Juntas Distritales Ejecutivas."
        ),
        "narrativa_mensaje": (
            "Continuidad del compromiso cívico como práctica permanente en comicios legislativos y locales, vinculando "
            "la participación juvenil con el seguimiento de propuestas y atribuciones de la Cámara de Diputados."
        ),
        "accion_operativa_ine": (
            "Despliegue de foros distritales 'Diálogos por la Democracia' de la DECEyEC, alianzas con redes juveniles y "
            "vecinales para promoción del voto informado rumbo a 2027 y monitoreo de capacidad instalada de casillas "
            "por la DEOE en secciones en crecimiento."
        ),
        "unidad_responsable": "DECEyEC en coordinación con las Juntas Distritales Ejecutivas y la DEOE",
        "costo_estimado_orden_magnitud": (
            "Nivel Bajo-Medio — Estimación indicativa de orden operativo (sujeta a presupuestación de DECEyEC y Juntas "
            "Distritales Ejecutivas; basada en foros distritales, vinculación comunitaria y comunicación digital institucional)."
        ),
        "meta_cuantitativa": (
            "Consolidar en la elección intermedia de 2027 una participación ponderada >= 60.4% (sosteniendo la línea "
            "base observada en la intermedia de 2021 de 60.4% e impidiendo una regresión hacia su media intermedia "
            "histórica de 50.5%) y mantener el ratio_participacion_joven >= 0.88."
        ),
        "indicador_seguimiento": (
            "Tasa de participación ponderada SV/(SV+NV) en la intermedia de 2027 (vs 60.4% en 2021 y vs 48.3% en 2015) "
            "y ratio_participacion_joven en el CCPC 2027."
        ),
        "horizonte_temporal": "Consolidación en el ciclo intermedio 2025-2027",
    },
    3: {
        "codigo": "C3",
        "nombre": "Liderazgo Femenino con Participación Estancada",
        "variables_rectoras_z": (
            "tendencia_participacion_beta (z=-0.83), brecha_genero (z=+0.78), "
            "brecha_presidencial_intermedia (z=-0.69), brecha_generacional (z=+0.62), "
            "ratio_participacion_joven (z=-0.56), estabilidad_participacion (z=+0.52)"
        ),
        "justificacion_regla_3_2": (
            "Sus 6 variables con |z|>=0.5 son tendencia_participacion_beta (z=-0.83 respecto a la media nacional: su "
            "pendiente global es +0.08 pts/año, positiva pero estancada porque las intermedias se mantuvieron en "
            "49.6% [2009], 50.4% [2015] y 49.5% [2021], mientras que la participación presidencial cayó de 61.2% "
            "ponderado en 2012 a 59.0% en 2018 y 55.6% en 2024), brecha_genero (+0.78, máxima nacional: +11.15 pts a "
            "favor de las mujeres con 60.85% vs 49.70% en hombres), brecha_presidencial_intermedia (-0.69: +8.20 pts), "
            "brecha_generacional (+0.62: +20.94 pts, 60+ con 65.35% vs 18-29 con 44.41%), ratio_participacion_joven "
            "(-0.56: 0.8007) y estabilidad_participacion (+0.52: 2.2047). Su composición es 48.8% urbana, 41.2% rural "
            "y 10.0% mixta (pluralidad urbana con sobrerrepresentación rural frente al 26.9% del panel)."
        ),
        "lema_neutral": "La participación de todas y todos cuenta: sumemos la voz de hombres y jóvenes en cada comunidad",
        "hipotesis_abstencionismo": (
            "Hipótesis: rezago persistente en la participación masculina (49.70% vs 60.85% femenina) y juvenil "
            "(44.41% vs 65.35% en adultos mayores) asociado a dinámicas laborales, movilidad ocupacional masculina y "
            "desvinculación en elecciones presidenciales (donde la votación bajó de 61.2% en 2012 a 55.6% en 2024), "
            "aunado en su segmento rural (41.2% de las secciones) a costos de traslado físico a la casilla."
        ),
        "objetivo_especifico": (
            "Elevar la participación masculina (línea base hexanual de 49.70% frente a 60.85% en mujeres) y revertir "
            "la caída en elecciones presidenciales (de 61.2% en 2012 a 55.6% en 2024) y el estancamiento en "
            "intermedias (49.5% en 2021) en las 12,574 secciones del perfil, atendiendo como acción secundaria la "
            "accesibilidad en sus localidades con sobrerrepresentación rural."
        ),
        "canal_principal": (
            "Acción principal: centros de trabajo con alta presencia masculina (agropecuarios, industriales, "
            "construcción, transporte y comercio), perifoneo y radiodifusoras regionales y comunitarias en tiempos "
            "oficiales. Acción secundaria (sobrerrepresentación rural 41.2%): módulos itinerantes de las Juntas "
            "Distritales Ejecutivas y asambleas comunitarias."
        ),
        "narrativa_mensaje": (
            "Corresponsabilidad de hombres y jóvenes en la vida comunitaria y en el ejercicio del sufragio tanto en "
            "comicios intermedios como presidenciales, complementada con información oportuna sobre ubicación y "
            "horarios de casilla."
        ),
        "accion_operativa_ine": (
            "Acción principal: campañas de promoción del voto masculino y juvenil de la DECEyEC y Juntas Distritales "
            "en centros laborales, gremios de transporte/construcción/agroindustria y radio regional en tiempos "
            "oficiales. Acción secundaria: brigadas móviles de educación cívica y revisión de accesibilidad geográfica "
            "de domicilios de casilla (DEOE) en el 41.2% de secciones rurales y 10.0% mixtas del perfil."
        ),
        "unidad_responsable": "Juntas Distritales Ejecutivas, DECEyEC y Dirección Ejecutiva de Organización Electoral (DEOE)",
        "costo_estimado_orden_magnitud": (
            "Nivel Medio — Estimación indicativa de orden operativo (sujeta a presupuestación de DECEyEC, DEOE y "
            "Juntas Distritales Ejecutivas; combina vinculación en centros laborales, pauta en tiempos oficiales de "
            "radio regional y rutas de campo distritales)."
        ),
        "meta_cuantitativa": (
            "Incrementar la participación ponderada del cluster en la elección intermedia de 2027 de 49.5% (línea base "
            "2021) a 51.5% (+2.0 pts), recuperar en la elección presidencial de 2030 la participación de 55.6% (línea "
            "base 2024) a 58.5% (+2.9 pts), y elevar la tasa de participación masculina de su línea base hexanual de "
            "49.7% a 52.5% (+2.8 pts, reduciendo la brecha de género de 11.15 a ~8.4 pts)."
        ),
        "indicador_seguimiento": (
            "Tasa de participación masculina SV/(SV+NV), participación ponderada en la intermedia de 2027 (vs 49.5% en "
            "2021) y participación ponderada en la presidencial de 2030 (vs 55.6% en 2024) en el CCPC."
        ),
        "horizonte_temporal": "Mediano y largo plazo con intervención en ciclos 2026-2027 y 2029-2030",
    },
}


def build_perfiles_and_estrategias(df_b: pd.DataFrame, df_univ: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye outputs/fase3/perfiles.csv y outputs/fase3/estrategias.csv para k=4."""
    total_sec_b = len(df_b)
    total_ln_b = int(df_b["ln_2024"].sum())
    total_sec_2024 = int(df_univ.loc[df_univ["etapa"] == "1_universo_2024", "secciones"].iloc[0])
    total_ln_2024 = int(df_univ.loc[df_univ["etapa"] == "1_universo_2024", "ln_2024"].iloc[0])

    # Medias y DE nacionales sobre el panel principal (N=53,644) para z-scores exactos
    nat_means = {col: float(df_b[col].mean()) for col in FEATURE_COLS}
    nat_stds = {col: float(df_b[col].std(ddof=1)) for col in FEATURE_COLS}

    perfiles_rows = []
    estrategias_rows = []

    for c in range(4):
        sub = df_b[df_b["cluster"] == c]
        meta = CLUSTER_META[c]
        n_sec = len(sub)
        ln_24 = int(sub["ln_2024"].sum())

        # Composición Urbana / Rural / Mixta
        u_sec_pct = float((sub["tipo_2024"] == "U").mean() * 100)
        r_sec_pct = float((sub["tipo_2024"] == "R").mean() * 100)
        m_sec_pct = float((sub["tipo_2024"] == "M").mean() * 100)

        u_ln_pct = float(sub.loc[sub["tipo_2024"] == "U", "ln_2024"].sum() / ln_24 * 100)
        r_ln_pct = float(sub.loc[sub["tipo_2024"] == "R", "ln_2024"].sum() / ln_24 * 100)
        m_ln_pct = float(sub.loc[sub["tipo_2024"] == "M", "ln_2024"].sum() / ln_24 * 100)

        # Top 5 entidades por % de secciones del cluster y por % de LN 2024 del cluster
        ent_sec = (
            sub.groupby("entidad", as_index=False)
            .agg(secciones=("seccion_id", "count"), ln_2024=("ln_2024", "sum"))
        )
        ent_sec["pct_sec_cluster"] = ent_sec["secciones"] / n_sec * 100
        ent_sec["pct_ln_cluster"] = ent_sec["ln_2024"] / ln_24 * 100

        top5_sec = ent_sec.sort_values("pct_sec_cluster", ascending=False).head(5)
        top5_ln = ent_sec.sort_values("pct_ln_cluster", ascending=False).head(5)

        top5_sec_str = "; ".join(
            f"{r['entidad']} ({r['pct_sec_cluster']:.1f}%, {int(r['secciones']):,} sec)"
            for _, r in top5_sec.iterrows()
        )
        top5_ln_str = "; ".join(
            f"{r['entidad']} ({r['pct_ln_cluster']:.1f}%, {int(r['ln_2024']):,} LN)"
            for _, r in top5_ln.iterrows()
        )

        # Top 5 entidades por presencia interna (qué % de las secciones de la entidad pertenecen a este cluster)
        ent_tot = df_b.groupby("entidad")["seccion_id"].count().rename("sec_entidad_total")
        ent_spec = ent_sec.merge(ent_tot, on="entidad")
        ent_spec["pct_dentro_entidad"] = ent_spec["secciones"] / ent_spec["sec_entidad_total"] * 100
        top5_spec = ent_spec[ent_spec["sec_entidad_total"] >= 200].sort_values("pct_dentro_entidad", ascending=False).head(5)
        top5_spec_str = "; ".join(
            f"{r['entidad']} ({r['pct_dentro_entidad']:.1f}% del estado)"
            for _, r in top5_spec.iterrows()
        )

        row_p = {
            "cluster_id": c,
            "codigo_cluster": meta["codigo"],
            "nombre_propuesto": meta["nombre"],
            "variables_rectoras_z": meta["variables_rectoras_z"],
            "justificacion_regla_3_2": meta["justificacion_regla_3_2"],
            "n_secciones": n_sec,
            "pct_secciones_panel": round(n_sec / total_sec_b * 100, 2),
            "pct_secciones_2024_total": round(n_sec / total_sec_2024 * 100, 2),
            "ln_2024": ln_24,
            "pct_ln_panel": round(ln_24 / total_ln_b * 100, 2),
            "pct_ln_2024_total": round(ln_24 / total_ln_2024 * 100, 2),
            "n_municipios_con_presencia": int((sub["edocve"].astype(str) + "_" + sub["municipio"].astype(str)).nunique()),
        }

        # Centroides en escala original y z-score respecto a la media nacional del panel
        for col in FEATURE_COLS:
            val_orig = float(sub[col].mean())
            z_val = (val_orig - nat_means[col]) / nat_stds[col]
            row_p[f"{col}_original"] = round(val_orig, 6)
            row_p[f"{col}_zscore"] = round(z_val, 4)

        # Series anuales 2009-2024 (media simple seccional y media ponderada SV/(SV+NV) del cluster)
        for y in YEARS:
            row_p[f"p_{y}_simple"] = round(float(sub[f"p_{y}"].mean()), 6)
            sv_sum = float(sub[f"sv_{y}"].sum())
            sv_nv_sum = float(sub[f"sv_nv_{y}"].sum())
            row_p[f"p_{y}_ponderada"] = round(sv_sum / sv_nv_sum, 6)

        # Medias presidencial, intermedia, demográficas y ambos cálculos del ratio joven
        row_p["media_presidencial_original"] = round(float(sub["media_presidencial"].mean()), 6)
        row_p["media_intermedia_original"] = round(float(sub["media_intermedia"].mean()), 6)
        row_p["volatilidad_std_original"] = round(float(sub["std_participacion"].mean()), 6)
        row_p["estabilidad_inv_cv_original"] = round(float(sub["estabilidad_inv_cv_raw"].mean()), 4)
        row_p["tasa_joven_18_29_original"] = round(float(sub["tasa_joven_18_29"].mean()), 6)
        row_p["tasa_mayor_60_mas_original"] = round(float(sub["tasa_mayor_60_mas"].mean()), 6)
        row_p["ratio_joven_ratio_de_medias_usado_en_modelo"] = round(float(sub["ratio_participacion_joven"].mean()), 6)
        row_p["ratio_joven_media_de_ratios_anuales"] = round(
            float(sub["ratio_participacion_joven_media_de_ratios"].mean()), 6
        )
        row_p["declaracion_metodo_ratio_joven"] = (
            "En el modelo se utiliza el cociente de medias hexanuales: tasa_joven_18_29 / participacion_media_historica"
        )
        row_p["tasa_mujeres_original"] = round(float(sub["tasa_mujeres"].mean()), 6)
        row_p["tasa_hombres_original"] = round(float(sub["tasa_hombres"].mean()), 6)

        # Composición Urbana / Rural / Mixta e indígena/afromexicana
        row_p["pct_secciones_urbanas"] = round(u_sec_pct, 2)
        row_p["pct_secciones_rurales"] = round(r_sec_pct, 2)
        row_p["pct_secciones_mixtas"] = round(m_sec_pct, 2)
        row_p["pct_ln_urbana"] = round(u_ln_pct, 2)
        row_p["pct_ln_rural"] = round(r_ln_pct, 2)
        row_p["pct_ln_mixta"] = round(m_ln_pct, 2)
        row_p["pct_secciones_indigenas_afromexicanas"] = (
            "[PENDIENTE: cálculo, datos necesarios — los CSV de datos abiertos del CCPC 2009-2024 no incluyen el "
            "indicador de sección indígena/afromexicana; dicho atributo sólo existe en el tablero web Tableau del INE]"
        )
        row_p["top5_entidades_por_pct_secciones"] = top5_sec_str
        row_p["top5_entidades_por_pct_ln_2024"] = top5_ln_str
        row_p["top5_entidades_por_especializacion_estatal"] = top5_spec_str

        perfiles_rows.append(row_p)

        estrategias_rows.append({
            "cluster_id": c,
            "codigo_cluster": meta["codigo"],
            "nombre_perfil": meta["nombre"],
            "n_secciones": n_sec,
            "pct_secciones_panel": round(n_sec / total_sec_b * 100, 2),
            "ln_2024": ln_24,
            "pct_ln_panel": round(ln_24 / total_ln_b * 100, 2),
            "variables_rectoras_z": meta["variables_rectoras_z"],
            "linea_base_intermedia_2021_pond_pct": round(float(sub["sv_2021"].sum() / sub["sv_nv_2021"].sum() * 100), 1),
            "linea_base_presidencial_2024_pond_pct": round(float(sub["sv_2024"].sum() / sub["sv_nv_2024"].sum() * 100), 1),
            "hipotesis_factor_abstencionismo": meta["hipotesis_abstencionismo"],
            "objetivo_especifico": meta["objetivo_especifico"],
            "canal_principal": meta["canal_principal"],
            "narrativa_mensaje_neutral": meta["narrativa_mensaje"],
            "accion_operativa_ine": meta["accion_operativa_ine"],
            "unidad_responsable": meta["unidad_responsable"],
            "costo_estimado_orden_magnitud": meta["costo_estimado_orden_magnitud"],
            "meta_cuantitativa": meta["meta_cuantitativa"],
            "indicador_seguimiento": meta["indicador_seguimiento"],
            "horizonte_temporal": meta["horizonte_temporal"],
            "lema_sugerido_neutral": meta["lema_neutral"],
        })

    df_perfiles = pd.DataFrame(perfiles_rows)
    df_estrategias = pd.DataFrame(estrategias_rows)

    df_perfiles.to_csv(OUT_FASE3 / "perfiles.csv", index=False)
    df_estrategias.to_csv(OUT_FASE3 / "estrategias.csv", index=False)
    return df_perfiles, df_estrategias


def compare_k4_k5_k6(df_b: pd.DataFrame) -> pd.DataFrame:
    """
    Compara la estructura de perfiles para k=4, k=5 y k=6 sobre el Panel Principal (N=53,644)
    y documenta por qué k=4 es la partición óptima dentro del rango 4-6 de la convocatoria.
    """
    nat_means = {col: float(df_b[col].mean()) for col in FEATURE_COLS}
    nat_stds = {col: float(df_b[col].std(ddof=1)) for col in FEATURE_COLS}

    rows = []
    for k, col_k in [(4, "cluster_k4"), (5, "cluster_k5"), (6, "cluster_k6")]:
        for c in range(k):
            sub = df_b[df_b[col_k] == c]
            row = {
                "k": k,
                "cluster_id": c,
                "n_secciones": len(sub),
                "pct_secciones": round(len(sub) / len(df_b) * 100, 2),
                "ln_2024": int(sub["ln_2024"].sum()),
                "pct_ln_2024": round(sub["ln_2024"].sum() / df_b["ln_2024"].sum() * 100, 2),
                "pct_urbana": round(float((sub["tipo_2024"] == "U").mean() * 100), 2),
                "pct_rural": round(float((sub["tipo_2024"] == "R").mean() * 100), 2),
                "pct_mixta": round(float((sub["tipo_2024"] == "M").mean() * 100), 2),
            }
            z_summary = []
            for fcol in FEATURE_COLS:
                val = float(sub[fcol].mean())
                z = (val - nat_means[fcol]) / nat_stds[fcol]
                row[f"{fcol}_orig"] = round(val, 4)
                row[f"{fcol}_z"] = round(z, 2)
                if abs(z) >= 0.5:
                    z_summary.append(f"{fcol}({z:+.2f})")
            row["n_variables_con_abs_z_ge_05"] = len(z_summary)
            row["variables_con_abs_z_ge_05"] = ", ".join(z_summary)
            rows.append(row)

    df_comp = pd.DataFrame(rows)
    df_comp.to_csv(OUT_FASE3 / "comparacion_k4_k5_k6.csv", index=False)

    md_lines = [
        "# Justificación de la Elección de $k=4$ dentro del Rango de la Convocatoria (4 a 6 Perfiles)",
        "",
        "## 1. Métricas de Validación Interna y Estabilidad Bootstrap (100 réplicas al 80%)",
        "",
        "- **$k=3$ (fuera del rango 4–6 de la convocatoria)**: Silhouette = `0.2099`, Davies-Bouldin = `1.4875`, Calinski-Harabasz = `16,402.41`, ARI Bootstrap = `0.9734 ± 0.0258` (IC 95%: `[0.9163, 0.9927]`). Aunque obtiene las mejores métricas internas al agregar el espacio en tres macro-estratos, queda fuera del rango de 4 a 6 perfiles requerido por la convocatoria.",
        "- **$k=4$ (seleccionado)**: Silhouette = `0.1789`, Davies-Bouldin = `1.5380`, Calinski-Harabasz = `14,435.43`, ARI Bootstrap = `0.9572 ± 0.0253` (IC 95%: `[0.9091, 0.9915]`).",
        "- **$k=5$ (dominado)**: Silhouette = `0.1625`, Davies-Bouldin = `1.6109`, Calinski-Harabasz = `12,676.61`, ARI Bootstrap = `0.9327 ± 0.0330` (IC 95%: `[0.8728, 0.9854]`).",
        "- **$k=6$**: Silhouette = `0.1639`, Davies-Bouldin = `1.5709`, Calinski-Harabasz = `11,550.69`, ARI Bootstrap = `0.9675 ± 0.0162` (IC 95%: `[0.9375, 0.9887]`).",
        "",
        "## 2. Criterios de Selección de $k=4$",
        "",
        "1. **Dominancia empírica en el rango 4–6:** Dentro del intervalo de 4 a 6 perfiles establecido por la convocatoria, **$k=4$ obtiene el mejor Silhouette (`0.1789`), el menor índice Davies-Bouldin (`1.5380`) y el mayor Calinski-Harabasz (`14,435.43`)**, superando a $k=5$ en las cuatro métricas y a $k=6$ en las tres métricas de separación y compacidad interna.",
        "2. **Estabilidad bootstrap estadísticamente indistinguible del máximo:** La estabilidad por remuestreo de $k=4$ (`ARI = 0.9572`, IC 95% `[0.9091, 0.9915]`) es comparable a la de $k=6$ (`ARI = 0.9675`, IC 95% `[0.9375, 0.9887]`), cuyos intervalos de confianza al 95% se traslapan ampliamente.",
        "3. **Diferenciación sustantiva completa frente a $k=6$:** En $k=4$, los cuatro perfiles cuentan con al menos **5 variables rectoras con $|z| \\ge 0.50$**. En contraste, $k=6$ produce un grupo sin diferenciación clara (`C1` en $k=6$, con `17.77%` del panel), el cual presenta una sola variable con $|z| \\ge 0.50$ (`tendencia_participacion_beta` con $z=-0.51$) y valores cercanos al promedio nacional en las seis dimensiones restantes ($|z| \\le 0.43$).",
        "4. **Utilidad de $k=6$ como sub-segmentación auxiliar:** Con $k=6$, el perfil de baja participación (`C0` en $k=4$) se divide en un subgrupo de rezago juvenil y otro de ciclo presidencial urbano, distinción útil cuando se requiere focalización territorial fina a nivel subdistrital.",
    ]
    (OUT_FASE3 / "comparacion_k4_k5_k6.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return df_comp


def build_panel_b_summary(df_b: pd.DataFrame, df_perfiles: pd.DataFrame) -> dict:
    """Calcula el resumen exacto del Panel Principal Opción B (N=53,644) para tablas y documento."""
    ln_24 = int(df_b["ln_2024"].sum())
    u_1d_sec = round(float((df_perfiles["pct_secciones_urbanas"].round(1) * df_perfiles["n_secciones"]).sum() / len(df_b)), 1)
    r_1d_sec = round(float((df_perfiles["pct_secciones_rurales"].round(1) * df_perfiles["n_secciones"]).sum() / len(df_b)), 1)
    m_1d_sec = round(float((df_perfiles["pct_secciones_mixtas"].round(1) * df_perfiles["n_secciones"]).sum() / len(df_b)), 1)
    u_1d_ln_cl = round(float((df_perfiles["pct_secciones_urbanas"].round(1) * df_perfiles["ln_2024"]).sum() / ln_24), 1)
    r_1d_ln_cl = round(float((df_perfiles["pct_secciones_rurales"].round(1) * df_perfiles["ln_2024"]).sum() / ln_24), 1)
    m_1d_ln_cl = round(float((df_perfiles["pct_secciones_mixtas"].round(1) * df_perfiles["ln_2024"]).sum() / ln_24), 1)
    summary = {
        "n_secciones": int(len(df_b)),
        "ln_2024": ln_24,
        "pct_secciones_urbanas": round(float((df_b["tipo_2024"] == "U").mean() * 100), 2),
        "pct_secciones_rurales": round(float((df_b["tipo_2024"] == "R").mean() * 100), 2),
        "pct_secciones_mixtas": round(float((df_b["tipo_2024"] == "M").mean() * 100), 2),
        "pct_secciones_urbanas_1d": u_1d_sec,
        "pct_secciones_rurales_1d": r_1d_sec,
        "pct_secciones_mixtas_1d": m_1d_sec,
        "pct_secciones_urbanas_pond_ln_clusters_1d": u_1d_ln_cl,
        "pct_secciones_rurales_pond_ln_clusters_1d": r_1d_ln_cl,
        "pct_secciones_mixtas_pond_ln_clusters_1d": m_1d_ln_cl,
        "pct_ln_urbana": round(float(df_b.loc[df_b["tipo_2024"] == "U", "ln_2024"].sum() / ln_24 * 100), 2),
        "pct_ln_rural": round(float(df_b.loc[df_b["tipo_2024"] == "R", "ln_2024"].sum() / ln_24 * 100), 2),
        "pct_ln_mixta": round(float(df_b.loc[df_b["tipo_2024"] == "M", "ln_2024"].sum() / ln_24 * 100), 2),
        "media_presidencial_original": round(float(df_b["media_presidencial"].mean()), 6),
        "media_intermedia_original": round(float(df_b["media_intermedia"].mean()), 6),
        "volatilidad_std_original": round(float(df_b["std_participacion"].mean()), 6),
        "estabilidad_inv_cv_original": round(float(df_b["estabilidad_inv_cv_raw"].mean()), 4),
        "tasa_joven_18_29_original": round(float(df_b["tasa_joven_18_29"].mean()), 6),
        "tasa_mayor_60_mas_original": round(float(df_b["tasa_mayor_60_mas"].mean()), 6),
        "tasa_mujeres_original": round(float(df_b["tasa_mujeres"].mean()), 6),
        "tasa_hombres_original": round(float(df_b["tasa_hombres"].mean()), 6),
        "ratio_joven_ratio_de_medias_usado_en_modelo": round(float(df_b["ratio_participacion_joven"].mean()), 6),
        "ratio_joven_media_de_ratios_anuales": round(float(df_b["ratio_participacion_joven_media_de_ratios"].mean()), 6),
    }
    for col in FEATURE_COLS:
        summary[f"{col}_media"] = round(float(df_b[col].mean()), 6)
        summary[f"{col}_std"] = round(float(df_b[col].std(ddof=1)), 6)
        summary[f"{col}_mediana"] = round(float(df_b[col].median()), 6)
        summary[f"{col}_iqr"] = round(float(df_b[col].quantile(0.75) - df_b[col].quantile(0.25)), 6)
    for y in YEARS:
        summary[f"p_{y}_simple"] = round(float(df_b[f"p_{y}"].mean()), 6)
        summary[f"p_{y}_ponderada"] = round(float(df_b[f"sv_{y}"].sum() / df_b[f"sv_nv_{y}"].sum()), 6)
    return summary


def export_metricas_finales_json(
    df_b: pd.DataFrame,
    df_univ: pd.DataFrame,
    df_perfiles: pd.DataFrame,
    df_estrategias: pd.DataFrame,
    df_comp: pd.DataFrame,
) -> tuple[Path, str]:
    """Exporta outputs/metricas_finales.json como fuente única de verdad y devuelve su hash SHA-256."""
    out_fase1 = PROJECT_ROOT / "outputs" / "fase1"
    metricas_path = PROJECT_ROOT / "outputs" / "metricas_finales.json"

    payload = {
        "k_seleccionado": 4,
        "entorno_software": {
            "python": "3.14.6",
            "duckdb": "2.0.0",
            "scikit_learn": "1.9.0",
            "scipy": "1.18.0",
            "umap_learn": "0.5.12",
            "pandas": "3.0.3",
            "numpy": "2.4.6",
            "reportlab": "5.1.0",
            "matplotlib": "3.11.0",
            "seaborn": "0.13.2",
            "statsmodels": "0.14.6",
            "pyarrow": "23.0.1",
            "jinja2": "3.1.6",
            "pytest": "9.0.3",
        },
        "universo_y_cobertura": {
            "winsor_p_min": 1,
            "winsor_p_max": 99,
            "secciones_union_historica_2009_2024": 72681,
            "secciones_2024_total": 70751,
            "secciones_continuas_2009_2024": 62048,
            "secciones_2024_creadas_post2009": 8703,
            "secciones_2009_2021_baja_antes_2024": 1930,
            "secciones_captura_valida_sv_nv_ge_50": 54804,
            "secciones_excluidas_sv_nv_lt_50": 7244,
            "secciones_excluidas_sv_nv_eq_0": 7156,
            "secciones_excluidas_sv_nv_1_a_49": 88,
            "secciones_salto_abrupto_ln_en_62048": 1311,
            "secciones_salto_abrupto_ln_en_54804": 1159,
            "secciones_sin_saltos_ln": 53645,
            "secciones_excluidas_sin_grupo_etario_60mas": 1,
            "secciones_excluidas_totales_en_2024_vs_panel_b": 17107,
            "secciones_continuas_excluidas_por_calidad": 8404,
            "panel_principal_secciones": int(len(df_b)),
            "panel_principal_pct_secciones_2024": round(len(df_b) / 70751 * 100, 2),
            "panel_principal_pct_secciones_continuas": round(len(df_b) / 62048 * 100, 2),
            "panel_principal_ln_2024": int(df_b["ln_2024"].sum()),
            "ln_2024_total_csv": 98330348,
            "ln_2024_oficial_ine": 98329591,
            "ln_2024_panel_continuo_62048": 85936860,
            "panel_principal_pct_ln_2024": round(df_b["ln_2024"].sum() / 98330348 * 100, 2),
            "panel_principal_municipios": int((df_b["edocve"].astype(str) + "_" + df_b["municipio"].astype(str)).nunique()),
            "municipios_2024_total": 2475,
            "municipios_panel_continuo_62048": 2473,
            "municipios_historicos_union": 2477,
            "cascada_filtrado": df_univ.to_dict(orient="records"),
        },
        "resumen_panel_b": build_panel_b_summary(df_b, df_perfiles),
        "medias_nacionales_panel_principal": {
            col: {
                "media": round(float(df_b[col].mean()), 6),
                "std": round(float(df_b[col].std(ddof=1)), 6),
                "mediana": round(float(df_b[col].median()), 6),
                "iqr": round(float(df_b[col].quantile(0.75) - df_b[col].quantile(0.25)), 6),
            }
            for col in FEATURE_COLS
        },
        "serie_nacional_2009_2024": pd.read_csv(out_fase1 / "serie_nacional.csv").to_dict(orient="records"),
        "incluidas_vs_excluidas_2024": pd.read_csv(out_fase1 / "incluidas_vs_excluidas.csv").to_dict(orient="records"),
        "estabilidad_comparacion": pd.read_csv(OUT_FASE2 / "estabilidad_comparacion.csv").to_dict(orient="records"),
        "vif_colinealidad": pd.read_csv(OUT_FASE2 / "vif_colinealidad.csv").to_dict(orient="records"),
        "ventanas_temporales": pd.read_csv(OUT_FASE2 / "ventanas_temporales.csv").to_dict(orient="records"),
        "benchmark_modelos": pd.read_csv(OUT_FASE2 / "benchmark.csv").to_dict(orient="records"),
        "sensibilidad_opcion_a": pd.read_csv(OUT_FASE2 / "sensibilidad_opcion_a.csv").to_dict(orient="records"),
        "transicion_clusters": pd.read_csv(OUT_FASE2 / "transicion_clusters.csv").to_dict(orient="records"),
        "interpretabilidad_rf_anova": pd.read_csv(OUT_FASE2 / "interpretabilidad_rf_anova.csv").to_dict(orient="records"),
        "proyecciones_pca": json.loads((OUT_FASE2 / "resumen_fase2.json").read_text(encoding="utf-8")),
        "perfiles": df_perfiles.to_dict(orient="records"),
        "estrategias": df_estrategias.to_dict(orient="records"),
        "comparacion_k4_k5_k6": df_comp.to_dict(orient="records"),
    }

    metricas_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    sha_m = hashlib.sha256(metricas_path.read_bytes()).hexdigest()
    return metricas_path, sha_m


def main() -> None:
    df_b = pd.read_parquet(OUT_FASE2 / "etiquetas_finales.parquet")
    df_univ = pd.read_csv(OUT_FASE2 / "universo_filtrado.csv")

    df_perfiles, df_estrategias = build_perfiles_and_estrategias(df_b, df_univ)
    df_comp = compare_k4_k5_k6(df_b)
    _, sha_metricas = export_metricas_finales_json(df_b, df_univ, df_perfiles, df_estrategias, df_comp)

    sha_perf = hashlib.sha256((OUT_FASE3 / "perfiles.csv").read_bytes()).hexdigest()
    sha_estr = hashlib.sha256((OUT_FASE3 / "estrategias.csv").read_bytes()).hexdigest()
    resumen = {
        "k_seleccionado": 4,
        "sha256_perfiles_csv": sha_perf,
        "sha256_estrategias_csv": sha_estr,
        "sha256_metricas_finales_json": sha_metricas,
        "n_perfiles": len(df_perfiles),
        "n_secciones_panel": len(df_b),
    }
    with open(OUT_FASE3 / "resumen_fase3.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    print(f"[Fase 3] Completado (k=4). SHA256(perfiles.csv) = {sha_perf}")
    print(f"[Fase 3] SHA256(metricas_finales.json) = {sha_metricas}")


if __name__ == "__main__":
    main()
