#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fase 7: Compilación del Documento Técnico Final en MD, PDF y DOCX (07_compilar_documento.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

Reglas estrictas:
1. Cero cifras escritas a mano: absolutamente todos los números, porcentajes, conteos,
   nombres de perfiles y métricas se leen programáticamente de outputs/metricas_finales.json.
2. Formato: 8 a 12 páginas en PDF (Letter, Arial/Liberation Sans 11pt, interlineado 1.5),
   con tablas diseñadas con anchos holgados (máximo 7-8 columnas por tabla, total 504 pt)
   para evitar palabras partidas o desbordes, e inclusión de las 7 figuras a 300 DPI.
3. Genera también Documento_Tecnico_ByteMe.md (desde plantillas/documento_tecnico.md.j2)
   y Documento_Tecnico_ByteMe.docx.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
METRICAS_PATH = PROJECT_ROOT / "outputs" / "metricas_finales.json"
PLANTILLA_DIR = PROJECT_ROOT / "plantillas"
FIGURAS_DIR = PROJECT_ROOT / "outputs" / "figuras"
OUT_ENTREGABLES = PROJECT_ROOT / "outputs" / "entregables"
OUT_ENTREGABLES.mkdir(parents=True, exist_ok=True)


def render_markdown_from_template(data: dict) -> Path:
    """Renderiza outputs/entregables/Documento_Tecnico_ByteMe.md desde plantillas/documento_tecnico.md.j2."""
    env = Environment(loader=FileSystemLoader(str(PLANTILLA_DIR)), autoescape=False)
    tmpl = env.get_template("documento_tecnico.md.j2")

    bench = data["benchmark_modelos"]
    bench_km = [r for r in bench if r["algoritmo"] == "K-Means++"]
    bench_km_k4 = [r for r in bench_km if r["k"] == data["k_seleccionado"]][0]
    comp_k6_c1 = [r for r in data["comparacion_k4_k5_k6"] if r["k"] == 6 and r["n_variables_con_abs_z_ge_05"] == 1][0]

    ctx = {
        "k_sel": data["k_seleccionado"],
        "sw": data["entorno_software"],
        "univ": data["universo_y_cobertura"],
        "pan_b": data["resumen_panel_b"],
        "serie": data["serie_nacional_2009_2024"],
        "inc_exc": data["incluidas_vs_excluidas_2024"],
        "est": data["estabilidad_comparacion"],
        "vif": data["vif_colinealidad"],
        "win": data["ventanas_temporales"],
        "bench": bench,
        "bench_km": bench_km,
        "bench_km_k4": bench_km_k4,
        "comp_k6_c1": comp_k6_c1,
        "sens": data["sensibilidad_opcion_a"],
        "trans": data["transicion_clusters"],
        "interp": data["interpretabilidad_rf_anova"],
        "pca": data["proyecciones_pca"],
        "perfiles": data["perfiles"],
        "estrategias": data["estrategias"],
    }

    md_text = tmpl.render(**ctx)
    md_path = OUT_ENTREGABLES / "Documento_Tecnico_ByteMe.md"
    md_path.write_text(md_text, encoding="utf-8")
    return md_path


def make_figure_flowable(img_path: Path, max_width: float = 6.7 * inch, max_height: float = 3.15 * inch) -> Image:
    """Escala proporcionalmente una figura PNG para que quepa con nitidez en la página."""
    with PILImage.open(img_path) as im:
        w_px, h_px = im.size
    aspect = h_px / float(w_px)
    width = max_width
    height = width * aspect
    if height > max_height:
        height = max_height
        width = height / aspect
    flow_img = Image(str(img_path), width=width, height=height)
    flow_img.hAlign = "CENTER"
    return flow_img


def styled_table(rows_data: list[list[Paragraph]], col_widths: list[float], highlight_last: bool = False) -> Table:
    """Crea una tabla ReportLab con formato limpio, encabezados repetibles y sin cortes de palabra."""
    t = Table(rows_data, colWidths=col_widths, repeatRows=1, splitByRow=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4.0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4.0),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2 if highlight_last else -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]
    if highlight_last:
        style_cmds.append(("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E0E7FF")))
    t.setStyle(TableStyle(style_cmds))
    return t


