#!/usr/bin/env python3
"""
Test rápido para verificar el sistema WebApp Manager
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Verificar que todas las importaciones funcionan"""
    print("🔍 Verificando importaciones...")
    
    try:
        from webapp_manager.cli import CLI
        print("✅ CLI importado correctamente")
        
        from webapp_manager.core.manager import WebAppManager
        print("✅ WebAppManager importado correctamente")
        
        from webapp_manager.gui.terminal_ui import TerminalUI
        print("✅ TerminalUI importado correctamente")
        
        from webapp_manager.deployers.deployer_factory import DeployerFactory
        print("✅ DeployerFactory importado correctamente")
        
        from webapp_manager.deployers.fastapi_deployer import FastAPIDeployer
        print("✅ FastAPIDeployer importado correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en importaciones: {e}")
        return False

def test_factory():
    """Verificar que el factory funciona"""
    print("\n🏭 Verificando DeployerFactory...")
    
    try:
        from webapp_manager.deployers.deployer_factory import DeployerFactory
        
        # Obtener tipos soportados
        types = DeployerFactory.get_supported_types()
        print(f"✅ Tipos soportados: {types}")
        
        # Crear deployer FastAPI
        deployer = DeployerFactory.create_deployer("fastapi", "/tmp", None)
        print(f"✅ Deployer FastAPI creado: {type(deployer).__name__}")
        
        # Verificar método get_start_command
        from webapp_manager.models.app_config import AppConfig
        from datetime import datetime
        
        config = AppConfig(
            domain="test.com",
            port=8000,
            app_type="fastapi",
            source="test",
            branch="main",
            ssl=False,
            created=datetime.now().isoformat(),
            build_command="",
            start_command=""
        )
        
        start_cmd = deployer.get_start_command(config)
        print(f"✅ Comando de inicio: {start_cmd}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en factory: {e}")
        return False

def test_manager():
    """Verificar que el manager funciona"""
    print("\n🎯 Verificando WebAppManager...")
    
    try:
        from webapp_manager.core.manager import WebAppManager
        
        manager = WebAppManager()
        print("✅ WebAppManager inicializado correctamente")
        
        # Verificar servicios
        if hasattr(manager, 'app_service'):
            print("✅ app_service disponible")
        if hasattr(manager, 'nginx_service'):
            print("✅ nginx_service disponible")
        if hasattr(manager, 'systemd_service'):
            print("✅ systemd_service disponible")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en manager: {e}")
        return False

def test_gui():
    """Verificar que la GUI funciona"""
    print("\n🎨 Verificando GUI...")
    
    try:
        from webapp_manager.gui.terminal_ui import TerminalUI
        
        # Verificar que se puede crear sin error
        ui = TerminalUI()
        print("✅ TerminalUI creado correctamente")
        
        # Verificar que el manager está inicializado
        if hasattr(ui, 'manager') and ui.manager is not None:
            print("✅ Manager inicializado en GUI")
        else:
            print("❌ Manager NO inicializado en GUI")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en GUI: {e}")
        return False

def main():
    """Ejecutar todos los tests"""
    print("🚀 WebApp Manager - Test de Sistema")
    print("=" * 50)
    
    tests = [
        ("Importaciones", test_imports),
        ("Factory Pattern", test_factory),
        ("Manager", test_manager),
        ("GUI", test_gui)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    print("\n📊 Resultados:")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        print("   El sistema está listo para usar")
    else:
        print("⚠️  HAY TESTS FALLANDO")
        print("   Revisa los errores arriba")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
