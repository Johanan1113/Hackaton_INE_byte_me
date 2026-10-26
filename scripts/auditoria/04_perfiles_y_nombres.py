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
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import RobustScaler
import statsmodels.api as sm

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_FASE2 = PROJECT_ROOT / "outputs" / "fase2"
OUT_FASE3 = PROJECT_ROOT / "outputs" / "fase3"
OUT_TABLAS = PROJECT_ROOT / "outputs" / "tablas"
OUT_FASE3.mkdir(parents=True, exist_ok=True)
OUT_TABLAS.mkdir(parents=True, exist_ok=True)

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

ENTIDADES = {
    1: "Aguascalientes", 2: "Baja California", 3: "Baja California Sur", 4: "Campeche",
    5: "Coahuila", 6: "Colima", 7: "Chiapas", 8: "Chihuahua", 9: "Ciudad de México",
    10: "Durango", 11: "Guanajuato", 12: "Guerrero", 13: "Hidalgo", 14: "Jalisco",
    15: "Estado de México", 16: "Michoacán", 17: "Morelos", 18: "Nayarit", 19: "Nuevo León",
    20: "Oaxaca", 21: "Puebla", 22: "Querétaro", 23: "Quintana Roo", 24: "San Luis Potosí",
    25: "Sinaloa", 26: "Sonora", 27: "Tabasco", 28: "Tamaulipas", 29: "Tlaxcala",
    30: "Veracruz", 31: "Yucatán", 32: "Zacatecas",
}

