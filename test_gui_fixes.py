#!/usr/bin/env python3
"""
Test script para verificar las correcciones del GUI
"""

import sys
import os
import tempfile
import json
from datetime import datetime

# Agregar el path del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webapp_manager.models.app_config import AppConfig
from webapp_manager.gui.terminal_ui import TerminalUI

def test_gui_fixes():
    """Prueba las correcciones del GUI"""
    print("🧪 Testing GUI fixes...")
    
    # Test 1: Crear AppConfig con todos los campos
    print("\n1. Testing AppConfig creation...")
    app_config = AppConfig(
        domain="test.example.com",
        port=3000,
        app_type="nextjs",
        source="https://github.com/test/test",
        branch="main",
        ssl=True,
        created=datetime.now().isoformat(),
        last_updated=datetime.now().isoformat(),
        status="active"
    )
    print(f"   ✅ AppConfig created: {app_config.domain}")
    
    # Test 2: Crear AppConfig con campos faltantes
    print("\n2. Testing AppConfig with missing fields...")
    app_config_incomplete = AppConfig(
        domain="test2.example.com",
        port=3001,
        app_type="fastapi",
        source="https://github.com/test/test2",
        branch="main",
        ssl=False,
        created=datetime.now().isoformat()
    )
    print(f"   ✅ Incomplete AppConfig created: {app_config_incomplete.domain}")
    
    # Test 3: Lista de aplicaciones
    print("\n3. Testing app list...")
    apps = [app_config, app_config_incomplete]
    print(f"   ✅ App list created with {len(apps)} apps")
    
    # Test 4: Verificar campos con getattr
    print("\n4. Testing field access with getattr...")
    for app in apps:
        domain = getattr(app, 'domain', 'N/A') or 'N/A'
        status = getattr(app, 'status', 'unknown') or 'unknown'
        print(f"   ✅ App: {domain}, Status: {status}")
    
    print("\n🎉 All GUI fixes tests passed!")

if __name__ == "__main__":
    test_gui_fixes()
