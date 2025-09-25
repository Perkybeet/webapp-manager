"""
Servicio para gestión de configuraciones nginx
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..utils import CommandRunner, Colors
from ..models import AppConfig
from .cmd_service import CmdService
from pathlib import Path
from typing import Optional

from ..utils import CommandRunner, Colors
from ..models import AppConfig
from .cmd_service import CmdService


class NginxService:
    """Servicio para gestión de nginx"""
    
    def __init__(self, nginx_sites_path: Path, nginx_enabled_path: Path, nginx_conf_path: Path, verbose: bool = False):
        self.nginx_sites = nginx_sites_path
        self.nginx_enabled = nginx_enabled_path
        self.nginx_conf = nginx_conf_path
        self.verbose = verbose
        self.cmd = CmdService(verbose=verbose)
    
    def create_config(self, app_config: AppConfig) -> bool:
        """Crear configuración nginx para aplicación"""
        try:
            config_content = self._get_nginx_config_content(app_config)
            config_path = self.nginx_sites / app_config.domain
            temp_config_path = self.nginx_sites / f"{app_config.domain}.temp"

            # Escribir configuración temporal
            with open(temp_config_path, "w") as f:
                f.write(config_content)

            # Validar configuración nginx
            print(Colors.info("Validando configuración nginx..."))
            test_result = self.cmd.run_sudo("nginx -t 2>&1", check=False)

            if test_result and ("syntax is ok" not in test_result or "test is successful" not in test_result):
                print(Colors.warning(f"Problemas en configuración nginx: {test_result}"))

            # Mover configuración temporal a definitiva
            shutil.move(temp_config_path, config_path)

            # Habilitar sitio
            self._enable_site(app_config.domain)

            # Validar configuración final
            final_test = self.cmd.run_sudo("nginx -t 2>&1", check=False)
            if final_test and "syntax is ok" in final_test and "test is successful" in final_test:
                print(Colors.success(f"Configuración nginx creada para {app_config.domain}"))
                return True
            else:
                print(Colors.warning(f"Configuración nginx creada con advertencias: {final_test}"))
                return True

        except Exception as e:
            print(Colors.error(f"Error creando configuración nginx: {e}"))
            temp_config = self.nginx_sites / f"{app_config.domain}.temp"
            if temp_config.exists():
                temp_config.unlink()
            return False

    def remove_config(self, domain: str) -> bool:
        """Remover configuración nginx"""
        try:
            # Deshabilitar sitio
            enabled_path = self.nginx_enabled / domain
            if enabled_path.exists():
                enabled_path.unlink()

            # Remover configuración
            config_path = self.nginx_sites / domain
            if config_path.exists():
                config_path.unlink()

            return True
        except Exception as e:
            print(Colors.error(f"Error removiendo configuración nginx: {e}"))
            return False

    def reload(self) -> bool:
        """Recargar nginx"""
        try:
            result = self.cmd.run_sudo("systemctl reload nginx", check=False)
            return result is not None
        except Exception:
            return False

    def test_config(self) -> bool:
        """Probar configuración nginx"""
        try:
            result = self.cmd.run_sudo("nginx -t 2>&1", check=False)
            return result and "syntax is ok" in result and "test is successful" in result
        except Exception:
            return False
    
    def enable_maintenance_mode(self, app_config: AppConfig) -> bool:
        """Activar modo mantenimiento para una aplicación"""
        try:
            # Crear directorio de mantenimiento si no existe
            maintenance_dir = Path("/var/www/maintenance")
            maintenance_dir.mkdir(parents=True, exist_ok=True)
            
            # Copiar template de mantenimiento
            template_path = Path(__file__).parent.parent / "templates" / "maintenance.html"
            shutil.copy2(template_path, maintenance_dir / "index.html")
            
            config_content = self._get_maintenance_config(app_config)
            config_path = self.nginx_sites / app_config.domain
            temp_config_path = self.nginx_sites / f"{app_config.domain}.maintenance"

            # Escribir configuración temporal
            with open(temp_config_path, "w") as f:
                f.write(config_content)

            # Validar configuración nginx
            test_result = self.cmd.run_sudo("nginx -t 2>&1", check=False)
            if not (test_result and "syntax is ok" in test_result and "test is successful" in test_result):
                print(f"Error en configuración de mantenimiento: {test_result}")
                return False

            # Backup de configuración original
            backup_path = self.nginx_sites / f"{app_config.domain}.backup"
            if config_path.exists():
                shutil.copy2(config_path, backup_path)

            # Mover configuración de mantenimiento
            shutil.move(temp_config_path, config_path)

            # Recargar nginx
            return self.reload()
        except Exception as e:
            print(f"Error activando modo mantenimiento: {e}")
            return False
    
    def disable_maintenance_mode(self, app_config: AppConfig) -> bool:
        """Desactivar modo mantenimiento para una aplicación"""
        try:
            config_path = self.nginx_sites / app_config.domain
            backup_path = self.nginx_sites / f"{app_config.domain}.backup"

            # Restaurar configuración original si existe backup
            if backup_path.exists():
                shutil.move(backup_path, config_path)
            else:
                # Recrear configuración normal si no hay backup
                return self.create_config(app_config)

            # Recargar nginx
            return self.reload()
        except Exception as e:
            print(f"Error desactivando modo mantenimiento: {e}")
            return False

    def _enable_site(self, domain: str):
        """Habilitar sitio nginx"""
        config_path = self.nginx_sites / domain
        enabled_path = self.nginx_enabled / domain
        
        if enabled_path.exists():
            enabled_path.unlink()
        enabled_path.symlink_to(config_path)

    def _get_nginx_config_content(self, app_config: AppConfig) -> str:
        """Obtener contenido de configuración nginx según tipo de app"""
        if app_config.app_type == "nextjs":
            return self._get_nextjs_config(app_config)
        elif app_config.app_type == "fastapi":
            return self._get_fastapi_config(app_config)
        elif app_config.app_type == "node":
            return self._get_node_config(app_config)
        elif app_config.app_type == "static":
            return self._get_static_config(app_config)
        else:
            return self._get_default_config(app_config)

    def _get_nextjs_config(self, app_config: AppConfig) -> str:
        """Configuración para aplicaciones Next.js"""
        return f"""# Next.js Application: {app_config.domain}
