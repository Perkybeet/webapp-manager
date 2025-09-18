#!/usr/bin/env python3
"""
WebApp Manager SAAS - Main Entry Point
Sistema completo de gestión de aplicaciones web con interfaz web SAAS
"""

import sys
import os
import argparse
from pathlib import Path

# Agregar el directorio actual al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Punto de entrada principal con soporte para interfaz web"""
    parser = argparse.ArgumentParser(
        description="WebApp Manager SAAS - Sistema de Gestión de Aplicaciones Web"
    )
    
    parser.add_argument('command', nargs='?', default='gui',
                       choices=['gui', 'web', 'cli', 'add', 'remove', 'list', 'status', 'types', 'detect'],
                       help='Comando a ejecutar')
    
    parser.add_argument('--host', default='0.0.0.0',
                       help='Host para el servidor web (default: 0.0.0.0)')
    
    parser.add_argument('--port', type=int, default=8080,
                       help='Puerto para el servidor web (default: 8080)')
    
    parser.add_argument('--debug', action='store_true',
                       help='Ejecutar en modo debug')
    
    # Argumentos para CLI tradicional
    parser.add_argument('--name', help='Nombre de la aplicación')
    parser.add_argument('--type', help='Tipo de aplicación')
    parser.add_argument('--port-app', type=int, help='Puerto de la aplicación')
    parser.add_argument('--directory', help='Directorio de la aplicación')
    parser.add_argument('--git-url', help='URL del repositorio Git')
    parser.add_argument('--domain', help='Dominio de la aplicación')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo verbose')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'web':
            # Ejecutar servidor web SAAS
            from webapp_manager.web.app import run_web_server
            
            print(f"🚀 Iniciando WebApp Manager SAAS...")
            print(f"🌐 Accesible en: http://{args.host}:{args.port}")
            print(f"👤 Usuario predeterminado: admin / admin123")
            print(f"🔧 Modo debug: {'activado' if args.debug else 'desactivado'}")
            
            run_web_server(
                host=args.host,
                port=args.port,
                debug=args.debug
            )
            
        elif args.command in ['gui', 'cli', 'add', 'remove', 'list', 'status', 'types', 'detect']:
            # Ejecutar CLI tradicional
            from webapp_manager.cli import CLI
            
            # Preparar argumentos para CLI
            cli_args = []
            if args.command != 'gui':
                cli_args.append(args.command)
            
            if args.name:
                cli_args.extend(['--name', args.name])
            if args.type:
                cli_args.extend(['--type', args.type])
            if args.port_app:
                cli_args.extend(['--port', str(args.port_app)])
            if args.directory:
                cli_args.extend(['--directory', args.directory])
            if args.git_url:
                cli_args.extend(['--git-url', args.git_url])
            if args.domain:
                cli_args.extend(['--domain', args.domain])
            if args.verbose:
                cli_args.append('--verbose')
            
            # Modificar sys.argv para CLI
            original_argv = sys.argv[:]
            sys.argv = [sys.argv[0]] + cli_args
            
            try:
                cli = CLI()
                cli.run()
            finally:
                sys.argv = original_argv
        
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()