"""
Servicio para manejo de archivos de configuración
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from ..models import AppConfig
from ..utils import Colors


class FileService:
    """Servicio para manejo de archivos de configuración"""
    
    def __init__(self, config_file: str):
        self.config_file = Path(config_file)
        self.config_dir = self.config_file.parent
        
        # Crear directorio de configuración si no existe
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear archivo de configuración si no existe
        if not self.config_file.exists():
            self._create_empty_config()
    
    def _create_empty_config(self):
        """Crear archivo de configuración vacío"""
        empty_config = {
            "version": "3.0",
            "apps": {},
            "created_at": "2024-01-01T00:00:00Z",
            "last_modified": "2024-01-01T00:00:00Z"
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(empty_config, f, indent=2)
            
            # Establecer permisos apropiados
            os.chmod(self.config_file, 0o600)
            
        except Exception as e:
            print(Colors.error(f"Error creando archivo de configuración: {e}"))
    
    def get_app_config(self, domain: str) -> Optional[AppConfig]:
        """Obtener configuración de una aplicación"""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            if domain in data.get("apps", {}):
                app_data = data["apps"][domain]
                
                # Asegurar que el dominio esté presente en los datos
                if "domain" not in app_data:
                    app_data["domain"] = domain
                    
                return AppConfig.from_dict(app_data)
            
            return None
            
        except Exception as e:
            print(Colors.error(f"Error leyendo configuración: {e}"))
            return None
    
    def save_app_config(self, app_config: AppConfig) -> bool:
        """Guardar configuración de una aplicación"""
        try:
            # Leer configuración existente
            data = {"apps": {}}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
            
            # Actualizar configuración
            data["apps"][app_config.domain] = app_config.to_dict()
            data["last_modified"] = "2024-01-01T00:00:00Z"
            
            # Guardar configuración
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(Colors.error(f"Error guardando configuración: {e}"))
            return False
    
    def get_all_configs(self) -> Dict[str, AppConfig]:
        """Obtener todas las configuraciones"""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            configs = {}
            for domain, app_data in data.get("apps", {}).items():
                try:
                    # Asegurar que el dominio esté presente en los datos
                    if "domain" not in app_data:
                        app_data["domain"] = domain
                        
                    configs[domain] = AppConfig.from_dict(app_data)
                except Exception as e:
                    print(Colors.warning(f"Error procesando configuración de {domain}: {e}"))
                    continue
            
            return configs
            
        except Exception as e:
            print(Colors.error(f"Error leyendo configuraciones: {e}"))
            return {}
    
    def remove_app_config(self, domain: str) -> bool:
        """Eliminar configuración de una aplicación"""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            if domain in data.get("apps", {}):
                del data["apps"][domain]
                data["last_modified"] = "2024-01-01T00:00:00Z"
                
                with open(self.config_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                return True
            
            return False
            
        except Exception as e:
            print(Colors.error(f"Error eliminando configuración: {e}"))
            return False
    
    def backup_config(self, backup_file: str) -> bool:
        """Crear backup de la configuración"""
        try:
            backup_path = Path(backup_file)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'r') as src:
                data = json.load(src)
            
            with open(backup_path, 'w') as dst:
                json.dump(data, dst, indent=2)
            
            print(Colors.success(f"Backup creado en: {backup_path}"))
            return True
            
        except Exception as e:
            print(Colors.error(f"Error creando backup: {e}"))
            return False
    
    def restore_config(self, backup_file: str) -> bool:
        """Restaurar configuración desde backup"""
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                print(Colors.error(f"Archivo de backup no encontrado: {backup_path}"))
                return False
            
            with open(backup_path, 'r') as src:
                data = json.load(src)
            
            with open(self.config_file, 'w') as dst:
                json.dump(data, dst, indent=2)
            
            print(Colors.success("Configuración restaurada exitosamente"))
            return True
            
        except Exception as e:
            print(Colors.error(f"Error restaurando configuración: {e}"))
            return False
    
    def validate_config(self) -> bool:
        """Validar archivo de configuración"""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            # Verificar estructura básica
            if "apps" not in data:
                print(Colors.error("Estructura de configuración inválida: falta 'apps'"))
                return False
            
            # Validar cada aplicación
            for domain, app_data in data["apps"].items():
                try:
                    AppConfig.from_dict(app_data)
                except Exception as e:
                    print(Colors.error(f"Configuración inválida para {domain}: {e}"))
                    return False
            
            print(Colors.success("Configuración válida"))
            return True
            
        except Exception as e:
            print(Colors.error(f"Error validando configuración: {e}"))
            return False