# Generated by WebApp Manager v3.0
# Date: {datetime.now().isoformat()}

server {{
    listen 80;
    server_name {app_config.domain};

    # Logs
    access_log /var/log/apps/{app_config.domain}-access.log combined;
    error_log /var/log/apps/{app_config.domain}-error.log warn;

    # Rate limiting
    limit_req zone=webapp_global burst=50 nodelay;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Proxy ALL requests to Next.js server
    location / {{
        proxy_pass http://localhost:{app_config.port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_cache_bypass $http_upgrade;

        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}

    # Health check endpoint
    location /nginx-health {{
        access_log off;
        return 200 "nginx healthy\\n";
        add_header Content-Type text/plain;
    }}

    # Block access to sensitive files
    location ~ /\\. {{
        deny all;
        access_log off;
        log_not_found off;
    }}

    location ~ /(package\\.json|package-lock\\.json|yarn\\.lock|\\.env|\\.env\\..*)$ {{
        deny all;
        access_log off;
        log_not_found off;
    }}

    # File upload settings
    client_max_body_size 100M;
    client_body_timeout 60s;
    client_header_timeout 60s;
}}"""

    def _get_fastapi_config(self, app_config: AppConfig) -> str:
        """Configuración para APIs FastAPI"""
        return f"""# FastAPI Application: {app_config.domain}
# Generated by WebApp Manager v3.0
# Date: {datetime.now().isoformat()}

server {{
    listen 80;
    server_name {app_config.domain};

    # Logs específicos para API
    access_log /var/log/apps/{app_config.domain}-access.log combined;
    error_log /var/log/apps/{app_config.domain}-error.log warn;

    # Rate limiting para API endpoints
    limit_req zone=webapp_global burst=100 nodelay;

    # Security headers para APIs
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # API endpoints - proxy a FastAPI/Uvicorn
    location / {{
        proxy_pass http://localhost:{app_config.port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_cache_bypass $http_upgrade;

        # Buffer settings para APIs
        proxy_buffering on;
        proxy_buffer_size 64k;
        proxy_buffers 8 64k;
        proxy_busy_buffers_size 128k;
        
        # Timeout settings para operaciones de API
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}

    # Documentación OpenAPI/Swagger
    location /docs {{
        proxy_pass http://localhost:{app_config.port}/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    location /redoc {{
        proxy_pass http://localhost:{app_config.port}/redoc;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    # Health check
    location /nginx-health {{
        access_log off;
        return 200 "nginx healthy\\n";
        add_header Content-Type text/plain;
    }}

    # Block access to sensitive files
    location ~ /\\. {{
        deny all;
        access_log off;
        log_not_found off;
    }}

    client_max_body_size 100M;
}}"""

    def _get_node_config(self, app_config: AppConfig) -> str:
        """Configuración para aplicaciones Node.js"""
        return f"""# Node.js Application: {app_config.domain}
# Generated by WebApp Manager v3.0
# Date: {datetime.now().isoformat()}

server {{
    listen 80;
    server_name {app_config.domain};

    access_log /var/log/apps/{app_config.domain}-access.log;
    error_log /var/log/apps/{app_config.domain}-error.log;

    # Rate limiting
    limit_req zone=webapp_global burst=50 nodelay;

    location / {{
        proxy_pass http://localhost:{app_config.port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_cache_bypass $http_upgrade;

        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}

    location /nginx-health {{
        access_log off;
        return 200 "nginx healthy\\n";
        add_header Content-Type text/plain;
    }}

    client_max_body_size 100M;
}}"""

    def _get_static_config(self, app_config: AppConfig) -> str:
        """Configuración para sitios estáticos"""
        return f"""# Static Site: {app_config.domain}
# Generated by WebApp Manager v3.0
# Date: {datetime.now().isoformat()}

server {{
    listen 80;
    server_name {app_config.domain};
    root /var/www/apps/{app_config.domain};
    index index.html index.htm;

    access_log /var/log/apps/{app_config.domain}-access.log;
    error_log /var/log/apps/{app_config.domain}-error.log;

    limit_req zone=webapp_global burst=50 nodelay;

    location / {{
        try_files $uri $uri/ =404;
    }}

    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {{
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
}}"""

    def _get_maintenance_config(self, app_config: AppConfig) -> str:
        """Configuración para modo mantenimiento"""
        return f"""# Maintenance Mode: {app_config.domain}
# Generated by WebApp Manager v3.0
# Date: {datetime.now().isoformat()}

server {{
    listen 80;
    server_name {app_config.domain};

    # Logs
    access_log /var/log/apps/{app_config.domain}-access.log combined;
    error_log /var/log/apps/{app_config.domain}-error.log warn;

    # Root directory for maintenance page
    root /var/www/maintenance;
    index index.html;

    # Serve maintenance page for all requests
    location / {{
        try_files /index.html =404;
    }}

    # Cache maintenance page briefly
    location ~* \\.(html)$ {{
        expires 30s;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }}
}}"""

    def _get_default_config(self, app_config: AppConfig) -> str:
        """Configuración por defecto"""
        return self._get_node_config(app_config)

    def _get_maintenance_config(self, app_config: AppConfig) -> str:
        """Obtener configuración para modo mantenimiento"""
        return f"""# Modo Mantenimiento: {app_config.domain}
# Generated by WebApp Manager v3.0
# Date: {datetime.now().isoformat()}

server {{
    listen 80;
    server_name {app_config.domain};

    # Ruta al directorio de mantenimiento
    location / {{
        root /var/www/maintenance;
        index index.html;
        try_files $uri $uri/ =404;
    }}

    # Logs
    access_log /var/log/apps/{app_config.domain}-access.log combined;
    error_log /var/log/apps/{app_config.domain}-error.log warn;

    # Seguridad adicional
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Health check
    location /nginx-health {{
        access_log off;
        return 200 "nginx healthy\\n";
        add_header Content-Type text/plain;
    }}

    # Bloquear acceso a archivos sensibles
    location ~ /\\. {{
        deny all;
        access_log off;
        log_not_found off;
    }}
}}"""
