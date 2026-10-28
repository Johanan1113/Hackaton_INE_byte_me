#!/usr/bin/env bash
# ==============================================================================
# Script de Creación del Paquete ZIP Oficial de Entrega
# Proyecto: Reto 1 - Perfiles Ciudadanos de Participación (Equipo "Byte me")
# Ubicación: entrega_ByteMe_Reto1/crear_zip_entrega.sh
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENTREGA_DIR="$REPO_ROOT/entrega_ByteMe_Reto1"
DOWNLOADS_DIR="/home/johan/Downloads"
ZIP_DEST="$DOWNLOADS_DIR/ByteMe_Reto1_PerfilesCiudadanos.zip"

echo "=== INICIANDO EMPAQUETADO DEL ENTREGABLE OFICIAL (Equipo Byte me) ==="

# ------------------------------------------------------------------------------
# 1. Verificación estricta de sumas de verificación MD5 de entregables
# ------------------------------------------------------------------------------
echo "--- Paso 1: Verificando MD5 de entregables revisados ---"
EXPECTED_DOC_MD5="7ff7c1375b45d7157ab57615a44deb1e"
EXPECTED_FICHAS_MD5="8af7a0f55cf7379ada5ee9d338a839c0"
EXPECTED_PRES_MD5="de8c3534b73bb42e495a422d10097671"

ACTUAL_DOC_MD5=$(md5sum "$ENTREGA_DIR/Documento_Tecnico_ByteMe.pdf" | awk '{print $1}')
ACTUAL_FICHAS_MD5=$(md5sum "$ENTREGA_DIR/Fichas_Perfiles_ByteMe.pdf" | awk '{print $1}')
ACTUAL_PRES_MD5=$(md5sum "$ENTREGA_DIR/Presentacion_Ejecutiva_ByteMe.pdf" | awk '{print $1}')

if [ "$ACTUAL_DOC_MD5" != "$EXPECTED_DOC_MD5" ]; then
    echo "ERROR: MD5 de Documento_Tecnico_ByteMe.pdf ($ACTUAL_DOC_MD5) no coincide con el esperado ($EXPECTED_DOC_MD5)." >&2
    exit 1
fi
if [ "$ACTUAL_FICHAS_MD5" != "$EXPECTED_FICHAS_MD5" ]; then
    echo "ERROR: MD5 de Fichas_Perfiles_ByteMe.pdf ($ACTUAL_FICHAS_MD5) no coincide con el esperado ($EXPECTED_FICHAS_MD5)." >&2
    exit 1
fi
if [ "$ACTUAL_PRES_MD5" != "$EXPECTED_PRES_MD5" ]; then
    echo "ERROR: MD5 de Presentacion_Ejecutiva_ByteMe.pdf ($ACTUAL_PRES_MD5) no coincide con el esperado ($EXPECTED_PRES_MD5)." >&2
    exit 1
fi
echo "✓ Sumas MD5 verificadas exitosamente:"
echo "  - Documento_Tecnico_ByteMe.pdf:    $ACTUAL_DOC_MD5"
echo "  - Fichas_Perfiles_ByteMe.pdf:      $ACTUAL_FICHAS_MD5"
echo "  - Presentacion_Ejecutiva_ByteMe.pdf: $ACTUAL_PRES_MD5"

# ------------------------------------------------------------------------------
# 2. Verificación de conteo de páginas y diapositivas
# ------------------------------------------------------------------------------
echo "--- Paso 2: Verificando conteo de páginas y diapositivas ---"
python -c '
import pptx
import pdfplumber
import sys

prs = pptx.Presentation("entrega_ByteMe_Reto1/Presentacion_Ejecutiva_ByteMe.pptx")
slides = len(prs.slides)
assert slides == 10, f"Error: PPTX tiene {slides} diapositivas (esperadas 10)"

with pdfplumber.open("entrega_ByteMe_Reto1/Presentacion_Ejecutiva_ByteMe.pdf") as pdf:
    p_pres = len(pdf.pages)
    assert p_pres == 10, f"Error: Presentación PDF tiene {p_pres} páginas (esperadas 10)"

with pdfplumber.open("entrega_ByteMe_Reto1/Documento_Tecnico_ByteMe.pdf") as pdf:
    p_doc = len(pdf.pages)
    assert p_doc == 12, f"Error: Documento Técnico PDF tiene {p_doc} páginas (esperadas 12)"

with pdfplumber.open("entrega_ByteMe_Reto1/Fichas_Perfiles_ByteMe.pdf") as pdf:
    p_fich = len(pdf.pages)
    assert p_fich == 5, f"Error: Fichas PDF tiene {p_fich} páginas (esperadas 5)"

print(f"✓ Conteo validado: Presentación {slides} láminas / {p_pres} págs PDF, Documento {p_doc} págs, Fichas {p_fich} págs.")
'

# ------------------------------------------------------------------------------
# 3. Construcción del árbol temporal para el ZIP
# ------------------------------------------------------------------------------
echo "--- Paso 3: Construyendo estructura temporal del paquete ---"
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

PKG_DIR="$TMP_DIR/ByteMe_Reto1_PerfilesCiudadanos"
mkdir -p "$PKG_DIR/01_Documento_Tecnico"
mkdir -p "$PKG_DIR/02_Fichas_Perfiles"
mkdir -p "$PKG_DIR/03_Presentacion_Ejecutiva"
mkdir -p "$PKG_DIR/04_Codigo"
mkdir -p "$PKG_DIR/05_Cartas"

