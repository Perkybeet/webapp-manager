#!/bin/bash
# Script de verificación para WebApp Manager - Solo Linux

set -e

echo "🔍 WebApp Manager - Verificación de Sistema Linux"
echo "================================================="

# Verificar que estamos en Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ ERROR: Este script solo funciona en Linux"
    echo "   Sistema detectado: $OSTYPE"
    exit 1
fi

echo "✅ Sistema Linux detectado: $OSTYPE"

# Verificar arquitectura
ARCH=$(uname -m)
echo "✅ Arquitectura: $ARCH"

# Verificar distribución
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "✅ Distribución: $NAME $VERSION"
else
    echo "⚠️  No se pudo detectar la distribución"
fi

# Verificar Python
echo ""
echo "🐍 Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ $PYTHON_VERSION"
else
    echo "❌ Python3 no encontrado"
    exit 1
fi

# Verificar pip
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version)
    echo "✅ $PIP_VERSION"
else
    echo "❌ pip3 no encontrado"
    exit 1
fi

# Verificar nginx
echo ""
echo "🌐 Verificando nginx..."
if command -v nginx &> /dev/null; then
    NGINX_VERSION=$(nginx -v 2>&1)
    echo "✅ $NGINX_VERSION"
else
    echo "❌ nginx no encontrado"
    echo "   Instalar con: sudo apt install nginx"
    exit 1
fi

# Verificar Node.js
echo ""
echo "🟢 Verificando Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js $NODE_VERSION"
else
    echo "❌ Node.js no encontrado"
    echo "   Instalar con: sudo apt install nodejs"
    exit 1
fi

# Verificar npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✅ npm $NPM_VERSION"
else
    echo "❌ npm no encontrado"
    echo "   Instalar con: sudo apt install npm"
    exit 1
fi

# Verificar git
echo ""
echo "📦 Verificando git..."
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    echo "✅ $GIT_VERSION"
else
    echo "❌ git no encontrado"
    echo "   Instalar con: sudo apt install git"
    exit 1
fi

# Verificar dependencias Python
echo ""
echo "🔧 Verificando dependencias Python..."
if python3 -c "import rich" 2>/dev/null; then
    echo "✅ rich library disponible"
else
    echo "❌ rich library no encontrada"
    echo "   Instalar con: pip3 install rich"
    exit 1
fi

if python3 -c "import colorama" 2>/dev/null; then
    echo "✅ colorama library disponible"
else
    echo "❌ colorama library no encontrada"
    echo "   Instalar con: pip3 install colorama"
    exit 1
fi

# Verificar permisos
echo ""
echo "🔐 Verificando permisos..."
if [ -x "webapp-manager.py" ]; then
    echo "✅ webapp-manager.py es ejecutable"
else
    echo "⚠️  webapp-manager.py no es ejecutable"
    echo "   Arreglar con: chmod +x webapp-manager.py"
fi

# Verificar terminadores de línea
echo ""
echo "📄 Verificando terminadores de línea..."
if file webapp-manager.py | grep -q "CRLF"; then
    echo "❌ webapp-manager.py tiene terminadores de línea Windows"
    echo "   Arreglar con: ./fix-linux.sh"
    exit 1
else
    echo "✅ webapp-manager.py tiene terminadores de línea Unix"
fi

# Verificar directorios del sistema
echo ""
echo "📁 Verificando directorios del sistema..."
DIRS="/var/www /var/log /etc"
for dir in $DIRS; do
    if [ -d "$dir" ]; then
        echo "✅ $dir existe"
    else
        echo "❌ $dir no existe"
        exit 1
    fi
done

# Verificar servicios
echo ""
echo "⚙️ Verificando servicios..."
if systemctl is-active --quiet nginx; then
    echo "✅ nginx está activo"
elif systemctl is-enabled --quiet nginx; then
    echo "⚠️  nginx está habilitado pero no activo"
    echo "   Iniciar con: sudo systemctl start nginx"
else
    echo "❌ nginx no está configurado"
    echo "   Habilitar con: sudo systemctl enable nginx"
fi

# Test básico del sistema
echo ""
echo "🧪 Test básico del sistema..."
if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from webapp_manager.cli import CLI
    print('✅ CLI importado correctamente')
except Exception as e:
    print(f'❌ Error importando CLI: {e}')
    exit(1)
"; then
    echo "✅ Sistema WebApp Manager funcional"
else
    echo "❌ Sistema WebApp Manager tiene problemas"
    exit 1
fi

# Verificar que rechaza sistemas no-Linux
echo ""
echo "🛡️  Verificando protección contra sistemas no-Linux..."
if python3 -c "
import sys, os
sys.path.insert(0, '.')
original_name = os.name
os.name = 'nt'  # Simular Windows
try:
    exec(open('webapp-manager.py').read())
    print('❌ ERROR: No rechaza sistemas Windows')
    exit(1)
except SystemExit as e:
    if e.code == 1:
        print('✅ Correctamente rechaza sistemas no-Linux')
    else:
        print(f'❌ Exit code incorrecto: {e.code}')
        exit(1)
finally:
    os.name = original_name
"; then
    echo "✅ Protección contra sistemas no-Linux funcional"
else
    echo "❌ Protección contra sistemas no-Linux falló"
    exit 1
fi

echo ""
echo "🎉 ¡VERIFICACIÓN COMPLETA!"
echo "========================="
echo "✅ Sistema Linux compatible"
echo "✅ Todas las dependencias instaladas"
echo "✅ WebApp Manager listo para usar"
echo ""
echo "🚀 Comandos para probar:"
echo "   ./webapp-manager.py gui"
echo "   ./webapp-manager.py types"
echo "   ./webapp-manager.py --help"
echo ""
echo "📖 Documentación:"
echo "   cat GITHUB_INSTRUCTIONS.md"
echo "   cat README_GITHUB.md"
