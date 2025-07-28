#!/usr/bin/env python3
"""
WebApp Manager v4.0 - Sistema Modular para Linux
Sistema completo de gestión de aplicaciones web con nginx proxy reverso
Optimizado para servidores Linux con interfaz gráfica terminal
"""

import sys
import os

# Verificar que estamos en Linux
if os.name != 'posix':
    print("❌ Error: WebApp Manager está diseñado solo para sistemas Linux")
    print("   Por favor, ejecuta esta aplicación en un servidor Linux")
    sys.exit(1)

# Agregar el directorio actual al path para importar el módulo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webapp_manager.cli import CLI


def main():
    """Función principal - Sistema modular para Linux"""
    try:
        cli = CLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n🔴 Operación cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
