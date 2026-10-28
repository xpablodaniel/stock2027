#!/bin/bash
# Script para iniciar el sistema de recepción

# Obtener el directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Cambiar al directorio del proyecto
cd "$DIR"

# Activar entorno virtual y ejecutar app.py
echo "🏨 Iniciando Sistema de Recepción 2026..."
echo "================================================"
echo "Activando entorno virtual..."
source .venv/bin/activate

echo "Iniciando servidor Flask..."
echo "================================================"
echo ""
echo "✅ Servidor iniciado correctamente"
echo "🌐 Accede desde tu navegador a: http://localhost:5000"
echo ""
echo "⚠️  NO CIERRES ESTA VENTANA mientras uses el sistema"
echo "⚠️  Para detener el servidor: presiona Ctrl+C"
echo ""
echo "================================================"

# Ejecutar la aplicación
python app.py
