#!/usr/bin/env bash
# ==============================================================================
# Script para Incorporar las Cartas Administrativas al ZIP de Entrega
# Uso: bash entrega_ByteMe_Reto1/agregar_cartas.sh <carta_cesion.pdf> <carta_declaratoria.pdf>
# ==============================================================================
set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "Uso: bash $0 <carta_cesion.pdf> <carta_declaratoria.pdf>" >&2
    exit 1
fi

CARTA_CESION="$(realpath "$1")"
CARTA_DECLARATORIA="$(realpath "$2")"
ZIP_FILE="${ZIP_OVERRIDE:-/home/johan/Downloads/ByteMe_Reto1_PerfilesCiudadanos.zip}"

echo "=== INCORPORANDO CARTAS AL PAQUETE ZIP DE ENTREGA ==="

# 1. Verificar existencia física de ambos archivos
if [ ! -f "$CARTA_CESION" ]; then
    echo "ERROR: No existe el archivo de cesión: $CARTA_CESION" >&2
    exit 1
fi
if [ ! -f "$CARTA_DECLARATORIA" ]; then
    echo "ERROR: No existe el archivo de declaratoria: $CARTA_DECLARATORIA" >&2
    exit 1
fi

# 2. Verificar tipo MIME application/pdf
MIME1=$(file -b --mime-type "$CARTA_CESION")
MIME2=$(file -b --mime-type "$CARTA_DECLARATORIA")

if [ "$MIME1" != "application/pdf" ]; then
    echo "ERROR: El archivo de cesión no es un PDF válido (detectado: $MIME1): $CARTA_CESION" >&2
    exit 1
fi
if [ "$MIME2" != "application/pdf" ]; then
    echo "ERROR: El archivo de declaratoria no es un PDF válido (detectado: $MIME2): $CARTA_DECLARATORIA" >&2
    exit 1
fi
echo "✓ Archivos PDF de cartas validados exitosamente:"
echo "  - Cesión:       $CARTA_CESION (MIME: $MIME1)"
echo "  - Declaratoria: $CARTA_DECLARATORIA (MIME: $MIME2)"

# 3. Verificar existencia del archivo ZIP en Downloads
if [ ! -f "$ZIP_FILE" ]; then
    echo "ERROR: No se encontró el archivo ZIP en: $ZIP_FILE" >&2
    echo "Ejecuta primero: bash entrega_ByteMe_Reto1/crear_zip_entrega.sh" >&2
    exit 1
fi

# 4. Preparar estructura temporal e incorporar cartas
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

DEST_DIR="$TMP_DIR/ByteMe_Reto1_PerfilesCiudadanos/05_Cartas"
mkdir -p "$DEST_DIR"

cp "$CARTA_CESION" "$DEST_DIR/Carta_Cesion_Derechos.pdf"
cp "$CARTA_DECLARATORIA" "$DEST_DIR/Carta_Declaratoria.pdf"

echo "--- Actualizando ZIP con las cartas ---"
(
    cd "$TMP_DIR"
    zip -u "$ZIP_FILE" \
        ByteMe_Reto1_PerfilesCiudadanos/05_Cartas/Carta_Cesion_Derechos.pdf \
        ByteMe_Reto1_PerfilesCiudadanos/05_Cartas/Carta_Declaratoria.pdf > /dev/null
)

echo "--- Eliminando LEEME_CARTAS.txt del ZIP ---"
zip -d "$ZIP_FILE" "ByteMe_Reto1_PerfilesCiudadanos/05_Cartas/LEEME_CARTAS.txt" > /dev/null || true

# 5. Auditoría del ZIP actualizado
echo "================================================================================"
echo "VERIFICACIÓN DE INTEGRIDAD TRAS AGREGAR CARTAS (unzip -t):"
unzip -t "$ZIP_FILE"
echo "================================================================================"
echo "CONTENIDO COMPLETO DEL ZIP (unzip -l):"
unzip -l "$ZIP_FILE"
echo "================================================================================"

ZIP_SIZE_BYTES=$(stat -c%s "$ZIP_FILE")
ZIP_SIZE_MB=$(awk "BEGIN {printf \"%.2f\", $ZIP_SIZE_BYTES / (1024 * 1024)}")
ZIP_SHA256=$(sha256sum "$ZIP_FILE" | awk '{print $1}')

echo "Tamaño del ZIP: ${ZIP_SIZE_MB} MB (${ZIP_SIZE_BYTES} bytes)"
echo "SHA-256 del ZIP: ${ZIP_SHA256}"

if [ "$ZIP_SIZE_BYTES" -gt 20971520 ]; then
    echo "AVISO: el ZIP supera 20 MB; súbelo a Google Drive con permiso de lectura y comparte el enlace en el correo."
else
    echo "✓ El ZIP pesa menos de 20 MB: es apto para envío directo por correo electrónico."
fi
echo "================================================================================"
echo "=== CARTAS INCORPORADAS EXITOSAMENTE AL ZIP ==="