# 01_Documento_Tecnico
cp "$ENTREGA_DIR/Documento_Tecnico_ByteMe.pdf" "$PKG_DIR/01_Documento_Tecnico/"

# 02_Fichas_Perfiles (excluyendo el PNG combinado de 7MB)
cp "$ENTREGA_DIR/Fichas_Perfiles_ByteMe.pdf" "$PKG_DIR/02_Fichas_Perfiles/"
cp "$ENTREGA_DIR/Fichas_Portada.png" "$PKG_DIR/02_Fichas_Perfiles/"
cp "$ENTREGA_DIR/Ficha_C0.png" "$PKG_DIR/02_Fichas_Perfiles/"
cp "$ENTREGA_DIR/Ficha_C1.png" "$PKG_DIR/02_Fichas_Perfiles/"
cp "$ENTREGA_DIR/Ficha_C2.png" "$PKG_DIR/02_Fichas_Perfiles/"
cp "$ENTREGA_DIR/Ficha_C3.png" "$PKG_DIR/02_Fichas_Perfiles/"

# 03_Presentacion_Ejecutiva
cp "$ENTREGA_DIR/Presentacion_Ejecutiva_ByteMe.pdf" "$PKG_DIR/03_Presentacion_Ejecutiva/"
cp "$ENTREGA_DIR/Presentacion_Ejecutiva_ByteMe.pptx" "$PKG_DIR/03_Presentacion_Ejecutiva/"

# 04_Codigo (copiado mediante git ls-files con exclusiones estrictas de src/, main.py y pipeline.log)
(
    cd "$REPO_ROOT"
    git ls-files \
        README.md \
        requirements.txt \
        run_all.py \
        BITACORA.md \
        plantillas/ \
        scripts/ \
        tests/ \
        outputs/metricas_finales.json \
        outputs/perfil_por_seccion_2024.csv \
        outputs/juntas_prioritarias_por_perfil.csv \
        outputs/tablas/ \
        outputs/figuras/ \
    | while read -r file; do
        case "$file" in
            *.parquet|*.joblib|*.zip|*__pycache__*|*.pytest_cache*|*[Cc]arta*|src/*|main.py|pipeline.log)
                continue
                ;;
        esac
        dest_file="$PKG_DIR/04_Codigo/$file"
        mkdir -p "$(dirname "$dest_file")"
        cp "$REPO_ROOT/$file" "$dest_file"
    done
)

# 05_Cartas
cat << 'EOF' > "$PKG_DIR/05_Cartas/LEEME_CARTAS.txt"
Aquí van la carta de cesión de derechos y la carta declaratoria, firmadas por las tres personas integrantes.
EOF

# LEEME.txt en raíz
cp "$ENTREGA_DIR/LEEME.txt" "$PKG_DIR/LEEME.txt"

# ENLACE_REPOSITORIO.txt en raíz
cp "$ENTREGA_DIR/ENLACE_REPOSITORIO.txt" "$PKG_DIR/ENLACE_REPOSITORIO.txt"

# ------------------------------------------------------------------------------
# 4. Compresión y generación de ByteMe_Reto1_PerfilesCiudadanos.zip
# ------------------------------------------------------------------------------
echo "--- Paso 4: Generando archivo ZIP en $ZIP_DEST ---"
mkdir -p "$DOWNLOADS_DIR"

if [ -f "$ZIP_DEST" ]; then
    BACKUP_NAME="$DOWNLOADS_DIR/ByteMe_Reto1_PerfilesCiudadanos_$(date +%Y%m%d_%H%M%S).zip"
    echo "Aviso: Ya existe un ZIP en destino. Respaldando como: $BACKUP_NAME"
    mv "$ZIP_DEST" "$BACKUP_NAME"
fi

(
    cd "$TMP_DIR"
    zip -r -X "$ZIP_DEST" "ByteMe_Reto1_PerfilesCiudadanos" > /dev/null
)

# ------------------------------------------------------------------------------
# 5. Reporte de verificación y métricas del ZIP generado
# ------------------------------------------------------------------------------
echo "--- Paso 5: Auditoría y reporte del archivo ZIP ---"
echo "================================================================================"
echo "VERIFICACIÓN DE INTEGRIDAD (unzip -t):"
unzip -t "$ZIP_DEST"
echo "================================================================================"
echo "CONTENIDO COMPLETO (unzip -l):"
unzip -l "$ZIP_DEST"
echo "================================================================================"

ZIP_SIZE_BYTES=$(stat -c%s "$ZIP_DEST")
ZIP_SIZE_MB=$(awk "BEGIN {printf \"%.2f\", $ZIP_SIZE_BYTES / (1024 * 1024)}")
ZIP_SHA256=$(sha256sum "$ZIP_DEST" | awk '{print $1}')

echo "Tamaño del ZIP: ${ZIP_SIZE_MB} MB (${ZIP_SIZE_BYTES} bytes)"
echo "SHA-256 del ZIP: ${ZIP_SHA256}"

if [ "$ZIP_SIZE_BYTES" -gt 20971520 ]; then
    echo "AVISO: el ZIP supera 20 MB; súbelo a Google Drive con permiso de lectura y comparte el enlace en el correo."
else
    echo "✓ El ZIP pesa menos de 20 MB: es apto para envío directo por correo electrónico."
fi
echo "================================================================================"
echo "=== PROCESO COMPLETADO EXITOSAMENTE ==="
