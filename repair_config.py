#!/usr/bin/env python3
"""
Utilidad para reparar archivos de configuración corruptos
"""

import json
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

def repair_config_file(config_path: str):
    """Reparar archivo de configuración corrupto"""
    config_file = Path(config_path)
    
    print(f"🔧 Reparando archivo de configuración: {config_file}")
    
    if not config_file.exists():
        print(f"❌ El archivo {config_file} no existe")
        return False
    
    # Crear backup
    backup_path = config_file.with_suffix(f".backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    print(f"📦 Creando backup: {backup_path}")
    shutil.copy2(config_file, backup_path)
    
    try:
        # Leer el archivo actual
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"📄 Contenido actual: {content[:200]}...")
        
        # Intentar parsear JSON
        try:
            config_data = json.loads(content)
            print("✅ JSON válido")
            
            # Verificar estructura
            if "apps" not in config_data:
                print("⚠️  Agregando sección 'apps' faltante")
                config_data["apps"] = {}
            
            # Validar cada aplicación
            valid_apps = {}
            for domain, app_data in config_data.get("apps", {}).items():
                if isinstance(app_data, dict) and app_data:
                    required_fields = ['domain', 'port', 'app_type', 'source', 'branch', 'ssl', 'created']
                    missing_fields = [field for field in required_fields if field not in app_data]
                    
                    if missing_fields:
                        print(f"⚠️  Aplicación {domain} tiene campos faltantes: {missing_fields}")
                        print(f"   Eliminando aplicación corrupta...")
                    else:
                        valid_apps[domain] = app_data
                        print(f"✅ Aplicación {domain} válida")
                else:
                    print(f"⚠️  Aplicación {domain} tiene datos inválidos, eliminando...")
            
            # Actualizar configuración
            config_data["apps"] = valid_apps
            
            # Asegurar metadatos
            if "version" not in config_data:
                config_data["version"] = "4.0"
            if "created_at" not in config_data:
                config_data["created_at"] = datetime.now().isoformat()
            config_data["last_modified"] = datetime.now().isoformat()
            
            # Escribir configuración reparada
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Archivo reparado exitosamente")
            print(f"   Aplicaciones válidas: {len(valid_apps)}")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON corrupto: {e}")
            print("🔧 Creando archivo de configuración nuevo...")
            
            # Crear configuración nueva
            new_config = {
                "version": "4.0",
                "apps": {},
                "created_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=2, ensure_ascii=False)
            
            print("✅ Archivo de configuración nuevo creado")
            return True
            
    except Exception as e:
        print(f"❌ Error al reparar archivo: {e}")
        
        # Restaurar backup si es posible
        if backup_path.exists():
            print(f"🔄 Restaurando backup...")
            shutil.copy2(backup_path, config_file)
        
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python repair_config.py <path_to_config_file>")
        print("Ejemplo: python repair_config.py /etc/webapp-manager/config.json")
        sys.exit(1)
    
    config_path = sys.argv[1]
    success = repair_config_file(config_path)
    
    if success:
        print("🎉 Reparación completada exitosamente")
    else:
        print("❌ Fallo en la reparación")
        sys.exit(1)
