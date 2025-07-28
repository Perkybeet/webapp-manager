"""
Gestión de configuración del sistema
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict

from ..models import AppConfig, GlobalConfig
from ..utils import Colors

logger = logging.getLogger(__name__)


class ConfigManager:
    """Gestor de configuración del sistema"""
    
    def __init__(self, config_file: Path, backup_dir: Path):
        self.config_file = config_file
        self.backup_dir = backup_dir
        self._ensure_config_dir()
    
    def load_config(self) -> Dict:
        """Cargar configuración desde archivo JSON"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return self._migrate_config(config)
            
            # Configuración por defecto
            return {
                "apps": {},
                "global": GlobalConfig().to_dict()
            }
            
        except Exception as e:
            print(Colors.error(f"Error cargando configuración: {e}"))
            return {"apps": {}, "global": GlobalConfig().to_dict()}

    def save_config(self, config: Dict):
        """Guardar configuración en archivo JSON"""
        try:
            # Crear backup si existe configuración previa
            if self.config_file.exists():
                backup_name = f"config-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
                backup_path = self.backup_dir / backup_name
                shutil.copy2(self.config_file, backup_path)

            # Guardar nueva configuración
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            # Configurar permisos
            import subprocess
            subprocess.run(f"sudo chown root:root {self.config_file}", shell=True, check=False)
            subprocess.run(f"sudo chmod 600 {self.config_file}", shell=True, check=False)

        except Exception as e:
            print(Colors.error(f"Error guardando configuración: {e}"))

    def add_app(self, app_config: AppConfig):
        """Agregar aplicación a la configuración"""
        config = self.load_config()
        config["apps"][app_config.domain] = app_config.to_dict()
        self.save_config(config)

    def remove_app(self, domain: str):
        """Remover aplicación de la configuración"""
        config = self.load_config()
        if domain in config["apps"]:
            del config["apps"][domain]
            self.save_config(config)

    def update_app(self, domain: str, app_config: AppConfig):
        """Actualizar configuración de aplicación"""
        config = self.load_config()
        if domain in config["apps"]:
            config["apps"][domain] = app_config.to_dict()
            self.save_config(config)

    def get_app(self, domain: str) -> AppConfig:
        """Obtener configuración de aplicación"""
        config = self.load_config()
        if domain in config["apps"]:
            try:
                app_data = config["apps"][domain]
                
                # Asegurar que el dominio esté presente en los datos
                if "domain" not in app_data:
                    app_data["domain"] = domain
                    
                return AppConfig.from_dict(app_data)
            except Exception as e:
                logger.error(f"Error al cargar aplicación {domain}: {e}")
                raise ValueError(f"Aplicación {domain} tiene configuración corrupta: {e}")
        raise ValueError(f"Aplicación {domain} no encontrada")

    def get_all_apps(self) -> Dict[str, AppConfig]:
        """Obtener todas las aplicaciones"""
        config = self.load_config()
        apps = {}
        
        if "apps" not in config or not config["apps"]:
            return apps
            
        for domain, app_data in config["apps"].items():
            try:
                if isinstance(app_data, dict) and app_data:
                    # Asegurar que el dominio esté presente en los datos
                    if "domain" not in app_data:
                        app_data["domain"] = domain
                    apps[domain] = AppConfig.from_dict(app_data)
                else:
                    logger.warning(f"Datos de aplicación inválidos para {domain}: {app_data}")
            except Exception as e:
                logger.error(f"Error al cargar aplicación {domain}: {e}")
                continue
                
        return apps

    def app_exists(self, domain: str) -> bool:
        """Verificar si una aplicación existe"""
        config = self.load_config()
        return domain in config["apps"]

    def is_port_in_use(self, port: int, exclude_domain: str = None) -> bool:
        """Verificar si un puerto está en uso"""
        config = self.load_config()
        for domain, app_data in config["apps"].items():
            if domain != exclude_domain and app_data.get("port") == port:
                return True
        return False

    def get_global_config(self) -> GlobalConfig:
        """Obtener configuración global"""
        config = self.load_config()
        return GlobalConfig.from_dict(config.get("global", {}))

    def update_global_config(self, global_config: GlobalConfig):
        """Actualizar configuración global"""
        config = self.load_config()
        config["global"] = global_config.to_dict()
        self.save_config(config)

    def _ensure_config_dir(self):
        """Asegurar que el directorio de configuración existe"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _migrate_config(self, config: Dict) -> Dict:
        """Migrar configuración antigua a nueva estructura"""
        # Asegurar que existe configuración global
        if "global" not in config:
            config["global"] = GlobalConfig().to_dict()

        # Migrar aplicaciones antiguas
        for domain, app_data in config.get("apps", {}).items():
            if isinstance(app_data, dict):
                # Agregar campos faltantes
                if "last_updated" not in app_data:
                    app_data["last_updated"] = app_data.get("created", "")
                if "status" not in app_data:
                    app_data["status"] = "unknown"
                if "build_command" not in app_data:
                    app_data["build_command"] = ""
                if "start_command" not in app_data:
                    app_data["start_command"] = ""
                if "env_vars" not in app_data:
                    app_data["env_vars"] = {}
                
                # Migrar campo 'type' a 'app_type' si es necesario
                if "type" in app_data and "app_type" not in app_data:
                    app_data["app_type"] = app_data["type"]
                    del app_data["type"]

        return config

    def export_config(self, export_path: Path) -> bool:
        """Exportar configuración a archivo"""
        try:
            config = self.load_config()
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(Colors.success(f"Configuración exportada a {export_path}"))
            return True
        except Exception as e:
            print(Colors.error(f"Error exportando configuración: {e}"))
            return False

    def import_config(self, import_path: Path) -> bool:
        """Importar configuración desde archivo"""
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Validar estructura básica
            if "apps" not in config:
                config["apps"] = {}
            if "global" not in config:
                config["global"] = GlobalConfig().to_dict()
            
            # Migrar configuración
            config = self._migrate_config(config)
            
            # Guardar configuración
            self.save_config(config)
            print(Colors.success(f"Configuración importada desde {import_path}"))
            return True
        except Exception as e:
            print(Colors.error(f"Error importando configuración: {e}"))
            return False
