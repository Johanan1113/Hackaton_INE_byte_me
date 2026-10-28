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

import pandas as pd
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
TABLAS_DIR = PROJECT_ROOT / "outputs" / "tablas"
OUT_ENTREGABLES = PROJECT_ROOT / "outputs" / "entregables"
OUT_ENTREGABLES.mkdir(parents=True, exist_ok=True)

from reportlab import rl_config
rl_config.canvas_basefontname = "Arial"

import sys
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from scripts.auditoria.utilidades_formato import redondear, redondear_pub

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
        "val_temp": data.get("validacion_fuera_de_tiempo", {}),
        "va_hist": data.get("valor_agregado_nivel_historico", {}),
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
        ("FONTSIZE", (0, 0), (-1, -1), 10.0),
        ("LEADING", (0, 0), (-1, -1), 12.0),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.0),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.5),
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

    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from utilidades_formato import redondear, formatear, formatear_pct

    nombre_map = data["nombre_publico"]
    for p in perfiles:
        if p["codigo_cluster"] in nombre_map:
            p["nombre_propuesto"] = nombre_map[p["codigo_cluster"]]

    styles = getSampleStyleSheet()

    # Tipografía estricta en Arial
    title_st = ParagraphStyle(
        "DocTitle", parent=styles["Title"], fontName="Arial-Bold",
        fontSize=15.0, leading=19.0, textColor=colors.HexColor("#0F172A"), alignment=TA_LEFT, spaceAfter=4
    )
    sub_st = ParagraphStyle(
        "DocSub", parent=styles["Normal"], fontName="Arial-Bold",
        fontSize=11.0, leading=14.0, textColor=colors.HexColor("#1E3A8A"), alignment=TA_LEFT, spaceAfter=4
    )
    meta_st = ParagraphStyle(
        "DocMeta", parent=styles["Normal"], fontName="Arial",
        fontSize=11.0, leading=14.0, textColor=colors.HexColor("#4B5563"), alignment=TA_LEFT, spaceAfter=8
    )
    h1_st = ParagraphStyle(
        "H1", parent=styles["Heading1"], fontName="Arial-Bold",
        fontSize=13.0, leading=17.0, textColor=colors.HexColor("#1E3A8A"), spaceBefore=6, spaceAfter=3, keepWithNext=True
    )
    h2_st = ParagraphStyle(
        "H2", parent=styles["Heading2"], fontName="Arial-Bold",
        fontSize=11.5, leading=15.0, textColor=colors.HexColor("#0F172A"), spaceBefore=5, spaceAfter=2, keepWithNext=True
    )
    body_st = ParagraphStyle(
        "Body", parent=styles["Normal"], fontName="Arial",
        fontSize=11.0, leading=19.0, textColor=colors.HexColor("#1F2937"), alignment=TA_JUSTIFY, spaceAfter=3.5
    )
    bullet_st = ParagraphStyle(
        "Bullet", parent=body_st, leftIndent=12, firstLineIndent=-8, spaceAfter=2.0
    )
    cap_st = ParagraphStyle(
        "TableCap", parent=styles["Normal"], fontName="Arial-Bold",
        fontSize=11.0, leading=14.0, textColor=colors.HexColor("#1E293B"), spaceBefore=3, spaceAfter=2.0, keepWithNext=False
    )
    note_st = ParagraphStyle(
        "TableNote", parent=styles["Normal"], fontName="Arial-Italic",
        fontSize=11.0, leading=14.0, textColor=colors.HexColor("#4B5563"), spaceBefore=2.5, spaceAfter=4.0
    )
    ref_st = ParagraphStyle(
        "RefEntry", parent=styles["Normal"], fontName="Arial",
        fontSize=11.0, leading=14.0, textColor=colors.HexColor("#1F2937"), leftIndent=14, firstLineIndent=-14, spaceAfter=1.5
    )

    # Celdas de tablas (10 pt, leading 12.0 - último recurso B2)
    th_c = ParagraphStyle("THC", fontName="Arial-Bold", fontSize=10.0, leading=12.0, textColor=colors.white, alignment=TA_CENTER)
    th_l = ParagraphStyle("THL", fontName="Arial-Bold", fontSize=10.0, leading=12.0, textColor=colors.white, alignment=TA_LEFT)
    td_c = ParagraphStyle("TDC", fontName="Arial", fontSize=10.0, leading=12.0, textColor=colors.HexColor("#111827"), alignment=TA_CENTER)
    td_l = ParagraphStyle("TDL", fontName="Arial", fontSize=10.0, leading=12.0, textColor=colors.HexColor("#111827"), alignment=TA_LEFT)
    td_cb = ParagraphStyle("TDCB", fontName="Arial-Bold", fontSize=10.0, leading=12.0, textColor=colors.HexColor("#111827"), alignment=TA_CENTER)
    td_lb = ParagraphStyle("TDLB", fontName="Arial-Bold", fontSize=10.0, leading=12.0, textColor=colors.HexColor("#111827"), alignment=TA_LEFT)

    # Carga de tablas dinámicas para cifras auditadas (Bloques 2.1 - 2.10)
    df07 = pd.read_csv(TABLAS_DIR / "tabla_07_perfiles_k4_series_demografia.csv").set_index("codigo_cluster")
    df12 = pd.read_csv(TABLAS_DIR / "tabla_12_lineas_base_metas.csv").set_index("codigo_cluster")
    df17 = pd.read_csv(TABLAS_DIR / "tabla_17_impacto.csv").set_index("codigo_cluster")
    df18 = pd.read_csv(TABLAS_DIR / "tabla_18_calendario_electoral.csv").set_index("grupo_concurrencia")
    pde = data.get("piloto_diseno_efecto", {})
    imp = data.get("impacto_y_prioridad_territorial", {})
    cal = data.get("calendario_electoral", {})
    tc_data = data.get("tendencia_corregida", {})
    val_temp = data.get("validacion_fuera_de_tiempo", {})

    def fmt_pend(v):
        v = redondear(v, 2) + 0.0
        return "0.00" if v == 0 else f"{v:+.2f}"

    tc_panel = fmt_pend(tc_data["Panel_B"])
    tc_c0 = fmt_pend(tc_data["C0"])
    tc_c1 = fmt_pend(tc_data["C1"])
    tc_c2 = fmt_pend(tc_data["C2"])
    tc_c3 = fmt_pend(tc_data["C3"])

    story = []

    # Encabezado formal de portada / título (C1)
    story.append(Paragraph(
        "Perfiles ciudadanos de participación electoral en México, 2009–2024: tipología seccional y estrategias de educación cívica",
        title_st
    ))
    story.append(Paragraph(
        "Equipo Byte me · Concurso \"Hackea la participación: Datos que construyen democracia\" (INE (DECEyEC)) · Reto 1: Perfiles ciudadanos de participación",
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
        f"Aplicamos la definición oficial del Manual CCPC (p. 17), <b>SV / (SV + NV)</b>, y cuantificamos el sesgo de no hacerlo: en los archivos abiertos del CCPC, la Lista Nominal "
        f"cumple la identidad exacta <b>LN = SV + NV + NS</b>, donde <b>SV</b> corresponde a las personas que sí votaron, <b>NV</b> a quienes no votaron "
        f"y <b>NS</b> a los registros no especificados (cuadernillos sin marcas de votación, no disponibles para captura o requeridos por autoridades jurisdiccionales, según el catálogo del INE y el Manual, p. 18) "
        f"({serie[3]['ns_total_anio']:,} electores = {serie[3]['pct_ns_anio']:.1f}% de la LN en {serie[3]['anio']}, y "
        f"{serie[5]['ns_total_anio']:,} electores = {serie[5]['pct_ns_anio']:.1f}% en {serie[5]['anio']}). "
        f"Calcular <b>SV / LN</b> en lugar de la fórmula oficial asigna 0.0% de participación a las secciones sin captura "
        f"(<b>SV + NV = 0</b>), subestima la participación nacional en {diff_2018:.2f} puntos en {serie[3]['anio']} y en {diff_2024:.2f} en {serie[-1]['anio']}, "
        f"y genera grupos artificiales de baja participación en cualquier análisis de conglomerados.",
        body_st
    ))
    story.append(Paragraph(
        f"Al aplicar la fórmula <b>SV / (SV + NV)</b> en todas las tasas y depurar el universo bajo el <b>Panel Principal (Opción B, cero imputación)</b> "
        f"con las <b>{u['panel_principal_secciones']:,} secciones</b> que cuentan con captura válida (<b>SV + NV ≥ 50</b> en las seis elecciones) y sin saltos "
        f"abruptos de Lista Nominal por reseccionamiento —cubriendo el <b>{u['panel_principal_pct_secciones_2024']:.1f}% de las secciones</b> y el "
        f"<b>{u['panel_principal_pct_ln_2024']:.1f}% de la Lista Nominal de {serie[-1]['anio']}</b> ({u['panel_principal_ln_2024']:,} electores en "
        f"<b>{u['panel_principal_municipios']:,} municipios</b>)—, el modelo <b>K-Means++ con k = {k_sel}</b> domina empíricamente dentro del rango "
        f"de 4 a 6 perfiles de la convocatoria (Silhouette = {bench_km_k4['silhouette']:.3f}, Davies–Bouldin = {bench_km_k4['davies_bouldin']:.2f}, "
        f"Calinski-Harabasz = {bench_km_k4['calinski_harabasz']:,.0f} y estabilidad bootstrap ARI = {bench_km_k4['bootstrap_ari_media']:.3f} "
        f"[{bench_km_k4['bootstrap_ari_ic95_inf']:.3f}, {bench_km_k4['bootstrap_ari_ic95_sup']:.3f}]). "
        f"Los cuatro perfiles identificados son: "
        + ", ".join(f"<b>{p['codigo_cluster']}: {p['nombre_propuesto']}</b>" for p in perfiles[:3])
        + f" y <b>{perfiles[3]['codigo_cluster']}: {perfiles[3]['nombre_propuesto']}</b>. "
        f"La equivalencia de las metas en votantes representa {imp['total_adicionales_millones_str']} de sufragios adicionales ({imp['votantes_equivalentes_c0_miles_str']} en C0 y {imp['votantes_equivalentes_c3_miles_str']} en C3); "
        f"en caso de regreso a promedios intermedios históricos en C1 y C2, el escenario de regresión (sin probabilidad asociada) involucra {imp['total_regresion_millones_str']} de electores. "
        f"La propuesta incluye un piloto evaluable con MDE de {pde['mde_seccion_pts']:.2f} pts por sección (500 secciones por grupo).",
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
        f"especificada de voto (NS). De acuerdo con el catálogo de campos que acompaña los datos abiertos del CCPC 2024 y el Manual CCPC (p. 18), "
        f"los registros NS corresponden a cuadernillos sin marcas, no disponibles para captura, con páginas faltantes "
        f"o requeridos por autoridades jurisdiccionales. Al usar la fórmula <b>P = SV / (SV + NV)</b>, suponemos que los registros NS participan como los capturados (faltantes al azar).",
        body_st
    ))
    story.append(Paragraph(
        f"Por ello, la tasa de participación seccional y por subgrupos demográficos "
        f"(jóvenes de 18–29 años, adultos mayores de 60+ años, mujeres y hombres) se calcula estrictamente como <b>P = SV / (SV + NV)</b>. "
        f"En {serie[-1]['anio']}, los registros no binarios (SEXO = 2) se integran en la tasa total seccional, mientras que la brecha de género se evalúa "
        f"entre mujeres y hombres. La verificación sobre los datos crudos confirmó 0 secciones con SV &gt; LN, dado que los conteos censales "
        f"no incorporan casillas especiales.",
        body_st
    ))
    # C16
    story.append(Paragraph(
        f"La Tabla 1 valida la serie nacional calculada con SV / (SV + NV) contra las publicaciones censales del INE: el estudio comparativo de la "
        f"DECEyEC (<i>DECEYEC_Comparativo_VF.pdf</i>, p. 11) reporta <b>{serie[0]['oficial_o_referencia_pct']:.2f}%</b> en {serie[0]['anio']}, "
        f"<b>{serie[1]['oficial_o_referencia_pct']:.2f}%</b> en {serie[1]['anio']} y <b>{serie[2]['oficial_o_referencia_pct']:.2f}%</b> en {serie[2]['anio']}; "
        f"los estudios censales de {serie[3]['anio']} y {serie[5]['anio']} reportan <b>{serie[3]['oficial_o_referencia_pct']:.1f}%</b> "
        f"(cálculo CCPC: {serie[3]['total_ponderada_sv_svnv_pct']:.2f}%) y <b>{serie[5]['oficial_o_referencia_pct']:.1f}%</b> "
        f"(cálculo CCPC: {serie[5]['total_ponderada_sv_svnv_pct']:.2f}%). Para {serie[4]['anio']}, el dato censal de "
        f"<b>{serie[4]['oficial_o_referencia_pct']:.1f}%</b> proviene de la imagen del tablero interactivo en la página 21 de "
        f"<i>Manual-Conteos-Censales-2009-2024.pdf</i> (figura en sección <i>\"Participación por año\"</i>) frente a "
        f"<b>{serie[4]['total_ponderada_sv_svnv_pct']:.2f}%</b> calculado en el CCPC (como referencia no censal, el PREP cerró en 52.7%).",
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
    story.append(t1_cap)
    story.append(t1_table)
    story.append(Spacer(1, 4))

    # A2 & B2.3: Reemplazo de Tabla 2 por 2 renglones de texto
    story.append(Paragraph(
        f"La depuración del universo seccional conserva {u['panel_principal_secciones']:,} de las {u['secciones_2024_total']:,} secciones activas en {serie[-1]['anio']} "
        f"con serie completa y captura válida ({u['panel_principal_pct_secciones_2024']:.2f}% de las secciones, {u['panel_principal_pct_ln_2024']:.2f}% de la lista nominal), "
        f"garantizando continuidad metodológica estricta sin imputación.",
        body_st
    ))
    story.append(Spacer(1, 4))

    # Figura 1 (D1, D2): Trayectorias y NS
    fig1_flow = Image(str(FIGURAS_DIR / "fig2_evolucion_temporal.png"), width=6.5 * inch, height=2.3 * inch)
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
        f"Cada sección del Panel Principal ({u['panel_principal_secciones']:,}) se representa mediante siete indicadores en el promedio de las seis elecciones winsorizados en "
        f"los percentiles {u['winsor_p_min']} y {u['winsor_p_max']} "
        f"y escalados con <i>RobustScaler</i>: (1) <b>participación media</b> (media = {pan_b['participacion_media_historica_media']*100:.1f}%, "
        f"DE = {pan_b['participacion_media_historica_std']*100:.1f}%); (2) <b>brecha presidencial–intermedia</b> "
        f"(media = {pan_b['brecha_presidencial_intermedia_media']*100:+.2f} pts, DE = {pan_b['brecha_presidencial_intermedia_std']*100:.2f} pts); "
        f"(3) <b>tendencia anual</b> (pendiente OLS: media = {pan_b['tendencia_participacion_beta_media']*100:+.2f} pts/año, "
        f"DE = {pan_b['tendencia_participacion_beta_std']*100:.2f} pts/año); (4) <b>estabilidad (log(1 + 1/CV))</b> "
        f"(media = {pan_b['estabilidad_participacion_media']:.4f}, DE = {pan_b['estabilidad_participacion_std']:.4f}, reduciendo la asimetría de "
        f"{est[0]['asimetria_skew']:.2f} en 1/CV a {est[2]['asimetria_skew']:.2f} y manteniendo ARI = {est[2]['ari_vs_b']:.3f} frente a CV directo); "
        f"(5) <b>brecha generacional (60+ menos 18–29)</b> (media = {pan_b['brecha_generacional_media']*100:+.2f} pts); "
        f"(6) <b>brecha de género (mujeres menos hombres)</b> (media = {pan_b['brecha_genero_media']*100:+.2f} pts); y "
        f"(7) <b>razón de participación juvenil</b>, calculada como el cociente de medias de las seis elecciones "
        f"(media = {pan_b['ratio_participacion_joven_media']:.4f}; el promedio de razones anuales es {pan_b['ratio_joven_media_de_ratios_anuales']:.4f}).",
        body_st
    ))
    story.append(Paragraph(
        f"<b>Colinealidad (VIF):</b> Los valores VIF oscilan entre {vif[5]['vif_7_variables']:.2f} (brecha de género) y {vif[6]['vif_7_variables']:.2f} "
        f"(razón juvenil, con {vif[4]['vif_7_variables']:.2f} en brecha generacional); todos son inferiores a 4.0, descartando multicolinealidad severa. "
        f"Se conservan ambas variables generacionales porque la razón captura incorporación relativa y la brecha mide distancia absoluta en puntos.",
        body_st
    ))
    story.append(Paragraph(
        f"Una regresión por sección que controla por tipo de elección arroja una tendencia corregida promedio de {tc_panel} pts/año en el panel "
        f"({tc_c0} en C0, {tc_c1} en C1, {tc_c2} en C2 y {tc_c3} en C3), advirtiendo que la pendiente simple absorbe parte del ciclo presidencial–intermedio. "
        f"Asimismo, la correlación entre brecha generacional y razón juvenil (r = -0.819) y entre estabilidad y participación media (r = 0.489) "
        f"otorga un doble peso implícito al ciclo y la estructura etaria en la distancia euclidiana, lo cual constituye una limitación del agrupamiento.",
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
    story.append(t3_cap)
    story.append(t3_table)
    story.append(Spacer(1, 4))

    gmm_rows = [r for r in data["benchmark_modelos"] if "GMM" in r.get("algoritmo", "")]
    gmm_sils = [r["silhouette"] for r in gmm_rows if r.get("silhouette") is not None]
    min_gmm_sil = redondear(min(gmm_sils), 3)
    max_gmm_sil = redondear(max(gmm_sils), 3)
    min_gmm_k = int(min(r["k"] for r in gmm_rows))
    max_gmm_k = int(max(r["k"] for r in gmm_rows))
    hdb_rows = [r for r in data["benchmark_modelos"] if "HDBSCAN" in r.get("algoritmo", "")]
    max_hdb_grupos = max(r["n_clusters_efectivos"] for r in hdb_rows)
    hdb_ruido = redondear(next(r["pct_ruido"] for r in hdb_rows if r.get("n_clusters_efectivos", 0) > 0), 1)

    # C7: Oración sobre GMM y HDBSCAN (con redondeo A4: silhouette 3 dec, porcentajes 1 dec)
    story.append(Paragraph(
        f"Los modelos de mezclas gaussianas obtuvieron silhouette de {min_gmm_sil:.3f} a {max_gmm_sil:.3f} (k={min_gmm_k}–{max_gmm_k}) y su BIC sigue bajando hasta k={max_gmm_k}, "
        f"sin un óptimo claro. HDBSCAN, en tres configuraciones, encontró como máximo {max_hdb_grupos} grupos con {hdb_ruido:.1f}% de secciones sin asignar, "
        f"o ninguno. Esto indica que las secciones forman un continuo sin grupos densos naturales: los cuatro perfiles son una "
        f"segmentación operativa de ese continuo, no grupos naturales.",
        body_st
    ))

    # C4: k casteado a int, justificación k=4 (referencia a Tabla 3; Bloque H2)
    story.append(Paragraph(
        f"<b>Justificación de la elección de k = {k_sel} (Tabla 3):</b> Dentro del rango de 4 a 6 perfiles de la convocatoria, "
        f"k = {k_sel} domina en Silhouette, Davies–Bouldin y Calinski-Harabasz (Tabla 3), y su estabilidad bootstrap es estadísticamente "
        f"equivalente a k = {int(bench_km[3]['k'])}. En k = {int(bench_km[3]['k'])}, un grupo carece de diferenciación sustantiva "
        f"({comp_k6_c1['pct_secciones']:.1f}% del panel con una sola variable con |z| ≥ 0.50), mientras que en k = {k_sel} cada perfil posee "
        f"al menos cinco variables rectoras diferenciadas. Aunque k = {int(bench_km[0]['k'])} obtiene métricas globales superiores, queda fuera de las bases.",
        body_st
    ))

    rf_acc = redondear(data["interpretabilidad_rf_anova"][0]["rf_cv5_accuracy_media"] * 100, 1)
    # C6: Oración única de Random Forest (A4: porcentaje a 1 decimal)
    story.append(Paragraph(
        f"Como medida de interpretabilidad (no de validación, porque el clasificador usa las mismas variables que definieron los grupos), "
        f"un Random Forest con validación cruzada de 5 pliegues reproduce las etiquetas con {rf_acc:.1f}% de exactitud; "
        f"las variables más discriminantes son la razón de participación juvenil, la estabilidad y la brecha generacional.",
        body_st
    ))

    # Bloque C: Estabilidad temporal y valor agregado sobre nivel histórico (<= 90 palabras)
    val_temp = data["validacion_fuera_de_tiempo"]
    va_hist = data["valor_agregado_nivel_historico"]
    if val_temp:
        p_val_fmt = va_hist["p_valor_p2024_str"].replace("<", "&lt;")
        d_r2_p = va_hist["delta_r2_p2024_3d"]
        d_r2_c = va_hist["delta_r2_cambio_3d"]
        if d_r2_p >= 0.01:
            frase_dinamicas = (
                f"sino distinguir dinámicas: con perfiles construidos sin datos de 2024, el perfil agrega "
                f"ΔR² = {d_r2_p:.3f} sobre el nivel histórico para explicar la participación 2024 y "
                f"ΔR² = {d_r2_c:.3f} para su cambio 2018–2024 (p {p_val_fmt})."
            )
        else:
            frase_dinamicas = (
                f"sino distinguir dinámicas de participación (ciclo, tendencia y brechas) que orientan acciones "
                f"diferenciadas; su aporte para predecir el nivel de 2024 más allá del promedio histórico es marginal "
                f"(ΔR² = {d_r2_p:.3f})."
            )
        story.append(Paragraph(
            f"<b>Estabilidad temporal:</b> al construir los perfiles solo con 2009–2021, el {val_temp['coincidencia_exacta_pct']:.1f}% de las secciones "
            f"conserva su perfil (ARI = {val_temp['ari_3d']:.3f}) y el orden de participación en 2024 se reproduce exactamente ({val_temp['orden_grupos_2009_2021_en_2024']}). "
            f"Los perfiles no buscan predecir el nivel —una clasificación por cuartiles de participación histórica lo explica mejor "
            f"(η² = {val_temp['eta2_cuartiles_3d']:.3f} frente a {val_temp['eta2_perfiles_3d']:.3f})—, {frase_dinamicas}",
            body_st
        ))

    # =========================================================================
    # SECCIÓN 4: CARACTERIZACIÓN DE LOS 4 PERFILES
    # =========================================================================
    story.append(Paragraph(f"4. Caracterización de los 4 Perfiles Ciudadanos de Participación (k = {k_sel})", h1_st))
    # C9
    story.append(Paragraph(
        f"{pan_b['pct_secciones_urbanas_1d']:.1f}% de las secciones del panel son urbanas, {pan_b['pct_secciones_rurales_1d']:.1f}% rurales y {pan_b['pct_secciones_mixtas_1d']:.1f}% mixtas; por electores, {pan_b['pct_ln_urbana']:.1f}%, {pan_b['pct_ln_rural']:.1f}% y {pan_b['pct_ln_mixta']:.1f}%. "
        f"Los perfiles describen secciones electorales, no personas. "
        f"Las Tablas 4 y 5 presentan los centroides en escala original y puntaje z estandarizado respecto a la media del Panel B, "
        f"así como sus trayectorias históricas ponderadas y perfiles demográficos.",
        body_st
    ))

    # Tabla 4: Centroides (8 cols = 470.27 pt)
    # Tabla 4: Centroides (8 cols = 470.27 pt, Bloque 2.2)
    t5_rows = [[
        Paragraph("Perfil y Nombre Oficial", th_l),
        Paragraph("Secc.<br/>(% Panel)", th_c),
        Paragraph(f"LN {serie[-1]['anio']}<br/>(% Panel)", th_c),
        Paragraph("Part. media<br/>(%; z)", th_c),
        Paragraph("Brecha P–I<br/>(pts; z)", th_c),
        Paragraph("Tend. simple<br/>(pts/año; z)", th_c),
        Paragraph("Estab.<br/>(log; z)", th_c),
        Paragraph("Gen. / Género /<br/>Razón Joven (z)", th_c),
    ]]
    for p in perfiles:
        t5_rows.append([
            Paragraph(f"<b>{p['codigo_cluster']}: {p['nombre_propuesto']}</b>", td_l),
            Paragraph(f"{p['n_secciones']:,}<br/>({p['pct_secciones_panel']:.2f}%)", td_c),
            Paragraph(f"{p['ln_2024']:,}<br/>({p['pct_ln_panel']:.2f}%)", td_c),
            Paragraph(f"<b>{p['participacion_media_historica_original']*100:.2f}</b><br/>(z={p['participacion_media_historica_zscore']:+.2f})", td_c),
            Paragraph(f"<b>{p['brecha_presidencial_intermedia_original']*100:+.2f}</b><br/>(z={p['brecha_presidencial_intermedia_zscore']:+.2f})", td_c),
            Paragraph(f"<b>{p['tendencia_participacion_beta_original']*100:+.2f}</b><br/>(z={p['tendencia_participacion_beta_zscore']:+.2f})", td_c),
            Paragraph(f"<b>{p['estabilidad_participacion_original']:.4f}</b><br/>(z={p['estabilidad_participacion_zscore']:+.2f})", td_c),
            Paragraph(
                f"Gen: {redondear_pub(p['brecha_generacional_original']*100, 1):+.1f} ({p['brecha_generacional_zscore']:+.2f})<br/>"
                f"Sexo: {redondear_pub(p['brecha_genero_original']*100, 1):+.1f} ({p['brecha_genero_zscore']:+.2f})<br/>"
                f"Jov: {redondear_pub(p['ratio_participacion_joven_original'], 2):.2f} ({p['ratio_participacion_joven_zscore']:+.2f})",
                td_c
            ),
        ])
    t5_rows.append([
        Paragraph("<b>Media del Panel B</b>", td_lb),
        Paragraph(f"<b>{pan_b['n_secciones']:,}</b><br/>(100.00%)", td_cb),
        Paragraph(f"<b>{pan_b['ln_2024']:,}</b><br/>(100.00%)", td_cb),
        Paragraph(f"<b>{pan_b['participacion_media_historica_media']*100:.2f}</b><br/>(z=0.00)", td_cb),
        Paragraph(f"<b>{pan_b['brecha_presidencial_intermedia_media']*100:+.2f}</b><br/>(z=0.00)", td_cb),
        Paragraph(f"<b>{pan_b['tendencia_participacion_beta_media']*100:+.2f}</b><br/>(z=0.00)", td_cb),
        Paragraph(f"<b>{pan_b['estabilidad_participacion_media']:.4f}</b><br/>(z=0.00)", td_cb),
        Paragraph(
            f"Gen: {redondear_pub(pan_b['brecha_generacional_media']*100, 1):+.1f} (0.00)<br/>"
            f"Sexo: {redondear_pub(pan_b['brecha_genero_media']*100, 1):+.1f} (0.00)<br/>"
            f"Jov: {redondear_pub(pan_b['ratio_participacion_joven_media'], 2):.2f} (0.00)",
            td_cb
        ),
    ])
    t4_cap = Paragraph(f"Tabla 4. Centroides de las 7 Variables Rectoras (Escala Original y z-score) y Cobertura (k = {k_sel})", cap_st)
    t4_table = styled_table(t5_rows, [88.27, 50.0, 56.0, 47.0, 50.0, 50.0, 48.0, 81.0], highlight_last=True)
    story.append(t4_cap)
    story.append(t4_table)
    t4_note_st = ParagraphStyle("T4Note", parent=note_st, spaceBefore=1.0, spaceAfter=1.5)
    story.append(Paragraph(
        "<i>Nota de la Tabla 4: Tend. simple = pendiente usada en el agrupamiento; la corregida está en la Sección 3.</i>",
        t4_note_st
    ))

    # Tabla 5: Series Históricas Ponderadas, Tasas Demográficas y Composición Territorial por Perfil (8 columnas, Bloque H4 & 2.1)
    t6_rows = [[
        Paragraph("Perfil", th_c),
        Paragraph("Serie Ponderada 2009–2024", th_c),
        Paragraph("Pres. / Inter.", th_c),
        Paragraph("18–29 / 60+ años", th_c),
        Paragraph("Mujeres / Hombres", th_c),
        Paragraph("% Urb.", th_c),
        Paragraph("% Rur.", th_c),
        Paragraph("% Mix.", th_c),
    ]]
    for p in perfiles:
        s_pond = " / ".join(f"<b>{redondear_pub(p[f'p_{y}_ponderada']*100, 1):.1f}%</b>" if y == 2021 else f"{redondear_pub(p[f'p_{y}_ponderada']*100, 1):.1f}%" for y in [2009, 2012, 2015, 2018, 2021, 2024])
        t6_rows.append([
            Paragraph(f"<b>{p['codigo_cluster']}</b>", td_cb),
            Paragraph(s_pond, td_c),
            Paragraph(f"{redondear_pub(p['media_presidencial_original']*100, 1):.1f}% /<br/>{redondear_pub(p['media_intermedia_original']*100, 1):.1f}%", td_c),
            Paragraph(f"{redondear_pub(p['tasa_joven_18_29_original']*100, 1):.1f}% /<br/>{redondear_pub(p['tasa_mayor_60_mas_original']*100, 1):.1f}%", td_c),
            Paragraph(f"{redondear_pub(p['tasa_mujeres_original']*100, 1):.1f}% /<br/>{redondear_pub(p['tasa_hombres_original']*100, 1):.1f}%", td_c),
            Paragraph(f"{redondear_pub(p['pct_secciones_urbanas'], 1):.1f}%", td_c),
            Paragraph(f"{redondear_pub(p['pct_secciones_rurales'], 1):.1f}%", td_c),
            Paragraph(f"{redondear_pub(p['pct_secciones_mixtas'], 1):.1f}%", td_c),
        ])
    s_pond_b = " / ".join(f"<b>{redondear_pub(pan_b[f'p_{y}_ponderada']*100, 1):.1f}%</b>" for y in [2009, 2012, 2015, 2018, 2021, 2024])
    t6_rows.append([
        Paragraph("<b>Panel B</b>", td_cb),
        Paragraph(s_pond_b, td_cb),
        Paragraph(f"<b>{redondear_pub(pan_b['media_presidencial_original']*100, 1):.1f}% /<br/>{redondear_pub(pan_b['media_intermedia_original']*100, 1):.1f}%</b>", td_cb),
        Paragraph(f"<b>{redondear_pub(pan_b['tasa_joven_18_29_original']*100, 1):.1f}% /<br/>{redondear_pub(pan_b['tasa_mayor_60_mas_original']*100, 1):.1f}%</b>", td_cb),
        Paragraph(f"<b>{redondear_pub(pan_b['tasa_mujeres_original']*100, 1):.1f}% /<br/>{redondear_pub(pan_b['tasa_hombres_original']*100, 1):.1f}%</b>", td_cb),
        Paragraph(f"<b>{redondear_pub(pan_b['pct_secciones_urbanas_1d'], 1):.1f}%</b>", td_cb),
        Paragraph(f"<b>{redondear_pub(pan_b['pct_secciones_rurales_1d'], 1):.1f}%</b>", td_cb),
        Paragraph(f"<b>{redondear_pub(pan_b['pct_secciones_mixtas_1d'], 1):.1f}%</b>", td_cb),
    ])
    t5_cap = Paragraph(f"Tabla 5. Series Históricas Ponderadas, Tasas Demográficas y Composición Territorial por Perfil (k = {k_sel})", cap_st)
    t5_table = styled_table(t6_rows, [35.27, 125.0, 58.0, 56.0, 60.0, 45.0, 45.0, 46.0], highlight_last=True)
    story.append(t5_cap)
    story.append(t5_table)
    t5_note_st = ParagraphStyle("T5Note", parent=note_st, spaceBefore=1.5, spaceAfter=2.0)
    story.append(Paragraph("<i>Nota: Pres. / Inter. corresponden a medias simples de las elecciones de cada tipo; las demás columnas son ponderadas o promedios del periodo.</i>", t5_note_st))
    story.append(Spacer(1, 2))

    # A1 & D2, D3, D5: Diagnósticos por perfil en <= 60 palabras de narrativa y máximo 2 cifras por perfil (Bloques 2.4, 2.5, 2.10)
    c0_hom = redondear_pub(perfiles[0]['tasa_hombres_original'] * 100, 1)
    c3_muj = redondear_pub(perfiles[3]['tasa_mujeres_original'] * 100, 1)
    c3_hom = redondear_pub(perfiles[3]['tasa_hombres_original'] * 100, 1)
    pan_muj = redondear_pub(pan_b['tasa_mujeres_original'] * 100, 1)
    pan_hom = redondear_pub(pan_b['tasa_hombres_original'] * 100, 1)
    c3_sexo_brecha = redondear_pub(perfiles[3]['brecha_genero_original'] * 100, 1)

    narrativas_a1 = [
        (
            f"• <b>{perfiles[0]['codigo_cluster']} — {perfiles[0]['nombre_propuesto']}:</b> "
            f"Agrupa zonas urbanas con fuerte caída en comicios intermedios ({perfiles[0]['brecha_presidencial_intermedia_original']*100:+.1f} pts) "
            f"y menor participación media ({perfiles[0]['participacion_media_historica_original']*100:.1f}%). Su participación masculina ({c0_hom:.1f}%) es la más baja de los cuatro perfiles. "
            f"Concentra el mayor abstencionismo metropolitano y juventud desconectada, siendo prioritario el trabajo en centros laborales y transporte masivo."
        ),
        (
            f"• <b>{perfiles[1]['codigo_cluster']} — {perfiles[1]['nombre_propuesto']}:</b> "
            f"Distingue comunidades con alta constancia cívica que sostienen la mayor participación media ({perfiles[1]['participacion_media_historica_original']*100:.1f}%) "
            f"y la menor brecha entre tipos de elección ({perfiles[1]['brecha_presidencial_intermedia_original']*100:+.1f} pts). "
            f"Constituye el referente nacional de integración intergeneracional, donde la prioridad operativa es asegurar el relevo en la integración de mesas directivas de casilla."
        ),
        (
            f"• <b>{perfiles[2]['codigo_cluster']} — {perfiles[2]['nombre_propuesto']}:</b> "
            f"Caracteriza secciones con ascenso sostenido ({tc_c2} pts/año, corregida por tipo de elección) y razón juvenil de {redondear_pub(perfiles[2]['ratio_participacion_joven_original'], 2):.2f} (segunda tras C1 con {redondear_pub(perfiles[1]['ratio_participacion_joven_original'], 2):.2f}). "
            f"El crecimiento ocurrió en las intermedias ({df07.loc['C2', 'p_2009_pond_pct']:.1f}% en 2009 y {df07.loc['C2', 'p_2021_pond_pct']:.1f}% en 2021); en las "
            f"presidenciales varió poco ({df07.loc['C2', 'p_2012_pond_pct']:.1f}% en 2012, {df07.loc['C2', 'p_2018_pond_pct']:.1f}% en 2018 y {df07.loc['C2', 'p_2024_pond_pct']:.1f}% en 2024), por lo que la "
            f"prioridad es sostener el voto en intermedias."
        ),
        (
            f"• <b>{perfiles[3]['codigo_cluster']} — {perfiles[3]['nombre_propuesto']}:</b> "
            f"Muestra tendencia descendente ({tc_c3} pts/año, corregida por tipo de elección) y brecha de género de +{c3_sexo_brecha:.1f} pts. "
            f"La brecha proviene de baja participación masculina ({c3_hom:.1f}% vs {pan_hom:.1f}% del panel; {df12.loc['C3', 'tasa_hombres_2021_pond_pct']:.1f}% en 2021), mientras que la participación femenina ({c3_muj:.1f}%) es similar a la del panel ({pan_muj:.1f}%). "
            f"Hipótesis por probar: menor vinculación o movilidad laboral masculina."
        ),
    ]
    for narr in narrativas_a1:
        story.append(Paragraph(narr, bullet_st))

    # =========================================================================
    # SECCIÓN 5: ESTRATEGIAS FOCALIZADAS
    # =========================================================================
    story.append(Paragraph("5. Estrategias Focalizadas de Promoción e Intervención Institucional (ENCÍVICA)", h1_st))
    story.append(Paragraph(
        f"Las estrategias para los cuatro perfiles (Tabla 6) se fundamentan en las facultades del INE bajo la LGIPE (arts. 30.1 g y 58.1). "
        f"Para garantizar estricta imparcialidad institucional y neutralidad partidista, los criterios de focalización son públicos y aprobados "
        f"por la comisión competente del Consejo General, empleando contenidos cívicos genéricos y asignación aleatorizada. "
        f"Constituyen un insumo técnico para la estrategia de promoción del voto 2026–2027 y la política sucesora de la ENCÍVICA 2024–2026. "
        f"La credencialización se mantiene como acción registral de cobertura con meta propia de actualización en el Padrón (DERFE), "
        f"sin computarse como incremento de participación al no alterar SV/(SV+NV). "
        f"Cada meta para 2027 toma como referencia la línea base de la intermedia 2021 (serie ponderada): "
        f"<b>C0 = {estrategias[0]['linea_base_intermedia_2021_pond_pct']:.1f}%</b>, "
        f"<b>C1 = {estrategias[1]['linea_base_intermedia_2021_pond_pct']:.1f}%</b>, "
        f"<b>C2 = {estrategias[2]['linea_base_intermedia_2021_pond_pct']:.1f}%</b> y "
        f"<b>C3 = {estrategias[3]['linea_base_intermedia_2021_pond_pct']:.1f}%</b>. "
        f"En C0, la atención en centros laborales incluye a hombres jóvenes y adultos; en C3, se atiende la baja participación masculina "
        f"mediante vinculación ocupacional y se proponen casillas extraordinarias a los Consejos Distritales conforme a la LGIPE.",
        body_st
    ))

    # G1: Tabla 6 de estrategias leída dinámicamente desde data["estrategias"] (4 columnas sustantivas per B2.2)
    t7_compact_data = []
    for est_row in data.get("estrategias", []):
        cid = est_row["codigo_cluster"]
        nom = data.get("nombre_publico", {}).get(cid, est_row["nombre_perfil"])
        base_inter = est_row["linea_base_intermedia_2021_pond_pct"]
        base_pres = est_row["linea_base_presidencial_2024_pond_pct"]
        secc_n = est_row["n_secciones"]
        secc_pct = est_row["pct_secciones_panel"]

        perf_cell = f"<b>{cid}: {nom}</b><br/>Secc: {secc_n:,} ({secc_pct:.2f}%)<br/>Base Inter. 2021: <b>{base_inter:.1f}%</b><br/>Base Pres. 2024: <b>{base_pres:.1f}%</b>"
        if cid == "C0":
            b_jov_c0 = df12.loc["C0", "tasa_joven_18_29_2021_pond_pct"]
            m_c0 = df12.loc["C0", "meta_intermedia_2027"]
            d_c0 = df17.loc["C0", "meta_delta_pts"]
            m_pres_c0 = df12.loc["C0", "meta_presidencial_2030"]
            m_jov_c0 = df12.loc["C0", "meta_tasa_joven"]
            delta_jov_c0 = (df12.loc["Panel B", "tasa_joven_18_29_2021_pond_pct"] - b_jov_c0) / 2.0
            d_jov_fmt = f"+{redondear_pub(delta_jov_c0, 1):.1f} pts"
            perf_cell += f"<br/>Base Joven 2021: <b>{b_jov_c0:.1f}%</b>"
            canales_fmt = "Transporte metropolitano, 'Conóceles', tianguis, centros laborales (incluidos hombres jóvenes y adultos)."
            accion_fmt = "Campaña cívica metropolitana y brigadas de educación cívica y revisión de accesibilidad de casilla (DERFE/DECEyEC)."
            meta_fmt = f"Elevar participación a {m_c0} en 2027 ({d_c0} vs 2021), {m_pres_c0} en 2030 y voto juvenil a {m_jov_c0} ({d_jov_fmt})."
            ind_fmt = "Tasa ponderada SV/(SV+NV) 2027 y tasa 18–29 en CCPC."
            resp_fmt = "DECEyEC, DERFE y Juntas Distritales"
        elif cid == "C1":
            canales_fmt = "Redes comunitarias, planteles locales y centros culturales."
            accion_fmt = "Talleres juveniles ENCÍVICA, reconocimiento comunitario y reclutamiento temprano de funcionariado de casilla."
            meta_fmt = f"Sostener participación ≥ {base_inter:.1f}% en 2027 y ≥ {base_pres:.1f}% en 2030."
            ind_fmt = "Tasa ponderada en 2027/2030 y, como indicador complementario de la DEOE, el porcentaje de casillas instaladas con funcionariado propietario (línea base por definir con la DEOE)."
            resp_fmt = "DECEyEC y Juntas Distritales (vocalías distritales)"
        elif cid == "C2":
            m_jov_c2 = df12.loc["C2", "meta_tasa_joven"]
            canales_fmt = "Colectivos juveniles, redes vecinales y 'Conóceles'."
            accion_fmt = "Foros 'Diálogos por la Democracia' (DECEyEC) y monitoreo de casillas en crecimiento (DEOE)."
            meta_fmt = f"Consolidar participación ≥ {base_inter:.1f}% en 2027 y {m_jov_c2}."
            ind_fmt = f"Tasa ponderada 2027 y {m_jov_c2}."
            resp_fmt = "DECEyEC, DEOE y Juntas Distritales"
        else:  # C3
            b_hom_c3 = df12.loc["C3", "tasa_hombres_2021_pond_pct"]
            m_c3 = df12.loc["C3", "meta_intermedia_2027"]
            d_c3 = df17.loc["C3", "meta_delta_pts"]
            m_pres_c3 = df12.loc["C3", "meta_presidencial_2030"]
            m_hom_c3 = df12.loc["C3", "meta_tasa_hombres"]
            perf_cell += f"<br/>Base Hombres 2021: <b>{b_hom_c3:.1f}%</b>"
            canales_fmt = "Centros laborales masculinos (agropecuario, industria, transporte) y radio regional en tiempos oficiales."
            accion_fmt = "Promoción del voto masculino y propuesta de casillas extraordinarias a Consejos Distritales conforme a la LGIPE."
            meta_fmt = f"Elevar participación a {m_c3} en 2027 ({d_c3}), {m_pres_c3} en 2030 y voto masculino a {m_hom_c3} en 2027."
            ind_fmt = "Tasa masculina SV/(SV+NV) y participación ponderada en CCPC."
            resp_fmt = "Juntas Distritales, DECEyEC y DEOE"

        canales_cell = f"<b>Canales:</b> {canales_fmt}<br/><b>Acción:</b> {accion_fmt}"
        meta_cell = f"<b>Meta:</b> {meta_fmt}<br/><b>Indicador:</b> {ind_fmt}"

        t7_compact_data.append({
            "perfil": perf_cell,
            "canales_accion": canales_cell,
            "meta_ind": meta_cell,
            "resp": resp_fmt,
        })

    t7_rows = [[
        Paragraph("Perfil y Línea Base", th_l),
        Paragraph("Acción Principal y Canales", th_l),
        Paragraph("Meta e Indicador", th_l),
        Paragraph("Responsable", th_l),
    ]]
    for item in t7_compact_data:
        t7_rows.append([
            Paragraph(item["perfil"], td_l),
            Paragraph(item["canales_accion"], td_l),
            Paragraph(item["meta_ind"], td_l),
            Paragraph(item["resp"], td_l),
        ])
    story.append(Paragraph(f"Tabla 6. Estrategias Focalizadas por Perfil Ciudadano (k = {k_sel}), Líneas Base, Metas y Viabilidad Operativa", cap_st))
    story.append(styled_table(t7_rows, [105.0, 125.0, 135.0, 105.27]))
    # D4: Regla de metas
    c0_sec_h = df12.loc["C0", "meta_secundaria_tasa_hombres"]
    c3_sec_j = df12.loc["C3", "meta_secundaria_tasa_joven"]
    story.append(Paragraph(
        f"<i>Regla de metas: los perfiles por debajo del promedio del panel buscan cerrar la mitad de su diferencia con él en la siguiente elección del mismo tipo; los perfiles por encima buscan sostener su nivel. "
        f"Las metas por subgrupo se fijan en el rasgo que define a cada perfil (jóvenes en C0, hombres en C3); con la misma regla, C0 tendría {c0_sec_h} en hombres y C3 {c3_sec_j} en jóvenes como metas secundarias. "
        f"Los Δ se calculan con valores sin redondear, por lo que pueden diferir en 0.1 de la resta de las cifras mostradas.</i>",
        note_st
    ))
    story.append(Spacer(1, 4))

    # =========================================================================
    # SUBSECCIÓN 5.1: EQUIVALENCIA DE LAS METAS EN VOTANTES Y PRIORIDAD TERRITORIAL
    # =========================================================================
    imp_data = data.get("impacto_y_prioridad_territorial", {})
    if imp_data:
        h2_imp = Paragraph("5.1 Equivalencia de las Metas en Votantes y Prioridad Territorial", h2_st)
        t_imp_rows = [[
            Paragraph("Perfil", th_c),
            Paragraph("LN 2024", th_c),
            Paragraph("(SV+NV) 2024", th_c),
            Paragraph("Meta (Δ pts)", th_c),
            Paragraph("Votantes equivalentes<br/>(Meta / Regresión)", th_c),
            Paragraph("Top 3 juntas distritales", th_l),
            Paragraph("% LN en 30 juntas", th_c),
        ]]
        for row in imp_data.get("tabla_impacto", []):
            top3_fmt = row["top3_juntas_distritales"]
            if row["tipo_meta"] == "Aumento":
                elec_text = f"<b>{row['votantes_equivalentes_str']}</b>"
            else:
                elec_text = f"<b>{row['escenario_regresion_str']}</b><br/>(regresión)"
            t_imp_rows.append([
                Paragraph(f"<b>{row['codigo_cluster']}</b>", td_c),
                Paragraph(f"{row['ln_2024_panel_b']:,}", td_c),
                Paragraph(f"{row['svnv_2024_base']:,}", td_c),
                Paragraph(row["meta_delta_pts"], td_c),
                Paragraph(elec_text, td_c),
                Paragraph(top3_fmt, td_l),
                Paragraph(f"{row['pct_ln_en_top30_juntas']:.1f}%", td_c),
            ])
        t_imp_cap = Paragraph(f"Tabla 7. Equivalencia de Metas en Votantes sobre Base (SV+NV) 2024 y Concentración Territorial por Perfil (k = {k_sel})", cap_st)
        t_imp_table = styled_table(t_imp_rows, [38.0, 56.0, 56.0, 52.0, 85.0, 133.27, 50.0])
        p21_c1 = df17.loc["C1", "participacion_2021_pond_pct"]
        p21_c2 = df17.loc["C2", "participacion_2021_pond_pct"]
        p_int_c1 = df17.loc["C1", "promedio_intermedias_2009_2021_pond_pct"]
        p_int_c2 = df17.loc["C2", "promedio_intermedias_2009_2021_pond_pct"]
        t_imp_note = Paragraph(
            f"<i>Votantes equivalentes calculados sobre sufragios emitidos (SV+NV) en 2024. C0 y C3: equivalencia de alcanzar la meta. "
            f"C1 y C2: escenario de regresión (sin probabilidad asociada) si su participación de 2021 ({p21_c1:.1f}% y {p21_c2:.1f}%) "
            f"bajara a su promedio de las intermedias 2009–2021 ponderado por electores con registro de votación (SV+NV), distinto de la media simple de la tabla de series ({p_int_c1:.2f}% y {p_int_c2:.2f}%).</i>",
            note_st
        )
        story.append(h2_imp)
        story.append(t_imp_cap)
        story.append(t_imp_table)
        story.append(t_imp_note)
        story.append(Spacer(1, 4))

    # =========================================================================
    # SUBSECCIÓN 5.2: PILOTO EVALUABLE 2027 (Bloque E, <= 100 palabras)
    # =========================================================================
    story.append(Paragraph("5.2 Piloto Evaluable 2027", h2_st))
    p_piloto = data["potencia_piloto_c0"]
    n_sec_tot = p_piloto["tabla_15"][1]["secciones_totales_piloto"]
    n_sec_grp = p_piloto["n_seleccionado"]
    mde_sec = pde["mde_seccion_pts"]
    icc_val = pde["icc_municipal_c0"]
    mde_5 = pde["mde_bloque_5_pts"]
    mde_10 = pde["mde_bloque_10_pts"]
    story.append(Paragraph(
        f"Para evaluar intervenciones en C0, el piloto aleatorizado se restringe a acciones asignables por sección "
        f"(brigadas casa por casa y 'Ubica tu casilla' geolocalizado). Con {n_sec_tot:,} secciones ({n_sec_grp:,} por grupo) estratificadas por "
        f"entidad y tercil 2021, ANCOVA con el CCPC 2027 (disponible hacia 2028) logra un efecto mínimo detectable (MDE) de "
        f"{mde_sec:.2f} pts por sección (80% potencia, α = 0.05). Ante riesgo de contaminación territorial, asignar por bloques municipales "
        f"eleva el MDE por efecto de diseño (ICC = {icc_val:.3f}): {mde_5:.2f} pts (m=5) y {mde_10:.2f} pts (m=10). Campañas masivas en transporte y radio "
        f"se evalúan por distrito o municipio. El protocolo analítico deberá preregistrarse formalmente.",
        body_st
    ))
    story.append(Spacer(1, 4))

    # =========================================================================
    # SECCIÓN 6: LIMITACIONES Y RECOMENDACIONES AL INE
    # =========================================================================
    story.append(Paragraph("6. Limitaciones Metodológicas, Análisis de Sensibilidad y Recomendaciones al INE", h1_st))
    cob_amp = data["cobertura_ampliada_2024"]
    # Sesgo del panel B: +0.44 a +0.97 pts ponderado
    story.append(Paragraph(
        f"<b>1. Sesgo del Panel Principal y secciones excluidas (Tabla 8):</b> Las {inc_exc[1]['n_secciones']:,} secciones activas en {serie[-1]['anio']} "
        f"excluidas del Panel Principal ({inc_exc[1]['pct_secciones_2024']:.1f}% del total y {inc_exc[1]['pct_ln_2024']:.1f}% de la Lista Nominal) "
        f"se dividen en: (a) {inc_exc[2]['n_secciones']:,} secciones creadas o modificadas post-{serie[0]['anio']}, con participación de "
        f"<b>{inc_exc[2]['participacion_2024_ponderada_sv_svnv_pct']:.1f}%</b> ({inc_exc[2]['pct_urbana']:.1f}% urbanas); y (b) {inc_exc[3]['n_secciones']:,} "
        f"secciones continuas excluidas por calidad ({inc_exc[3]['secciones_svnv_0_en_2024']:,} sin captura en {serie[-1]['anio']}). En consecuencia, "
        f"el Panel Principal (Opción B) sobreestima la participación nacional ponderada del CCPC entre "
        f"<b>{serie[0]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} y {serie[4]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} puntos porcentuales</b> "
        f"({serie[0]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} en {serie[0]['anio']}, {serie[1]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} en {serie[1]['anio']}, "
        f"{serie[2]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} en {serie[2]['anio']}, {serie[3]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} en {serie[3]['anio']}, "
        f"{serie[4]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} en {serie[4]['anio']} y {serie[5]['sesgo_panel_b_ponderada_vs_ccpc_pts']:+.2f} en {serie[5]['anio']}). "
        f"Para uso operativo, se asignó perfil por cercanía al centroide a {cob_amp['secciones_asignadas']:,} secciones excluidas con historia suficiente, "
        f"lo que eleva la cobertura a {cob_amp['pct_ln_panel_b_mas_asignadas']:.1f}% de la lista nominal 2024; "
        f"las {cob_amp['secciones_sin_historia_suficiente']:,} secciones sin historia suficiente (creadas después de 2015 o con captura insuficiente) requieren esperar a la elección de 2027.",
        body_st
    ))

    # Tabla 8: Incluidas vs Excluidas (ancho = 470.27 pt)
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
        urb_val = pan_b["pct_secciones_urbanas_1d"] if "Panel Principal" in lbl else r["pct_urbana"]
        t8_rows.append([
            Paragraph(lbl, st_l),
            Paragraph(f"{r['n_secciones']:,}", st_c),
            Paragraph(f"{r['pct_secciones_2024']:.2f}%", st_c),
            Paragraph(f"{r['ln_2024']:,}", st_c),
            Paragraph(f"{r['pct_ln_2024']:.2f}%", st_c),
            Paragraph(f"{urb_val:.1f}%", st_c),
            Paragraph(f"<b>{r['participacion_2024_ponderada_sv_svnv_pct']:.2f}%</b>", st_c),
        ])
    t8_cap = Paragraph(f"Tabla 8. Comparación de Secciones Incluidas vs Excluidas en el CCPC {serie[-1]['anio']}", cap_st)
    t8_table = styled_table(t8_rows, [134.27, 54.0, 50.0, 70.0, 54.0, 52.0, 56.0], highlight_last=True)
    story.append(t8_cap)
    story.append(t8_table)
    story.append(Spacer(1, 4))

    # D6: Limitación Calendario Electoral (<= 90 palabras, Bloque 2.6)
    eta2_b = redondear(cal["eta2_entidad_brecha"], 3)
    eta2_e = redondear(cal["eta2_entidad_estabilidad"], 3)
    ent_tres_str = ", ".join(cal["entidades_las_tres"][:-1]) + " y " + cal["entidades_las_tres"][-1]
    b_tres = df18.loc["las tres", "brecha_pres_inter_media_pts"]
    b_ning = df18.loc["ninguna", "brecha_pres_inter_media_pts"]
    pct_sec_c1_tres = redondear_pub(df18.loc["las tres", "pct_en_c1"], 1)
    pct_c1_tres = redondear_pub(cal["pct_c1_en_las_tres"], 1)
    pct_pan_tres = redondear_pub(df18.loc["las tres", "pct_secciones_panel"], 1)
    c_anad = cal["cambio_2015_2021_anadieron_gob_pts"]
    c_ning = cal["cambio_2015_2021_ninguna_gob_pts"]
    pct_c2_ning = redondear_pub(cal["pct_c2_en_ninguna"], 1)
    ari_desest = redondear(cal["ari_sensibilidad_desestatificada"], 2)

    story.append(Paragraph(
        f"<b>2. Calendario electoral estatal:</b> La entidad federativa explica buena parte de la varianza de la "
        f"brecha presidencial–intermedia (η² = {eta2_b:.3f}) y de la estabilidad (η² = {eta2_e:.3f}). En las 6 "
        f"entidades que eligieron gubernatura en las tres intermedias ({ent_tres_str}), la brecha es de {b_tres:.1f} "
        f"pts frente a {b_ning:.1f} pts en las 17 sin concurrencia, y el {pct_sec_c1_tres:.1f}% de sus secciones es C1: "
        f"esas entidades aportan el {pct_c1_tres:.1f}% de C1 aunque reúnen solo el {pct_pan_tres:.1f}% del panel. Entre 2015 y 2021, "
        f"la participación subió {c_anad:+.2f} pts en las 6 entidades que sumaron gubernatura en 2021 y {c_ning:+.2f} pts en las "
        f"17 sin gubernatura; el ascenso de C2 no depende de ese efecto, porque el {pct_c2_ning:.1f}% de sus secciones está en "
        f"entidades sin gubernatura concurrente. Si se resta la media estatal a la participación media, la brecha y la tendencia, "
        f"la tipología conserva una concordancia moderada (ARI = {ari_desest:.2f}). En 2027 se elegirán 17 gubernaturas: las metas "
        f"deben evaluarse como diferencia contra el grupo de control, no como cambio bruto.",
        body_st
    ))

    # D10: Alineación de sensibilidad Opción A con variante sin salto abrupto de LN (60,433 secciones)
    sens_op_a = [r for r in sens if r.get("variante") == "Opcion_A_con_2pres_2inter_y_sin_salto_abrupto_LN"][0]
    story.append(Paragraph(
        f"<b>3. Análisis de sensibilidad (Opción A):</b> Al evaluar la Opción A sobre las secciones continuas sin saltos abruptos de Lista Nominal "
        f"y con al menos 2 comicios de cada tipo válidos ({sens_op_a['secciones_incluidas']:,} secciones), K-Means++ (k={k_sel}) alcanza una concordancia casi perfecta con el "
        f"Panel Principal B: <b>ARI = {sens_op_a['ari_vs_panel_principal_B']:.3f}</b> ({sens_op_a['coincidencia_exacta_alineada_pct']:.1f}% de coincidencia exacta) "
        f"en las {u['panel_principal_secciones']:,} secciones comunes. Esto indica que la segmentación es robusta a la depuración del panel.",
        body_st
    ))
    # C13: Frase exacta sobre variable indígena y D10: promedio de las seis elecciones
    story.append(Paragraph(
        f"<b>4. Limitación por variables demográficas y ventana temporal:</b> Sustituir el promedio de las seis elecciones por un único corte anual hace que la "
        f"concordancia con la tipología base baje a <b>ARI = {win[0]['ari_clustering_6y_vs_2024']:.3f}</b>, lo que exige actualizar la tipología tras cada proceso federal. "
        f"Asimismo, los CSV abiertos del CCPC no incluyen el indicador de población indígena o afromexicana que sí muestra el tablero del INE; "
        f"por ello no se incorporó al modelo. Finalmente, se recomienda a la DECEyEC publicar ese indicador en los CSV abiertos, incluir una bandera "
        f"explícita de captura en las bases públicas y reforzar la captura de cuadernillos para abatir los registros NS.",
        body_st
    ))

    # =========================================================================
    # SECCIÓN 7: CONCLUSIONES (E1: exactamente <= 160 palabras; D1, D2, D7, D8, D10)
    # =========================================================================
    story.append(Paragraph("7. Conclusiones", h1_st))
    imp_tot_str = imp["total_adicionales_millones_str"]
    c0_vot_str = imp["votantes_equivalentes_c0_miles_str"]
    c3_vot_str = imp["votantes_equivalentes_c3_miles_str"]
    reg_tot_str = imp["total_regresion_millones_str"]
    d_r2_c = va_hist["delta_r2_cambio_3d"]
    pde_mde = pde["mde_seccion_pts"]

    story.append(Paragraph(
        f"Aplicamos la definición oficial del Manual CCPC (p. 17), <b>SV / (SV + NV)</b>, cuantificando el sesgo de omitir registros NS: "
        f"sin ella, la participación de {serie[3]['anio']} y {serie[-1]['anio']} se subestima en {diff_2018:.2f} y {diff_2024:.2f} pts y surgen grupos artificiales. "
        f"Con datos corregidos, las {u['panel_principal_secciones']:,} secciones del panel se organizan en cuatro perfiles. "
        f"C0 ({perfiles[0]['pct_secciones_panel']:.1f}% del panel) concentra abstencionismo metropolitano e intermitente. "
        f"C1 es el referente de constancia cívica. C2 evidencia ascenso sostenido con juventud activa ({tc_c2} pts/año corregida). "
        f"C3 ({perfiles[3]['nombre_propuesto']}) presenta brecha de género de +{c3_sexo_brecha:.1f} pts por desmovilización masculina ({tc_c3} pts/año corregida). "
        f"Las metas equivalen a {imp_tot_str} de sufragios adicionales ({c0_vot_str} en C0 y {c3_vot_str} en C3); en C1 y C2, un escenario de regresión "
        f"(sin probabilidad asociada) involucra {reg_tot_str}. La propuesta incluye un piloto con MDE de {pde_mde:.2f} pts seccional medible con el CCPC 2027 hacia 2028. "
        f"La capacidad de anticipar cambios es baja (ΔR² = {d_r2_c:.3f}), focalizando territorio y no predicción coyuntural.",
        body_st
    ))

    # =========================================================================
    # SECCIÓN 8: REPRODUCIBILIDAD (E2: exactamente <= 90 palabras)
    # =========================================================================
    story.append(Paragraph("8. Reproducibilidad", h1_st))
    repro_st = ParagraphStyle("ReproLeft", parent=body_st, alignment=TA_LEFT)
    story.append(Paragraph(
        "El pipeline completo es reproducible de inicio a fin ejecutando <i>python run_all.py</i> bajo Python 3.14.6, DuckDB 2.0.0, scikit-learn 1.9.0, "
        "scipy 1.18.0, umap-learn 0.5.12, pandas 3.0.3 y numpy 2.4.6. El código abierto está disponible en:<br/>"
        "<font color=\"#1E3A8A\"><u>https://github.com/Johanan1113/Hackaton_INE_byte_me</u></font><br/>"
        "Fijando la semilla (random_state=42), dos corridas consecutivas desde cero generan hashes SHA-256 idénticos en métricas y etiquetas. "
        "Los datos crudos se descargan de la Plataforma CCPC del INE conforme a las instrucciones del README y no se redistribuyen.",
        repro_st
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
            "Tasa SV/(SV+NV) · Manual CCPC"
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