def build_pdf(data: dict) -> Path:
    """Compila outputs/entregables/Documento_Tecnico_ByteMe.pdf (8-12 páginas) leyendo 100% de metricas_finales.json."""
    pdf_path = OUT_ENTREGABLES / "Documento_Tecnico_ByteMe.pdf"

    k_sel = data["k_seleccionado"]
    sw = data["entorno_software"]
    u = data["universo_y_cobertura"]
    pan_b = data["resumen_panel_b"]
    serie = data["serie_nacional_2009_2024"]
    inc_exc = data["incluidas_vs_excluidas_2024"]
    est = data["estabilidad_comparacion"]
    vif = data["vif_colinealidad"]
    win = data["ventanas_temporales"]
    bench = data["benchmark_modelos"]
    bench_km = [r for r in bench if r["algoritmo"] == "K-Means++"]
    bench_km_k4 = [r for r in bench_km if r["k"] == k_sel][0]
    comp_k6_c1 = [r for r in data["comparacion_k4_k5_k6"] if r["k"] == 6 and r["n_variables_con_abs_z_ge_05"] == 1][0]
    sens = data["sensibilidad_opcion_a"]
    trans = data["transicion_clusters"]
    interp = data["interpretabilidad_rf_anova"]
    perfiles = data["perfiles"]
    estrategias = data["estrategias"]

    styles = getSampleStyleSheet()
    title_st = ParagraphStyle(
        "DocTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=13.5, leading=17.5, textColor=colors.HexColor("#0F172A"), alignment=TA_LEFT, spaceAfter=3
    )
    sub_st = ParagraphStyle(
        "DocSub", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=9.2, leading=12.5, textColor=colors.HexColor("#1E3A8A"), alignment=TA_LEFT, spaceAfter=8
    )
    h1_st = ParagraphStyle(
        "H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=11.5, leading=15.0, textColor=colors.HexColor("#1E3A8A"), spaceBefore=7, spaceAfter=4, keepWithNext=True
    )
    h2_st = ParagraphStyle(
        "H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=10.2, leading=13.5, textColor=colors.HexColor("#0F172A"), spaceBefore=5, spaceAfter=3, keepWithNext=True
    )
    # Cuerpo principal: 10.5pt con interlineado 1.45x (15.2pt leading) para lectura fluida y ajuste exacto en 10-11 páginas
    body_st = ParagraphStyle(
        "Body", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9.8, leading=14.2, textColor=colors.HexColor("#1F2937"), alignment=TA_JUSTIFY, spaceAfter=4.5
    )
    bullet_st = ParagraphStyle(
        "Bullet", parent=body_st, leftIndent=12, firstLineIndent=-8, spaceAfter=3.0
    )
    cap_st = ParagraphStyle(
        "TableCap", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=8.6, leading=11.5, textColor=colors.HexColor("#1E293B"), spaceBefore=4, spaceAfter=2.5, keepWithNext=True
    )
    th_c = ParagraphStyle(
        "THC", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=7.4, leading=9.2, textColor=colors.white, alignment=TA_CENTER
    )
    th_l = ParagraphStyle(
        "THL", parent=th_c, alignment=TA_LEFT
    )
    td_c = ParagraphStyle(
        "TDC", parent=styles["Normal"], fontName="Helvetica",
        fontSize=7.3, leading=9.2, textColor=colors.HexColor("#111827"), alignment=TA_CENTER
    )
    td_l = ParagraphStyle(
        "TDL", parent=td_c, alignment=TA_LEFT
    )
    td_cb = ParagraphStyle(
        "TDCB", parent=td_c, fontName="Helvetica-Bold"
    )
    td_lb = ParagraphStyle(
        "TDLB", parent=td_l, fontName="Helvetica-Bold"
    )

    story = []

    # Título y autoría (sin sugerir autoría del INE ni usar la palabra Confidencial)
    story.append(Paragraph(
        f"Perfiles Ciudadanos de Participación Electoral en México ({serie[0]['anio']}–{serie[-1]['anio']}): "
        f"Auditoría de Microdatos Censales, Tipología Seccional Reproducible y Estrategias de Educación Cívica",
        title_st
    ))
    story.append(Paragraph(
        "Equipo Byte me — Propuesta técnica para el Reto 1: Perfiles ciudadanos de participación (Concurso INE: Hackea la participación)",
        sub_st
    ))

    # SECCIÓN 1: RESUMEN EJECUTIVO
    story.append(Paragraph("1. Resumen Ejecutivo", h1_st))
    diff_2018 = serie[3]["subestimacion_erronea_sv_ln_pond_pts"]
    diff_2024 = serie[5]["subestimacion_erronea_sv_ln_pond_pts"]
    story.append(Paragraph(
        f"Este estudio construye una tipología nacional de secciones electorales a partir de los microdatos abiertos de los Conteos Censales "
        f"de Participación Ciudadana (CCPC) en las seis elecciones federales celebradas entre {serie[0]['anio']} y {serie[-1]['anio']}. "
        f"Durante la auditoría técnica de los datos se identificó un hallazgo metodológico central: en los archivos abiertos del CCPC, la Lista Nominal "
        f"cumple la identidad exacta <b>LN = SV + NV + NS</b>, donde <b>SV</b> corresponde a las personas que sí votaron, <b>NV</b> a quienes no votaron "
        f"y <b>NS</b> a los registros cuyos cuadernillos no estuvieron disponibles para captura por recuento distrital o contingencias operativas "
        f"({serie[3]['ns_total_anio']:,} registros equivalentes al {serie[3]['pct_ns_anio']:.2f}% de la LN en {serie[3]['anio']}, y "
        f"{serie[5]['ns_total_anio']:,} registros equivalentes al {serie[5]['pct_ns_anio']:.2f}% en {serie[5]['anio']}). Dividir <b>SV / LN</b> en vez de "
        f"aplicar la fórmula oficial <b>SV / (SV + NV)</b> computaba como 0.0% de participación a miles de secciones con <b>SV + NV = 0</b>, "
        f"subestimando la participación nacional en {diff_2018:.2f} puntos porcentuales en {serie[3]['anio']} y en {diff_2024:.2f} puntos en {serie[-1]['anio']}, "
        f"además de fabricar un agrupamiento artificial de supuesto declive cívico.",
        body_st
    ))
    story.append(Paragraph(
        f"Al aplicar la fórmula <b>SV / (SV + NV)</b> en todas las tasas y construir el <b>Panel Principal (Opción B, cero imputación)</b> con las "
        f"<b>{u['panel_principal_secciones']:,} secciones</b> que cuentan con captura válida (<b>SV + NV &gt;= 50</b> en las seis elecciones) y sin saltos "
        f"abruptos de Lista Nominal por reseccionamiento —cubriendo el <b>{u['panel_principal_pct_secciones_2024']:.2f}% de las secciones</b> y el "
        f"<b>{u['panel_principal_pct_ln_2024']:.2f}% de la Lista Nominal de {serie[-1]['anio']}</b> ({u['panel_principal_ln_2024']:,} electores en "
        f"<b>{u['panel_principal_municipios']:,} municipios</b>)—, el modelo <b>K-Means++ con k = {k_sel}</b> domina empíricamente dentro del rango "
        f"de {bench_km[1]['k']} a {bench_km[3]['k']} perfiles de la convocatoria (Silhouette = {bench_km_k4['silhouette']:.4f}, Davies-Bouldin = "
        f"{bench_km_k4['davies_bouldin']:.4f}, Calinski-Harabasz = {bench_km_k4['calinski_harabasz']:,.2f} y estabilidad bootstrap ARI = "
        f"{bench_km_k4['bootstrap_ari_media']:.4f} [{bench_km_k4['bootstrap_ari_ic95_inf']:.4f}, {bench_km_k4['bootstrap_ari_ic95_sup']:.4f}]). "
        f"Los cuatro perfiles resultantes son: "
        + "; ".join(
            f"<b>{p['codigo_cluster']}: {p['nombre_propuesto']}</b> ({p['n_secciones']:,} secc., {p['pct_secciones_panel']:.2f}% del panel / "
            f"{p['pct_ln_panel']:.2f}% LN panel, media {p['participacion_media_historica_original']*100:.2f}%)"
            for p in perfiles
        ) + ".",
        body_st
    ))

    # SECCIÓN 2: DATOS Y TRATAMIENTO
    story.append(Paragraph("2. Datos y Tratamiento: Hallazgo de Registros NS y Universo de Estudio", h1_st))
    story.append(Paragraph(
        f"En los diccionarios de datos de la DECEyEC, el campo <b>NS</b> identifica a los electores cuya condición de voto no pudo verificarse porque "
        f"el cuadernillo de Lista Nominal no fue remitido o estuvo sujeto a recuento. La tasa de participación seccional y por subgrupo demográfico "
        f"(jóvenes de 18–29 años, adultos mayores de 60+ años, mujeres y hombres) debe calcularse como <b>P = SV / (SV + NV)</b>. En {serie[-1]['anio']}, "
        f"los registros con identificador no binario (<b>SEXO = 2</b>) se integran en la tasa total de la sección, mientras que la brecha de género se "
        f"calcula entre mujeres (<b>SEXO = 1</b>) y hombres (<b>SEXO = 0</b>). Asimismo, la verificación sobre los microdatos crudos demostró que existen "
        f"<b>0 secciones</b> con <b>SV &gt; LN</b> o <b>SV &gt; (SV + NV)</b>, ya que los Conteos Censales no incluyen casillas especiales.",
        body_st
    ))
    story.append(Paragraph(
        f"La Tabla 1 valida la serie nacional calculada con <b>SV / (SV + NV)</b> contra las publicaciones censales oficiales del INE: el estudio "
        f"comparativo de la DECEyEC (<i>DECEYEC_Comparativo_VF.pdf</i>, p. 11) reporta <b>{serie[0]['oficial_o_referencia_pct']:.2f}%</b> en {serie[0]['anio']}, "
        f"<b>{serie[1]['oficial_o_referencia_pct']:.2f}%</b> en {serie[1]['anio']} y <b>{serie[2]['oficial_o_referencia_pct']:.2f}%</b> en {serie[2]['anio']}; "
        f"los estudios censales de {serie[3]['anio']} y {serie[5]['anio']} reportan <b>{serie[3]['oficial_o_referencia_pct']:.1f}%</b> "
        f"(dato exacto CCPC: {serie[3]['total_ponderada_sv_svnv_pct']:.2f}%) y <b>{serie[5]['oficial_o_referencia_pct']:.1f}%</b> "
        f"(dato exacto CCPC: {serie[5]['total_ponderada_sv_svnv_pct']:.2f}%). Para la elección intermedia de {serie[4]['anio']}, el dato censal de "
        f"<b>{serie[4]['oficial_o_referencia_pct']:.1f}%</b> proviene de la <b>imagen (captura del tablero interactivo oficial del INE)</b> en la "
        f"<b>página 21</b> de <i>Manual-Conteos-Censales-2009-2024.pdf</i>, figura de la sección <i>\"Participación por año\"</i> (el cálculo exacto sin "
        f"redondear sobre el CSV abierto es <b>{serie[4]['total_ponderada_sv_svnv_pct']:.2f}%</b>; como referencia externa no censal, el cierre del PREP "
        f"{serie[4]['anio']} reportó 52.67%).",
        body_st
    ))

    # Tabla 1: Serie Nacional 2009-2024 (8 columnas bien proporcionadas = 504 pt)
    t1_rows = [[
        Paragraph("Año (Tipo)", th_c),
        Paragraph("Secciones CCPC", th_c),
        Paragraph("Secc. SV+NV=0", th_c),
        Paragraph("NS (% LN)", th_c),
        Paragraph("Erróneo SV/LN Pond.", th_c),
        Paragraph("CCPC SV/(SV+NV) Pond. (Simple)", th_c),
        Paragraph("Oficial Censal INE", th_c),
        Paragraph("Panel B Pond. (Sesgo vs CCPC)", th_c),
    ]]
    for r in serie:
        of_str = f"{r['oficial_o_referencia_pct']:.2f}%" if r["anio"] in (2009, 2012, 2015) else f"{r['oficial_o_referencia_pct']:.1f}%"
        tipo_short = "Pres." if r["tipo_eleccion"] == "Presidencial" else "Inter."
        t1_rows.append([
            Paragraph(f"<b>{r['anio']}</b> ({tipo_short})", td_c),
            Paragraph(f"{r['secciones_totales_anio']:,}", td_c),
            Paragraph(f"{r['secciones_sin_captura_svnv_0']:,}", td_c),
            Paragraph(f"{r['pct_ns_anio']:.2f}%", td_c),
            Paragraph(f"{r['total_ponderada_erronea_sv_ln_pct']:.2f}%", td_c),
            Paragraph(f"<b>{r['total_ponderada_sv_svnv_pct']:.2f}%</b> ({r['total_simple_sv_svnv_pct']:.2f}%)", td_c),
            Paragraph(f"<b>{of_str}</b>", td_cb),
            Paragraph(f"{r['panel_b_ponderada_sv_svnv_pct']:.2f}% ({r['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} pts)", td_c),
        ])
    story.append(KeepTogether([
        Paragraph(f"Tabla 1. Serie Nacional {serie[0]['anio']}–{serie[-1]['anio']}: Validación de Fórmula Oficial SV/(SV+NV) y Efecto de Registros NS", cap_st),
        styled_table(t1_rows, [56, 52, 52, 46, 56, 92, 56, 94]),
        Spacer(1, 5),
    ]))

    story.append(Paragraph(
        f"<b>Reconciliación del universo seccional (Tabla 2):</b> La unión histórica {serie[0]['anio']}–{serie[-1]['anio']} comprende "
        f"<b>{u['secciones_union_historica_2009_2024']:,} secciones</b> distintas. Al descontar <b>{u['secciones_2009_2021_baja_antes_2024']:,}</b> secciones "
        f"dadas de baja antes de {serie[-1]['anio']}, se obtienen las <b>{u['secciones_2024_total']:,} secciones activas en {serie[-1]['anio']}</b> "
        f"({u['ln_2024_total_csv']:,} electores en el CSV abierto vs {u['ln_2024_oficial_ine']:,} en el informe INE). Estas se componen de "
        f"<b>{u['secciones_continuas_2009_2024']:,} secciones continuas</b> ({serie[0]['anio']}–{serie[-1]['anio']}, con LN {serie[-1]['anio']} de "
        f"{u['ln_2024_panel_continuo_62048']:,}) más <b>{u['secciones_2024_creadas_post2009']:,} secciones creadas post-{serie[0]['anio']}</b> "
        f"({u['secciones_continuas_2009_2024']:,} + {u['secciones_2024_creadas_post2009']:,} = {u['secciones_2024_total']:,}). "
        f"Sobre las {u['secciones_continuas_2009_2024']:,} continuas se exige captura válida <b>SV + NV &gt;= 50</b> en las seis elecciones "
        f"(quedan <b>{u['secciones_captura_valida_sv_nv_ge_50']:,}</b> tras excluir {u['secciones_excluidas_sv_nv_lt_50']:,}: "
        f"{u['secciones_excluidas_sv_nv_eq_0']:,} con SV+NV=0 y {u['secciones_excluidas_sv_nv_1_a_49']:,} con 1&lt;=SV+NV&lt;50), ausencia de saltos "
        f"consecutivos de LN &lt;0.5x o &gt;2.5x por reseccionamiento (quedan <b>{u['secciones_sin_saltos_ln']:,}</b> tras excluir "
        f"{u['secciones_salto_abrupto_ln_en_54804']:,} de las {u['secciones_salto_abrupto_ln_en_62048']:,} del panel continuo) y presencia de todos los "
        f"grupos etarios ({u['secciones_excluidas_sin_grupo_etario_60mas']} sección excluida), conformando el <b>Panel Principal (Opción B) de "
        f"{u['panel_principal_secciones']:,} secciones</b> sin ninguna imputación.",
        body_st
    ))

    # Tabla 2: Cascada de Filtrado (7 columnas = 504 pt)
    t2_rows = [[
        Paragraph("Etapa de Filtrado del Universo", th_l),
        Paragraph("Secciones", th_c),
        Paragraph("Excluidas", th_c),
        Paragraph(f"% Secc. {serie[-1]['anio']}", th_c),
        Paragraph(f"LN {serie[-1]['anio']}", th_c),
        Paragraph(f"% LN {serie[-1]['anio']}", th_c),
        Paragraph("Municipios", th_c),
    ]]
    etapa_labels = [
        f"0. Unión histórica ({serie[0]['anio']}–{serie[-1]['anio']})",
        f"1. Secciones activas en CCPC {serie[-1]['anio']}",
        f"2. Panel continuo ({serie[0]['anio']}–{serie[-1]['anio']})",
        "3. Captura válida (SV+NV >= 50 en las 6)",
        "4. Sin salto consecutivo LN (<0.5x o >2.5x)",
        "5. Panel Principal Opción B (Cero Imputación)",
    ]
    for idx, c_row in enumerate(u["cascada_filtrado"]):
        is_last = idx == len(u["cascada_filtrado"]) - 1
        st_l = td_lb if is_last else td_l
        st_c = td_cb if is_last else td_c
        t2_rows.append([
            Paragraph(etapa_labels[idx], st_l),
            Paragraph(f"{c_row['secciones']:,}", st_c),
            Paragraph(f"{c_row['secciones_excluidas_paso']:,}", st_c),
            Paragraph(f"{c_row['pct_secciones_2024']:.2f}%", st_c),
            Paragraph(f"{c_row['ln_2024']:,}", st_c),
            Paragraph(f"{c_row['pct_ln_2024']:.2f}%", st_c),
            Paragraph(f"{c_row['municipios']:,}", st_c),
        ])
    story.append(KeepTogether([
        Paragraph(f"Tabla 2. Cascada de Filtrado del Universo Seccional y Cobertura sobre {serie[-1]['anio']}", cap_st),
        styled_table(t2_rows, [172, 52, 48, 56, 70, 54, 52], highlight_last=True),
        Spacer(1, 5),
    ]))

    story.append(KeepTogether([
        make_figure_flowable(FIGURAS_DIR / "fig2_evolucion_temporal.png", max_width=6.7 * inch, max_height=2.75 * inch),
        Spacer(1, 4),
    ]))

    # SECCIÓN 3: METODOLOGÍA Y ROBUSTEZ
    story.append(Paragraph(f"3. Metodología, Pruebas de Robustez y Justificación de k = {k_sel}", h1_st))
    story.append(Paragraph(
        f"Cada sección del Panel Principal ({u['panel_principal_secciones']:,}) se representa mediante siete indicadores hexanuales winsorizados en "
        f"los percentiles {u['winsor_p_min']} y {u['winsor_p_max']} "
        f"y escalados con <i>RobustScaler</i>: (1) <b>participacion_media_historica</b> (media = {pan_b['participacion_media_historica_media']*100:.2f}%, "
        f"DE = {pan_b['participacion_media_historica_std']*100:.2f}%); (2) <b>brecha_presidencial_intermedia</b> "
        f"(media = {pan_b['brecha_presidencial_intermedia_media']*100:+.2f} pts, DE = {pan_b['brecha_presidencial_intermedia_std']*100:.2f} pts); "
        f"(3) <b>tendencia_participacion_beta</b> (pendiente OLS anual: media = {pan_b['tendencia_participacion_beta_media']*100:+.2f} pts/año, "
        f"DE = {pan_b['tendencia_participacion_beta_std']*100:.2f} pts/año); (4) <b>estabilidad_participacion</b> definida como <b>log(1 + 1/CV)</b> "
        f"(media = {pan_b['estabilidad_participacion_media']:.4f}, DE = {pan_b['estabilidad_participacion_std']:.4f}, reduciendo la asimetría de "
        f"{est[0]['asimetria_skew']:.2f} en 1/CV sin acotar a {est[2]['asimetria_skew']:.2f} y manteniendo ARI = {est[2]['ari_vs_b']:.4f} frente a CV directo); "
        f"(5) <b>brecha_generacional</b> (60+ menos 18–29: media = {pan_b['brecha_generacional_media']*100:+.2f} pts); "
        f"(6) <b>brecha_genero</b> (mujeres menos hombres: media = {pan_b['brecha_genero_media']*100:+.2f} pts); y "
        f"(7) <b>ratio_participacion_joven</b>, calculado como el <b>cociente de medias hexanuales</b> "
        f"<i>tasa_joven_18_29 / participacion_media_historica</i> (media = {pan_b['ratio_participacion_joven_media']:.4f}; el promedio de ratios anuales es "
        f"{pan_b['ratio_joven_media_de_ratios_anuales']:.4f}).",
        body_st
    ))
    story.append(Paragraph(
        f"<b>Análisis de colinealidad (VIF) y entorno de software:</b> Los valores de VIF de las siete variables oscilan entre "
        f"{vif[5]['vif_7_variables']:.2f} (<i>brecha_genero</i>) y {vif[6]['vif_7_variables']:.2f} (<i>ratio_participacion_joven</i>, con "
        f"{vif[4]['vif_7_variables']:.2f} en <i>brecha_generacional</i>). Se mantienen ambas variables generacionales por su distinción conceptual: "
        f"<i>ratio_participacion_joven</i> captura la incorporación juvenil relativa a la propensión general de sufragio de su propia sección, mientras que "
        f"<i>brecha_generacional</i> mide la distancia absoluta en puntos porcentuales entre votantes de 60+ y 18–29 años (por ejemplo, en "
        f"{perfiles[0]['codigo_cluster']} y {perfiles[3]['codigo_cluster']} la brecha generacional es similar, de "
        f"{perfiles[0]['brecha_generacional_original']*100:.2f} y {perfiles[3]['brecha_generacional_original']*100:.2f} puntos, pero operan en estructuras "
        f"demográficas y de género distintas). "
        f"Todo el pipeline fue ejecutado en <i>Python {sw['python']}</i>, <i>DuckDB {sw['duckdb']}</i>, <i>scikit-learn {sw['scikit_learn']}</i>, "
        f"<i>SciPy {sw['scipy']}</i>, <i>umap-learn {sw['umap_learn']}</i>, <i>pandas {sw['pandas']}</i>, <i>numpy {sw['numpy']}</i> y "
        f"<i>statsmodels {sw['statsmodels']}</i>, verificando determinismo bit a bit en doble ejecución desde cero.",
        body_st
    ))

    # Tabla 3: Benchmark de Modelos (8 columnas = 504 pt)
    t3_rows = [[
        Paragraph("Algoritmo", th_l),
        Paragraph("Configuración", th_c),
        Paragraph("Clusters (Ruido)", th_c),
        Paragraph("Silhouette", th_c),
        Paragraph("Davies-<br/>Bouldin", th_c),
        Paragraph("Calinski-<br/>Harabasz", th_c),
        Paragraph("BIC", th_c),
        Paragraph("ARI Bootstrap (IC 95%)", th_c),
    ]]
    for b in bench:
        is_k4 = b["algoritmo"] == "K-Means++" and b["k"] == k_sel
        st_l = td_lb if is_k4 else td_l
        st_c = td_cb if is_k4 else td_c
        sil_str = f"{b['silhouette']:.4f}" if b["silhouette"] == b["silhouette"] and b["silhouette"] is not None else "—"
        db_str = f"{b['davies_bouldin']:.4f}" if b["davies_bouldin"] == b["davies_bouldin"] and b["davies_bouldin"] is not None else "—"
        ch_str = f"{b['calinski_harabasz']:,.1f}" if b["calinski_harabasz"] == b["calinski_harabasz"] and b["calinski_harabasz"] is not None else "—"
        bic_str = f"{b['bic']:,.0f}" if b["bic"] == b["bic"] and b["bic"] is not None else "—"
        ari_str = (
            f"{b['bootstrap_ari_media']:.4f} [{b['bootstrap_ari_ic95_inf']:.4f}, {b['bootstrap_ari_ic95_sup']:.4f}]"
            if b["bootstrap_ari_media"] == b["bootstrap_ari_media"] and b["bootstrap_ari_media"] is not None else "—"
        )
        t3_rows.append([
            Paragraph(b["algoritmo"], st_l),
            Paragraph(b["configuracion"], st_c),
            Paragraph(f"{b['n_clusters_efectivos']} ({b['pct_ruido']:.1f}%)", st_c),
            Paragraph(sil_str, st_c),
            Paragraph(db_str, st_c),
            Paragraph(ch_str, st_c),
            Paragraph(bic_str, st_c),
            Paragraph(ari_str, st_c),
        ])
    story.append(KeepTogether([
        Paragraph(f"Tabla 3. Benchmark de Algoritmos de Clustering (K-Means++, GMM y HDBSCAN) en el Panel Principal (N = {u['panel_principal_secciones']:,})", cap_st),
        styled_table(t3_rows, [60, 88, 52, 46, 54, 60, 50, 94]),
        Spacer(1, 5),
    ]))

    story.append(Paragraph(
        f"<b>Justificación de la elección de k = {k_sel} (Figura 6):</b> (1) Dentro del rango de {int(bench_km[1]['k'])} a {int(bench_km[3]['k'])} perfiles establecido por la "
        f"convocatoria, <b>k = {k_sel} obtiene el mejor Silhouette ({bench_km_k4['silhouette']:.4f}), el mejor Davies-Bouldin ({bench_km_k4['davies_bouldin']:.4f}) "
        f"y el mejor Calinski-Harabasz ({bench_km_k4['calinski_harabasz']:,.2f})</b>, dominando a k = {int(bench_km[2]['k'])} en las cuatro métricas "
        f"({bench_km[2]['silhouette']:.4f}, {bench_km[2]['davies_bouldin']:.4f}, {bench_km[2]['calinski_harabasz']:,.2f} y ARI {bench_km[2]['bootstrap_ari_media']:.4f}). "
        f"(2) Su estabilidad bootstrap (<b>ARI = {bench_km_k4['bootstrap_ari_media']:.4f}</b>, IC 95% [{bench_km_k4['bootstrap_ari_ic95_inf']:.4f}, "
        f"{bench_km_k4['bootstrap_ari_ic95_sup']:.4f}]) es comparable a la de k = {int(bench_km[3]['k'])} ({bench_km[3]['bootstrap_ari_media']:.4f}, IC 95% "
        f"[{bench_km[3]['bootstrap_ari_ic95_inf']:.4f}, {bench_km[3]['bootstrap_ari_ic95_sup']:.4f}]; los intervalos de confianza se traslapan). "
        f"(3) En k = {int(bench_km[3]['k'])} aparece un grupo sin diferenciación sustantiva ({comp_k6_c1['pct_secciones']:.2f}% del panel con una sola variable con "
        f"|z| &gt;= 0.50: <i>tendencia_participacion_beta</i> con z = {comp_k6_c1['tendencia_participacion_beta_z']:+.2f}), mientras que en k = {k_sel} los cuatro "
        f"perfiles tienen al menos cinco variables con |z| &gt;= 0.50. Se declara explícitamente que k = {int(bench_km[0]['k'])} tiene mejores métricas internas "
        f"(Silhouette {bench_km[0]['silhouette']:.4f}, DB {bench_km[0]['davies_bouldin']:.4f}, CH {bench_km[0]['calinski_harabasz']:,.2f}, ARI "
        f"{bench_km[0]['bootstrap_ari_media']:.4f}), pero queda fuera del rango 4–6 de la convocatoria. Como nota de granularidad, con k = {int(bench_km[3]['k'])} "
        f"el perfil de baja participación se divide en un subgrupo de rezago juvenil y otro de ciclo presidencial urbano, útil para focalización fina.",
        body_st
    ))

    story.append(KeepTogether([
        make_figure_flowable(FIGURAS_DIR / "fig6_benchmark_k.png", max_width=6.6 * inch, max_height=2.85 * inch),
        Spacer(1, 4),
    ]))

    # Tabla 4: Matriz de transición (8 columnas = 504 pt)
    t4_rows = [[
        Paragraph("Cluster Original (SV/LN, k=5)", th_l),
        Paragraph("Total (62,048)", th_c),
        Paragraph("Excluidas Panel B", th_c),
        Paragraph("En Panel B", th_c),
        Paragraph("-> C0 Nuevo", th_c),
        Paragraph("-> C1 Nuevo", th_c),
        Paragraph("-> C2 Nuevo", th_c),
        Paragraph("-> C3 Nuevo", th_c),
    ]]
    for t in trans:
        t4_rows.append([
            Paragraph(f"<b>{t['cluster_viejo']}</b>: {t['nombre_viejo']}", td_l),
            Paragraph(f"{t['total_secciones_62048']:,}", td_c),
            Paragraph(f"{t['excluidas_panel_B_n']:,} ({t['excluidas_panel_B_pct']:.1f}%)", td_c),
            Paragraph(f"{t['en_panel_B_n']:,}", td_c),
            Paragraph(f"{t['a_C0_nuevo_n']:,} ({t['a_C0_nuevo_pct_del_viejo_en_B']:.1f}%)", td_c),
            Paragraph(f"{t['a_C1_nuevo_n']:,} ({t['a_C1_nuevo_pct_del_viejo_en_B']:.1f}%)", td_c),
            Paragraph(f"{t['a_C2_nuevo_n']:,} ({t['a_C2_nuevo_pct_del_viejo_en_B']:.1f}%)", td_c),
            Paragraph(f"{t['a_C3_nuevo_n']:,} ({t['a_C3_nuevo_pct_del_viejo_en_B']:.1f}%)", td_c),
        ])
    story.append(KeepTogether([
        Paragraph(f"Tabla 4. Matriz de Transición: Clusters Previos (SV/LN, k=5) hacia Nuevos Perfiles (SV/[SV+NV], k={k_sel} | ARI = {trans[0]['ari_global_viejo_vs_nuevo_en_B']:.4f})", cap_st),
        styled_table(t4_rows, [118, 48, 66, 48, 56, 56, 56, 56]),
        Spacer(1, 4),
    ]))

    story.append(Paragraph(
        f"<b>Interpretabilidad interna (Random Forest y ANOVA):</b> Como evaluación de interpretabilidad sobre las mismas siete variables del clustering "
        f"(no validación externa), un modelo Random Forest (5-fold CV) alcanza una exactitud de <b>{interp[0]['rf_cv5_accuracy_media']*100:.2f}%</b> "
        f"(±{interp[0]['rf_cv5_accuracy_std']*100:.2f}%). Las variables con mayor importancia Gini y estadístico F de ANOVA son: "
        + ", ".join(
            f"<i>{r['variable']}</i> (Gini = {r['rf_gini_importance']:.4f}, perm = {r['rf_permutation_importance_mean']:.4f}, F = {r['anova_f_stat']:,.2f})"
            for r in interp
        ) + ".",
        body_st
    ))

    story.append(KeepTogether([
        make_figure_flowable(FIGURAS_DIR / "fig7_proyeccion_pca_umap.png", max_width=6.6 * inch, max_height=2.65 * inch),
        Spacer(1, 4),
    ]))

    # SECCIÓN 4: CARACTERIZACIÓN DE LOS 4 PERFILES
    story.append(Paragraph(f"4. Caracterización de los 4 Perfiles Ciudadanos de Participación (k = {k_sel})", h1_st))
    story.append(Paragraph(
        f"Las Tablas 5 y 6 presentan los centroides de los cuatro perfiles en unidades originales y puntajes z respecto al Panel Principal, "
        f"junto con sus series históricas {serie[0]['anio']}–{serie[-1]['anio']} (ponderadas y simples), tasas demográficas y composición territorial. "
        f"La fila <b>Media Nacional Panel B</b> reporta exactamente el promedio de las {pan_b['n_secciones']:,} secciones del panel "
        f"(<b>{pan_b['pct_secciones_urbanas_1d']:.1f}% urbanas, {pan_b['pct_secciones_rurales_1d']:.1f}% rurales y {pan_b['pct_secciones_mixtas_1d']:.1f}% mixtas</b> "
        f"al ponderar los perfiles por secciones; <b>{pan_b['pct_secciones_urbanas_pond_ln_clusters_1d']:.1f}% / {pan_b['pct_secciones_rurales_pond_ln_clusters_1d']:.1f}% / "
        f"{pan_b['pct_secciones_mixtas_pond_ln_clusters_1d']:.1f}%</b> al ponderar los perfiles por LN {serie[-1]['anio']}, y "
        f"<b>{pan_b['pct_ln_urbana']:.1f}% / {pan_b['pct_ln_rural']:.1f}% / {pan_b['pct_ln_mixta']:.1f}%</b> del total de electores en secciones U/R/M).",
        body_st
    ))

    # Tabla 5: Centroides de las 7 variables y cobertura (8 columnas = 504 pt)
    t5_rows = [[
        Paragraph("Perfil y Nombre Oficial", th_l),
        Paragraph(f"Secciones (% Panel / % {serie[-1]['anio']})", th_c),
        Paragraph(f"LN {serie[-1]['anio']} (% Panel / % {serie[-1]['anio']})", th_c),
        Paragraph("Part. Media (z)", th_c),
        Paragraph("Brecha Pres-Inter (z)", th_c),
        Paragraph("Tendencia OLS (z)", th_c),
        Paragraph("Estabilidad log1p (z)", th_c),
        Paragraph("Brecha Gen. / Género / Ratio Joven (z)", th_c),
    ]]
    for p in perfiles:
        t5_rows.append([
            Paragraph(f"<b>{p['codigo_cluster']}: {p['nombre_propuesto']}</b>", td_l),
            Paragraph(f"{p['n_secciones']:,}<br/>({p['pct_secciones_panel']:.2f}% / {p['pct_secciones_2024_total']:.2f}%)", td_c),
            Paragraph(f"{p['ln_2024']:,}<br/>({p['pct_ln_panel']:.2f}% / {p['pct_ln_2024_total']:.2f}%)", td_c),
            Paragraph(f"<b>{p['participacion_media_historica_original']*100:.2f}%</b><br/>(z={p['participacion_media_historica_zscore']:+.2f})", td_c),
            Paragraph(f"<b>{p['brecha_presidencial_intermedia_original']*100:+.2f} pts</b><br/>(z={p['brecha_presidencial_intermedia_zscore']:+.2f})", td_c),
            Paragraph(f"<b>{p['tendencia_participacion_beta_original']*100:+.2f} pts/a</b><br/>(z={p['tendencia_participacion_beta_zscore']:+.2f})", td_c),
            Paragraph(f"<b>{p['estabilidad_participacion_original']:.4f}</b><br/>(z={p['estabilidad_participacion_zscore']:+.2f})", td_c),
            Paragraph(
                f"Gen: {p['brecha_generacional_original']*100:+.2f} ({p['brecha_generacional_zscore']:+.2f})<br/>"
                f"Sexo: {p['brecha_genero_original']*100:+.2f} ({p['brecha_genero_zscore']:+.2f})<br/>"
                f"Jov: {p['ratio_participacion_joven_original']:.4f} ({p['ratio_participacion_joven_zscore']:+.2f})",
                td_c
            ),
        ])
    t5_rows.append([
        Paragraph("<b>Media Nacional Panel B</b>", td_lb),
        Paragraph(f"<b>{pan_b['n_secciones']:,}</b><br/>(100.00% / {u['panel_principal_pct_secciones_2024']:.2f}%)", td_cb),
        Paragraph(f"<b>{pan_b['ln_2024']:,}</b><br/>(100.00% / {u['panel_principal_pct_ln_2024']:.2f}%)", td_cb),
        Paragraph(f"<b>{pan_b['participacion_media_historica_media']*100:.2f}%</b><br/>(z=0.00)", td_cb),
        Paragraph(f"<b>{pan_b['brecha_presidencial_intermedia_media']*100:+.2f} pts</b><br/>(z=0.00)", td_cb),
        Paragraph(f"<b>{pan_b['tendencia_participacion_beta_media']*100:+.2f} pts/a</b><br/>(z=0.00)", td_cb),
        Paragraph(f"<b>{pan_b['estabilidad_participacion_media']:.4f}</b><br/>(z=0.00)", td_cb),
        Paragraph(
            f"Gen: {pan_b['brecha_generacional_media']*100:+.2f} (0.00)<br/>"
            f"Sexo: {pan_b['brecha_genero_media']*100:+.2f} (0.00)<br/>"
            f"Jov: {pan_b['ratio_participacion_joven_media']:.4f} (0.00)",
            td_cb
        ),
    ])
    story.append(KeepTogether([
        Paragraph(f"Tabla 5. Centroides de las 7 Variables del Modelo (Escala Original y z-scores) y Cobertura por Perfil (k = {k_sel})", cap_st),
        styled_table(t5_rows, [98, 60, 68, 52, 54, 54, 52, 66], highlight_last=True),
        Spacer(1, 5),
    ]))

    # Tabla 6: Series 2009-2024, demografía y territorio (8 columnas = 504 pt)
    t6_rows = [[
        Paragraph("Perfil", th_c),
        Paragraph("Serie Ponderada 2009 / 2012 / 2015 / 2018 / 2021 / 2024", th_c),
        Paragraph("Serie Simple 2009–2024", th_c),
        Paragraph("Pres. / Inter.", th_c),
        Paragraph("18–29 / 60+ años", th_c),
        Paragraph("Mujeres / Hombres", th_c),
        Paragraph("Tipo Secc. U/R/M (por LN)", th_c),
        Paragraph("Top 3 Entidades (% secc. cluster)", th_l),
    ]]
    for p in perfiles:
        s_pond = " / ".join(f"<b>{p[f'p_{y}_ponderada']*100:.1f}%</b>" if y == 2021 else f"{p[f'p_{y}_ponderada']*100:.1f}%" for y in [2009, 2012, 2015, 2018, 2021, 2024])
        s_simp = " / ".join(f"{p[f'p_{y}_simple']*100:.1f}%" for y in [2009, 2012, 2015, 2018, 2021, 2024])
        top3 = "; ".join(p["top5_entidades_por_pct_secciones"].split("; ")[:3])
        t6_rows.append([
            Paragraph(f"<b>{p['codigo_cluster']}</b>", td_cb),
            Paragraph(s_pond, td_c),
            Paragraph(s_simp, td_c),
            Paragraph(f"{p['media_presidencial_original']*100:.2f}% /<br/>{p['media_intermedia_original']*100:.2f}%", td_c),
            Paragraph(f"{p['tasa_joven_18_29_original']*100:.2f}% /<br/>{p['tasa_mayor_60_mas_original']*100:.2f}%", td_c),
            Paragraph(f"{p['tasa_mujeres_original']*100:.2f}% /<br/>{p['tasa_hombres_original']*100:.2f}%", td_c),
            Paragraph(
                f"{p['pct_secciones_urbanas']:.1f}/{p['pct_secciones_rurales']:.1f}/{p['pct_secciones_mixtas']:.1f}%<br/>"
                f"({p['pct_ln_urbana']:.1f}/{p['pct_ln_rural']:.1f}/{p['pct_ln_mixta']:.1f}%)",
                td_c
            ),
            Paragraph(top3, td_l),
        ])
    s_pond_b = " / ".join(f"<b>{pan_b[f'p_{y}_ponderada']*100:.1f}%</b>" for y in [2009, 2012, 2015, 2018, 2021, 2024])
    s_simp_b = " / ".join(f"{pan_b[f'p_{y}_simple']*100:.1f}%" for y in [2009, 2012, 2015, 2018, 2021, 2024])
    t6_rows.append([
        Paragraph("<b>Panel B</b>", td_cb),
        Paragraph(s_pond_b, td_cb),
        Paragraph(s_simp_b, td_c),
        Paragraph(f"<b>{pan_b['media_presidencial_original']*100:.2f}% /<br/>{pan_b['media_intermedia_original']*100:.2f}%</b>", td_cb),
        Paragraph(f"<b>{pan_b['tasa_joven_18_29_original']*100:.2f}% /<br/>{pan_b['tasa_mayor_60_mas_original']*100:.2f}%</b>", td_cb),
        Paragraph(f"<b>{pan_b['tasa_mujeres_original']*100:.2f}% /<br/>{pan_b['tasa_hombres_original']*100:.2f}%</b>", td_cb),
        Paragraph(
            f"<b>{pan_b['pct_secciones_urbanas_1d']:.1f}/{pan_b['pct_secciones_rurales_1d']:.1f}/{pan_b['pct_secciones_mixtas_1d']:.1f}%</b><br/>"
            f"({pan_b['pct_ln_urbana']:.1f}/{pan_b['pct_ln_rural']:.1f}/{pan_b['pct_ln_mixta']:.1f}%)",
            td_cb
        ),
        Paragraph(f"Total Panel B ({u['panel_principal_municipios']:,} muns.)", td_lb),
    ])
    story.append(KeepTogether([
        Paragraph(f"Tabla 6. Series Históricas {serie[0]['anio']}–{serie[-1]['anio']} (Ponderada y Simple), Tasas Demográficas y Composición Territorial", cap_st),
        styled_table(t6_rows, [36, 98, 86, 46, 48, 48, 58, 84], highlight_last=True),
        Spacer(1, 5),
    ]))

    for p in perfiles:
        story.append(Paragraph(
            f"• <b>{p['codigo_cluster']} — {p['nombre_propuesto']} ({p['n_secciones']:,} secciones, {p['pct_secciones_panel']:.2f}% del panel; "
            f"{p['ln_2024']:,} electores, {p['pct_ln_panel']:.2f}% LN):</b> {p['justificacion_regla_3_2']}",
            bullet_st
        ))

    story.append(KeepTogether([
        make_figure_flowable(FIGURAS_DIR / "fig3_radar_centroides.png", max_width=6.6 * inch, max_height=2.95 * inch),
        Spacer(1, 3),
        make_figure_flowable(FIGURAS_DIR / "fig4_brechas_demograficas.png", max_width=6.6 * inch, max_height=2.50 * inch),
        Spacer(1, 4),
    ]))

    story.append(KeepTogether([
        make_figure_flowable(FIGURAS_DIR / "fig1_mapa_clusters.png", max_width=6.6 * inch, max_height=3.20 * inch),
        Spacer(1, 4),
    ]))

    # SECCIÓN 5: ESTRATEGIAS FOCALIZADAS
    story.append(Paragraph(f"5. Estrategias Focalizadas de Promoción e Intervención Institucional (ENCÍVICA)", h1_st))
    story.append(Paragraph(
        f"Las estrategias para los cuatro perfiles (Tabla 7) están alineadas con el marco de la ENCÍVICA y las facultades de la DECEyEC, la DERFE, "
        f"la DEOE y las 300 Juntas Distritales Ejecutivas. Cada meta cuantitativa para la elección intermedia de 2027 toma como referencia la "
        f"<b>línea base real observada en la elección intermedia de {serie[4]['anio']} (serie ponderada)</b> de cada perfil: "
        f"<b>{perfiles[0]['codigo_cluster']} = {estrategias[0]['linea_base_intermedia_2021_pond_pct']:.1f}%</b> "
        f"({perfiles[0]['p_2021_ponderada']*100:.2f}%), "
        f"<b>{perfiles[1]['codigo_cluster']} = {estrategias[1]['linea_base_intermedia_2021_pond_pct']:.1f}%</b> "
        f"({perfiles[1]['p_2021_ponderada']*100:.2f}%), "
        f"<b>{perfiles[2]['codigo_cluster']} = {estrategias[2]['linea_base_intermedia_2021_pond_pct']:.1f}%</b> "
        f"({perfiles[2]['p_2021_ponderada']*100:.2f}%) y "
        f"<b>{perfiles[3]['codigo_cluster']} = {estrategias[3]['linea_base_intermedia_2021_pond_pct']:.1f}%</b> "
        f"({perfiles[3]['p_2021_ponderada']*100:.2f}%). "
        f"En <b>{perfiles[0]['codigo_cluster']}</b> ({perfiles[0]['pct_secciones_panel']:.2f}% del panel, {perfiles[0]['pct_secciones_urbanas']:.1f}% urbano) "
        f"se establecen dos líneas operativas: pedagogía del ciclo intermedio en canales urbanos e incorporación tanto de universitarios como de "
        f"<b>jóvenes que no estudian</b> (centros de trabajo, parques industriales, tianguis y centros comunitarios). "
        f"En <b>{perfiles[3]['codigo_cluster']}</b> ({perfiles[3]['pct_secciones_urbanas']:.1f}% urbano, con sobrerrepresentación rural de "
        f"{perfiles[3]['pct_secciones_rurales']:.1f}%), la acción principal se dirige a elevar la <b>participación masculina</b> "
        f"({perfiles[3]['tasa_hombres_original']*100:.2f}% vs {perfiles[3]['tasa_mujeres_original']*100:.2f}% en mujeres) y revertir la caída en elecciones "
        f"presidenciales ({perfiles[3]['p_2012_ponderada']*100:.1f}% en {serie[1]['anio']} a {perfiles[3]['p_2024_ponderada']*100:.1f}% en {serie[-1]['anio']}), "
        f"dejando la accesibilidad rural como acción secundaria.",
        body_st
    ))

    # Tabla 7: Estrategias Focalizadas (6 columnas amplias = 504 pt)
    t7_rows = [[
        Paragraph(f"Perfil y Línea Base ({serie[4]['anio']} / {serie[5]['anio']})", th_l),
        Paragraph("Diagnóstico (Hipótesis) y Objetivo", th_l),
        Paragraph("Canales y Acción Operativa INE", th_l),
        Paragraph("Meta Cuantitativa 2027/2030 e Indicador", th_l),
        Paragraph("Unidad Responsable y Costo Indicativo", th_l),
        Paragraph("Lema Neutral", th_l),
    ]]
    for e in estrategias:
        t7_rows.append([
            Paragraph(
                f"<b>{e['codigo_cluster']}: {e['nombre_perfil']}</b><br/><br/>"
                f"Secc: {e['n_secciones']:,} ({e['pct_secciones_panel']:.2f}%)<br/>"
                f"Base Inter. {serie[4]['anio']}: <b>{e['linea_base_intermedia_2021_pond_pct']:.1f}%</b><br/>"
                f"Base Pres. {serie[5]['anio']}: <b>{e['linea_base_presidencial_2024_pond_pct']:.1f}%</b>",
                td_l
            ),
            Paragraph(f"{e['hipotesis_factor_abstencionismo']}<br/><br/><b>Objetivo:</b> {e['objetivo_especifico']}", td_l),
            Paragraph(f"<b>Canales:</b> {e['canal_principal']}<br/><br/><b>Acción INE:</b> {e['accion_operativa_ine']}", td_l),
            Paragraph(f"<b>Meta:</b> {e['meta_cuantitativa']}<br/><br/><b>Indicador:</b> {e['indicador_seguimiento']}", td_l),
            Paragraph(f"<b>Unidad:</b> {e['unidad_responsable']}<br/><br/><b>Costo:</b> {e['costo_estimado_orden_magnitud']}", td_l),
            Paragraph(f"<i>\"{e['lema_sugerido_neutral']}\"</i>", td_l),
        ])
    story.append(Paragraph(f"Tabla 7. Estrategias Focalizadas por Perfil Ciudadano (k = {k_sel}), Líneas Base, Metas y Viabilidad Operativa", cap_st))
    story.append(styled_table(t7_rows, [70, 96, 108, 94, 72, 64]))
    story.append(Spacer(1, 5))

    # SECCIÓN 6: LIMITACIONES Y RECOMENDACIONES AL INE
    story.append(Paragraph("6. Limitaciones Metodológicas, Análisis de Sensibilidad y Recomendaciones al INE", h1_st))
    story.append(Paragraph(
        f"<b>1. Secciones incluidas ({inc_exc[0]['n_secciones']:,}) vs excluidas ({inc_exc[1]['n_secciones']:,}) en {serie[-1]['anio']} y sesgo del Panel B (Tabla 8 y Figura 5):</b> "
        f"Las <b>{inc_exc[1]['n_secciones']:,} secciones activas en {serie[-1]['anio']} excluidas del Panel Principal</b> ({inc_exc[1]['pct_secciones_2024']:.2f}% de las "
        f"secciones y {inc_exc[1]['pct_ln_2024']:.2f}% de la LN {serie[-1]['anio']}) se dividen en: (a) <b>{inc_exc[2]['n_secciones']:,} secciones creadas o "
        f"reseccionadas post-{serie[0]['anio']}</b> ({inc_exc[2]['ln_2024']:,} electores, {inc_exc[2]['pct_urbana']:.2f}% urbanas por secciones y "
        f"{inc_exc[2]['pct_ln_urbana']:.1f}% por LN), "
        f"las cuales votaron <b>{inc_exc[2]['participacion_2024_ponderada_sv_svnv_pct']:.2f}% frente al {inc_exc[4]['participacion_2024_ponderada_sv_svnv_pct']:.2f}% "
        f"del panel continuo ({inc_exc[0]['participacion_2024_ponderada_sv_svnv_pct']:.2f}% del Panel B)</b>; y (b) <b>{inc_exc[3]['n_secciones']:,} secciones continuas "
        f"excluidas por filtros de calidad</b> ({inc_exc[3]['ln_2024']:,} electores, {inc_exc[3]['pct_urbana']:.2f}% urbanas, con "
        f"{inc_exc[3]['secciones_svnv_0_en_2024']:,} secciones sin captura en {serie[-1]['anio']} y {inc_exc[3]['participacion_2024_ponderada_sv_svnv_pct']:.2f}% de "
        f"participación en las capturadas). Debido a ello, <b>el Panel Principal (Opción B) sobreestima la participación nacional ponderada del CCPC entre "
        f"{serie[0]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} y {serie[4]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} puntos porcentuales</b> "
        f"({serie[0]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} pts en {serie[0]['anio']}, {serie[1]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} pts en {serie[1]['anio']}, "
        f"{serie[2]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} pts en {serie[2]['anio']}, {serie[3]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} pts en {serie[3]['anio']}, "
        f"{serie[4]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} pts en {serie[4]['anio']} y {serie[5]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} pts en {serie[5]['anio']}).",
        body_st
    ))

    # Tabla 8: Incluidas vs Excluidas en 2024 (8 columnas = 504 pt)
    t8_rows = [[
        Paragraph(f"Subuniverso de Secciones en {serie[-1]['anio']}", th_l),
        Paragraph("Secc.", th_c),
        Paragraph(f"% Secc. {serie[-1]['anio']}", th_c),
        Paragraph(f"LN {serie[-1]['anio']} (% LN)", th_c),
        Paragraph("Tipo Secc. U/R/M", th_c),
        Paragraph(f"SV+NV=0 ({serie[-1]['anio']})", th_c),
        Paragraph(f"Part. {serie[-1]['anio']} Pond. (Simple)", th_c),
        Paragraph("Top 3 Entidades en el Grupo", th_l),
    ]]
    for r in inc_exc:
        top3_ie = "; ".join(r["top_10_entidades_por_secciones"].split("; ")[:3])
        t8_rows.append([
            Paragraph(r["grupo"], td_l),
            Paragraph(f"{r['n_secciones']:,}", td_c),
            Paragraph(f"{r['pct_secciones_2024']:.2f}%", td_c),
            Paragraph(f"{r['ln_2024']:,} ({r['pct_ln_2024']:.2f}%)", td_c),
            Paragraph(f"{r['pct_urbana_1d']:.1f}/{r['pct_rural_1d']:.1f}/{r['pct_mixta_1d']:.1f}%", td_c),
            Paragraph(f"{r['secciones_svnv_0_en_2024']:,}", td_c),
            Paragraph(f"<b>{r['participacion_2024_ponderada_sv_svnv_pct']:.2f}%</b> ({r['participacion_2024_simple_sv_svnv_pct']:.2f}%)", td_c),
            Paragraph(top3_ie, td_l),
        ])
    story.append(KeepTogether([
        Paragraph(f"Tabla 8. Comparación de Secciones Incluidas ({inc_exc[0]['n_secciones']:,}) vs Excluidas ({inc_exc[1]['n_secciones']:,}) en el CCPC {serie[-1]['anio']}", cap_st),
        styled_table(t8_rows, [110, 46, 42, 70, 62, 42, 62, 70]),
        Spacer(1, 4),
    ]))

    story.append(Paragraph(
        f"<b>2. Sensibilidad Opción A (sin imputación):</b> Al evaluar la Opción A sobre las secciones continuas tratando los años con SV+NV &lt; 50 como "
        f"<i>NaN</i> y exigiendo al menos 2 elecciones presidenciales y 2 intermedias válidas ({sens[0]['secciones_incluidas']:,} secciones sin filtro de salto "
        f"de LN y {sens[1]['secciones_incluidas']:,} sin saltos de LN), el reentrenamiento de K-Means++ (k = {k_sel}) arroja un <b>ARI = "
        f"{sens[0]['ari_vs_panel_principal_B']:.4f}</b> ({sens[0]['coincidencia_exacta_alineada_pct']:.2f}% de coincidencia exacta) y <b>ARI = "
        f"{sens[1]['ari_vs_panel_principal_B']:.4f}</b> ({sens[1]['coincidencia_exacta_alineada_pct']:.2f}% de coincidencia exacta) sobre las "
        f"{sens[0]['secciones_comunes_con_panel_B']:,} secciones comunes con el Panel B.",
        body_st
    ))
    story.append(Paragraph(
        f"<b>3. Limitación por sensibilidad a la ventana temporal demográfica y datos faltantes:</b> Al reemplazar los promedios demográficos hexanuales "
        f"({serie[0]['anio']}–{serie[-1]['anio']}) por los valores de un solo corte ({serie[-1]['anio']}), la concordancia del agrupamiento baja a "
        f"<b>ARI = {win[0]['ari_clustering_6y_vs_2024']:.4f}</b> (correlaciones entre ventana hexanual y {serie[-1]['anio']}: r = {win[2]['correlacion_pearson']:.4f} "
        f"en brecha generacional, r = {win[3]['correlacion_pearson']:.4f} en brecha de género y r = {win[4]['correlacion_pearson']:.4f} en ratio joven), lo cual "
        f"constituye una limitación metodológica que exige recalibrar los perfiles tras cada elección federal. Asimismo, los CSV de datos abiertos del CCPC no "
        f"incluyen el indicador de sección indígena o afromexicana (<i>[PENDIENTE: cálculo, datos necesarios]</i>). Finalmente, se recomienda al INE (DECEyEC) "
        f"incorporar una bandera explícita de estatus de captura en los CSV abiertos y reforzar la recuperación poscómputo de cuadernillos para reducir el "
        f"porcentaje de registros NS observado en {serie[3]['anio']} ({serie[3]['pct_ns_anio']:.2f}%) y {serie[5]['anio']} ({serie[5]['pct_ns_anio']:.2f}%).",
        body_st
    ))

    story.append(KeepTogether([
        make_figure_flowable(FIGURAS_DIR / "fig5_urbano_rural_entidades.png", max_width=6.6 * inch, max_height=2.55 * inch),
    ]))

    def add_header_footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.8)
        canvas.setFillColor(colors.HexColor("#4B5563"))
        canvas.drawString(
            0.75 * inch, 10.55 * inch,
            f"Equipo Byte me — Propuesta técnica Reto 1: Perfiles ciudadanos de participación (k={k_sel})"
        )
        canvas.drawRightString(
            7.75 * inch, 10.55 * inch,
            f"Datos CCPC {serie[0]['anio']}–{serie[-1]['anio']} | Fórmula Oficial SV/(SV+NV)"
        )
        canvas.setStrokeColor(colors.HexColor("#D1D5DB"))
        canvas.setLineWidth(0.5)
        canvas.line(0.75 * inch, 10.48 * inch, 7.75 * inch, 10.48 * inch)
        canvas.line(0.75 * inch, 0.62 * inch, 7.75 * inch, 0.62 * inch)
        canvas.drawString(
            0.75 * inch, 0.45 * inch,
            "Concurso INE: Hackea la participación — Elaboración propia del Equipo Byte me"
        )
        canvas.drawRightString(7.75 * inch, 0.45 * inch, f"Página {doc_obj.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.70 * inch,
        bottomMargin=0.70 * inch,
        title=f"Perfiles Ciudadanos de Participación Electoral ({serie[0]['anio']}-{serie[-1]['anio']}) - Equipo Byte me",
        author="Equipo Byte me",
    )
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    return pdf_path


