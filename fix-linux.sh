#!/bin/bash
# Script para arreglar terminadores de línea en Linux

echo "🔧 Arreglando terminadores de línea para Linux..."

# Convertir terminadores de línea de Windows a Linux
if command -v dos2unix &> /dev/null; then
    echo "✅ Usando dos2unix..."
    dos2unix webapp-manager.py
    dos2unix install.sh
    find webapp_manager -name "*.py" -exec dos2unix {} \;
else
    echo "✅ Usando sed..."
    sed -i 's/\r$//' webapp-manager.py
    sed -i 's/\r$//' install.sh
    find webapp_manager -name "*.py" -exec sed -i 's/\r$//' {} \;
fi

# Hacer ejecutables los scripts
chmod +x webapp-manager.py
chmod +x install.sh

echo "✅ Terminadores de línea arreglados"
echo "✅ Permisos de ejecución configurados"
echo ""
echo "🚀 Ahora puedes usar:"
echo "   ./webapp-manager.py gui"
echo "   ./webapp-manager.py add -d api.africarsrent.com -s git@github.com:STC-Soluciones/africars-api.git -t fastapi -p 8000"
