#!/usr/bin/env python3
"""
WebApp Manager v4.0 - Sistema Modular para Linux
Sistema completo de gestión de aplicaciones web con nginx proxy reverso
Optimizado para servidores Linux con interfaz gráfica terminal
"""

import sys
import os

# Agregar el directorio actual al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webapp_manager.cli import CLI

def main():
    """Punto de entrada principal"""
    try:
        cli = CLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()