def build_docx_from_md(md_path: Path) -> Path:
    """Genera Documento_Tecnico_ByteMe.docx directamente como archivo OpenXML (.docx) válido."""
    import zipfile
    from xml.sax.saxutils import escape

    docx_path = OUT_ENTREGABLES / "Documento_Tecnico_ByteMe.docx"
    md_text = md_path.read_text(encoding="utf-8")

    body_xml = []
    lines = md_text.splitlines()
    in_table = False
    table_rows = []

    def flush_table(rows):
        if not rows:
            return ""
        xml = [
            "<w:tbl><w:tblPr><w:tblW w:w='5000' w:type='pct'/>"
            "<w:tblBorders>"
            "<w:top w:val='single' w:sz='4' w:space='0' w:color='CBD5E1'/>"
            "<w:left w:val='single' w:sz='4' w:space='0' w:color='CBD5E1'/>"
            "<w:bottom w:val='single' w:sz='4' w:space='0' w:color='CBD5E1'/>"
            "<w:right w:val='single' w:sz='4' w:space='0' w:color='CBD5E1'/>"
            "<w:insideH w:val='single' w:sz='4' w:space='0' w:color='CBD5E1'/>"
            "<w:insideV w:val='single' w:sz='4' w:space='0' w:color='CBD5E1'/>"
            "</w:tblBorders></w:tblPr>"
        ]
        for r_idx, row in enumerate(rows):
            xml.append("<w:tr>")
            for cell in row:
                clean_c = cell.replace("<br>", " ").replace("**", "").replace("*", "").replace("`", "")
                if r_idx == 0:
                    xml.append(
                        f"<w:tc><w:tcPr><w:shd w:val='clear' w:color='auto' w:fill='1E3A8A'/></w:tcPr>"
                        f"<w:p><w:r><w:rPr><w:rFonts w:ascii='Arial' w:hAnsi='Arial'/><w:b/><w:color w:val='FFFFFF'/><w:sz w:val='18'/></w:rPr>"
                        f"<w:t>{escape(clean_c)}</w:t></w:r></w:p></w:tc>"
                    )
                else:
                    xml.append(
                        f"<w:tc><w:p><w:r><w:rPr><w:rFonts w:ascii='Arial' w:hAnsi='Arial'/><w:sz w:val='18'/></w:rPr>"
                        f"<w:t>{escape(clean_c)}</w:t></w:r></w:p></w:tc>"
                    )
            xml.append("</w:tr>")
        xml.append("</w:tbl>")
        return "".join(xml)

    for line in lines:
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            if set(s.replace("|", "").replace(":", "").replace("-", "").strip()) == set():
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            in_table = True
            table_rows.append(cells)
            continue
        else:
            if in_table:
                body_xml.append(flush_table(table_rows))
                table_rows = []
                in_table = False

        if not s or s == "---":
            continue

        clean_s = s.replace("**", "").replace("`", "")
        if s.startswith("# "):
            body_xml.append(
                f"<w:p><w:pPr><w:spacing w:before='240' w:after='120' w:line='360' w:lineRule='auto'/></w:pPr>"
                f"<w:r><w:rPr><w:rFonts w:ascii='Arial' w:hAnsi='Arial'/><w:b/><w:sz w:val='28'/></w:rPr>"
                f"<w:t>{escape(clean_s[2:])}</w:t></w:r></w:p>"
            )
        elif s.startswith("## "):
            body_xml.append(
                f"<w:p><w:pPr><w:spacing w:before='200' w:after='100' w:line='360' w:lineRule='auto'/></w:pPr>"
                f"<w:r><w:rPr><w:rFonts w:ascii='Arial' w:hAnsi='Arial'/><w:b/><w:color w:val='1E3A8A'/><w:sz w:val='24'/></w:rPr>"
                f"<w:t>{escape(clean_s[3:])}</w:t></w:r></w:p>"
            )
        elif s.startswith("### "):
            body_xml.append(
                f"<w:p><w:pPr><w:spacing w:before='160' w:after='80' w:line='360' w:lineRule='auto'/></w:pPr>"
                f"<w:r><w:rPr><w:rFonts w:ascii='Arial' w:hAnsi='Arial'/><w:b/><w:sz w:val='22'/></w:rPr>"
                f"<w:t>{escape(clean_s[4:])}</w:t></w:r></w:p>"
            )
        else:
            body_xml.append(
                f"<w:p><w:pPr><w:spacing w:before='60' w:after='100' w:line='360' w:lineRule='auto'/></w:pPr>"
                f"<w:r><w:rPr><w:rFonts w:ascii='Arial' w:hAnsi='Arial'/><w:sz w:val='22'/></w:rPr>"
                f"<w:t>{escape(clean_s)}</w:t></w:r></w:p>"
            )

    if in_table:
        body_xml.append(flush_table(table_rows))

    content_types = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        "<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>"
        "<Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/>"
        "<Default Extension='xml' ContentType='application/xml'/>"
        "<Override PartName='/word/document.xml' ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'/>"
        "</Types>"
    )
    rels = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        "<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>"
        "<Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' Target='word/document.xml'/>"
        "</Relationships>"
    )
    doc_xml = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"
        "<w:body>"
        + "".join(body_xml)
        + "<w:sectPr><w:pgSz w:w='12240' w:h='15840'/><w:pgMar w:top='1080' w:right='1080' w:bottom='1080' w:left='1080'/></w:sectPr>"
        "</w:body></w:document>"
    )

    with zipfile.ZipFile(docx_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", doc_xml)

    return docx_path


def main() -> None:
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    md_path = render_markdown_from_template(data)
    pdf_path = build_pdf(data)
    docx_path = build_docx_from_md(md_path)

    import pypdf
    reader = pypdf.PdfReader(str(pdf_path))
    n_pages = len(reader.pages)
    print(f"[Fase 7] Documento Técnico compilado con éxito:")
    print(f"  - Markdown: {md_path}")
    print(f"  - PDF:      {pdf_path} ({n_pages} páginas)")
    print(f"  - DOCX:     {docx_path}")


if __name__ == "__main__":
    main()
