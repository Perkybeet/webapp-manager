"""
Módulo base para deployers de aplicaciones
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, List
from ..models.app_config import AppConfig
from ..utils.command_runner import CommandRunner
from ..utils.colors import Colors


class BaseDeployer(ABC):
    """Clase base para todos los deployers"""
    
    def __init__(self, apps_dir: str, cmd_service=None):
        self.apps_dir = Path(apps_dir)
        self.cmd = cmd_service or CommandRunner
        self.app_type = self.get_app_type()
    
    @abstractmethod
    def get_app_type(self) -> str:
        """Retorna el tipo de aplicación que maneja este deployer"""
        pass
    
    @abstractmethod
    def validate_structure(self, app_dir: Path) -> bool:
        """Valida que la estructura de la aplicación sea correcta"""
        pass
    
    @abstractmethod
    def install_dependencies(self, app_dir: Path, app_config: AppConfig) -> bool:
        """Instala las dependencias de la aplicación"""
        pass
    
    @abstractmethod
    def build_application(self, app_dir: Path, app_config: AppConfig) -> bool:
        """Construye la aplicación"""
        pass
    
    @abstractmethod
    def get_default_start_command(self, app_config: AppConfig) -> str:
        """Retorna el comando de inicio por defecto"""
        pass
    
    @abstractmethod
    def get_default_build_command(self, app_config: AppConfig) -> str:
        """Retorna el comando de build por defecto"""
        pass
    
    @abstractmethod
    def get_required_files(self) -> List[str]:
        """Retorna la lista de archivos requeridos"""
        pass
    
    @abstractmethod
    def get_optional_files(self) -> List[str]:
        """Retorna la lista de archivos opcionales"""
        pass
    
    @abstractmethod
    def get_environment_variables(self, app_config: AppConfig) -> Dict[str, str]:
        """Retorna las variables de entorno por defecto"""
        pass
    
    def deploy(self, app_config: AppConfig) -> bool:
        """Proceso completo de despliegue"""
        try:
            app_dir = self.apps_dir / app_config.domain
            
            print(Colors.info(f"Iniciando despliegue {self.app_type} para {app_config.domain}"))
            
            # Validar estructura
            if not self.validate_structure(app_dir):
                print(Colors.error("Estructura de aplicación inválida"))
                return False
            
            # Instalar dependencias
            if not self.install_dependencies(app_dir, app_config):
                print(Colors.error("Error instalando dependencias"))
                return False
            
            # Construir aplicación
            if not self.build_application(app_dir, app_config):
                print(Colors.error("Error construyendo aplicación"))
                return False
            
            # Configurar permisos
            self.set_permissions(app_dir)
            
            print(Colors.success(f"Despliegue {self.app_type} completado exitosamente"))
            return True
            
        except Exception as e:
            print(Colors.error(f"Error en despliegue {self.app_type}: {e}"))
            return False
    
    def rebuild(self, app_config: AppConfig) -> bool:
        """Reconstruir aplicación existente"""
        try:
            app_dir = self.apps_dir / app_config.domain
            
            print(Colors.info(f"Reconstruyendo aplicación {self.app_type}"))
            
            # Limpiar build anterior
            self.clean_build_artifacts(app_dir)
            
            # Reinstalar dependencias
            if not self.install_dependencies(app_dir, app_config):
                return False
            
            # Reconstruir
            if not self.build_application(app_dir, app_config):
                return False
            
            # Configurar permisos
            self.set_permissions(app_dir)
            
            print(Colors.success(f"Reconstrucción {self.app_type} completada"))
            return True
            
        except Exception as e:
            print(Colors.error(f"Error en reconstrucción {self.app_type}: {e}"))
            return False
    
    def clean_build_artifacts(self, app_dir: Path):
        """Limpiar artefactos de build"""
        # Implementación por defecto - los deployers específicos pueden sobrescribir
        pass
    
    def set_permissions(self, app_dir: Path):
        """Configurar permisos de la aplicación"""
        self.cmd.run(f"chown -R www-data:www-data {app_dir}", check=False)
        self.cmd.run(f"chmod -R 755 {app_dir}", check=False)
    
    def check_requirements(self) -> bool:
        """Verificar que los requerimientos del sistema estén instalados"""
        return True
    
    def get_health_check_command(self, app_config: AppConfig) -> Optional[str]:
        """Retorna comando para verificar salud de la aplicación"""
        return f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{app_config.port}"
    
    def get_log_files(self, app_config: AppConfig) -> List[str]:
        """Retorna archivos de log específicos de la aplicación"""
        return [
            f"/var/log/webapp-manager/{app_config.domain}.log",
            f"/var/log/{app_config.domain}.log"
        ]
