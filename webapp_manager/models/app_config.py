"""
Modelos de datos para WebApp Manager
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class AppConfig:
    """Configuración de una aplicación web"""
    domain: str
    port: int
    app_type: str
    source: str
    branch: str
    ssl: bool
    created: str
    last_updated: str = ""
    status: str = "unknown"
    build_command: str = ""
    start_command: str = ""
    env_vars: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Inicialización posterior a la creación"""
        if not self.last_updated:
            self.last_updated = self.created
        if self.env_vars is None:
            self.env_vars = {}
    
    @classmethod
    def create_new(
        cls,
        domain: str,
        port: int,
        app_type: str,
        source: str,
        branch: str = "main",
        ssl: bool = True,
        build_command: str = "",
        start_command: str = "",
        env_vars: Optional[Dict[str, str]] = None
    ) -> 'AppConfig':
        """Crear nueva configuración de aplicación"""
        now = datetime.now().isoformat()
        return cls(
            domain=domain,
            port=port,
            app_type=app_type,
            source=source,
            branch=branch,
            ssl=ssl,
            created=now,
            last_updated=now,
            status="pending",
            build_command=build_command,
            start_command=start_command,
            env_vars=env_vars or {}
        )
    
    def update_timestamp(self):
        """Actualizar timestamp de última modificación"""
        self.last_updated = datetime.now().isoformat()
    
    def set_active(self):
        """Marcar aplicación como activa"""
        self.status = "active"
        self.update_timestamp()
    
    def set_failed(self):
        """Marcar aplicación como fallida"""
        self.status = "failed"
        self.update_timestamp()
    
    def to_dict(self) -> dict:
        """Convertir a diccionario para serialización"""
        return {
            'domain': self.domain,
            'port': self.port,
            'app_type': self.app_type,
            'source': self.source,
            'branch': self.branch,
            'ssl': self.ssl,
            'created': self.created,
            'last_updated': self.last_updated,
            'status': self.status,
            'build_command': self.build_command,
            'start_command': self.start_command,
            'env_vars': self.env_vars
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AppConfig':
        """Crear instancia desde diccionario"""
        if not data or not isinstance(data, dict):
            raise ValueError("Datos inválidos: se esperaba un diccionario no vacío")
        
        # Validar campos requeridos
        required_fields = ['domain', 'port', 'app_type', 'source', 'branch', 'ssl', 'created']
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Campo requerido faltante: {', '.join(missing_fields)}")
        
        # Asegurar valores por defecto
        defaults = {
            'last_updated': data.get('last_updated', data.get('created', '')),
            'status': data.get('status', 'unknown'),
            'build_command': data.get('build_command', ''),
            'start_command': data.get('start_command', ''),
            'env_vars': data.get('env_vars', {})
        }
        
        # Combinar datos con defaults
        config_data = {**data, **defaults}
        
        return cls(**config_data)


@dataclass
class GlobalConfig:
    """Configuración global del sistema"""
    default_ssl: bool = True
    auto_backup: bool = True
    backup_retention_days: int = 30
    max_backups_per_app: int = 5
    nginx_worker_processes: str = "auto"
    nginx_worker_connections: int = 1024
    log_level: str = "INFO"
    
    def to_dict(self) -> dict:
        """Convertir a diccionario"""
        return {
            'default_ssl': self.default_ssl,
            'auto_backup': self.auto_backup,
            'backup_retention_days': self.backup_retention_days,
            'max_backups_per_app': self.max_backups_per_app,
            'nginx_worker_processes': self.nginx_worker_processes,
            'nginx_worker_connections': self.nginx_worker_connections,
            'log_level': self.log_level
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GlobalConfig':
        """Crear instancia desde diccionario"""
        return cls(**data)


@dataclass
class SystemPaths:
    """Rutas del sistema"""
    apps_dir: str = "/var/www/apps"
    nginx_sites: str = "/etc/nginx/sites-available"
    nginx_enabled: str = "/etc/nginx/sites-enabled"
    systemd_dir: str = "/etc/systemd/system"
    log_dir: str = "/var/log/apps"
    config_file: str = "/etc/webapp-manager/config.json"
    backup_dir: str = "/var/backups/webapp-manager"
    nginx_conf: str = "/etc/nginx/nginx.conf"
    
    def __post_init__(self):
        """Convertir strings a Path objects en core.manager"""
        pass
