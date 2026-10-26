#!/usr/bin/env bash
# ==============================================================================
# Script de Empaquetado de Entrega Oficial (Reto 1 · Equipo Byte me)
# Valida la existencia de todos los archivos obligatorios y genera el paquete ZIP.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
DIR_NAME="$(basename "$SCRIPT_DIR")"
ZIP_NAME="ByteMe_Reto1_PerfilesCiudadanos.zip"
ZIP_PATH="$PARENT_DIR/$ZIP_NAME"

echo "=== Verificación de Entregables Obligatorios ==="

OBLIGATORIOS=(
    "Documento_Tecnico_ByteMe.pdf"
    "Fichas_Perfiles_ByteMe.pdf"
    "Presentacion_Ejecutiva_ByteMe.pdf"
    "Presentacion_Ejecutiva_ByteMe.pptx"
    "LEEME.txt"
    "cartas/Carta_Cesion_Derechos.pdf"
    "cartas/Carta_Declaratoria.pdf"
)

FALTANTES=0

for archivo in "${OBLIGATORIOS[@]}"; do
    if [ ! -f "$SCRIPT_DIR/$archivo" ]; then
        echo "  [ERROR] Falta el archivo obligatorio: $archivo"
        FALTANTES=$((FALTANTES + 1))
    else
        echo "  [OK] Encontrado: $archivo"
    fi
done

if [ "$FALTANTES" -gt 0 ]; then
    echo ""
    echo "=============================================================================="
    echo "ERROR: Se detectaron $FALTANTES archivo(s) obligatorio(s) faltante(s)."
    echo "Por favor verifique que los archivos firmados se encuentren en la carpeta 'cartas/'"
    echo "y vuelva a ejecutar este script."
    echo "=============================================================================="
    exit 1
fi

echo ""
echo "Todos los archivos obligatorios están presentes. Creando $ZIP_NAME..."

# Generar archivo ZIP conteniendo la carpeta completa
(
    cd "$PARENT_DIR"
    # Eliminar ZIP previo si existe
    rm -f "$ZIP_NAME"
    zip -r "$ZIP_NAME" "$DIR_NAME"
)

echo ""
echo "=== Paquete generado exitosamente ==="
echo "Ubicación: $ZIP_PATH"
ls -lh "$ZIP_PATH"
