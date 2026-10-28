#!/bin/bash
# Inicio del Sistema de Gestión Hotelera
# No instala ni actualiza paquetes automáticamente en cada arranque.

set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR" || exit 1

echo "🏨 Sistema de Gestión Hotelera - Recepción 2026"
echo "================================================"
echo

# 1. Verificar que el entorno virtual exista.
if [ ! -x ".venv/bin/python" ]; then
    echo "❌ No se encontró un entorno virtual utilizable en .venv."
    echo "Crealo con: python3 -m venv .venv"
    echo "Después instalá las dependencias con: .venv/bin/python -m pip install -r requirements.txt"
    exit 1
fi

# 2. Activar el entorno virtual.
echo "🔄 Activando entorno virtual..."
# shellcheck disable=SC1091
source .venv/bin/activate

# Usar siempre el Python del entorno virtual.
PYTHON=".venv/bin/python"

# 3. Comprobar dependencias sin instalar ni actualizar nada.
echo "📦 Comprobando dependencias..."
if ! "$PYTHON" - <<'PY'
import importlib.util
import sys

required = ("flask", "pandas", "openpyxl")
missing = [name for name in required if importlib.util.find_spec(name) is None]
if missing:
    print("Faltan dependencias:", ", ".join(missing))
    sys.exit(1)
print("Dependencias disponibles.")
PY
then
    echo
    echo "❌ Faltan dependencias en .venv. Para instalarlas, ejecutá:"
    echo "   .venv/bin/python -m pip install -r requirements.txt"
    exit 1
fi

echo "✅ Dependencias verificadas"
echo

# 4. Abrir el navegador en segundo plano (si xdg-open está disponible).
if command -v xdg-open >/dev/null 2>&1; then
    echo "🌐 Se abrirá el navegador en 3 segundos..."
    (sleep 3 && xdg-open http://127.0.0.1:5000 >/dev/null 2>&1) &
else
    echo "ℹ️ Abrí el navegador en http://127.0.0.1:5000"
fi

# 5. Iniciar Flask con el intérprete del entorno virtual.
echo "🚀 Iniciando servidor Flask..."
echo "================================================"
echo "🌐 Dirección: http://127.0.0.1:5000"
echo "⚠️ Para detener el servidor, presioná Ctrl+C."
echo "================================================"
echo

exec "$PYTHON" app.py
