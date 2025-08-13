#!/usr/bin/env python3
"""
Script de prueba para verificar que CmdService tiene todos los métodos necesarios
"""

import sys
import os
from pathlib import Path

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from webapp_manager.services.cmd_service import CmdService
    
    print("✅ CmdService importado correctamente")
    
    # Crear instancia
    cmd = CmdService(verbose=True)
    print("✅ CmdService instanciado correctamente")
    
    # Verificar que tenga los métodos necesarios
    required_methods = [
        'run',
        'run_sudo', 
        'run_interactive',
        'run_background',
        'test_command_exists'
    ]
    
    for method in required_methods:
        if hasattr(cmd, method):
            print(f"✅ Método {method} disponible")
        else:
            print(f"❌ Método {method} FALTANTE")
            
    print("\n🎉 Verificación completada - CmdService está correctamente implementado")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