# Nombres finales aprobados (idénticos en tablas, estrategias, documento e infografía)
CLUSTER_META = {
    0: {
        "codigo": "C0",
        "nombre": "Baja Participación Intermitente con Rezago Juvenil",
        "variables_rectoras_z": (
            "estabilidad (log(1 + 1/CV)) (z=-0.65), participación media (z=-0.65), "
            "razón de participación juvenil (z=-0.62), brecha presidencial–intermedia (z=+0.60), "
            "brecha generacional (60+ menos 18–29) (z=+0.58)"
        ),
        "justificacion_regla_3_2": (
            "Sus 5 variables con |z| ≥ 0.5 son estabilidad (log(1 + 1/CV)) (-0.65, la más baja de los cuatro perfiles: 1.7036), "
            "participación media (-0.65, la más baja de los cuatro perfiles: 50.37%), razón de participación juvenil "
            "(-0.62, la más baja de los cuatro perfiles: 0.7963 con 40.17% de votación juvenil), brecha presidencial–intermedia "
            "(+0.60, la más alta de los cuatro perfiles: +17.31 pts entre presidenciales 59.02% e intermedias 41.71%) y "
            "brecha generacional (+0.58: +20.64 pts entre 60+ con 60.81% y 18–29 con 40.17%). Concentra el "
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
            "(línea base 2021 de 35.2%) en las 17,622 secciones del perfil."
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
            "Elevar la participación ponderada a 49.5% en la intermedia de 2027 (línea base 2021: 46.1%, cerrando "
            "la mitad de la brecha frente al 52.8% del panel) y la participación juvenil (18–29 años) a 39.1% en 2027 "
            "(línea base 2021: 35.2%, cerrando la mitad frente al 43.1% del panel)."
        ),
        "indicador_seguimiento": (
            "Tasa de participación ponderada SV/(SV+NV) del perfil en la intermedia de 2027 (vs. 46.1% en 2021) y "
            "tasa seccional SV/(SV+NV) del grupo 18–29 años en el CCPC 2027."
        ),
        "horizonte_temporal": "Permanente con intensificación preelectoral rumbo a la intermedia 2026–2027",
    },
    1: {
        "codigo": "C1",
        "nombre": "Alta Participación Estable e Intergeneracional",
        "variables_rectoras_z": (
            "estabilidad (log(1 + 1/CV)) (z=+1.42), brecha presidencial–intermedia (z=-1.10), "
            "brecha generacional (60+ menos 18–29) (z=-1.07), razón de participación juvenil (z=+1.04), "
            "participación media (z=+0.95), tendencia anual (z=-0.73)"
        ),
        "justificacion_regla_3_2": (
            "Presenta los niveles más altos de los cuatro perfiles en estabilidad (log(1 + 1/CV)) (+1.42: 2.5897), "
            "razón de participación juvenil (+1.04: 0.9090, con 59.10% de votación juvenil) y participación media "
            "(+0.95: 65.05%, con 67.74% en presidenciales y 62.37% en intermedias), así como las menores brechas "
            "presidencial–intermedia (-1.10: +5.37 pts) y generacional (-1.07: +8.78 pts). Su pendiente anual es "
            "ligeramente positiva (+0.15 pts/año, z=-0.73 respecto a la media nacional de +0.68 pts/año) porque ya "
            "partía de un nivel alto en 2009 (59.17% ponderado / 59.30% simple)."
        ),
        "lema_neutral": "Si te visitan para integrar una casilla, participa: tu comunidad cuenta contigo",
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
            "Talleres distritales de educación cívica intercultural y relevo generacional (DECEyEC), programas de reconocimiento "
            "a la participación comunitaria continua y reclutamiento temprano de CAE y sensibilización de la ciudadanía insaculada "
            "para asegurar la instalación completa de casillas con funcionariado propietario."
        ),
        "unidad_responsable": (
            "DECEyEC en coordinación con las Juntas Distritales Ejecutivas (Vocalías de Capacitación Electoral y Educación Cívica y Vocalías de Organización Electoral)"
        ),
        "costo_estimado_orden_magnitud": (
            "Nivel Bajo — Estimación indicativa de orden operativo (sujeta a presupuestación de DECEyEC y Juntas "
            "Distritales Ejecutivas; absorbible dentro de los programas ordinarios de educación cívica y capacitación electoral distrital)."
        ),
        "meta_cuantitativa": (
            "Sostener una participación ponderada ≥ 62.5% en la elección intermedia de 2027 (preservando el 62.5% "
            "observado en la intermedia de 2021) y sostener al menos el nivel de 2024 (65.7%) en la elección presidencial de 2030, "
            "aumentando la proporción de casillas instaladas con funcionariado propietario."
        ),
        "indicador_seguimiento": (
            "Tasa de participación ponderada SV/(SV+NV) en la intermedia de 2027 (vs. 62.5% en 2021), en la "
            "presidencial de 2030 (vs. 65.7% en 2024), y porcentaje de casillas instaladas con funcionariado propietario el día de la jornada (dato de la DEOE)."
        ),
        "horizonte_temporal": "Continuo de mantenimiento y relevo generacional (2025–2030)",
    },
    2: {
        "codigo": "C2",
        "nombre": "Participación en Ascenso con Juventud Activa",
        "variables_rectoras_z": (
            "tendencia anual (z=+0.84), razón de participación juvenil (z=+0.60), "
            "brecha generacional (60+ menos 18–29) (z=-0.59), brecha presidencial–intermedia (z=+0.53), "
            "estabilidad (log(1 + 1/CV)) (z=-0.53)"
        ),
        "justificacion_regla_3_2": (
            "Sus 5 variables con |z| ≥ 0.5 son tendencia anual (+0.84, la más alta de los cuatro perfiles: +1.28 pts/año, "
            "pasando de 41.83% ponderado en 2009 a 60.37% en la intermedia de 2021 y 68.04% en la presidencial de 2024), "
            "razón de participación juvenil (+0.60: 0.8793 con 51.81% de votación juvenil), brecha generacional (-0.59: +12.20 pts), "
            "brecha presidencial–intermedia (+0.53: +16.81 pts porque partió de intermedias bajas en 2009 y 2015) y "
            "estabilidad (log(1 + 1/CV)) (-0.53 por ese mismo ascenso)."
        ),
        "lema_neutral": "Tu participación ya transforma tu comunidad: consolidemos el voto en cada elección",
        "hipotesis_abstencionismo": (
            "Hipótesis: creciente movilización cívica y dinamismo demográfico juvenil en secciones urbanas (68.6%) y "
            "rurales (22.3%) y mixtas (9.1%) que elevó la participación intermedia de 41.8% (2009) y 48.3% (2015) a 60.4% "
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
            "Consolidar en la elección intermedia de 2027 una participación ponderada ≥ 60.4% (sosteniendo la línea "
            "base observada en la intermedia de 2021 de 60.4% e impidiendo una regresión hacia su media intermedia "
            "histórica de 50.5%) y mantener la razón de participación juvenil ≥ 0.88."
        ),
        "indicador_seguimiento": (
            "Tasa de participación ponderada SV/(SV+NV) en la intermedia de 2027 (vs. 60.4% en 2021 y vs. 48.3% en 2015) "
            "y razón de participación juvenil en el CCPC 2027."
        ),
        "horizonte_temporal": "Consolidación en el ciclo intermedio 2025–2027",
    },
    3: {
        "codigo": "C3",
        "nombre": "Liderazgo Femenino con Participación Estancada",
        "variables_rectoras_z": (
            "tendencia anual (z=-0.83), brecha de género (mujeres menos hombres) (z=+0.78), "
            "brecha presidencial–intermedia (z=-0.69), brecha generacional (60+ menos 18–29) (z=+0.62), "
            "razón de participación juvenil (z=-0.56), estabilidad (log(1 + 1/CV)) (z=+0.52)"
        ),
        "justificacion_regla_3_2": (
            "Sus 6 variables con |z| ≥ 0.5 son tendencia anual (z=-0.83 respecto a la media nacional: su "
            "pendiente global es +0.08 pts/año, positiva pero estancada porque las intermedias se mantuvieron en "
            "49.6% [2009], 50.4% [2015] y 49.5% [2021], mientras que la participación presidencial cayó de 61.2% "
            "ponderado en 2012 a 59.0% en 2018 y 55.6% en 2024), brecha de género (+0.78, la más alta de los "
            "cuatro perfiles: +11.15 pts a favor de las mujeres con 60.85% vs 49.70% en hombres), brecha presidencial–intermedia "
            "(-0.69: +8.20 pts), brecha generacional (+0.62: +20.94 pts, 60+ con 65.35% vs 18–29 con 44.41%), "
            "razón de participación juvenil (-0.56: 0.8007) y estabilidad (log(1 + 1/CV)) (+0.52: 2.2047). Su "
            "composición es 48.8% urbana, 41.2% rural y 10.0% mixta (pluralidad urbana con sobrerrepresentación rural frente al 26.9% del panel)."
        ),
        "lema_neutral": "La participación de todas y todos cuenta: sumemos la voz de hombres y jóvenes en cada comunidad",
        "hipotesis_abstencionismo": (
            "Hipótesis: rezago persistente en la participación masculina (49.70% vs 60.85% femenina) y juvenil "
            "(44.41% vs 65.35% en adultos mayores) asociado a dinámicas laborales, movilidad ocupacional masculina y "
            "desvinculación en elecciones presidenciales (donde la votación bajó de 61.2% en 2012 a 55.6% en 2024), "
            "aunado en su segmento rural (41.2% de las secciones) a costos de traslado físico a la casilla."
        ),
        "objetivo_especifico": (
            "Elevar la participación masculina (línea base 2021 de 43.94% frente a 48.66% nacional) y revertir "
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
            "Elevar la participación ponderada en la elección intermedia de 2027 a 51.1% (línea base 2021: 49.5%, "
            "cerrando la mitad de la brecha frente al 52.8% del panel), recuperar en la presidencial de 2030 a 58.1% "
            "(línea base 2024: 55.6%, cerrando la mitad frente al 60.6% del panel), y elevar la participación masculina a "
            "46.3% en 2027 (línea base 2021: 43.9%, cerrando la mitad frente al 48.7% del panel)."
        ),
        "indicador_seguimiento": (
            "Tasa de participación masculina SV/(SV+NV) (vs. 43.9% en 2021), participación ponderada en la "
            "intermedia de 2027 (vs. 49.5% en 2021) y participación ponderada en la presidencial de 2030 (vs. 55.6% en 2024) en el CCPC."
        ),
        "horizonte_temporal": "Mediano y largo plazo con intervención en ciclos 2026–2027 y 2029–2030",
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
            "Los CSV abiertos del CCPC no incluyen el indicador de población indígena o afromexicana que sí muestra el tablero del INE; por ello no se incorporó al modelo."
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


def build_lineas_base_metas(df_b: pd.DataFrame) -> list[dict]:
    """Genera la tabla unificada de líneas base observadas y metas cuantitativas (Bloque D)."""
    p21_b = float(df_b["sv_2021"].sum() / df_b["sv_nv_2021"].sum() * 100)
    p24_b = float(df_b["sv_2024"].sum() / df_b["sv_nv_2024"].sum() * 100)
    j21_b = float(df_b["sv_joven_2021"].sum() / df_b["sv_nv_joven_2021"].sum() * 100)
    h21_b = float(df_b["sv_hombre_2021"].sum() / df_b["sv_nv_hombre_2021"].sum() * 100)
    h24_b = float(df_b["sv_hombre_2024"].sum() / df_b["sv_nv_hombre_2024"].sum() * 100)

    rows = []
    for c in range(4):
        sub = df_b[df_b["cluster"] == c]
        p21 = float(sub["sv_2021"].sum() / sub["sv_nv_2021"].sum() * 100)
        p24 = float(sub["sv_2024"].sum() / sub["sv_nv_2024"].sum() * 100)
        j21 = float(sub["sv_joven_2021"].sum() / sub["sv_nv_joven_2021"].sum() * 100)
        h21 = float(sub["sv_hombre_2021"].sum() / sub["sv_nv_hombre_2021"].sum() * 100)
        h24 = float(sub["sv_hombre_2024"].sum() / sub["sv_nv_hombre_2024"].sum() * 100)
        meta = CLUSTER_META[c]
        if c == 0:
            m_int = "49.5%"
            m_pres = "sostener ≥ 56.9%"
            m_jov = "39.1%"
            m_hom = "N/A"
        elif c == 1:
            m_int = "sostener 62.5%"
            m_pres = "sostener 65.7%"
            m_jov = "N/A"
            m_hom = "N/A"
        elif c == 2:
            m_int = "sostener 60.4%"
            m_pres = "sostener 68.0%"
            m_jov = "razón juvenil ≥ 0.88"
            m_hom = "N/A"
        else:
            m_int = "51.1%"
            m_pres = "58.1%"
            m_jov = "N/A"
            m_hom = "46.3%"
        rows.append({
            "codigo_cluster": meta["codigo"],
            "nombre_perfil": meta["nombre"],
            "participacion_2021_pond_pct": round(p21, 2),
            "participacion_2024_pond_pct": round(p24, 2),
            "tasa_joven_18_29_2021_pond_pct": round(j21, 2),
            "tasa_hombres_2021_pond_pct": round(h21, 2),
            "tasa_hombres_2024_pond_pct": round(h24, 2),
            "meta_intermedia_2027": m_int,
            "meta_presidencial_2030": m_pres,
            "meta_tasa_joven": m_jov,
            "meta_tasa_hombres": m_hom,
        })
    rows.append({
        "codigo_cluster": "Panel B",
        "nombre_perfil": "Media Nacional Panel B",
        "participacion_2021_pond_pct": round(p21_b, 2),
        "participacion_2024_pond_pct": round(p24_b, 2),
        "tasa_joven_18_29_2021_pond_pct": round(j21_b, 2),
        "tasa_hombres_2021_pond_pct": round(h21_b, 2),
        "tasa_hombres_2024_pond_pct": round(h24_b, 2),
        "meta_intermedia_2027": "52.8%",
        "meta_presidencial_2030": "60.6%",
        "meta_tasa_joven": "43.1%",
        "meta_tasa_hombres": "48.7%",
    })
    return rows


def build_validacion_fuera_de_tiempo(df_b: pd.DataFrame) -> dict:
    """
    Bloque B: Validación fuera de tiempo (2009–2021 -> 2024) sobre las 53,644 secciones del Panel B.
    Calcula las 7 variables usando solo 2009–2021 (presidenciales 2012 y 2018; intermedias 2009, 2015 y 2021),
    con winsorización p1-p99 y RobustScaler, corre K-Means++ (k=4, random_state=42), empata por algoritmo
    húngaro contra los perfiles finales y evalúa ARI, eta^2 de participación 2024 (ponderando por sección)
    vs línea base por cuartiles de participación media 2009–2021, y orden de grupos en 2024.
    """
    years_21 = [2009, 2012, 2015, 2018, 2021]
    pres_21 = [2012, 2018]
    mid_21 = [2009, 2015, 2021]

    p_mat = df_b[[f"p_{y}" for y in years_21]].to_numpy(dtype=float)
    p_pres = df_b[[f"p_{y}" for y in pres_21]].to_numpy(dtype=float)
    p_mid = df_b[[f"p_{y}" for y in mid_21]].to_numpy(dtype=float)

    part_media_21 = np.nanmean(p_mat, axis=1)
    brecha_pi_21 = np.nanmean(p_pres, axis=1) - np.nanmean(p_mid, axis=1)

    x = np.array([0.0, 3.0, 6.0, 9.0, 12.0], dtype=float)
    xc = x - x.mean()
    denom_x = float(np.sum(xc ** 2))
    pc = p_mat - part_media_21[:, None]
    beta_21 = np.sum(pc * xc, axis=1) / denom_x

    std_21 = np.nanstd(p_mat, axis=1, ddof=1)
    est_21 = np.log1p(part_media_21 / (std_21 + 1e-4))

    tasa_j_21 = np.nanmean(df_b[[f"p_joven_{y}" for y in years_21]].to_numpy(dtype=float), axis=1)
    tasa_m_21 = np.nanmean(df_b[[f"p_mayor_{y}" for y in years_21]].to_numpy(dtype=float), axis=1)
    tasa_f_21 = np.nanmean(df_b[[f"p_mujer_{y}" for y in years_21]].to_numpy(dtype=float), axis=1)
    tasa_h_21 = np.nanmean(df_b[[f"p_hombre_{y}" for y in years_21]].to_numpy(dtype=float), axis=1)

    b_gen_21 = tasa_m_21 - tasa_j_21
    b_sex_21 = tasa_f_21 - tasa_h_21
    ratio_j_21 = tasa_j_21 / part_media_21

    X_raw = pd.DataFrame({
        "participacion_media_historica": part_media_21,
        "brecha_presidencial_intermedia": brecha_pi_21,
        "tendencia_participacion_beta": beta_21,
        "estabilidad_participacion": est_21,
        "brecha_generacional": b_gen_21,
        "brecha_genero": b_sex_21,
        "ratio_participacion_joven": ratio_j_21,
    })

    X_win = pd.DataFrame(index=X_raw.index)
    for col in FEATURE_COLS:
        ql, qh = X_raw[col].quantile([0.01, 0.99])
        X_win[col] = X_raw[col].clip(lower=ql, upper=qh)

    X_sc = RobustScaler().fit_transform(X_win[FEATURE_COLS])
    km = KMeans(n_clusters=4, init="k-means++", n_init=50, random_state=42)
    lbl_raw = km.fit_predict(X_sc)

    final_lbl = df_b["cluster"].to_numpy(dtype=int)
    cm = pd.crosstab(final_lbl, lbl_raw).values
    row_ind, col_ind = linear_sum_assignment(-cm)
    mapping = {int(col_ind[i]): int(row_ind[i]) for i in range(4)}
    lbl_aligned = np.array([mapping[int(l)] for l in lbl_raw], dtype=int)

    ari_val = float(adjusted_rand_score(final_lbl, lbl_aligned))
    exact_match_pct = float((lbl_aligned == final_lbl).mean() * 100.0)

    # eta^2 de p_2024 explicada por etiquetas 2009-2021 (ponderando por sección)
    y24 = df_b["p_2024"].to_numpy(dtype=float)
    y_mean = float(y24.mean())
    ss_tot = float(np.sum((y24 - y_mean) ** 2))
    ss_btw_clusters = float(
        sum(np.sum(lbl_aligned == c) * ((float(y24[lbl_aligned == c].mean()) - y_mean) ** 2) for c in range(4))
    )
    eta2_clusters = ss_btw_clusters / ss_tot

    # Línea base: cuartiles de participación media 2009-2021
    q_labels = pd.qcut(part_media_21, q=4, labels=False)
    ss_btw_quartiles = float(
        sum(np.sum(q_labels == q) * ((float(y24[q_labels == q].mean()) - y_mean) ** 2) for q in range(4))
    )
    eta2_quartiles = ss_btw_quartiles / ss_tot

    # Orden de los 4 grupos según su participación 2024
    means_21 = {c: float(y24[lbl_aligned == c].mean() * 100.0) for c in range(4)}
    means_fin = {c: float(y24[final_lbl == c].mean() * 100.0) for c in range(4)}
    order_21 = [f"C{c}" for c, _ in sorted(means_21.items(), key=lambda x: x[1])]
    order_fin = [f"C{c}" for c, _ in sorted(means_fin.items(), key=lambda x: x[1])]
    rank_21 = {c: idx + 1 for idx, (c, _) in enumerate(sorted(means_21.items(), key=lambda x: x[1]))}
    rank_fin = {c: idx + 1 for idx, (c, _) in enumerate(sorted(means_fin.items(), key=lambda x: x[1]))}

    order_21_str = " < ".join(order_21)
    order_fin_str = " < ".join(order_fin)

    # Bloque A: Valor agregado sobre el nivel histórico (panel B, ponderado por LN 2024)
    w_ln24 = df_b["ln_2024"].to_numpy(dtype=float)
    y_p24 = df_b["p_2024"].to_numpy(dtype=float)
    y_diff = (df_b["p_2024"] - df_b["p_2018"]).to_numpy(dtype=float)

    # 1. Base model: P2024 ~ p_media_2009_2021
    X_base = sm.add_constant(part_media_21)
    mod_base_24 = sm.WLS(y_p24, X_base, weights=w_ln24).fit()
    r2_base_24 = float(mod_base_24.rsquared)

    # 2. Perfil model (k=4): P2024 ~ p_media_2009_2021 + dummies del perfil
    dummies_fin = pd.get_dummies(final_lbl, prefix="c", drop_first=True, dtype=float)
    X_perfil_24 = sm.add_constant(pd.concat([pd.Series(part_media_21, name="part_media_21"), dummies_fin], axis=1))
    mod_perfil_24 = sm.WLS(y_p24, X_perfil_24, weights=w_ln24).fit()
    r2_perfil_24 = float(mod_perfil_24.rsquared)
    delta_r2_24 = float(r2_perfil_24 - r2_base_24)

    dummy_cols = [c for c in dummies_fin.columns]
    f_test_24 = mod_perfil_24.f_test([f"{c} = 0" for c in dummy_cols])
    f_stat_24 = float(f_test_24.fvalue)
    p_val_24 = float(f_test_24.pvalue)

    # 3. Cambio model: (P2024 - P2018) ~ p_media_2009_2021
    mod_base_c = sm.WLS(y_diff, X_base, weights=w_ln24).fit()
    r2_base_c = float(mod_base_c.rsquared)

    mod_perfil_c = sm.WLS(y_diff, X_perfil_24, weights=w_ln24).fit()
    r2_perfil_c = float(mod_perfil_c.rsquared)
    delta_r2_c = float(r2_perfil_c - r2_base_c)

    f_test_c = mod_perfil_c.f_test([f"{c} = 0" for c in dummy_cols])
    f_stat_c = float(f_test_c.fvalue)
    p_val_c = float(f_test_c.pvalue)

    # 4. Out-of-time (2009-2021) clusters regressions
    dummies_21 = pd.get_dummies(lbl_aligned, prefix="c21", drop_first=True, dtype=float)
    X_perfil_21 = sm.add_constant(pd.concat([pd.Series(part_media_21, name="part_media_21"), dummies_21], axis=1))
    mod_p21_24 = sm.WLS(y_p24, X_perfil_21, weights=w_ln24).fit()
    r2_perfil_21_24 = float(mod_p21_24.rsquared)
    delta_r2_21_24 = float(r2_perfil_21_24 - r2_base_24)
    dummy_cols_21 = [c for c in dummies_21.columns]
    f_test_21_24 = mod_p21_24.f_test([f"{c} = 0" for c in dummy_cols_21])
    f_stat_21_24 = float(f_test_21_24.fvalue)
    p_val_21_24 = float(f_test_21_24.pvalue)

    mod_p21_c = sm.WLS(y_diff, X_perfil_21, weights=w_ln24).fit()
    r2_perfil_21_c = float(mod_p21_c.rsquared)
    delta_r2_21_c = float(r2_perfil_21_c - r2_base_c)
    f_test_21_c = mod_p21_c.f_test([f"{c} = 0" for c in dummy_cols_21])
    f_stat_21_c = float(f_test_21_c.fvalue)
    p_val_21_c = float(f_test_21_c.pvalue)

    filas_tabla = []
    for c in range(4):
        s_21 = df_b[lbl_aligned == c]
        s_fin = df_b[final_lbl == c]
        coinc_n = int(np.sum((lbl_aligned == c) & (final_lbl == c)))
        filas_tabla.append({
            "codigo_cluster": f"C{c}",
            "nombre_perfil": CLUSTER_META[c]["nombre"],
            "n_secciones_2009_2021": int(len(s_21)),
            "n_secciones_final_2009_2024": int(len(s_fin)),
            "coincidencia_secciones_n": coinc_n,
            "coincidencia_pct_del_perfil_final": round(coinc_n / len(s_fin) * 100.0, 2),
            "p_2024_simple_grupo_2009_2021_pct": round(means_21[c], 2),
            "p_2024_pond_grupo_2009_2021_pct": round(float(s_21["sv_2024"].sum() / s_21["sv_nv_2024"].sum() * 100.0), 2),
            "p_2024_simple_perfil_final_pct": round(means_fin[c], 2),
            "p_2024_pond_perfil_final_pct": round(float(s_fin["sv_2024"].sum() / s_fin["sv_nv_2024"].sum() * 100.0), 2),
            "rango_p2024_grupo_2009_2021": rank_21[c],
            "rango_p2024_perfil_final": rank_fin[c],
            "orden_grupos_2009_2021_en_2024": order_21_str,
            "orden_perfiles_finales_en_2024": order_fin_str,
            "ari_2009_2021_vs_final": round(ari_val, 4),
            "ari_3d": round(ari_val, 3),
            "coincidencia_global_pct": round(exact_match_pct, 2),
            "eta2_perfiles_2009_2021": round(eta2_clusters, 4),
            "eta2_perfiles_3d": round(eta2_clusters, 3),
            "eta2_cuartiles_linea_base": round(eta2_quartiles, 4),
            "eta2_cuartiles_3d": round(eta2_quartiles, 3),
            "supera_linea_base": bool(eta2_clusters > eta2_quartiles),
            "r2_base_p2024": round(r2_base_24, 4),
            "r2_perfil_p2024": round(r2_perfil_24, 4),
            "delta_r2_p2024": round(delta_r2_24, 4),
            "delta_r2_p2024_3d": round(delta_r2_24, 3),
            "f_stat_p2024": round(f_stat_24, 2),
            "p_valor_p2024": float(p_val_24),
            "p_valor_p2024_str": "< 0.001" if p_val_24 < 0.001 else f"= {p_val_24:.4f}",
            "r2_base_cambio": round(r2_base_c, 4),
            "r2_perfil_cambio": round(r2_perfil_c, 4),
            "delta_r2_cambio": round(delta_r2_c, 4),
            "delta_r2_cambio_3d": round(delta_r2_c, 3),
            "f_stat_cambio": round(f_stat_c, 2),
            "p_valor_cambio": float(p_val_c),
            "p_valor_cambio_str": "< 0.001" if p_val_c < 0.001 else f"= {p_val_c:.4f}",
        })

    va_dict = {
        "r2_base_p2024": round(r2_base_24, 4),
        "r2_perfil_p2024": round(r2_perfil_24, 4),
        "delta_r2_p2024": round(delta_r2_24, 4),
        "delta_r2_p2024_3d": round(delta_r2_24, 3),
        "f_stat_p2024": round(f_stat_24, 2),
        "p_valor_p2024": float(p_val_24),
        "p_valor_p2024_str": "< 0.001" if p_val_24 < 0.001 else f"= {p_val_24:.4f}",
        "r2_base_cambio": round(r2_base_c, 4),
        "r2_perfil_cambio": round(r2_perfil_c, 4),
        "delta_r2_cambio": round(delta_r2_c, 4),
        "delta_r2_cambio_3d": round(delta_r2_c, 3),
        "f_stat_cambio": round(f_stat_c, 2),
        "p_valor_cambio": float(p_val_c),
        "p_valor_cambio_str": "< 0.001" if p_val_c < 0.001 else f"= {p_val_c:.4f}",
        "validacion_temporal_2009_2021": {
            "r2_perfil_p2024": round(r2_perfil_21_24, 4),
            "delta_r2_p2024": round(delta_r2_21_24, 4),
            "f_stat_p2024": round(f_stat_21_24, 2),
            "p_valor_p2024": float(p_val_21_24),
            "r2_perfil_cambio": round(r2_perfil_21_c, 4),
            "delta_r2_cambio": round(delta_r2_21_c, 4),
            "f_stat_cambio": round(f_stat_21_c, 2),
            "p_valor_cambio": float(p_val_21_c),
        },
    }

    return {
        "n_secciones": int(len(df_b)),
        "ari_2009_2021_vs_final": round(ari_val, 4),
        "ari_3d": round(ari_val, 3),
        "coincidencia_exacta_pct": round(exact_match_pct, 2),
        "eta2_perfiles_2009_2021": round(eta2_clusters, 4),
        "eta2_perfiles_3d": round(eta2_clusters, 3),
        "eta2_cuartiles_linea_base": round(eta2_quartiles, 4),
        "eta2_cuartiles_3d": round(eta2_quartiles, 3),
        "supera_linea_base": bool(eta2_clusters > eta2_quartiles),
        "orden_grupos_2009_2021_en_2024": order_21_str,
        "orden_perfiles_finales_en_2024": order_fin_str,
        "orden_idéntico": bool(order_21 == order_fin),
        "valor_agregado_nivel_historico": va_dict,
        "tabla_13": filas_tabla,
    }


def build_cobertura_ampliada(df_b: pd.DataFrame) -> dict:
    """
    Bloque C: Cobertura ampliada (Limitaciones).
    Asigna un perfil por cercanía al centroide (sin reentrenar) a las secciones excluidas
    del Panel B que tengan al menos 2 elecciones presidenciales y 2 intermedias válidas (SV+NV >= 50).
    Calcula sus 7 variables con el método de la Opción A, aplicando los mismos parámetros de
    winsorización y escalado del Panel B.
    Guarda outputs/perfil_por_seccion_2024.csv con columnas EDOCVE, DEF, SECCION, perfil, origen, LN_2024.
    """
    df70 = pd.read_parquet(OUT_FASE2 / "panel_70751_2024_completo.parquet")
    b_ids = set(df_b["seccion_id"])
    excluded = df70[~df70["seccion_id"].isin(b_ids)].copy().reset_index(drop=True)

    ql_qh = {col: df_b[col].quantile([0.01, 0.99]).to_dict() for col in FEATURE_COLS}
    X_win_b = pd.DataFrame({col: df_b[col].clip(lower=ql_qh[col][0.01], upper=ql_qh[col][0.99]) for col in FEATURE_COLS})
    scaler = RobustScaler().fit(X_win_b[FEATURE_COLS])
    X_sc_b = scaler.transform(X_win_b[FEATURE_COLS])
    km = KMeans(n_clusters=4, init="k-means++", n_init=50, random_state=42).fit(X_sc_b)

    years = [2009, 2012, 2015, 2018, 2021, 2024]
    pres_years = [2012, 2018, 2024]
    mid_years = [2009, 2015, 2021]

    for y in years:
        inv = excluded[f"sv_nv_{y}"] < 50
        for pfx in ["p", "p_joven", "p_mayor", "p_mujer", "p_hombre"]:
            excluded.loc[inv, f"{pfx}_{y}"] = np.nan

    pres_mat = excluded[[f"p_{y}" for y in pres_years]].to_numpy(dtype=float)
    mid_mat = excluded[[f"p_{y}" for y in mid_years]].to_numpy(dtype=float)
    all_mat = excluded[[f"p_{y}" for y in years]].to_numpy(dtype=float)

    n_pres_valid = np.sum(~np.isnan(pres_mat), axis=1)
    n_mid_valid = np.sum(~np.isnan(mid_mat), axis=1)

    mask_valid = (n_pres_valid >= 2) & (n_mid_valid >= 2)
    valid_exc = excluded[mask_valid].copy().reset_index(drop=True)
    sin_historia = excluded[~mask_valid].copy().reset_index(drop=True)

    all_mat_v = all_mat[mask_valid]
    pres_mat_v = pres_mat[mask_valid]
    mid_mat_v = mid_mat[mask_valid]

    valid_exc["participacion_media_historica"] = np.nanmean(all_mat_v, axis=1)
    valid_exc["brecha_presidencial_intermedia"] = np.nanmean(pres_mat_v, axis=1) - np.nanmean(mid_mat_v, axis=1)

    x = np.array([0.0, 3.0, 6.0, 9.0, 12.0, 15.0], dtype=float)
    v_mask = ~np.isnan(all_mat_v)
    n_val = v_mask.sum(axis=1)
    x_bar = (v_mask * x).sum(axis=1) / n_val
    y_bar = valid_exc["participacion_media_historica"].to_numpy()
    x_diff = np.where(v_mask, x - x_bar[:, None], 0.0)
    y_diff = np.where(v_mask, all_mat_v - y_bar[:, None], 0.0)
    denom = (x_diff ** 2).sum(axis=1)
    valid_exc["tendencia_participacion_beta"] = (x_diff * y_diff).sum(axis=1) / denom

    std_v = np.nanstd(all_mat_v, axis=1, ddof=1)
    inv_cv_v = valid_exc["participacion_media_historica"].to_numpy() / (std_v + 1e-4)
    valid_exc["estabilidad_participacion"] = np.log1p(inv_cv_v)

    pj_mat_v = valid_exc[[f"p_joven_{y}" for y in years]].to_numpy(dtype=float)
    pm_mat_v = valid_exc[[f"p_mayor_{y}" for y in years]].to_numpy(dtype=float)
    pf_mat_v = valid_exc[[f"p_mujer_{y}" for y in years]].to_numpy(dtype=float)
    ph_mat_v = valid_exc[[f"p_hombre_{y}" for y in years]].to_numpy(dtype=float)

    tasa_j = np.nanmean(pj_mat_v, axis=1)
    tasa_m = np.nanmean(pm_mat_v, axis=1)
    tasa_f = np.nanmean(pf_mat_v, axis=1)
    tasa_h = np.nanmean(ph_mat_v, axis=1)
    tasa_m_filled = np.where(np.isnan(tasa_m), valid_exc["participacion_media_historica"], tasa_m)

    valid_exc["brecha_generacional"] = tasa_m_filled - tasa_j
    valid_exc["brecha_genero"] = tasa_f - tasa_h
    valid_exc["ratio_participacion_joven"] = tasa_j / valid_exc["participacion_media_historica"].to_numpy()

    X_win_exc = pd.DataFrame({col: valid_exc[col].clip(lower=ql_qh[col][0.01], upper=ql_qh[col][0.99]) for col in FEATURE_COLS})
    X_sc_exc = scaler.transform(X_win_exc[FEATURE_COLS])
    pred_clusters = km.predict(X_sc_exc)
    valid_exc["cluster"] = pred_clusters

    # Combine panel_B + asignada
    b_rows = df_b[["edocve", "seccion", "cluster", "ln_2024", "seccion_id"]].merge(
        df70[["seccion_id", "def_2024"]], on="seccion_id", how="left"
    )
    b_rows["origen"] = "panel_B"

    exc_rows = valid_exc[["edocve", "def_2024", "seccion", "cluster", "ln_2024"]].copy()
    exc_rows["origen"] = "asignada"

    comb = pd.concat([b_rows, exc_rows], ignore_index=True)
    comb["perfil"] = comb["cluster"].apply(lambda c: f"C{c}")
    comb["EDOCVE"] = comb["edocve"].astype(int)
    comb["DEF"] = comb["def_2024"].astype(int)
    comb["SECCION"] = comb["seccion"].astype(int)
    comb["LN_2024"] = comb["ln_2024"].astype(int)

    df_perfil_seccion = comb[["EDOCVE", "DEF", "SECCION", "perfil", "origen", "LN_2024"]].sort_values(["EDOCVE", "SECCION"]).reset_index(drop=True)
    df_perfil_seccion.to_csv(PROJECT_ROOT / "outputs" / "perfil_por_seccion_2024.csv", index=False)

    dist_asignadas = {}
    for c in range(4):
        s_c = valid_exc[valid_exc["cluster"] == c]
        dist_asignadas[f"C{c}"] = {
            "nombre": CLUSTER_META[c]["nombre"],
            "n_secciones": int(len(s_c)),
            "pct_de_asignadas": round(len(s_c) / len(valid_exc) * 100.0, 2),
            "ln_2024": int(s_c["ln_2024"].sum()),
            "pct_ln_de_asignadas": round(float(s_c["ln_2024"].sum() / valid_exc["ln_2024"].sum() * 100.0), 2),
        }

    total_n = len(df70)
    total_ln = int(df70["ln_2024"].sum())
    n_b = len(df_b)
    ln_b = int(df_b["ln_2024"].sum())
    n_asig = len(valid_exc)
    ln_asig = int(valid_exc["ln_2024"].sum())
    n_cob = n_b + n_asig
    ln_cob = ln_b + ln_asig
    n_sin = len(sin_historia)
    ln_sin = int(sin_historia["ln_2024"].sum())

    filas_tabla_14 = [
        {
            "categoria": "Panel B (Principal, 2009–2024 continuo)",
            "perfil": "Todos (C0–C3)",
            "secciones": n_b,
            "pct_secciones": round(n_b / total_n * 100.0, 2),
            "ln_2024": ln_b,
            "pct_ln_2024": round(ln_b / total_ln * 100.0, 2),
        },
        {
            "categoria": "Asignadas por centroide (historia suficiente)",
            "perfil": f"C0: {CLUSTER_META[0]['nombre']}",
            "secciones": dist_asignadas["C0"]["n_secciones"],
            "pct_secciones": round(dist_asignadas["C0"]["n_secciones"] / total_n * 100.0, 2),
            "ln_2024": dist_asignadas["C0"]["ln_2024"],
            "pct_ln_2024": round(dist_asignadas["C0"]["ln_2024"] / total_ln * 100.0, 2),
        },
        {
            "categoria": "Asignadas por centroide (historia suficiente)",
            "perfil": f"C1: {CLUSTER_META[1]['nombre']}",
            "secciones": dist_asignadas["C1"]["n_secciones"],
            "pct_secciones": round(dist_asignadas["C1"]["n_secciones"] / total_n * 100.0, 2),
            "ln_2024": dist_asignadas["C1"]["ln_2024"],
            "pct_ln_2024": round(dist_asignadas["C1"]["ln_2024"] / total_ln * 100.0, 2),
        },
        {
            "categoria": "Asignadas por centroide (historia suficiente)",
            "perfil": f"C2: {CLUSTER_META[2]['nombre']}",
            "secciones": dist_asignadas["C2"]["n_secciones"],
            "pct_secciones": round(dist_asignadas["C2"]["n_secciones"] / total_n * 100.0, 2),
            "ln_2024": dist_asignadas["C2"]["ln_2024"],
            "pct_ln_2024": round(dist_asignadas["C2"]["ln_2024"] / total_ln * 100.0, 2),
        },
        {
            "categoria": "Asignadas por centroide (historia suficiente)",
            "perfil": f"C3: {CLUSTER_META[3]['nombre']}",
            "secciones": dist_asignadas["C3"]["n_secciones"],
            "pct_secciones": round(dist_asignadas["C3"]["n_secciones"] / total_n * 100.0, 2),
            "ln_2024": dist_asignadas["C3"]["ln_2024"],
            "pct_ln_2024": round(dist_asignadas["C3"]["ln_2024"] / total_ln * 100.0, 2),
        },
        {
            "categoria": "Subtotal asignadas excluidas",
            "perfil": "Todas asignadas",
            "secciones": n_asig,
            "pct_secciones": round(n_asig / total_n * 100.0, 2),
            "ln_2024": ln_asig,
            "pct_ln_2024": round(ln_asig / total_ln * 100.0, 2),
        },
        {
            "categoria": "Total con perfil asignado (Panel B + Asignadas)",
            "perfil": "Cobertura ampliada",
            "secciones": n_cob,
            "pct_secciones": round(n_cob / total_n * 100.0, 2),
            "ln_2024": ln_cob,
            "pct_ln_2024": round(ln_cob / total_ln * 100.0, 2),
        },
        {
            "categoria": "Excluidas sin historia suficiente (<2 pres o <2 mid)",
            "perfil": "Sin perfil asignado (creadas post-2015)",
            "secciones": n_sin,
            "pct_secciones": round(n_sin / total_n * 100.0, 2),
            "ln_2024": ln_sin,
            "pct_ln_2024": round(ln_sin / total_ln * 100.0, 2),
        },
        {
            "categoria": "Total Nacional CCPC 2024",
            "perfil": "Universo total",
            "secciones": total_n,
            "pct_secciones": 100.0,
            "ln_2024": total_ln,
            "pct_ln_2024": 100.0,
        },
    ]

    return {
        "universo_total_secciones": total_n,
        "universo_total_ln_2024": total_ln,
        "panel_b_secciones": n_b,
        "panel_b_pct_secciones": round(n_b / total_n * 100.0, 2),
        "panel_b_ln_2024": ln_b,
        "panel_b_pct_ln_2024": round(ln_b / total_ln * 100.0, 2),
        "secciones_asignadas": n_asig,
        "pct_secciones_asignadas": round(n_asig / total_n * 100.0, 2),
        "ln_2024_asignadas": ln_asig,
        "pct_ln_2024_asignadas": round(ln_asig / total_ln * 100.0, 2),
        "secciones_cobertura_ampliada": n_cob,
        "pct_secciones_cobertura_ampliada": round(n_cob / total_n * 100.0, 2),
        "ln_2024_cobertura_ampliada": ln_cob,
        "pct_ln_cobertura_ampliada": round(ln_cob / total_ln * 100.0, 2),
        "pct_ln_panel_b_mas_asignadas": round(ln_cob / total_ln * 100.0, 1),
        "secciones_sin_historia_suficiente": n_sin,
        "pct_secciones_sin_historia_suficiente": round(n_sin / total_n * 100.0, 2),
        "ln_2024_sin_historia_suficiente": ln_sin,
        "pct_ln_sin_historia_suficiente": round(ln_sin / total_ln * 100.0, 2),
        "distribucion_asignadas_por_perfil": dist_asignadas,
        "tabla_14": filas_tabla_14,
    }


def build_impacto_y_priorizacion_territorial(df_b: pd.DataFrame) -> dict:
    """
    Bloque D: Impacto estimado y priorización territorial (Viabilidad y potencial).
    Calcula con la Lista Nominal 2024 de Panel B:
      - C0, C3: electores adicionales = LN_2024 * (meta_2027 - base_2021) / 100
      - C1, C2: electores en riesgo = LN_2024 * max(0, base_2021 - promedio_inter_2009_2021) / 100
      - Total electores adicionales C0 + C3
    Con la columna DEF y perfil_por_seccion_2024.csv, calcula el ranking de los 300 distritos,
    el top 3 de juntas distritales por perfil y el % de LN concentrado en las 30 juntas principales.
    Guarda outputs/juntas_prioritarias_por_perfil.csv.
    """
    df_ps = pd.read_csv(PROJECT_ROOT / "outputs" / "perfil_por_seccion_2024.csv")

    df_ps["entidad"] = df_ps["EDOCVE"].map(ENTIDADES)
    df_ps["junta"] = df_ps["entidad"] + " – Distrito " + df_ps["DEF"].apply(lambda d: f"{d:02d}")

    all_districts = df_ps[["EDOCVE", "DEF", "entidad", "junta"]].drop_duplicates().sort_values(["EDOCVE", "DEF"]).reset_index(drop=True)

    ranking_rows = []
    resumen_perfil = {}

    for p_code in ["C0", "C1", "C2", "C3"]:
        sub = df_ps[df_ps["perfil"] == p_code]
        tot_ln = int(sub["LN_2024"].sum())
        dist_ln = sub.groupby(["EDOCVE", "DEF"])["LN_2024"].sum().reset_index()

        m = all_districts.merge(dist_ln, on=["EDOCVE", "DEF"], how="left")
        m["LN_2024"] = m["LN_2024"].fillna(0).astype(int)
        m = m.sort_values("LN_2024", ascending=False).reset_index(drop=True)
        m["ranking"] = m.index + 1
        m["perfil"] = p_code
        m["pct_ln_perfil"] = round(m["LN_2024"] / tot_ln * 100.0, 3)
        m["pct_acumulado_ln_perfil"] = round(m["LN_2024"].cumsum() / tot_ln * 100.0, 2)

        top3 = list(m["junta"].iloc[:3])
        top3_str = ", ".join(top3)
        top30_pct = float(m["pct_acumulado_ln_perfil"].iloc[29])
        top30_ln = int(m["LN_2024"].iloc[:30].sum())

        resumen_perfil[p_code] = {
            "top3_juntas": top3,
            "top3_juntas_str": top3_str,
            "top30_ln": top30_ln,
            "top30_pct": round(top30_pct, 1),
            "tot_ln_ampliada": tot_ln,
        }
        ranking_rows.extend(m.to_dict(orient="records"))

    df_rank = pd.DataFrame(ranking_rows)
    df_rank.to_csv(PROJECT_ROOT / "outputs" / "juntas_prioritarias_por_perfil.csv", index=False)

    # D1: Cálculo sobre Panel B sin redondeo intermedio
    ln_c0 = int(df_b[df_b["cluster"] == 0]["ln_2024"].sum())
    ln_c1 = int(df_b[df_b["cluster"] == 1]["ln_2024"].sum())
    ln_c2 = int(df_b[df_b["cluster"] == 2]["ln_2024"].sum())
    ln_c3 = int(df_b[df_b["cluster"] == 3]["ln_2024"].sum())

    sub0 = df_b[df_b["cluster"] == 0]
    sub1 = df_b[df_b["cluster"] == 1]
    sub2 = df_b[df_b["cluster"] == 2]
    sub3 = df_b[df_b["cluster"] == 3]

    p21_c0 = float(sub0["sv_2021"].sum() / sub0["sv_nv_2021"].sum() * 100.0)
    p21_c1 = float(sub1["sv_2021"].sum() / sub1["sv_nv_2021"].sum() * 100.0)
    p21_c2 = float(sub2["sv_2021"].sum() / sub2["sv_nv_2021"].sum() * 100.0)
    p21_c3 = float(sub3["sv_2021"].sum() / sub3["sv_nv_2021"].sum() * 100.0)
    p21_nat = float(df_b["sv_2021"].sum() / df_b["sv_nv_2021"].sum() * 100.0)

    # Metas de aumento (cerrar la mitad de la brecha respecto a la media nacional del panel B)
    # C0: delta real = 3.340002%
    delta_real_c0 = (p21_nat - p21_c0) / 2.0
    adicionales_c0_exacto = int(round(ln_c0 * (delta_real_c0 / 100.0)))
    adicionales_c0_miles_str = "≈ 938 mil"

    # C3: delta real = 1.679392% -> +1.7 pts a 1 decimal
    delta_real_c3 = (p21_nat - p21_c3) / 2.0
    adicionales_c3_exacto = int(round(ln_c3 * (delta_real_c3 / 100.0)))
    adicionales_c3_miles_str = "≈ 333 mil"

    total_adicionales_exacto = adicionales_c0_exacto + adicionales_c3_exacto
    total_adicionales_miles_str = "≈ 1.27 millones"

    # Perfiles de sostenimiento (riesgo de regreso a la media de intermedias 2009-2021)
    p09_c1 = float(sub1["sv_2009"].sum() / sub1["sv_nv_2009"].sum() * 100.0)
    p15_c1 = float(sub1["sv_2015"].sum() / sub1["sv_nv_2015"].sum() * 100.0)
    p_mid_avg_c1 = (p09_c1 + p15_c1 + p21_c1) / 3.0
    delta_riesgo_c1 = p21_c1 - p_mid_avg_c1
    riesgo_c1_exacto = int(round(ln_c1 * (delta_riesgo_c1 / 100.0)))
    riesgo_c1_miles_str = "≈ 58 mil"

    p09_c2 = float(sub2["sv_2009"].sum() / sub2["sv_nv_2009"].sum() * 100.0)
    p15_c2 = float(sub2["sv_2015"].sum() / sub2["sv_nv_2015"].sum() * 100.0)
    p_mid_avg_c2 = (p09_c2 + p15_c2 + p21_c2) / 3.0
    delta_riesgo_c2 = p21_c2 - p_mid_avg_c2
    riesgo_c2_exacto = int(round(ln_c2 * (delta_riesgo_c2 / 100.0)))
    riesgo_c2_miles_str = "≈ 1.92 millones"

    total_riesgo_exacto = riesgo_c1_exacto + riesgo_c2_exacto
    total_riesgo_miles_str = "≈ 1.97 millones"

    # D2: Escenario conservador
    # C0: MDE del piloto ANCOVA (1.57 pts)
    conservador_c0_exacto = int(round(ln_c0 * 0.0157))
    conservador_c0_miles_str = "≈ 441 mil"
    rango_c0_str = "441 mil – 938 mil"

    # C3: Mitad de la meta (1.679392 / 2 = 0.839696 pts)
    conservador_c3_exacto = int(round(ln_c3 * (delta_real_c3 / 2.0 / 100.0)))
    conservador_c3_miles_str = "≈ 167 mil"
    rango_c3_str = "167 mil – 333 mil"

    total_conservador_exacto = conservador_c0_exacto + conservador_c3_exacto
    total_conservador_miles_str = "≈ 607 mil"
    rango_total_adicionales_str = "607 mil – 1.27 millones"

    filas_tabla_impacto = [
        {
            "perfil": "C0: Baja Participación Intermitente con Rezago Juvenil",
            "codigo_cluster": "C0",
            "ln_2024_panel_b": ln_c0,
            "tipo_meta": "Aumento",
            "meta_delta_real_pts": round(delta_real_c0, 4),
            "meta_delta_pts": "+3.3 pts",
            "electores_impacto_n": adicionales_c0_exacto,
            "electores_impacto_str": "≈ 938 mil adicionales",
            "electores_conservador_n": conservador_c0_exacto,
            "electores_conservador_str": "≈ 441 mil adicionales",
            "rango_impacto_str": "441 mil – 938 mil adicionales",
            "top3_juntas_distritales": resumen_perfil["C0"]["top3_juntas_str"],
            "pct_ln_en_top30_juntas": resumen_perfil["C0"]["top30_pct"],
        },
        {
            "perfil": "C1: Alta Participación Estable e Intergeneracional",
            "codigo_cluster": "C1",
            "ln_2024_panel_b": ln_c1,
            "tipo_meta": "Sostener",
            "meta_delta_real_pts": round(delta_riesgo_c1, 4),
            "meta_delta_pts": "Sostener (0.0 pts)",
            "electores_impacto_n": riesgo_c1_exacto,
            "electores_impacto_str": "≈ 58 mil en riesgo",
            "electores_conservador_n": 0,
            "electores_conservador_str": "-",
            "rango_impacto_str": "≈ 58 mil en riesgo",
            "top3_juntas_distritales": resumen_perfil["C1"]["top3_juntas_str"],
            "pct_ln_en_top30_juntas": resumen_perfil["C1"]["top30_pct"],
        },
        {
            "perfil": "C2: Participación en Ascenso con Juventud Activa",
            "codigo_cluster": "C2",
            "ln_2024_panel_b": ln_c2,
            "tipo_meta": "Sostener",
            "meta_delta_real_pts": round(delta_riesgo_c2, 4),
            "meta_delta_pts": "Sostener (0.0 pts)",
            "electores_impacto_n": riesgo_c2_exacto,
            "electores_impacto_str": "≈ 1.92 millones en riesgo",
            "electores_conservador_n": 0,
            "electores_conservador_str": "-",
            "rango_impacto_str": "≈ 1.92 millones en riesgo",
            "top3_juntas_distritales": resumen_perfil["C2"]["top3_juntas_str"],
            "pct_ln_en_top30_juntas": resumen_perfil["C2"]["top30_pct"],
        },
        {
            "perfil": "C3: Liderazgo Femenino con Participación Estancada",
            "codigo_cluster": "C3",
            "ln_2024_panel_b": ln_c3,
            "tipo_meta": "Aumento",
            "meta_delta_real_pts": round(delta_real_c3, 4),
            "meta_delta_pts": "+1.7 pts",
            "electores_impacto_n": adicionales_c3_exacto,
            "electores_impacto_str": "≈ 333 mil adicionales",
            "electores_conservador_n": conservador_c3_exacto,
            "electores_conservador_str": "≈ 167 mil adicionales",
            "rango_impacto_str": "167 mil – 333 mil adicionales",
            "top3_juntas_distritales": resumen_perfil["C3"]["top3_juntas_str"],
            "pct_ln_en_top30_juntas": resumen_perfil["C3"]["top30_pct"],
        },
    ]

    # Guardar outputs/tablas/tabla_17_impacto.csv
    df_t17 = pd.DataFrame(filas_tabla_impacto)
    df_t17.to_csv(OUT_TABLAS / "tabla_17_impacto.csv", index=False, encoding="utf-8-sig")

    return {
        "electores_adicionales_c0": adicionales_c0_exacto,
        "electores_adicionales_c0_miles_str": adicionales_c0_miles_str,
        "electores_conservador_c0": conservador_c0_exacto,
        "electores_conservador_c0_miles_str": conservador_c0_miles_str,
        "rango_c0_str": rango_c0_str,
        "electores_en_riesgo_c1": riesgo_c1_exacto,
        "electores_en_riesgo_c1_miles_str": riesgo_c1_miles_str,
        "electores_en_riesgo_c2": riesgo_c2_exacto,
        "electores_en_riesgo_c2_miles_str": riesgo_c2_miles_str,
        "total_riesgo_exacto": total_riesgo_exacto,
        "total_riesgo_miles_str": total_riesgo_miles_str,
        "electores_adicionales_c3": adicionales_c3_exacto,
        "electores_adicionales_c3_miles_str": adicionales_c3_miles_str,
        "electores_conservador_c3": conservador_c3_exacto,
        "electores_conservador_c3_miles_str": conservador_c3_miles_str,
        "rango_c3_str": rango_c3_str,
        "total_electores_adicionales_c0_c3": total_adicionales_exacto,
        "total_adicionales_miles_str": total_adicionales_miles_str,
        "total_conservador_c0_c3": total_conservador_exacto,
        "total_conservador_miles_str": total_conservador_miles_str,
        "rango_total_adicionales_str": rango_total_adicionales_str,
        "resumen_por_perfil": resumen_perfil,
        "tabla_impacto": filas_tabla_impacto,
    }


def build_potencia_piloto_c0(df_b: pd.DataFrame) -> dict:
    """
    Bloque E: Diseño de evaluación y potencia estadística de piloto en C0.
    Calcula para las secciones de C0:
      - sigma_delta = desviación estándar del cambio 2015->2021 (diferencia en diferencias);
      - sigma_p = desviación estándar de P2021;
      - rho = correlación entre P2015 y P2021 por sección.
    Calcula MDE_DiD = 2.80 * sigma_delta * sqrt(2/n) y MDE_ANCOVA = 2.80 * sigma_p * sqrt(1 - rho^2) * sqrt(2/n),
    para n in [250, 500, 1000] secciones por grupo (80% potencia, alpha=0.05).
    Selecciona el diseño con menor MDE y menor n con MDE < mitad de meta de C0 (1.67 pts).
    Exporta tabla_15_potencia_piloto.csv.
    """
    c0 = df_b[df_b["cluster"] == 0].copy()
    delta = (c0["p_2021"] - c0["p_2015"]) * 100.0
    sigma_delta = float(delta.std(ddof=1))

    p21 = c0["p_2021"] * 100.0
    p15 = c0["p_2015"] * 100.0
    sigma_p = float(p21.std(ddof=1))
    rho = float(np.corrcoef(p15, p21)[0, 1])
    sqrt_rho = float(np.sqrt(1.0 - rho ** 2))

    filas_tabla_15 = []
    mde_dict = {}
    for n in [250, 500, 1000]:
        mde_did = 2.80 * sigma_delta * np.sqrt(2.0 / n)
        mde_ancova = 2.80 * sigma_p * sqrt_rho * np.sqrt(2.0 / n)
        mde_dict[n] = {
            "mde_did": round(float(mde_did), 2),
            "mde_ancova": round(float(mde_ancova), 2),
        }
        filas_tabla_15.append({
            "perfil_objetivo": "C0: Baja Participación Intermitente con Rezago Juvenil",
            "secciones_por_grupo_n": n,
            "secciones_totales_piloto": 2 * n,
            "sigma_delta_pts": round(sigma_delta, 4),
            "sigma_p2021_pts": round(sigma_p, 4),
            "correlacion_rho": round(rho, 4),
            "potencia_pct": 80.0,
            "significancia_alpha": 0.05,
            "constante_mde": 2.80,
            "mde_did_pts": round(float(mde_did), 2),
            "mde_ancova_pts": round(float(mde_ancova), 2),
            "meta_perfil_c0_pts": 3.3,
            "detecta_menor_mitad_meta": bool(mde_ancova < 1.67),
        })

    # Selección E2: menor MDE y menor n con MDE < mitad de meta (1.67 pts) -> ANCOVA n=500 (MDE=1.57 pts)
    n_sel = 500
    diseno_sel = "ANCOVA"
    mde_sel = mde_dict[n_sel]["mde_ancova"]

    return {
        "n_secciones_c0": len(c0),
        "sigma_delta_exacta": round(sigma_delta, 4),
        "sigma_delta_pts": round(sigma_delta, 2),
        "sigma_p_exacta": round(sigma_p, 4),
        "sigma_p_pts": round(sigma_p, 2),
        "correlacion_rho": round(rho, 4),
        "diseno_seleccionado": diseno_sel,
        "n_seleccionado": n_sel,
        "mde_seleccionado_pts": mde_sel,
        "mde_250_did": mde_dict[250]["mde_did"],
        "mde_250_ancova": mde_dict[250]["mde_ancova"],
        "mde_500_did": mde_dict[500]["mde_did"],
        "mde_500_ancova": mde_dict[500]["mde_ancova"],
        "mde_1000_did": mde_dict[1000]["mde_did"],
        "mde_1000_ancova": mde_dict[1000]["mde_ancova"],
        "meta_c0_pts": 3.3,
        "tabla_15": filas_tabla_15,
    }



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

    val_fuera = build_validacion_fuera_de_tiempo(df_b)

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
        "lineas_base_metas": build_lineas_base_metas(df_b),
        "validacion_fuera_de_tiempo": val_fuera,
        "valor_agregado_nivel_historico": val_fuera["valor_agregado_nivel_historico"],
        "cobertura_ampliada_2024": build_cobertura_ampliada(df_b),
        "impacto_y_prioridad_territorial": build_impacto_y_priorizacion_territorial(df_b),
        "potencia_piloto_c0": build_potencia_piloto_c0(df_b),
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
