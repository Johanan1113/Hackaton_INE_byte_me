#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fase 3 y 4: Reconstrucción de Perfiles, Nombres Objetivos, Estrategias y Viabilidad (04_perfiles_y_nombres.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

Genera a partir de outputs/fase2/etiquetas_finales.parquet:
- outputs/fase3/perfiles.csv: Caracterización integral de los 5 perfiles en escala original y z-scores,
  series 2009-2024 (simples y ponderadas), métricas demográficas (incluyendo ambos cálculos del ratio joven),
  composición U/R/M, campo indígena/afromexicano marcado como [PENDIENTE] y Top 5 entidades.
- outputs/fase3/estrategias.csv: Estrategias reasignadas desde cero conforme a las reglas 3.2, 3.4 y Fase 4
  (viabilidad legal/operativa ENCÍVICA, unidades responsables DECEyEC / Juntas Distritales Ejecutivas,
  costos como orden de magnitud estimado, lemas neutrales y factores causales etiquetados como hipótesis).
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

# Nombres derivados estrictamente con la Regla 3.2 sobre los nuevos clusters (k=5)
CLUSTER_META = {
    0: {
        "codigo": "C0",
        "nombre": "Abstencionismo Crónico con Rezago Juvenil",
        "variables_rectoras_z": "ratio_participacion_joven (z=-1.19), brecha_generacional (z=+0.87), participacion_media_historica (z=-0.84)",
        "justificacion_regla_3_2": (
            "Sus 3 únicas variables con |z|>=0.5 son ratio_participacion_joven (-1.19, mínimo nacional: 36.77% de votación joven), "
            "brecha_generacional (+0.87, máxima nacional: +22.71 pts entre 60+ y 18-29) y participacion_media_historica "
            "(-0.84, mínima nacional: 48.55%). Ninguna otra variable supera |z|>=0.40."
        ),
        "lema_neutral": "Tu primer voto abre camino: infórmate, ubica tu casilla y participa",
        "hipotesis_abstencionismo": (
            "Hipótesis: barreras de incorporación al primer sufragio en juventudes urbanas y periurbanas, "
            "combinadas con movilidad residencial temprana y menor socialización cívica escolar/comunitaria."
        ),
        "objetivo_especifico": (
            "Incrementar la tasa de participación de los electores inscritos de 18 a 29 años y reducir la brecha "
            "generacional en las 9,535 secciones con abstencionismo crónico."
        ),
        "canal_principal": (
            "Universidades, planteles de educación media superior, centros de trabajo juvenil y mensajería "
            "cívica digital geolocalizada (chatbot 'Ubica tu Casilla' y recordatorios SMS/WhatsApp institucionales)."
        ),
        "narrativa_mensaje": (
            "Informativa y de acompañamiento práctico al primer votante: guías paso a paso sobre cómo votar por "
            "primera vez, vigencia de la credencial para votar y localización exacta de casilla."
        ),
        "accion_operativa_ine": (
            "Brigadas universitarias y de educación media superior de las Juntas Distritales Ejecutivas para "
            "actualización de domicilio en el Padrón Electoral, simulacros de votación estudiantiles y difusión "
            "focalizada de 'Ubica tu Casilla' en las 9,535 secciones del perfil."
        ),
        "unidad_responsable": "DECEyEC en coordinación con las Juntas Distritales Ejecutivas y la DERFE",
        "costo_estimado_orden_magnitud": (
            "Orden de magnitud bajo-medio (~$18 a $28 millones MXN por proceso electoral federal; estimación "
            "sujeta a presupuesto operativo de Juntas Distritales y convenios con IES públicas y privadas)."
        ),
        "meta_cuantitativa": (
            "+3.0 a +4.5 puntos porcentuales en la tasa de participación de 18-29 años del cluster y cobertura "
            "operativa en al menos el 60% de las 9,535 secciones."
        ),
        "indicador_seguimiento": (
            "Tasa seccional SV/(SV+NV) del grupo 18-29 años y ratio_participacion_joven en el CCPC 2027 y 2030."
        ),
        "horizonte_temporal": "Permanente con intensificación preelectoral (2025-2027 y 2028-2030)",
    },
    1: {
        "codigo": "C1",
        "nombre": "Participación Intermitente de Ciclo Presidencial",
        "variables_rectoras_z": "brecha_presidencial_intermedia (z=+0.90), estabilidad_participacion (z=-0.72), tendencia_participacion_beta (z=+0.63)",
        "justificacion_regla_3_2": (
            "Sus variables con |z|>=0.5 son brecha_presidencial_intermedia (+0.90, máxima nacional: +19.42 pts entre "
            "presidenciales 63.53% e intermedias 44.12%), estabilidad_participacion (-0.72, mínima nacional por la fuerte "
            "oscilación bianual) y tendencia_participacion_beta (+0.63, +1.14 pts/año). Concentra 83.20% de secciones urbanas."
        ),
        "lema_neutral": "La democracia se ejerce cada tres años: conocer las atribuciones legislativas importa",
        "hipotesis_abstencionismo": (
            "Hipótesis: asimetría de visibilidad informativa entre comicios presidenciales y elecciones intermedias "
            "en zonas metropolitanas, donde el electorado percibe menor relevancia directa en la renovación de la Cámara de Diputados."
        ),
        "objetivo_especifico": (
            "Reducir la caída de participación en elecciones intermedias en las 16,244 secciones predominantemente "
            "urbanas que sí acuden a votar en comicios presidenciales."
        ),
        "canal_principal": (
            "Transporte público masivo, mobiliario urbano en zonas metropolitanas, plataformas digitales de "
            "consulta ('Conóceles') y foros distritales transmitidos por medios públicos y digitales."
        ),
        "narrativa_mensaje": (
            "Pedagogía institucional sobre las funciones de la Cámara de Diputados (presupuesto federal, "
            "fiscalización y legislación cotidiana) y difusión neutral del sistema 'Conóceles'."
        ),
        "accion_operativa_ine": (
            "Campaña cívica focalizada pre-intermedia (2027) de la DECEyEC y Juntas Locales/Distritales en "
            "corredores metropolitanos, foros distritales informativos y despliegue de códigos QR hacia la "
            "plataforma 'Conóceles' en las 16,244 secciones del perfil."
        ),
        "unidad_responsable": "DECEyEC en coordinación con Juntas Locales y Distritales Ejecutivas",
        "costo_estimado_orden_magnitud": (
            "Orden de magnitud medio (~$25 a $40 millones MXN en proceso electoral intermedio; estimación "
            "basada en pauta institucional, tiempos oficiales del Estado y activaciones metropolitanas)."
        ),
        "meta_cuantitativa": (
            "Reducir la brecha presidencial-intermedia del cluster en 3.5 a 5.0 puntos porcentuales en la "
            "elección intermedia de 2027, alcanzando al menos el 70% de las secciones urbanas del perfil."
        ),
        "indicador_seguimiento": (
            "Brecha presidencial-intermedia (media_presidencial - p_2027) y tasa SV/(SV+NV) en 2027 en el CCPC."
        ),
        "horizonte_temporal": "Focalizado en ciclo intermedio (2026-2027)",
    },
    2: {
        "codigo": "C2",
        "nombre": "Alta Participación Consolidada y Estable",
        "variables_rectoras_z": "estabilidad_participacion (z=+1.64), brecha_presidencial_intermedia (z=-1.20), brecha_generacional (z=-1.11), participacion_media_historica (z=+1.06), ratio_participacion_joven (z=+1.06)",
        "justificacion_regla_3_2": (
            "Presenta los valores más altos de estabilidad_participacion (+1.64), participacion_media_historica (+1.06, "
            "66.08%) y ratio_participacion_joven (+1.06, 60.17% de votación juvenil), junto con la menor "
            "brecha_presidencial_intermedia (-1.20, solo +4.67 pts) y la menor brecha_generacional (-1.11, +8.50 pts). "
            "Su pendiente es plana (+0.10 pts/año, z=-0.80) por Efecto Techo: ya partía de 61.07% en 2009 y se mantuvo en 66.19% en 2024."
        ),
        "lema_neutral": "Participar fortalece a tu comunidad: formemos a las próximas generaciones de funcionarias y funcionarios de casilla",
        "hipotesis_abstencionismo": (
            "Hipótesis: cohesión comunitaria e intergeneracional consolidada que sostiene altos niveles de sufragio "
            "en todo tipo de elección, cuyo principal riesgo operativo es la fatiga o falta de relevo en la integración de mesas directivas de casilla."
        ),
        "objetivo_especifico": (
            "Preservar los niveles de participación superiores al 65%, documentar buenas prácticas comunitarias "
            "y fortalecer el voluntariado cívico y la observación electoral en las 6,947 secciones del perfil."
        ),
        "canal_principal": (
            "Redes comunitarias, escuelas locales, centros culturales y sesiones de reconocimiento cívico "
            "organizadas por las Juntas Distritales Ejecutivas."
        ),
        "narrativa_mensaje": (
            "Reconocimiento institucional a la constancia cívica comunitaria e invitación a participar como "
            "funcionariado de mesa directiva de casilla, observadores electorales y promotores de educación cívica."
        ),
        "accion_operativa_ine": (
            "Documentación de casos de éxito por la DECEyEC en el marco de ENCÍVICA, talleres de formación de "
            "liderazgos cívicos juveniles para el relevo generacional y reclutamiento temprano de CAE y "
            "funcionariado de casilla por las Juntas Distritales Ejecutivas."
        ),
        "unidad_responsable": "DECEyEC y Dirección Ejecutiva de Capacitación Electoral (en Juntas Distritales Ejecutivas)",
        "costo_estimado_orden_magnitud": (
            "Orden de magnitud bajo (~$8 a $14 millones MXN por ciclo; estimación absorbible dentro de los "
            "programas ordinarios de educación cívica y capacitación electoral distrital)."
        ),
        "meta_cuantitativa": (
            "Mantener la participación media del cluster por encima del 65.0% y lograr una cobertura del 100% "
            "de mesas directivas de casilla con ciudadanas y ciudadanos propietarios capacitados en primera insaculación."
        ),
        "indicador_seguimiento": (
            "Tasa SV/(SV+NV), índice de estabilidad_participacion y porcentaje de integración de casillas sin sustitución en 2027."
        ),
        "horizonte_temporal": "Continuo de mantenimiento y sistematización (2025-2030)",
    },
    3: {
        "codigo": "C3",
        "nombre": "Constancia de Ciclo con Liderazgo Femenino y Estancamiento Secular",
        "variables_rectoras_z": "brecha_genero (z=+0.97), tendencia_participacion_beta (z=-0.79), brecha_presidencial_intermedia (z=-0.73), estabilidad_participacion (z=+0.65)",
        "justificacion_regla_3_2": (
            "Sus 4 variables con |z|>=0.5 son brecha_genero (+0.97, máxima nacional: +11.96 pts a favor de las mujeres, "
            "62.96% vs 51.00% hombres), tendencia_participacion_beta (-0.79: estancamiento secular y descenso en comicios "
            "presidenciales de 63.41% en 2012 a 58.24% en 2024), brecha_presidencial_intermedia (-0.73, +7.96 pts) y "
            "estabilidad_participacion (+0.65). Tiene la mayor proporción rural del país (41.75%)."
        ),
        "lema_neutral": "Cada voz en la comunidad cuenta: facilitemos el acceso a la casilla para todas las edades",
        "hipotesis_abstencionismo": (
            "Hipótesis: migración laboral masculina y juvenil en localidades rurales y semiurbanas, aunada a costos "
            "de traslado físico a la casilla y envejecimiento del padrón local que frena el crecimiento en elecciones presidenciales."
        ),
        "objetivo_especifico": (
            "Revertir el estancamiento en comicios presidenciales (de 63.41% en 2012 a 58.24% en 2024) facilitando el acceso "
            "físico e informativo al sufragio y promoviendo la participación masculina y juvenil en las 10,689 secciones del perfil."
        ),
        "canal_principal": (
            "Radiodifusoras comunitarias y regionales, perifoneo institucional, asambleas informativas "
            "comunitarias y módulos itinerantes de las Juntas Distritales Ejecutivas."
        ),
        "narrativa_mensaje": (
            "Corresponsabilidad comunitaria en el ejercicio del voto, información oportuna sobre ubicación y "
            "accesibilidad de casillas rurales/mixtas, y promoción de la participación de jóvenes y hombres en edad productiva."
        ),
        "accion_operativa_ine": (
            "Despliegue de brigadas móviles de educación cívica de las Juntas Distritales en secciones rurales y "
            "mixtas, difusión en radio local/comunitaria mediante tiempos oficiales y revisión de accesibilidad "
            "geográfica de domicilios de casilla en localidades dispersas."
        ),
        "unidad_responsable": "Juntas Distritales Ejecutivas, DECEyEC y Dirección Ejecutiva de Organización Electoral (DEOE)",
        "costo_estimado_orden_magnitud": (
            "Orden de magnitud medio (~$20 a $32 millones MXN por proceso electoral; estimación asociada a "
            "rutas de campo de Juntas Distritales en zonas rurales y producción radiofónica regional)."
        ),
        "meta_cuantitativa": (
            "Incrementar en +2.5 puntos porcentuales la participación masculina (de 51.00% a >=53.50%) y juvenil "
            "en al menos el 50% de sus 10,689 secciones durante el ciclo 2027-2030."
        ),
        "indicador_seguimiento": (
            "Pendiente de participación, tasa masculina SV/(SV+NV) y tasa 18-29 años en el CCPC 2027 y 2030."
        ),
        "horizonte_temporal": "Mediano plazo con trabajo territorial continuo (2025-2027)",
    },
    4: {
        "codigo": "C4",
        "nombre": "Participación en Ascenso con Juventud Activa",
        "variables_rectoras_z": "brecha_generacional (z=-0.95), ratio_participacion_joven (z=+0.87), tendencia_participacion_beta (z=+0.72), brecha_genero (z=-0.57)",
        "justificacion_regla_3_2": (
            "Destaca por baja brecha_generacional (-0.95, +9.62 pts), alto ratio_participacion_joven (+0.87, 53.76% de "
            "votación joven), la mayor tendencia_participacion_beta nacional (+0.72, +1.20 pts/año: sube de 43.46% en 2009 "
            "a 67.39% en 2024, +23.93 pts) y menor brecha_genero (-0.57, +5.35 pts por mayor paridad de votación masculina 57.16% y femenina 62.51%)."
        ),
        "lema_neutral": "Tu participación transforma tu entorno: mantengamos activa la conversación cívica",
        "hipotesis_abstencionismo": (
            "Hipótesis: dinamismo demográfico y creciente politización cívica tanto en periferias en expansión como "
            "en municipios con alta integración juvenil, donde el reto es institucionalizar el hábito del voto más allá de coyunturas."
        ),
        "objetivo_especifico": (
            "Consolidar el crecimiento histórico (+23.93 pts entre 2009 y 2024) evitando retrocesos en elecciones "
            "intermedias y canalizando la participación juvenil hacia mecanismos de educación cívica permanente."
        ),
        "canal_principal": (
            "Colectivos estudiantiles y juveniles, plataformas digitales interactivas, espacios públicos "
            "municipales y diálogo cívico convocado por las Juntas Distritales Ejecutivas."
        ),
        "narrativa_mensaje": (
            "Consolidación del hábito del voto como práctica permanente (tanto en elecciones presidenciales como "
            "intermedias) y fomento del diálogo informado y la verificación de información electoral."
        ),
        "accion_operativa_ine": (
            "Implementación de foros juveniles 'Diálogos por la Democracia' de la DECEyEC, alianzas con redes "
            "universitarias y comunitarias para promoción del voto informado en 2027 y seguimiento de capacidad "
            "instalada de casillas en secciones con rápido crecimiento de Lista Nominal."
        ),
        "unidad_responsable": "DECEyEC en coordinación con las Juntas Distritales Ejecutivas",
        "costo_estimado_orden_magnitud": (
            "Orden de magnitud bajo-medio (~$12 a $20 millones MXN por proceso electoral; estimación enfocada "
            "en actividades de vinculación juvenil, foros distritales y comunicación digital institucional)."
        ),
        "meta_cuantitativa": (
            "Sostener una participación superior al 60.0% en la elección intermedia de 2027 (preservando el nivel "
            "de 62.15% alcanzado en 2021) y mantener el ratio de participación joven por encima de 0.89."
        ),
        "indicador_seguimiento": (
            "Tasa SV/(SV+NV) en 2027, ratio_participacion_joven y retención del crecimiento respecto a 2021."
        ),
        "horizonte_temporal": "Consolidación en el ciclo 2025-2027",
    },
}


