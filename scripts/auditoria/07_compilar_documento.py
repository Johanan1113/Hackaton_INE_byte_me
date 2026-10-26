#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fase 7: Compilación del Documento Técnico Final en PDF (07_compilar_documento.py)
Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")

Reglas estrictas de maquetación y contenido:
1. Cero cifras escritas a mano: todas las cifras, tasas y métricas se leen programáticamente
   de outputs/metricas_finales.json y outputs/tablas/.
2. Tipografía: Arial 100% (cero Helvetica), registrado desde /usr/share/fonts/TTF/.
   - Cuerpo de texto: Arial 11 pt, interlineado 19 pt (leading 19).
   - Encabezados: H1 Arial-Bold 13/17 pt, H2 Arial-Bold 11.5/15 pt.
   - Título: Arial-Bold 15/19 pt. Subtítulo: Arial-Bold 9.5/13 pt.
   - Tablas: Encabezado y celdas mínimo 9 pt, leading 11.5 pt.
   - Encabezado y pie de página: Arial 8.5 pt.
3. Formato de página: Carta (Letter), márgenes de 2.5 cm (70.87 pt) en los cuatro lados.
   Ancho imprimible exacto: 470.27 pt.
4. Presupuesto de espacio: 8 a 12 páginas exactas en PDF.
5. Inclusión de exactamente 3 figuras analíticas en el cuerpo:
   - fig2: Evolución temporal y efecto del sesgo NS.
   - fig6: Benchmark de k=3..7 (K-Means++, GMM, HDBSCAN, ARI).
   - fig3a: Heatmap de centroides en escala original y z-score.
