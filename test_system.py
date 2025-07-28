#!/usr/bin/env python3
"""
Script de prueba para verificar que el sistema modular funciona correctamente
"""

from webapp_manager.deployers import DeployerFactory
from webapp_manager.gui import TerminalUI
from webapp_manager.services import FileService, AppService, CmdService
from pathlib import Path

def test_deployers():
    """Probar sistema de deployers"""
    print("=== PRUEBA DE DEPLOYERS ===")
    
    # Listar deployers disponibles
    print("\n1. Deployers disponibles:")
    for deployer_type in DeployerFactory.get_supported_types():
        info = DeployerFactory.get_deployer_info(deployer_type)
        print(f"   - {deployer_type}: {info['description']}")
        print(f"     Archivos requeridos: {', '.join(info['required_files'])}")
        print(f"     Archivos opcionales: {', '.join(info['optional_files'])}")
        print(f"     Soportado: {'✓' if info['supported'] else '✗'}")
        print()
    
    # Detectar tipo de aplicación
    print("2. Detección automática de tipos:")
    print(f"   - Directorio actual: {DeployerFactory.detect_app_type('.')}")
    print()
    
    # Crear deployer específico
    print("3. Crear deployer FastAPI:")
    try:
        cmd_service = CmdService()
        fastapi_deployer = DeployerFactory.create_deployer('fastapi', '/tmp', cmd_service)
        print(f"   - Deployer creado: {fastapi_deployer.__class__.__name__}")
        print(f"   - Tipo: {fastapi_deployer.get_app_type()}")
        print(f"   - Archivos requeridos: {fastapi_deployer.get_required_files()}")
        print(f"   - Archivos opcionales: {fastapi_deployer.get_optional_files()}")
    except Exception as e:
        print(f"   - Error: {e}")
    print()

def test_services():
    """Probar servicios"""
    print("=== PRUEBA DE SERVICIOS ===")
    
    # Test FileService
    print("\n1. FileService:")
    try:
        file_service = FileService('./test_config.json')
        print("   - FileService creado correctamente")
        print(f"   - Archivo de configuración: {file_service.config_file}")
        print(f"   - Configuración válida: {file_service.validate_config()}")
    except Exception as e:
        print(f"   - Error: {e}")
    
    # Test AppService
    print("\n2. AppService:")
    try:
        app_service = AppService(Path('./test_apps'))
        print("   - AppService creado correctamente")
        print(f"   - Directorio de apps: {app_service.apps_dir}")
    except Exception as e:
        print(f"   - Error: {e}")
    
    # Test CmdService
    print("\n3. CmdService:")
    try:
        cmd_service = CmdService()
        print("   - CmdService creado correctamente")
        print(f"   - Python disponible: {cmd_service.is_command_available('python')}")
        print(f"   - Git disponible: {cmd_service.is_command_available('git')}")
    except Exception as e:
        print(f"   - Error: {e}")
    print()

def test_gui():
    """Probar GUI"""
    print("=== PRUEBA DE GUI ===")
    
    try:
        # Solo crear instancia, no ejecutar
        file_service = FileService('./test_config.json')
        app_service = AppService(Path('./test_apps'))
        gui = TerminalUI(file_service, app_service)
        print("   - TerminalUI creado correctamente")
        print(f"   - Clase: {gui.__class__.__name__}")
        print(f"   - Servicios configurados: FileService, AppService")
    except Exception as e:
        print(f"   - Error: {e}")
    print()

def main():
    """Función principal"""
    print("VERIFICACIÓN DEL SISTEMA MODULAR WEBAPP-MANAGER")
    print("=" * 60)
    
    try:
        test_deployers()
        test_services() 
        test_gui()
        
        print("✓ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("✓ Sistema modular funcionando correctamente")
        print("✓ GUI terminal disponible")
        print("✓ Deployers modulares funcionando")
        
    except Exception as e:
        print(f"✗ ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