def build_perfiles_and_estrategias(df_b: pd.DataFrame, df_univ: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye outputs/fase3/perfiles.csv y outputs/fase3/estrategias.csv."""
    total_sec_b = len(df_b)
    total_ln_b = int(df_b["ln_2024"].sum())
    total_sec_2024 = int(df_univ.loc[df_univ["etapa"] == "1_universo_2024", "secciones"].iloc[0])
    total_ln_2024 = int(df_univ.loc[df_univ["etapa"] == "1_universo_2024", "ln_2024"].iloc[0])

    # Medias y DE nacionales sobre el panel principal (N=53,644) para z-scores exactos
    nat_means = {col: float(df_b[col].mean()) for col in FEATURE_COLS}
    nat_stds = {col: float(df_b[col].std(ddof=1)) for col in FEATURE_COLS}

    perfiles_rows = []
    estrategias_rows = []

    for c in range(5):
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
    y documenta por qué k=5 es la partición óptima frente a k=4 y k=6.
    """
    nat_means = {col: float(df_b[col].mean()) for col in FEATURE_COLS}
    nat_stds = {col: float(df_b[col].std(ddof=1)) for col in FEATURE_COLS}

    rows = []
    for k, col_k in [(4, "cluster_k4"), (5, "cluster"), (6, "cluster_k6")]:
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
            }
            z_summary = []
            for fcol in FEATURE_COLS:
                val = float(sub[fcol].mean())
                z = (val - nat_means[fcol]) / nat_stds[fcol]
                row[f"{fcol}_orig"] = round(val, 4)
                row[f"{fcol}_z"] = round(z, 2)
                if abs(z) >= 0.5:
                    z_summary.append(f"{fcol}({z:+.2f})")
            row["variables_con_abs_z_ge_05"] = ", ".join(z_summary)
            rows.append(row)

    df_comp = pd.DataFrame(rows)
    df_comp.to_csv(OUT_FASE3 / "comparacion_k4_k5_k6.csv", index=False)

    # Generar reporte narrativo comparacion_k4_k5_k6.md
    md_lines = [
        "# Evaluación Comparativa de $k \\in \\{4, 5, 6\\}$ dentro del Rango de la Convocatoria (4 a 6 Perfiles)",
        "",
        "## 1. Métricas de Validación Interna y Estabilidad Bootstrap (100 réplicas al 80%)",
        "",
        "- **$k=4$**: Silhouette = `0.1789`, Davies-Bouldin = `1.5380`, Calinski-Harabasz = `14,435.43`, ARI Bootstrap = `0.9572 ± 0.0253` (IC 95%: `[0.9091, 0.9915]`).",
        "- **$k=5$**: Silhouette = `0.1625`, Davies-Bouldin = `1.6109`, Calinski-Harabasz = `12,676.61`, ARI Bootstrap = `0.9327 ± 0.0330` (IC 95%: `[0.8728, 0.9854]`).",
        "- **$k=6$**: Silhouette = `0.1639`, Davies-Bouldin = `1.5709`, Calinski-Harabasz = `11,550.69`, ARI Bootstrap = `0.9675 ± 0.0162` (IC 95%: `[0.9375, 0.9887]`).",
        "",
        "## 2. Interpretabilidad Sustantiva y Diferenciación de Política Pública",
        "",
        "1. **¿Qué ocurre en $k=4$?**",
        "   - En $k=4$, las secciones de *Alta Participación Consolidada y Estable* (`C2` en $k=5$, con $z=+1.64$ en estabilidad y $66.08\\%$ de participación) se fusionan parcialmente con las secciones de *Participación en Ascenso con Juventud Activa* (`C4` en $k=5$, con $\\beta=+1.20$ pts/año) y con las de liderazgo femenino rural (`C3` en $k=5$).",
        "   - Esto oculta la distinción operativa crítica entre: (a) comunidades donde la participación ya es alta y estable desde 2009 (`66.08\\%`), que sólo requieren mantenimiento y relevo de funcionariado de casilla, y (b) secciones donde la participación creció `+23.93 pts` entre 2009 y 2024 impulsada por votantes jóvenes (`C4`), que requieren consolidar el hábito en elecciones intermedias.",
        "",
        "2. **¿Qué aporta $k=5$?**",
        "   - Los 5 clusters tienen tamaños equilibrados (entre `12.95%` y `30.28%` de las secciones; ningún cluster marginal ni residual), alta estabilidad bootstrap (`ARI = 0.9327`) y cada uno posee al menos **3 variables rectoras con $|z| \\ge 0.50$ sin traslape conceptual**:",
        "     - **C0 (`17.77%`)**: Abstencionismo crónico (`48.55%`, $z=-0.84$) con rezago juvenil severo (`ratio_joven = 0.758`, $z=-1.19$; `brecha_generacional = +22.71 pts`, $z=+0.87$).",
        "     - **C1 (`30.28%`)**: Participación intermitente de ciclo presidencial (`brecha_pres_inter = +19.42 pts`, $z=+0.90$; `estabilidad` $z=-0.72$; `tendencia = +1.14 pts/año`, $z=+0.63$; `83.20%` urbano).",
        "     - **C2 (`12.95%`)**: Alta participación consolidada y estable (`66.08%`, $z=+1.06$; `estabilidad` $z=+1.64$; `brecha_pres_inter = +4.67 pts`, $z=-1.20$; `ratio_joven = 0.910`, $z=+1.06$).",
        "     - **C3 (`19.93%`)**: Constancia de ciclo con liderazgo femenino y estancamiento secular (`brecha_genero = +11.96 pts`, $z=+0.97$; `tendencia` $z=-0.79$; `brecha_pres_inter = +7.96 pts`, $z=-0.73$; `estabilidad` $z=+0.65$; `41.75%` rural).",
        "     - **C4 (`19.07%`)**: Participación en ascenso con juventud activa (`brecha_generacional = +9.62 pts`, $z=-0.95$; `ratio_joven = 0.898`, $z=+0.87$; `tendencia = +1.20 pts/año`, $z=+0.72$; `brecha_genero = +5.35 pts`, $z=-0.57$).",
        "",
        "3. **¿Qué ocurre en $k=6$?**",
        "   - En $k=6$, el cluster de *Participación Intermitente de Ciclo Presidencial* (`C1` en $k=5$) se subdivide en dos subgrupos urbanos con el mismo diagnóstico operativo (alta brecha presidencial-intermedia en zonas metropolitanas), diferenciados principalmente por la pendiente histórica (`beta`), lo que generaría dos estrategias redundantes orientadas al mismo canal metropolitano en elecciones intermedias.",
        "",
        "## 3. Conclusión Metodológica",
        "",
        "Se recomienda mantener **$k=5$** como solución principal porque maximiza la utilidad accionable para la DECEyEC y las Juntas Distritales Ejecutivas: produce 5 perfiles con diagnósticos causales hipotéticos y canales de intervención mutuamente excluyentes, cumple con holgura el criterio de estabilidad (`ARI = 0.9327 > 0.85`), evita fusionar la participación consolidada con la participación emergente (como hace $k=4$) y evita fragmentar el perfil urbano intermitente en dos subperfiles con la misma intervención operativa (como hace $k=6$).",
    ]
    (OUT_FASE3 / "comparacion_k4_k5_k6.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return df_comp


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
        },
        "universo_y_cobertura": {
            "secciones_union_historica_2009_2024": 72681,
            "secciones_2024_total": 70751,
            "secciones_continuas_2009_2024": 62048,
            "secciones_2024_creadas_post2009": 8703,
            "secciones_2009_2021_baja_antes_2024": 1930,
            "secciones_captura_valida_sv_nv_ge_50": 54804,
            "secciones_excluidas_sv_nv_lt_50": 7244,
            "secciones_excluidas_sv_nv_eq_0": 4769,
            "secciones_excluidas_sv_nv_1_a_49": 2475,
            "secciones_salto_abrupto_ln_en_62048": 1311,
            "secciones_salto_abrupto_ln_en_54804": 1159,
            "secciones_sin_saltos_ln": 53645,
            "secciones_excluidas_sin_grupo_etario_60mas": 1,
            "panel_principal_secciones": int(len(df_b)),
            "panel_principal_pct_secciones_2024": round(len(df_b) / 70751 * 100, 2),
            "panel_principal_pct_secciones_continuas": round(len(df_b) / 62048 * 100, 2),
            "panel_principal_ln_2024": int(df_b["ln_2024"].sum()),
            "ln_2024_total_csv": 98330348,
            "ln_2024_oficial_ine": 98329591,
            "panel_principal_pct_ln_2024": round(df_b["ln_2024"].sum() / 98330348 * 100, 2),
            "panel_principal_municipios": int((df_b["edocve"].astype(str) + "_" + df_b["municipio"].astype(str)).nunique()),
            "municipios_2024_total": 2475,
            "municipios_historicos_union": 2477,
            "cascada_filtrado": df_univ.to_dict(orient="records"),
        },
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
        "sha256_perfiles_csv": sha_perf,
        "sha256_estrategias_csv": sha_estr,
        "sha256_metricas_finales_json": sha_metricas,
        "n_perfiles": len(df_perfiles),
        "n_secciones_panel": len(df_b),
    }
    with open(OUT_FASE3 / "resumen_fase3.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    print(f"[Fase 3] Completado. SHA256(perfiles.csv) = {sha_perf}")
    print(f"[Fase 3] SHA256(metricas_finales.json) = {sha_metricas}")


if __name__ == "__main__":
    main()