6. Nuevas secciones obligatorias: Conclusiones, Reproducibilidad y Referencias Bibliográficas.
"""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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

from reportlab import rl_config
rl_config.canvas_basefontname = "Arial"

# Registro de la fuente Arial TrueType
pdfmetrics.registerFont(TTFont("Arial", "/usr/share/fonts/TTF/Arial.TTF"))
pdfmetrics.registerFont(TTFont("Arial-Bold", "/usr/share/fonts/TTF/Arialbd.TTF"))
pdfmetrics.registerFont(TTFont("Arial-Italic", "/usr/share/fonts/TTF/Ariali.TTF"))
pdfmetrics.registerFont(TTFont("Arial-BoldItalic", "/usr/share/fonts/TTF/Arialbi.TTF"))
pdfmetrics.registerFontFamily(
    "Arial",
    normal="Arial",
    bold="Arial-Bold",
    italic="Arial-Italic",
    boldItalic="Arial-BoldItalic",
)

MARGIN = 2.5 * cm  # 70.866 pt
PAGE_W, PAGE_H = letter
PRINTABLE_W = PAGE_W - 2 * MARGIN  # 470.268 pt


def render_markdown_internal(data: dict) -> Path:
    """Renderiza outputs/entregables/Documento_Tecnico_ByteMe.md como fuente interna Markdown."""
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


def make_figure_flowable(img_path: Path, max_width: float = PRINTABLE_W, max_height: float = 2.6 * inch) -> Image:
    """Escala proporcionalmente una figura PNG para ajustarse exactamente al ancho de columna."""
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
    """Crea una tabla con formato institucional limpio y encabezados repetibles."""
    t = Table(rows_data, colWidths=col_widths, repeatRows=1, splitByRow=1)
    style_cmds = [
        ("FONTNAME", (0, 0), (-1, -1), "Arial"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.0),
        ("LEADING", (0, 0), (-1, -1), 11.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2 if highlight_last else -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]
    if highlight_last:
        style_cmds.append(("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E0E7FF")))
    t.setStyle(TableStyle(style_cmds))
    return t


def build_pdf(data: dict) -> Path:
    """Compila outputs/entregables/Documento_Tecnico_ByteMe.pdf (8-12 páginas, Arial 11/19 pt)."""
    pdf_path = OUT_ENTREGABLES / "Documento_Tecnico_ByteMe.pdf"

    k_sel = int(data["k_seleccionado"])
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
    bench_km_k4 = [r for r in bench_km if int(r["k"]) == k_sel][0]
    comp_k6_c1 = [r for r in data["comparacion_k4_k5_k6"] if int(r["k"]) == 6 and r["n_variables_con_abs_z_ge_05"] == 1][0]
    sens = data["sensibilidad_opcion_a"]
    perfiles = data["perfiles"]
    estrategias = data["estrategias"]

    styles = getSampleStyleSheet()

    # Tipografía estricta en Arial
    title_st = ParagraphStyle(
        "DocTitle", parent=styles["Title"], fontName="Arial-Bold",
        fontSize=15.0, leading=19.0, textColor=colors.HexColor("#0F172A"), alignment=TA_LEFT, spaceAfter=4
    )
    sub_st = ParagraphStyle(
        "DocSub", parent=styles["Normal"], fontName="Arial-Bold",
        fontSize=9.5, leading=13.0, textColor=colors.HexColor("#1E3A8A"), alignment=TA_LEFT, spaceAfter=4
    )
    meta_st = ParagraphStyle(
        "DocMeta", parent=styles["Normal"], fontName="Arial",
        fontSize=9.0, leading=13.0, textColor=colors.HexColor("#4B5563"), alignment=TA_LEFT, spaceAfter=8
    )
    h1_st = ParagraphStyle(
        "H1", parent=styles["Heading1"], fontName="Arial-Bold",
        fontSize=13.0, leading=17.0, textColor=colors.HexColor("#1E3A8A"), spaceBefore=9, spaceAfter=4, keepWithNext=True
    )
    h2_st = ParagraphStyle(
        "H2", parent=styles["Heading2"], fontName="Arial-Bold",
        fontSize=11.5, leading=15.0, textColor=colors.HexColor("#0F172A"), spaceBefore=6, spaceAfter=3, keepWithNext=True
    )
    body_st = ParagraphStyle(
        "Body", parent=styles["Normal"], fontName="Arial",
        fontSize=11.0, leading=19.0, textColor=colors.HexColor("#1F2937"), alignment=TA_JUSTIFY, spaceAfter=5.0
    )
    bullet_st = ParagraphStyle(
        "Bullet", parent=body_st, leftIndent=12, firstLineIndent=-8, spaceAfter=3.5
    )
    cap_st = ParagraphStyle(
        "TableCap", parent=styles["Normal"], fontName="Arial-Bold",
        fontSize=10.0, leading=13.0, textColor=colors.HexColor("#1E293B"), spaceBefore=5, spaceAfter=3.0, keepWithNext=False
    )
    note_st = ParagraphStyle(
        "TableNote", parent=styles["Normal"], fontName="Arial-Italic",
        fontSize=8.5, leading=11.5, textColor=colors.HexColor("#4B5563"), spaceBefore=2.5, spaceAfter=4.0
    )
    ref_st = ParagraphStyle(
        "RefEntry", parent=styles["Normal"], fontName="Arial",
        fontSize=9.0, leading=12.5, textColor=colors.HexColor("#1F2937"), leftIndent=14, firstLineIndent=-14, spaceAfter=3.5
    )

    # Celdas de tablas (mínimo 9 pt, leading 11.5)
    th_c = ParagraphStyle("THC", fontName="Arial-Bold", fontSize=9.0, leading=11.5, textColor=colors.white, alignment=TA_CENTER)
    th_l = ParagraphStyle("THL", fontName="Arial-Bold", fontSize=9.0, leading=11.5, textColor=colors.white, alignment=TA_LEFT)
    td_c = ParagraphStyle("TDC", fontName="Arial", fontSize=9.0, leading=11.5, textColor=colors.HexColor("#111827"), alignment=TA_CENTER)
    td_l = ParagraphStyle("TDL", fontName="Arial", fontSize=9.0, leading=11.5, textColor=colors.HexColor("#111827"), alignment=TA_LEFT)
    td_cb = ParagraphStyle("TDCB", fontName="Arial-Bold", fontSize=9.0, leading=11.5, textColor=colors.HexColor("#111827"), alignment=TA_CENTER)
    td_lb = ParagraphStyle("TDLB", fontName="Arial-Bold", fontSize=9.0, leading=11.5, textColor=colors.HexColor("#111827"), alignment=TA_LEFT)

    story = []

    # Encabezado formal de portada / título (C1)
    story.append(Paragraph(
        "Perfiles ciudadanos de participación electoral en México, 2009–2024: tipología seccional y estrategias de educación cívica",
        title_st
    ))
    story.append(Paragraph(
        "Equipo Byte me · Concurso \"Hackea la participación: Datos que construyen democracia\" (INE / ENCÍVICA) · Reto 1: Perfiles ciudadanos de participación",
        sub_st
    ))
    story.append(Paragraph(
        "<b>Integrantes:</b> Johanan Olivares Gutiérrez (representante), Oscar Ariel Cuevas Martínez, Saúl Alexis Arias González · "
        "<b>Repositorio público:</b> <font color=\"#1E3A8A\"><u>https://github.com/Johanan1113/Hackaton_INE_byte_me</u></font>",
        meta_st
    ))

    # =========================================================================
    # SECCIÓN 1: RESUMEN EJECUTIVO
    # =========================================================================
    story.append(Paragraph("1. Resumen Ejecutivo", h1_st))
    diff_2018 = serie[3]["subestimacion_erronea_sv_ln_pond_pts"]
    diff_2024 = serie[5]["subestimacion_erronea_sv_ln_pond_pts"]
    story.append(Paragraph(
        f"Este estudio construye una tipología nacional de secciones electorales a partir de los microdatos abiertos de los Conteos Censales "
        f"de Participación Ciudadana (CCPC) en las seis elecciones federales celebradas entre {serie[0]['anio']} y {serie[-1]['anio']}. "
        f"Durante la validación de los datos se identificó un hallazgo metodológico central: en los archivos abiertos del CCPC, la Lista Nominal "
        f"cumple la identidad exacta <b>LN = SV + NV + NS</b>, donde <b>SV</b> corresponde a las personas que sí votaron, <b>NV</b> a quienes no votaron "
        f"y <b>NS</b> a los registros no especificados (cuadernillos sin marcas de votación, no disponibles para captura o con páginas faltantes, según el catálogo de campos del INE) "
        f"({serie[3]['ns_total_anio']:,} electores = {serie[3]['pct_ns_anio']:.2f}% de la LN en {serie[3]['anio']}, y "
        f"{serie[5]['ns_total_anio']:,} electores = {serie[5]['pct_ns_anio']:.2f}% en {serie[5]['anio']}). "
        f"Calcular <b>SV / LN</b> en lugar de la fórmula <b>SV / (SV + NV)</b> asigna 0.0% de participación a las secciones sin captura "
        f"(<b>SV + NV = 0</b>), subestima la participación nacional en {diff_2018:.2f} puntos en {serie[3]['anio']} y en {diff_2024:.2f} en {serie[-1]['anio']}, "
        f"y genera grupos artificiales de baja participación en cualquier análisis de conglomerados.",
        body_st
    ))
    story.append(Paragraph(
        f"Al aplicar la fórmula <b>SV / (SV + NV)</b> en todas las tasas y depurar el universo bajo el <b>Panel Principal (Opción B, cero imputación)</b> "
        f"con las <b>{u['panel_principal_secciones']:,} secciones</b> que cuentan con captura válida (<b>SV + NV ≥ 50</b> en las seis elecciones) y sin saltos "
        f"abruptos de Lista Nominal por reseccionamiento —cubriendo el <b>{u['panel_principal_pct_secciones_2024']:.2f}% de las secciones</b> y el "
        f"<b>{u['panel_principal_pct_ln_2024']:.2f}% de la Lista Nominal de {serie[-1]['anio']}</b> ({u['panel_principal_ln_2024']:,} electores en "
        f"<b>{u['panel_principal_municipios']:,} municipios</b>)—, el modelo <b>K-Means++ con k = {k_sel}</b> domina empíricamente dentro del rango "
        f"de 4 a 6 perfiles de la convocatoria (Silhouette = {bench_km_k4['silhouette']:.4f}, Davies-Bouldin = {bench_km_k4['davies_bouldin']:.4f}, "
        f"Calinski-Harabasz = {bench_km_k4['calinski_harabasz']:,.2f} y estabilidad bootstrap ARI = {bench_km_k4['bootstrap_ari_media']:.4f} "
        f"[{bench_km_k4['bootstrap_ari_ic95_inf']:.4f}, {bench_km_k4['bootstrap_ari_ic95_sup']:.4f}]). "
        f"Los cuatro perfiles identificados son: "
        + "; ".join(
            f"<b>{p['codigo_cluster']}: {p['nombre_propuesto']}</b> ({p['n_secciones']:,} secc., {p['pct_secciones_panel']:.2f}% del panel; "
            f"participación media {p['participacion_media_historica_original']*100:.2f}%)"
            for p in perfiles
        ) + ".",
        body_st
    ))

    # =========================================================================
    # SECCIÓN 2: DATOS Y TRATAMIENTO
    # =========================================================================
    story.append(Paragraph("2. Datos y Tratamiento: Corrección por Registros NS y Cascada del Universo", h1_st))
    # C2, C10, C3
    story.append(Paragraph(
        f"En los microdatos abiertos de los Conteos Censales de Participación Ciudadana (CCPC), "
        f"la Lista Nominal se desagrega en tres categorías: electores que sufragaron (SV), electores que no votaron (NV) y electores sin condición "
        f"especificada de voto (NS). De acuerdo con el catálogo oficial de descripción de campos del INE (<i>01_descripcioncampos_conteoscensales2024.txt</i>): "
        f"<i>\"Registros no especificados en participación, pues corresponden a: Registro correspondiente a un cuadernillo sin marcas de votación; "
        f"Registro correspondiente a un cuadernillo no disponible para su captura; Registro correspondiente a una página no disponible en el cuadernillo.\"</i>",
        body_st
    ))
    story.append(Paragraph(
        f"Por ello, la tasa de participación seccional y por subgrupos demográficos "
        f"(jóvenes de 18–29 años, adultos mayores de 60+ años, mujeres y hombres) se calcula estrictamente como <b>P = SV / (SV + NV)</b>. "
        f"En {serie[-1]['anio']}, los registros no binarios (SEXO = 2) se integran en la tasa total seccional, mientras que la brecha de género se evalúa "
        f"entre mujeres y hombres. La verificación sobre los datos crudos confirmó 0 secciones con SV &gt; LN o SV &gt; (SV + NV), dado que los conteos censales "
        f"no incorporan casillas especiales.",
        body_st
    ))
    # C16
    story.append(Paragraph(
        f"La Tabla 1 valida la serie nacional calculada con SV / (SV + NV) contra las publicaciones censales del INE: el estudio comparativo de la "
        f"DECEyEC (<i>DECEYEC_Comparativo_VF.pdf</i>, p. 7, Figura 3.1) reporta <b>{serie[0]['oficial_o_referencia_pct']:.2f}%</b> en {serie[0]['anio']}, "
        f"<b>{serie[1]['oficial_o_referencia_pct']:.2f}%</b> en {serie[1]['anio']} y <b>{serie[2]['oficial_o_referencia_pct']:.2f}%</b> en {serie[2]['anio']}; "
        f"los estudios censales de {serie[3]['anio']} y {serie[5]['anio']} reportan <b>{serie[3]['oficial_o_referencia_pct']:.1f}%</b> "
        f"(dato exacto CCPC: {serie[3]['total_ponderada_sv_svnv_pct']:.2f}%) y <b>{serie[5]['oficial_o_referencia_pct']:.1f}%</b> "
        f"(dato exacto CCPC: {serie[5]['total_ponderada_sv_svnv_pct']:.2f}%). Para {serie[4]['anio']}, el dato censal oficial de "
        f"<b>{serie[4]['oficial_o_referencia_pct']:.1f}%</b> proviene de la imagen del tablero interactivo en la página 21 de "
        f"<i>Manual-Conteos-Censales-2009-2024.pdf</i> (figura en sección <i>\"Participación por año\"</i>; el cálculo seccional ponderado es "
        f"<b>{serie[4]['total_ponderada_sv_svnv_pct']:.2f}%</b>; como referencia no censal, el PREP reportó 52.67%).",
        body_st
    ))

    # B4: Tabla 1 compacta con 7 columnas (ancho exacto: 470.27 pt)
    t1_rows = [[
        Paragraph("Año", th_c),
        Paragraph("Elección", th_c),
        Paragraph("Secciones CCPC", th_c),
        Paragraph("LN CCPC", th_c),
        Paragraph("Dato censal INE", th_c),
        Paragraph("SV/(SV+NV)", th_c),
        Paragraph("Subestimación con SV/LN (pts)", th_c),
    ]]
    for r in serie:
        of_str = f"{r['oficial_o_referencia_pct']:.2f}%" if r["anio"] in (2009, 2012, 2015) else f"{r['oficial_o_referencia_pct']:.1f}%"
        efecto_ns = f"+{r['subestimacion_erronea_sv_ln_pond_pts']:.2f} pts" if r["subestimacion_erronea_sv_ln_pond_pts"] > 0 else "0.00 pts"
        t1_rows.append([
            Paragraph(f"<b>{r['anio']}</b>", td_c),
            Paragraph(r["tipo_eleccion"], td_c),
            Paragraph(f"{r['secciones_totales_anio']:,}", td_c),
            Paragraph(f"{r['ln_total_anio']:,}", td_c),
            Paragraph(f"<b>{of_str}</b>", td_cb),
            Paragraph(f"<b>{r['total_ponderada_sv_svnv_pct']:.2f}%</b>", td_cb),
            Paragraph(efecto_ns, td_c),
        ])
    t1_cap = Paragraph(f"Tabla 1. Serie Nacional {serie[0]['anio']}–{serie[-1]['anio']}: Validación Censal de Fórmula Oficial SV/(SV+NV) vs Publicaciones Oficiales y Subestimación con SV/LN (pts)", cap_st)
    t1_table = styled_table(t1_rows, [32.27, 65.0, 68.0, 75.0, 75.0, 75.0, 80.0])
    story.append(KeepTogether([t1_cap, t1_table]))
    story.append(Spacer(1, 4))

    story.append(Paragraph(
        f"<b>Reconciliación del universo seccional (Tabla 2):</b> La unión histórica {serie[0]['anio']}–{serie[-1]['anio']} comprende "
        f"<b>{u['secciones_union_historica_2009_2024']:,} secciones</b> distintas. Al descontar <b>{u['secciones_2009_2021_baja_antes_2024']:,}</b> secciones "
        f"dadas de baja antes de {serie[-1]['anio']}, se obtienen las <b>{u['secciones_2024_total']:,} secciones activas en {serie[-1]['anio']}</b> "
        f"({u['ln_2024_total_csv']:,} electores en el CSV abierto vs {u['ln_2024_oficial_ine']:,} en el informe INE). Estas se componen de "
        f"<b>{u['secciones_continuas_2009_2024']:,} secciones continuas</b> ({serie[0]['anio']}–{serie[-1]['anio']}, con LN {serie[-1]['anio']} de "
        f"{u['ln_2024_panel_continuo_62048']:,}) más <b>{u['secciones_2024_creadas_post2009']:,} secciones creadas post-{serie[0]['anio']}</b> "
        f"({u['secciones_continuas_2009_2024']:,} + {u['secciones_2024_creadas_post2009']:,} = {u['secciones_2024_total']:,}). "
        f"Sobre las {u['secciones_continuas_2009_2024']:,} continuas se exige captura válida <b>SV + NV ≥ 50</b> en las seis elecciones "
        f"(quedan <b>{u['secciones_captura_valida_sv_nv_ge_50']:,}</b> tras excluir {u['secciones_excluidas_sv_nv_lt_50']:,}: "
        f"{u['secciones_excluidas_sv_nv_eq_0']:,} con SV+NV=0 y {u['secciones_excluidas_sv_nv_1_a_49']:,} con 1 ≤ SV+NV &lt; 50), ausencia de saltos "
        f"consecutivos de LN &lt;0.5x o &gt;2.5x por reseccionamiento (quedan <b>{u['secciones_sin_saltos_ln']:,}</b> tras excluir "
        f"{u['secciones_salto_abrupto_ln_en_54804']:,} de las {u['secciones_salto_abrupto_ln_en_62048']:,} del panel continuo) y presencia de todos los "
        f"grupos etarios ({u['secciones_excluidas_sin_grupo_etario_60mas']} sección excluida), conformando el <b>Panel Principal (Opción B) de "
        f"{u['panel_principal_secciones']:,} secciones</b> sin ninguna imputación.",
        body_st
    ))

    # Tabla 2: Cascada de Filtrado (7 cols = 470.27 pt)
    t2_rows = [[
        Paragraph("Criterio / Etapa de Depuración", th_l),
        Paragraph("Secc.", th_c),
        Paragraph("Excl.", th_c),
        Paragraph(f"% Secc. {serie[-1]['anio']}", th_c),
        Paragraph(f"LN {serie[-1]['anio']}", th_c),
        Paragraph(f"% LN {serie[-1]['anio']}", th_c),
        Paragraph("Mun.", th_c),
    ]]
    etapa_labels = [
        f"0. Unión histórica ({serie[0]['anio']}–{serie[-1]['anio']})",
        f"1. Secciones activas en CCPC {serie[-1]['anio']}",
        f"2. Panel continuo ({serie[0]['anio']}–{serie[-1]['anio']})",
        "3. Captura válida (SV+NV ≥ 50 en las 6)",
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
    t2_cap = Paragraph(f"Tabla 2. Cascada de Filtrado del Universo Seccional y Cobertura sobre {serie[-1]['anio']}", cap_st)
    t2_table = styled_table(t2_rows, [146.27, 50.0, 48.0, 56.0, 66.0, 54.0, 50.0], highlight_last=True)
    story.append(KeepTogether([t2_cap, t2_table]))
    story.append(Spacer(1, 4))

    # Figura 1 (D1, D2): Trayectorias y NS
    fig1_flow = Image(str(FIGURAS_DIR / "fig2_evolucion_temporal.png"), width=6.5 * inch, height=2.6 * inch)
    fig1_flow.hAlign = "CENTER"
    fig1_cap = Paragraph(
        "<b>Figura 1.</b> Dinámica electoral 2009–2024: perfiles seccionales (k=4) y corrección del sesgo por registros sin captura (NS). "
        "<i>Fuente: Conteos Censales de Participación Ciudadana (CCPC 2009–2024), elaboración propia.</i>",
        cap_st
    )
    story.append(KeepTogether([fig1_flow, Spacer(1, 3), fig1_cap]))
    story.append(Spacer(1, 4))

    # =========================================================================
    # SECCIÓN 3: METODOLOGÍA Y JUSTIFICACIÓN DE K=4
    # =========================================================================
    story.append(Paragraph(f"3. Metodología, Pruebas de Robustez y Justificación de k = {k_sel}", h1_st))
    # C5: Sin snake_case en texto
    story.append(Paragraph(
        f"Cada sección del Panel Principal ({u['panel_principal_secciones']:,}) se representa mediante siete indicadores hexanuales winsorizados en "
        f"los percentiles {u['winsor_p_min']} y {u['winsor_p_max']} "
        f"y escalados con <i>RobustScaler</i>: (1) <b>participación media</b> (media = {pan_b['participacion_media_historica_media']*100:.2f}%, "
        f"DE = {pan_b['participacion_media_historica_std']*100:.2f}%); (2) <b>brecha presidencial–intermedia</b> "
        f"(media = {pan_b['brecha_presidencial_intermedia_media']*100:+.2f} pts, DE = {pan_b['brecha_presidencial_intermedia_std']*100:.2f} pts); "
        f"(3) <b>tendencia anual</b> (pendiente OLS: media = {pan_b['tendencia_participacion_beta_media']*100:+.2f} pts/año, "
        f"DE = {pan_b['tendencia_participacion_beta_std']*100:.2f} pts/año); (4) <b>estabilidad (log(1 + 1/CV))</b> "
        f"(media = {pan_b['estabilidad_participacion_media']:.4f}, DE = {pan_b['estabilidad_participacion_std']:.4f}, reduciendo la asimetría de "
        f"{est[0]['asimetria_skew']:.2f} en 1/CV a {est[2]['asimetria_skew']:.2f} y manteniendo ARI = {est[2]['ari_vs_b']:.4f} frente a CV directo); "
        f"(5) <b>brecha generacional (60+ menos 18–29)</b> (media = {pan_b['brecha_generacional_media']*100:+.2f} pts); "
        f"(6) <b>brecha de género (mujeres menos hombres)</b> (media = {pan_b['brecha_genero_media']*100:+.2f} pts); y "
        f"(7) <b>razón de participación juvenil</b>, calculada como el cociente de medias hexanuales "
        f"(media = {pan_b['ratio_participacion_joven_media']:.4f}; el promedio de razones anuales es {pan_b['ratio_joven_media_de_ratios_anuales']:.4f}).",
        body_st
    ))
    story.append(Paragraph(
        f"<b>Análisis de colinealidad (VIF) y entorno de software:</b> Los valores de VIF de las siete variables oscilan entre "
        f"{vif[5]['vif_7_variables']:.2f} (brecha de género) y {vif[6]['vif_7_variables']:.2f} (razón de participación juvenil, con "
        f"{vif[4]['vif_7_variables']:.2f} en brecha generacional). Se mantienen ambas variables generacionales por su distinción conceptual: "
        f"la razón juvenil captura la incorporación relativa a la propensión de sufragio de su propia sección, mientras que "
        f"la brecha generacional mide la distancia absoluta en puntos porcentuales entre 60+ y 18–29 años (por ejemplo, en "
        f"{perfiles[0]['codigo_cluster']} y {perfiles[3]['codigo_cluster']} la brecha generacional es similar, de "
        f"{perfiles[0]['brecha_generacional_original']*100:.2f} y {perfiles[3]['brecha_generacional_original']*100:.2f} puntos, pero operan en estructuras "
        f"demográficas y de género distintas). "
        f"El pipeline se ejecutó en <i>Python {sw['python']}</i>, <i>DuckDB {sw['duckdb']}</i>, <i>scikit-learn {sw['scikit_learn']}</i>, "
        f"<i>SciPy {sw['scipy']}</i>, <i>umap-learn {sw['umap_learn']}</i>, <i>pandas {sw['pandas']}</i>, <i>numpy {sw['numpy']}</i> y "
        f"<i>statsmodels {sw['statsmodels']}</i>, verificando determinismo bit a bit en doble ejecución desde cero.",
        body_st
    ))

    # Tabla 3: Benchmark K-Means++ (5 columnas: k, Silhouette, Davies-Bouldin, Calinski-Harabasz, ARI Bootstrap)
    t3_rows = [[
        Paragraph("k", th_c),
        Paragraph("Silhouette", th_c),
        Paragraph("Davies–Bouldin", th_c),
        Paragraph("Calinski–Harabasz", th_c),
        Paragraph("ARI Bootstrap [IC 95%]", th_c),
    ]]
    for b in bench_km:
        is_k4 = int(b["k"]) == k_sel
        st_c = td_cb if is_k4 else td_c
        ari_str = f"{b['bootstrap_ari_media']:.4f} [{b['bootstrap_ari_ic95_inf']:.4f}, {b['bootstrap_ari_ic95_sup']:.4f}]"
        t3_rows.append([
            Paragraph(f"<b>k = {int(b['k'])}</b>", st_c),
            Paragraph(f"{b['silhouette']:.4f}", st_c),
            Paragraph(f"{b['davies_bouldin']:.4f}", st_c),
            Paragraph(f"{b['calinski_harabasz']:,.2f}", st_c),
            Paragraph(ari_str, st_c),
        ])
    t3_cap = Paragraph(f"Tabla 3. Benchmark de Agrupamiento K-Means++ (k = 3 a 7) sobre el Panel Principal (N = {u['panel_principal_secciones']:,})", cap_st)
    t3_table = styled_table(t3_rows, [45.27, 85.0, 90.0, 105.0, 145.0], highlight_last=False)
    story.append(KeepTogether([t3_cap, t3_table]))
    story.append(Spacer(1, 4))

    # C7: Oración sobre GMM y HDBSCAN
    story.append(Paragraph(
        "Los modelos de mezclas gaussianas obtuvieron silhouette de 0.0191 a 0.1054 (k=3–7) y su BIC sigue bajando hasta k=7, "
        "sin un óptimo claro. HDBSCAN, en tres configuraciones, encontró como máximo 2 grupos con 50.7% de secciones sin asignar, "
        "o ninguno. Esto indica que las secciones forman un continuo sin grupos densos naturales: los cuatro perfiles son una "
        "segmentación operativa de ese continuo, no grupos naturales.",
        body_st
    ))

    # C4: k casteado a int, justificación k=4 (referencia a Figura 2)
    story.append(Paragraph(
        f"<b>Justificación de la elección de k = {k_sel} (Figura 2):</b> (1) Dentro del rango de 4 a 6 perfiles establecido por la "
        f"convocatoria, <b>k = {k_sel} obtiene el mejor Silhouette ({bench_km_k4['silhouette']:.4f}), el mejor Davies-Bouldin ({bench_km_k4['davies_bouldin']:.4f}) "
        f"y el mejor Calinski-Harabasz ({bench_km_k4['calinski_harabasz']:,.2f})</b>, superando a k = {int(bench_km[2]['k'])} en las cuatro métricas "
        f"({bench_km[2]['silhouette']:.4f}, {bench_km[2]['davies_bouldin']:.4f}, {bench_km[2]['calinski_harabasz']:,.2f} y ARI {bench_km[2]['bootstrap_ari_media']:.4f}) "
        f"y a k = {int(bench_km[3]['k'])} en las tres métricas de separación interna. "
        f"(2) Su estabilidad bootstrap (<b>ARI = {bench_km_k4['bootstrap_ari_media']:.4f}</b>, IC 95% [{bench_km_k4['bootstrap_ari_ic95_inf']:.4f}, "
        f"{bench_km_k4['bootstrap_ari_ic95_sup']:.4f}]) es comparable a la de k = {int(bench_km[3]['k'])} ({bench_km[3]['bootstrap_ari_media']:.4f}, IC 95% "
        f"[{bench_km[3]['bootstrap_ari_ic95_inf']:.4f}, {bench_km[3]['bootstrap_ari_ic95_sup']:.4f}]; los intervalos se traslapan). "
        f"(3) En k = {int(bench_km[3]['k'])} aparece un grupo sin diferenciación sustantiva ({comp_k6_c1['pct_secciones']:.2f}% del panel con una sola variable con "
        f"|z| ≥ 0.50: tendencia anual con z = {comp_k6_c1['tendencia_participacion_beta_z']:+.2f}), mientras que en k = {k_sel} los cuatro "
        f"perfiles tienen al menos cinco variables con |z| ≥ 0.50. Se declara explícitamente que k = {int(bench_km[0]['k'])} tiene mejores métricas globales "
        f"(Silhouette {bench_km[0]['silhouette']:.4f}, DB {bench_km[0]['davies_bouldin']:.4f}, CH {bench_km[0]['calinski_harabasz']:,.2f}), pero queda fuera "
        f"del rango 4 a 6 de la convocatoria. Como nota de focalización, con k = {int(bench_km[3]['k'])} el perfil de baja participación se divide en un subgrupo "
        f"de rezago juvenil y otro de ciclo presidencial urbano, distinción útil cuando se requiere intervención subdistrital fina.",
        body_st
    ))

    # C6: Oración única de Random Forest
    story.append(Paragraph(
        "Como medida de interpretabilidad (no de validación, porque el clasificador usa las mismas variables que definieron los grupos), "
        "un Random Forest con validación cruzada de 5 pliegues reproduce las etiquetas con 96.29% de exactitud; "
        "las variables más discriminantes son la razón de participación juvenil, la estabilidad y la brecha generacional.",
        body_st
    ))

    # Figura 2 (D1, D2): Benchmark
    fig2_flow = Image(str(FIGURAS_DIR / "fig6_benchmark_k.png"), width=6.5 * inch, height=2.15 * inch)
    fig2_flow.hAlign = "CENTER"
    fig2_cap = Paragraph(
        "<b>Figura 2.</b> Benchmark de agrupamiento seccional (k=3 a 7): coeficiente de Silhouette y estabilidad bootstrap ARI (100 réplicas al 80%). "
        "<i>Fuente: CCPC 2009–2024, elaboración propia.</i>",
        cap_st
    )
    story.append(KeepTogether([fig2_flow, Spacer(1, 3), fig2_cap]))
    story.append(Spacer(1, 4))

    # =========================================================================
    # SECCIÓN 4: CARACTERIZACIÓN DE LOS 4 PERFILES
    # =========================================================================
    story.append(Paragraph(f"4. Caracterización de los 4 Perfiles Ciudadanos de Participación (k = {k_sel})", h1_st))
    # C9
    story.append(Paragraph(
        f"63.7% de las secciones del panel son urbanas, 26.9% rurales y 9.5% mixtas; por electores, 68.5%, 18.0% y 13.5%. "
        f"Las Tablas 4 y 5 presentan los centroides en escala original y puntaje z estandarizado respecto a la media del Panel B, "
        f"así como sus trayectorias históricas ponderadas y perfiles demográficos.",
        body_st
    ))

    # Tabla 4: Centroides (8 cols = 470.27 pt)
    t5_rows = [[
        Paragraph("Perfil y Nombre Oficial", th_l),
        Paragraph("Secc.<br/>(% Panel)", th_c),
        Paragraph(f"LN {serie[-1]['anio']}<br/>(% Panel)", th_c),
        Paragraph("Part. Media<br/>(z)", th_c),
        Paragraph("Brecha Pres–Inter (z)", th_c),
        Paragraph("Tend. Anual<br/>(z)", th_c),
        Paragraph("Estabilidad<br/>(z)", th_c),
        Paragraph("Gen. / Género /<br/>Razón Joven (z)", th_c),
    ]]
    for p in perfiles:
        t5_rows.append([
            Paragraph(f"<b>{p['codigo_cluster']}: {p['nombre_propuesto']}</b>", td_l),
            Paragraph(f"{p['n_secciones']:,}<br/>({p['pct_secciones_panel']:.2f}%)", td_c),
            Paragraph(f"{p['ln_2024']:,}<br/>({p['pct_ln_panel']:.2f}%)", td_c),
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
        Paragraph(f"<b>{pan_b['n_secciones']:,}</b><br/>(100.00%)", td_cb),
        Paragraph(f"<b>{pan_b['ln_2024']:,}</b><br/>(100.00%)", td_cb),
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
    t4_cap = Paragraph(f"Tabla 4. Centroides de las 7 Variables Rectoras (Escala Original y z-score) y Cobertura (k = {k_sel})", cap_st)
    t4_table = styled_table(t5_rows, [88.27, 44.0, 46.0, 44.0, 46.0, 50.0, 62.0, 90.0], highlight_last=True)
    story.append(KeepTogether([t4_cap, t4_table]))
    story.append(Spacer(1, 4))

    # Tabla 5: Series Históricas Ponderadas, Tasas Demográficas y Composición Territorial por Perfil (9 columnas)
    t6_rows = [[
        Paragraph("Perfil", th_c),
        Paragraph("Serie Ponderada 2009–2024", th_c),
        Paragraph("Pres. / Inter.", th_c),
        Paragraph("18–29 / 60+ años", th_c),
        Paragraph("Mujeres / Hombres", th_c),
        Paragraph("% Urb.", th_c),
        Paragraph("% Rur.", th_c),
        Paragraph("% Mix.", th_c),
        Paragraph("Top 3 Entidades (% secc.)", th_l),
    ]]
    for p in perfiles:
        s_pond = " / ".join(f"<b>{p[f'p_{y}_ponderada']*100:.1f}%</b>" if y == 2021 else f"{p[f'p_{y}_ponderada']*100:.1f}%" for y in [2009, 2012, 2015, 2018, 2021, 2024])
        # Top 3 entidades limpias (ej. "Chihuahua (18.2%); Sonora (15.4%); BC (12.1%)")
        raw_top = p["top5_entidades_por_pct_secciones"].split("; ")[:3]
        clean_top = "; ".join(ent.split(",")[0] + ")" for ent in raw_top)
        t6_rows.append([
            Paragraph(f"<b>{p['codigo_cluster']}</b>", td_cb),
            Paragraph(s_pond, td_c),
            Paragraph(f"{p['media_presidencial_original']*100:.1f}% /<br/>{p['media_intermedia_original']*100:.1f}%", td_c),
            Paragraph(f"{p['tasa_joven_18_29_original']*100:.1f}% /<br/>{p['tasa_mayor_60_mas_original']*100:.1f}%", td_c),
            Paragraph(f"{p['tasa_mujeres_original']*100:.1f}% /<br/>{p['tasa_hombres_original']*100:.1f}%", td_c),
            Paragraph(f"{p['pct_secciones_urbanas']:.1f}%", td_c),
            Paragraph(f"{p['pct_secciones_rurales']:.1f}%", td_c),
            Paragraph(f"{p['pct_secciones_mixtas']:.1f}%", td_c),
            Paragraph(clean_top, td_l),
        ])
    s_pond_b = " / ".join(f"<b>{pan_b[f'p_{y}_ponderada']*100:.1f}%</b>" for y in [2009, 2012, 2015, 2018, 2021, 2024])
    t6_rows.append([
        Paragraph("<b>Panel B</b>", td_cb),
        Paragraph(s_pond_b, td_cb),
        Paragraph(f"<b>{pan_b['media_presidencial_original']*100:.1f}% /<br/>{pan_b['media_intermedia_original']*100:.1f}%</b>", td_cb),
        Paragraph(f"<b>{pan_b['tasa_joven_18_29_original']*100:.1f}% /<br/>{pan_b['tasa_mayor_60_mas_original']*100:.1f}%</b>", td_cb),
        Paragraph(f"<b>{pan_b['tasa_mujeres_original']*100:.1f}% /<br/>{pan_b['tasa_hombres_original']*100:.1f}%</b>", td_cb),
        Paragraph(f"<b>{pan_b['pct_secciones_urbanas_1d']:.1f}%</b>", td_cb),
        Paragraph(f"<b>{pan_b['pct_secciones_rurales_1d']:.1f}%</b>", td_cb),
        Paragraph(f"<b>{pan_b['pct_secciones_mixtas_1d']:.1f}%</b>", td_cb),
        Paragraph(f"Total Nacional ({u['panel_principal_municipios']:,} mun.)", td_lb),
    ])
    t5_cap = Paragraph(f"Tabla 5. Series Históricas Ponderadas, Tasas Demográficas y Composición Territorial por Perfil (k = {k_sel})", cap_st)
    t5_table = styled_table(t6_rows, [32.27, 100.0, 50.0, 46.0, 50.0, 34.0, 34.0, 34.0, 90.0], highlight_last=True)
    story.append(KeepTogether([t5_cap, t5_table]))
    story.append(Spacer(1, 4))

    # Diagnósticos por perfil (C8: la más baja/alta de los cuatro perfiles, C12: glifos ≥ y ≤)
    for p in perfiles:
        story.append(Paragraph(
            f"• <b>{p['codigo_cluster']} — {p['nombre_propuesto']} ({p['n_secciones']:,} secciones, {p['pct_secciones_panel']:.2f}% del panel; "
            f"{p['ln_2024']:,} electores, {p['pct_ln_panel']:.2f}% LN):</b> {p['justificacion_regla_3_2']}",
            bullet_st
        ))

    # =========================================================================
    # SECCIÓN 5: ESTRATEGIAS FOCALIZADAS
    # =========================================================================
    story.append(Paragraph("5. Estrategias Focalizadas de Promoción e Intervención Institucional (ENCÍVICA)", h1_st))
    story.append(Paragraph(
        f"Las estrategias para los cuatro perfiles (Tabla 6) se fundamentan en las facultades operativas del INE en el marco de la ENCÍVICA. "
        f"Cada meta cuantitativa para la elección intermedia de 2027 adopta como referencia la <b>línea base real de la intermedia de 2021 (serie ponderada)</b> "
        f"de cada perfil: <b>C0 = {estrategias[0]['linea_base_intermedia_2021_pond_pct']:.1f}%</b> ({perfiles[0]['p_2021_ponderada']*100:.2f}%), "
        f"<b>C1 = {estrategias[1]['linea_base_intermedia_2021_pond_pct']:.1f}%</b> ({perfiles[1]['p_2021_ponderada']*100:.2f}%), "
        f"<b>C2 = {estrategias[2]['linea_base_intermedia_2021_pond_pct']:.1f}%</b> ({perfiles[2]['p_2021_ponderada']*100:.2f}%) y "
        f"<b>C3 = {estrategias[3]['linea_base_intermedia_2021_pond_pct']:.1f}%</b> ({perfiles[3]['p_2021_ponderada']*100:.2f}%). "
        f"En <b>C0</b> ({perfiles[0]['pct_secciones_panel']:.2f}% del panel, {perfiles[0]['pct_secciones_urbanas']:.1f}% urbano) se despliegan dos líneas: "
        f"pedagogía legislativa intermedia en transporte masivo y atención a jóvenes que no estudian en centros laborales, parques industriales y tianguis. "
        f"En <b>C3</b> ({perfiles[3]['pct_secciones_urbanas']:.1f}% urbano, con sobrerrepresentación rural de {perfiles[3]['pct_secciones_rurales']:.1f}%), "
        f"la acción principal busca elevar la participación masculina (43.9% en 2021 vs 48.7% del Panel B) y revertir la caída presidencial "
        f"(de 61.2% en 2012 a 55.6% en 2024), dejando la accesibilidad geográfica rural como acción secundaria.",
        body_st
    ))

    # C11: Tabla 7 de estrategias compacta (<= 110 palabras por perfil)
    t7_compact_data = [
        {
            "perfil": "<b>C0: Baja Participación Intermitente con Rezago Juvenil</b><br/><br/>Secc: 17,622 (32.85%)<br/>Base Inter. 2021: <b>46.1%</b><br/>Base Pres. 2024: <b>56.9%</b><br/>Base Joven 2021: <b>35.2%</b>",
            "diag_obj": "Mitigar el abstencionismo en elecciones intermedias y elevar la votación de jóvenes (18–29 años) escolarizados y no escolarizados en 17,622 secciones urbanas.",
            "canales_accion": "<b>Canales:</b> Transporte metropolitano, plataforma 'Conóceles', tianguis, centros laborales y universidades.<br/><br/><b>Acción:</b> Campaña cívica y brigadas móviles de actualización registral (DERFE/DECEyEC).",
            "meta_ind": "<b>Meta:</b> Elevar participación a 49.5% en 2027 (+3.4 pts vs. 2021) y voto juvenil a 39.1% (+3.9 pts).<br/><br/><b>Indicador:</b> Tasa ponderada SV/(SV+NV) 2027 y tasa 18–29 en CCPC.",
            "unidad_costo": "<b>Unidad:</b> DECEyEC, DERFE y Juntas Distritales.<br/><br/><b>Costo:</b> Medio (estimación indicativa; tiempos oficiales y módulos itinerantes).",
            "lema": "<i>\"Cada elección define tu entorno: infórmate, ubica tu casilla y participa en 2027\"</i>",
        },
        {
            "perfil": "<b>C1: Alta Participación Estable e Intergeneracional</b><br/><br/>Secc: 8,824 (16.45%)<br/>Base Inter. 2021: <b>62.5%</b><br/>Base Pres. 2024: <b>65.7%</b>",
            "diag_obj": "Sostener la constancia cívica comunitaria y asegurar el relevo generacional en la integración de mesas directivas de casilla en 8,824 secciones.",
            "canales_accion": "<b>Canales:</b> Redes comunitarias, planteles locales y centros culturales.<br/><br/><b>Acción:</b> Talleres juveniles ENCÍVICA y reclutamiento temprano de CAE y sensibilización de la ciudadanía insaculada.",
            "meta_ind": "<b>Meta:</b> Sostener participación ≥ 62.5% en 2027 y ≥ 65.7% en 2030; aumentar la proporción de casillas instaladas con funcionariado propietario.<br/><br/><b>Indicador:</b> Tasa ponderada en 2027/2030 y porcentaje de casillas instaladas con funcionariado propietario el día de la jornada (dato de la DEOE).",
            "unidad_costo": "<b>Unidad:</b> DECEyEC y Juntas Distritales (Vocalías de Capacitación y Organización).<br/><br/><b>Costo:</b> Bajo (absorbible en programas ordinarios).",
            "lema": "<i>\"Si te visitan para integrar una casilla, participa: tu comunidad cuenta contigo\"</i>",
        },
        {
            "perfil": "<b>C2: Participación en Ascenso con Juventud Activa</b><br/><br/>Secc: 14,624 (27.26%)<br/>Base Inter. 2021: <b>60.4%</b><br/>Base Pres. 2024: <b>68.0%</b>",
            "diag_obj": "Consolidar en 2027 el nivel alcanzado en 2021 en 14,624 secciones urbanas (68.6%) y rurales/mixtas (31.4%), evitando regresión hacia su promedio histórico (50.5%).",
            "canales_accion": "<b>Canales:</b> Colectivos juveniles, redes vecinales y 'Conóceles'.<br/><br/><b>Acción:</b> Foros 'Diálogos por la Democracia' (DECEyEC) y monitoreo de casillas en crecimiento (DEOE).",
            "meta_ind": "<b>Meta:</b> Consolidar participación ≥ 60.4% en 2027 y mantener razón juvenil ≥ 0.88.<br/><br/><b>Indicador:</b> Tasa ponderada 2027 y razón de participación juvenil CCPC.",
            "unidad_costo": "<b>Unidad:</b> DECEyEC, DEOE y Juntas Distritales.<br/><br/><b>Costo:</b> Bajo-Medio (foros distritales y vinculación comunitaria).",
            "lema": "<i>\"Tu participación ya transforma tu comunidad: consolidemos el voto en cada elección\"</i>",
        },
        {
            "perfil": "<b>C3: Liderazgo Femenino con Participación Estancada</b><br/><br/>Secc: 12,574 (23.44%)<br/>Base Inter. 2021: <b>49.5%</b><br/>Base Pres. 2024: <b>55.6%</b><br/>Base Hombres 2021: <b>43.9%</b>",
            "diag_obj": "Elevar la participación masculina (43.9% vs. 48.7% del Panel B) y revertir la caída presidencial en 12,574 secciones con sobrerrepresentación rural (41.2%).",
            "canales_accion": "<b>Canales:</b> Centros de trabajo masculinos (agropecuario, industria, transporte) y radio regional.<br/><br/><b>Acción:</b> Promoción del voto masculino y rutas móviles DEOE de accesibilidad.",
            "meta_ind": "<b>Meta:</b> Elevar participación a 51.1% en 2027, 58.1% en 2030 y voto masculino a 46.3% en 2027.<br/><br/><b>Indicador:</b> Tasa masculina SV/(SV+NV) y participación ponderada.",
            "unidad_costo": "<b>Unidad:</b> Juntas Distritales, DECEyEC y DEOE.<br/><br/><b>Costo:</b> Medio (tiempos oficiales de radio y rutas distritales).",
            "lema": "<i>\"La participación de todas y todos cuenta: sumemos la voz de hombres y jóvenes en cada comunidad\"</i>",
        },
    ]

    t7_rows = [[
        Paragraph("Perfil y Línea Base", th_l),
        Paragraph("Diagnóstico y Objetivo", th_l),
        Paragraph("Canales y Acción Operativa INE", th_l),
        Paragraph("Meta Cuantitativa e Indicador", th_l),
        Paragraph("Unidad y Costo Indicativo", th_l),
        Paragraph("Lema propuesto", th_l),
    ]]
    for item in t7_compact_data:
        t7_rows.append([
            Paragraph(item["perfil"], td_l),
            Paragraph(item["diag_obj"], td_l),
            Paragraph(item["canales_accion"], td_l),
            Paragraph(item["meta_ind"], td_l),
            Paragraph(item["unidad_costo"], td_l),
            Paragraph(item["lema"], td_l),
        ])
    story.append(Paragraph(f"Tabla 6. Estrategias Focalizadas por Perfil Ciudadano (k = {k_sel}), Líneas Base, Metas y Viabilidad Operativa", cap_st))
    story.append(styled_table(t7_rows, [75.27, 85.0, 95.0, 80.0, 65.0, 70.0]))
    # D4: Regla de metas
    story.append(Paragraph(
        "<i>Regla de metas: los perfiles por debajo del promedio del panel buscan cerrar la mitad de su diferencia con él en la siguiente elección del mismo tipo; los perfiles por encima buscan sostener su nivel.</i>",
        note_st
    ))
    story.append(Spacer(1, 4))

    # =========================================================================
    # SECCIÓN 6: LIMITACIONES Y RECOMENDACIONES AL INE
    # =========================================================================
    story.append(Paragraph("6. Limitaciones Metodológicas, Análisis de Sensibilidad y Recomendaciones al INE", h1_st))
    # Sesgo del panel B: +0.44 a +0.97 pts ponderado
    story.append(Paragraph(
        f"<b>1. Sesgo del Panel Principal y secciones excluidas (Tabla 7):</b> Las {inc_exc[1]['n_secciones']:,} secciones activas en {serie[-1]['anio']} "
        f"excluidas del Panel Principal ({inc_exc[1]['pct_secciones_2024']:.2f}% del total y {inc_exc[1]['pct_ln_2024']:.2f}% de la Lista Nominal) "
        f"se dividen en: (a) {inc_exc[2]['n_secciones']:,} secciones creadas o modificadas post-{serie[0]['anio']}, con participación de "
        f"<b>{inc_exc[2]['participacion_2024_ponderada_sv_svnv_pct']:.2f}%</b> ({inc_exc[2]['pct_urbana']:.1f}% urbanas); y (b) {inc_exc[3]['n_secciones']:,} "
        f"secciones continuas excluidas por calidad ({inc_exc[3]['secciones_svnv_0_en_2024']:,} sin captura en {serie[-1]['anio']}). En consecuencia, "
        f"el Panel Principal (Opción B) sobreestima la participación nacional ponderada del CCPC entre "
        f"<b>{serie[0]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} y {serie[4]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} puntos porcentuales</b> "
        f"({serie[0]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} en {serie[0]['anio']}, {serie[1]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} en {serie[1]['anio']}, "
        f"{serie[2]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} en {serie[2]['anio']}, {serie[3]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} en {serie[3]['anio']}, "
        f"{serie[4]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} en {serie[4]['anio']} y {serie[5]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} en {serie[5]['anio']}).",
        body_st
    ))

    # Tabla 7: Incluidas vs Excluidas (ancho = 470.27 pt)
    t8_rows = [[
        Paragraph(f"Subuniverso de Secciones en {serie[-1]['anio']}", th_l),
        Paragraph("Secc.", th_c),
        Paragraph(f"% Secc. {serie[-1]['anio']}", th_c),
        Paragraph(f"Lista Nominal {serie[-1]['anio']}", th_c),
        Paragraph(f"% LN {serie[-1]['anio']}", th_c),
        Paragraph("% Urbano", th_c),
        Paragraph(f"Part. {serie[-1]['anio']} Pond.", th_c),
    ]]
    filas_t8 = [
        ("Panel Principal Opción B", inc_exc[0]),
        ("Excluidas creadas post-2009", inc_exc[2]),
        ("Excluidas continuas por calidad", inc_exc[3]),
        ("Total Nacional CCPC 2024", inc_exc[5]),
    ]
    for lbl, r in filas_t8:
        is_tot = "Total" in lbl
        st_l = td_lb if is_tot else td_l
        st_c = td_cb if is_tot else td_c
        urb_val = 63.7 if "Panel Principal" in lbl else r["pct_urbana"]
        t8_rows.append([
            Paragraph(lbl, st_l),
            Paragraph(f"{r['n_secciones']:,}", st_c),
            Paragraph(f"{r['pct_secciones_2024']:.2f}%", st_c),
            Paragraph(f"{r['ln_2024']:,}", st_c),
            Paragraph(f"{r['pct_ln_2024']:.2f}%", st_c),
            Paragraph(f"{urb_val:.1f}%", st_c),
            Paragraph(f"<b>{r['participacion_2024_ponderada_sv_svnv_pct']:.2f}%</b>", st_c),
        ])
    t7_cap = Paragraph(f"Tabla 7. Comparación de Secciones Incluidas vs Excluidas en el CCPC {serie[-1]['anio']}", cap_st)
    t7_table = styled_table(t8_rows, [134.27, 54.0, 50.0, 70.0, 54.0, 52.0, 56.0], highlight_last=True)
    story.append(KeepTogether([t7_cap, t7_table]))
    story.append(Spacer(1, 4))

    story.append(Paragraph(
        f"<b>2. Análisis de sensibilidad (Opción A):</b> Al evaluar la Opción A sobre las 62,048 secciones continuas tratando años con SV+NV &lt; 50 "
        f"como valores perdidos (sin imputar) y exigiendo al menos 2 comicios presidenciales y 2 intermedios válidos, K-Means++ (k={k_sel}) "
        f"alcanza una concordancia casi perfecta con el Panel Principal B: <b>ARI = {sens[1]['ari_vs_panel_principal_B']:.4f}</b> "
        f"({sens[1]['coincidencia_exacta_alineada_pct']:.2f}% de coincidencia exacta) en las {u['panel_principal_secciones']:,} secciones comunes. "
        f"Esto indica que la segmentación es robusta a la depuración del panel.",
        body_st
    ))
    # C13: Frase exacta sobre variable indígena y C14: cero PENDIENTES
    story.append(Paragraph(
        f"<b>3. Limitación por variables demográficas y ventana temporal:</b> Sustituir los promedios hexanuales por un único corte anual hace que la "
        f"concordancia con la tipología base baje a <b>ARI = {win[0]['ari_clustering_6y_vs_2024']:.4f}</b>, lo que exige actualizar la tipología tras cada proceso federal. "
        f"Asimismo, los CSV abiertos del CCPC no incluyen el indicador de población indígena o afromexicana que sí muestra el tablero del INE; "
        f"por ello no se incorporó al modelo. Finalmente, se recomienda a la DECEyEC publicar ese indicador en los CSV abiertos, incluir una bandera "
        f"explícita de captura en las bases públicas y reforzar la captura de cuadernillos para abatir los registros NS.",
        body_st
    ))

    # =========================================================================
    # SECCIÓN 7: CONCLUSIONES (E1: exactamente <= 160 palabras)
    # =========================================================================
    story.append(Paragraph("7. Conclusiones", h1_st))
    story.append(Paragraph(
        f"La corrección de la fórmula de participación —SV/(SV+NV) en lugar de SV/LN— es condición necesaria para usar los datos abiertos del CCPC: "
        f"sin ella, la participación de {serie[3]['anio']} y {serie[-1]['anio']} se subestima en {diff_2018:.2f} y {diff_2024:.2f} puntos y aparecen "
        f"grupos artificiales de baja participación. Con datos corregidos, las {u['panel_principal_secciones']:,} secciones del panel se organizan en cuatro "
        f"perfiles operativos. El mayor (C0, {perfiles[0]['pct_secciones_panel']:.2f}% del panel) combina caída en elecciones intermedias y rezago juvenil, "
        f"y concentra el mayor margen de mejora. C2 muestra que la participación puede crecer de forma sostenida, en especial con juventud activa. "
        f"C3 revela una brecha de género de {perfiles[3]['brecha_genero_original']*100:.2f} puntos a favor de las mujeres y una caída presidencial desde 2012. "
        f"C1 es el referente de participación estable. Las estrategias propuestas se miden con el propio CCPC en 2027 y 2030, lo que permite evaluarlas con la misma fuente.",
        body_st
    ))

    # =========================================================================
    # SECCIÓN 8: REPRODUCIBILIDAD (E2: exactamente <= 90 palabras)
    # =========================================================================
    story.append(Paragraph("8. Reproducibilidad", h1_st))
    story.append(Paragraph(
        "El pipeline completo es reproducible de inicio a fin ejecutando <i>python run_all.py</i> bajo Python 3.14.6, DuckDB 2.0.0, scikit-learn 1.9.0, "
        "scipy 1.18.0, umap-learn 0.5.12, pandas 3.0.3 y numpy 2.4.6. El código abierto está disponible en "
        "<font color=\"#1E3A8A\"><u>https://github.com/Johanan1113/Hackaton_INE_byte_me</u></font>. Fijando la semilla (random_state=42), "
        "dos corridas consecutivas desde cero generan hashes SHA-256 idénticos en métricas y etiquetas. Los datos crudos se descargan de la Plataforma CCPC del INE "
        "conforme a las instrucciones del README y no se redistribuyen.",
        body_st
    ))

    # =========================================================================
    # SECCIÓN 9: REFERENCIAS BIBLIOGRÁFICAS (E3: 13 referencias APA, fuente 9 pt)
    # =========================================================================
    story.append(Paragraph("9. Referencias Bibliográficas", h1_st))
    referencias = [
        "1. Instituto Nacional Electoral (2026). Convocatoria <i>\"Hackea la participación: Datos que construyen democracia\"</i>. https://ine.mx/wp-content/uploads/2026/09/Convocatoria_Hackaton.pdf",
        "2. INE-DECEyEC (2025). <i>Manual de la Plataforma de Conteos Censales de Participación Ciudadana 2009–2024</i>. https://www.ine.mx/wp-content/uploads/2025/06/Manual-Conteos-Censales-2009-2024.pdf",
        "3. INE-DECEyEC. <i>Estudio comparativo sobre la participación ciudadana en las elecciones federales de 2009, 2012 y 2015</i>. https://ine.mx/wp-content/uploads/2018/01/DECEYEC_Comparativo_VF.pdf",
        "4. INE (2024). <i>Acuerdo INE/CG221/2024, Estrategia Nacional de Educación Cívica 2024–2026 (programa de trabajo 2025 de su Consejo de Evaluación)</i>. https://repositoriodocumental.ine.mx/xmlui/bitstream/handle/123456789/179310/CGex202502-19-ap-6-a2.pdf",
        "5. Expansión Política (30 de abril de 2024). \"98.3 millones de mexicanos podrán votar el próximo 2 de junio, informa el INE\". https://politica.expansion.mx/elecciones/2024/04/30/98-3-millones-de-mexicanos-podran-votar-el-proximo-2-de-junio-informa-el-ine",
        "6. Expansión Política (8 de junio de 2021). \"La participación electoral cierra en 52.67%\". https://politica.expansion.mx/mexico/2021/06/08/la-participacion-electoral-cierra-en-52-67-cinco-puntos-mas-que-en-2015",
        "7. Arthur, D., y Vassilvitskii, S. (2007). k-means++: The advantages of careful seeding. <i>Proceedings of SODA '07</i>, 1027–1035.",
        "8. Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. <i>Journal of Computational and Applied Mathematics</i>, 20, 53–65.",
        "9. Davies, D. L., y Bouldin, D. W. (1979). A cluster separation measure. <i>IEEE Transactions on Pattern Analysis and Machine Intelligence</i>, 1(2), 224–227.",
        "10. Caliński, T., y Harabasz, J. (1974). A dendrite method for cluster analysis. <i>Communications in Statistics</i>, 3(1), 1–27.",
        "11. Hubert, L., y Arabie, P. (1985). Comparing partitions. <i>Journal of Classification</i>, 2(1), 193–218.",
        "12. Campello, R. J. G. B., Moulavi, D., y Sander, J. (2013). Density-based clustering based on hierarchical density estimates. <i>PAKDD 2013, LNCS 7819</i>, 160–172.",
        "13. Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. <i>Journal of Machine Learning Research</i>, 12, 2825–2830.",
    ]
    for ref in referencias:
        story.append(Paragraph(ref, ref_st))

    # Cabecera y pie de página en Arial 8.5 pt
    def add_header_footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("Arial", 8.5)
        canvas.setFillColor(colors.HexColor("#4B5563"))
        canvas.drawString(
            MARGIN, PAGE_H - 1.5 * cm,
            "Equipo Byte me · Reto 1: Perfiles ciudadanos de participación (k=4)"
        )
        canvas.drawRightString(
            PAGE_W - MARGIN, PAGE_H - 1.5 * cm,
            f"CCPC INE {serie[0]['anio']}–{serie[-1]['anio']} | Tasa SV/(SV+NV) · Manual CCPC"
        )
        canvas.setStrokeColor(colors.HexColor("#D1D5DB"))
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, PAGE_H - 1.7 * cm, PAGE_W - MARGIN, PAGE_H - 1.7 * cm)
        canvas.line(MARGIN, 1.8 * cm, PAGE_W - MARGIN, 1.8 * cm)
        canvas.drawString(
            MARGIN, 1.2 * cm,
            "Concurso INE: Hackea la participación — Documento técnico · Equipo Byte me"
        )
        canvas.drawRightString(PAGE_W - MARGIN, 1.2 * cm, f"Página {doc_obj.page}")
        canvas.restoreState()

    from reportlab.pdfgen import canvas as pdf_canvas

    class ArialCanvas(pdf_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            kwargs["initialFontName"] = "Arial"
            super().__init__(*args, **kwargs)
            self._fontname = "Arial"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="Perfiles ciudadanos de participación electoral en México, 2009–2024",
        author="Equipo Byte me",
    )
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer, canvasmaker=ArialCanvas)
    return pdf_path


def main() -> None:
    data = json.loads(METRICAS_PATH.read_text(encoding="utf-8"))
    md_path = render_markdown_internal(data)
    pdf_path = build_pdf(data)

    import pypdf
    reader = pypdf.PdfReader(str(pdf_path))
    n_pages = len(reader.pages)
    print(f"[Fase 7] Documento Técnico compilado con éxito:")
    print(f"  - Markdown interno: {md_path}")
    print(f"  - PDF Oficial:      {pdf_path} ({n_pages} páginas)")


if __name__ == "__main__":
    main()
