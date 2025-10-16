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
    
    def has_maintenance_config(self, domain: str) -> bool:
        """Verificar si el dominio ya tiene configuración de mantenimiento"""
        try:
            config_path = self.nginx_sites / domain
            if not config_path.exists():
                return False
                
            with open(config_path, 'r') as f:
                content = f.read()
                return "error_page 502 503 504 /maintenance/error502.html" in content and "location ^~ /maintenance/" in content
        except Exception:
            return False
    
    def ensure_maintenance_directory(self) -> bool:
        """Asegurar que el directorio de mantenimiento existe"""
        try:
            maintenance_dir = Path("/apps/maintenance")
            maintenance_dir.mkdir(parents=True, exist_ok=True)
            
            # Copiar archivos de mantenimiento desde templates
            template_dir = Path(__file__).parent.parent.parent / "apps" / "maintenance"
            
            if template_dir.exists():
                for html_file in template_dir.glob("*.html"):
                    target_file = maintenance_dir / html_file.name
                    if not target_file.exists():
                        shutil.copy2(html_file, target_file)
                        print(Colors.info(f"Copiado archivo de mantenimiento: {html_file.name}"))
            
            return True
        except Exception as e:
            print(Colors.error(f"Error creando directorio de mantenimiento: {e}"))
            return False
    
    def update_config_with_maintenance(self, app_config: AppConfig) -> bool:
        """Actualizar configuración existente para incluir páginas de mantenimiento"""
        try:
            if self.has_maintenance_config(app_config.domain):
                print(Colors.info(f"El dominio {app_config.domain} ya tiene configuración de mantenimiento"))
                return True
            
            print(Colors.info(f"Actualizando configuración de {app_config.domain} con páginas de mantenimiento"))
            
            # Asegurar que el directorio de mantenimiento existe
            self.ensure_maintenance_directory()
            
            # Recrear la configuración con mantenimiento
            return self.create_config(app_config)
            
        except Exception as e:
            print(Colors.error(f"Error actualizando configuración con mantenimiento: {e}"))
            return False
    
    def enable_maintenance_mode(self, app_config: AppConfig) -> bool:
        """Activar modo mantenimiento para una aplicación"""
        try:
            # Asegurar que el directorio de mantenimiento existe
            self.ensure_maintenance_directory()
            
            # Leer la configuración actual para preservar SSL si existe
            config_path = self.nginx_sites / app_config.domain
            has_ssl = False
            ssl_lines = []
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    content = f.read()
                    # Detectar si tiene SSL configurado
                    has_ssl = 'ssl_certificate' in content and 'listen 443' in content
                    
                    if has_ssl:
                        # Extraer las líneas SSL para preservarlas
                        import re
                        # Buscar el bloque del servidor SSL (puerto 443)
                        ssl_block_match = re.search(
                            r'server\s*\{[^}]*listen\s+443\s+ssl[^}]*ssl_certificate[^}]*\}',
                            content,
                            re.DOTALL
                        )
                        if ssl_block_match:
                            ssl_lines = ssl_block_match.group(0)
            
            config_content = self._get_maintenance_config(app_config, has_ssl, ssl_lines)
            temp_config_path = self.nginx_sites / f"{app_config.domain}.maintenance"

            # Escribir configuración temporal
            with open(temp_config_path, "w") as f:
                f.write(config_content)

            # Validar configuración nginx
            test_result = self.cmd.run_sudo("nginx -t 2>&1", check=False)
            if not (test_result and "syntax is ok" in test_result and "test is successful" in test_result):
                print(f"Error en configuración de mantenimiento: {test_result}")
                if temp_config_path.exists():
                    temp_config_path.unlink()
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
                if self.verbose:
                    print(Colors.info(f"Restaurando configuración desde backup: {backup_path}"))
                
                # Verificar que el backup es válido antes de restaurar
                temp_restore = self.nginx_sites / f"{app_config.domain}.restore_temp"
                shutil.copy2(backup_path, temp_restore)
                
                # Temporalmente mover la configuración actual
                if config_path.exists():
                    temp_current = self.nginx_sites / f"{app_config.domain}.current_temp"
                    shutil.move(config_path, temp_current)
                
                # Intentar usar el backup
                shutil.move(temp_restore, config_path)
                
                # Verificar que nginx acepta la configuración
                test_result = self.cmd.run_sudo("nginx -t 2>&1", check=False)
                if test_result and "syntax is ok" in test_result and "test is successful" in test_result:
                    # Configuración válida, eliminar backups temporales
                    if Path(temp_current).exists():
                        Path(temp_current).unlink()
                    backup_path.unlink()  # Eliminar el backup usado
                    
                    if self.verbose:
                        print(Colors.success("Configuración restaurada correctamente"))
                else:
                    # Configuración inválida, restaurar la configuración de mantenimiento
                    if self.verbose:
                        print(Colors.warning("Backup inválido, restaurando configuración de mantenimiento"))
                    config_path.unlink()
                    shutil.move(temp_current, config_path)
                    
                    # Como el backup falló, recrear configuración normal
                    if self.verbose:
                        print(Colors.info("Recreando configuración normal"))
                    return self.create_config(app_config)
            else:
                # No hay backup, recrear configuración normal
                if self.verbose:
                    print(Colors.info(f"No se encontró backup, recreando configuración para {app_config.domain}"))
                return self.create_config(app_config)

            # Recargar nginx
            return self.reload()
        except Exception as e:
            print(Colors.error(f"Error desactivando modo mantenimiento: {e}"))
            if self.verbose:
                import traceback
                print(Colors.error(f"Detalles: {traceback.format_exc()}"))
            return False
    
    def enable_updating_mode(self, app_config: AppConfig) -> bool:
        """Activar modo actualización (similar a mantenimiento pero con página de updating)
        
        Args:
            app_config: Configuración de la aplicación
            
        Returns:
            bool: True si la operación fue exitosa
        """
        try:
            # Asegurar que el directorio de mantenimiento existe
            self.ensure_maintenance_directory()
            
            # Leer la configuración actual para preservar SSL si existe
            config_path = self.nginx_sites / app_config.domain
            has_ssl = False
            ssl_lines = []
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    content = f.read()
                    # Detectar si tiene SSL configurado
                    has_ssl = 'ssl_certificate' in content and 'listen 443' in content
                    
                    if has_ssl:
                        # Extraer las líneas SSL para preservarlas
                        import re
                        # Buscar el bloque del servidor SSL (puerto 443)
                        ssl_block_match = re.search(
                            r'server\s*\{[^}]*listen\s+443\s+ssl[^}]*ssl_certificate[^}]*\}',
                            content,
                            re.DOTALL
                        )
                        if ssl_block_match:
                            ssl_lines = ssl_block_match.group(0)
            
            # Usar la configuración de mantenimiento (sirve la misma página)
            config_content = self._get_updating_config(app_config, has_ssl, ssl_lines)
            temp_config_path = self.nginx_sites / f"{app_config.domain}.updating"

            # Escribir configuración temporal
            with open(temp_config_path, "w") as f:
                f.write(config_content)

            # Validar configuración nginx
            test_result = self.cmd.run_sudo("nginx -t 2>&1", check=False)
            if not (test_result and "syntax is ok" in test_result and "test is successful" in test_result):
                print(f"Error en configuración de actualización: {test_result}")
                if temp_config_path.exists():
                    temp_config_path.unlink()
                return False

            # Backup de configuración original
            backup_path = self.nginx_sites / f"{app_config.domain}.backup"
            if config_path.exists():
                shutil.copy2(config_path, backup_path)

            # Mover configuración de actualización
            shutil.move(temp_config_path, config_path)

            # Recargar nginx
            return self.reload()
        except Exception as e:
            print(f"Error activando modo actualización: {e}")
            return False

    def _get_updating_config(self, app_config: AppConfig, has_ssl: bool = False, ssl_config: str = "") -> str:
        """Configuración para modo actualización (usa updating.html)"""
        from datetime import datetime
        
        # Configuración base HTTP que sirve updating.html
        base_config = f"""# Updating Mode: {app_config.domain}
# Generated by WebApp Manager v3.0
# Date: {datetime.now().isoformat()}

server {{
    listen 80;
    server_name {app_config.domain};

    # Logs
    access_log /var/log/apps/{app_config.domain}-access.log combined;
    error_log /var/log/apps/{app_config.domain}-error.log warn;

    # Root directory for updating page
    root /apps;

    # Serve updating page for all requests
    location / {{
        try_files /maintenance/updating.html =404;
    }}
    
    # Allow access to maintenance directory for assets
    location ^~ /maintenance/ {{
        root /apps;
        expires 30s;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }}

    # Cache updating page briefly
    location ~* \\.(html)$ {{
        expires 15s;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }}
}}"""

        # Si tiene SSL, preservar la configuración SSL
        if has_ssl and ssl_config:
            # Modificar el bloque SSL para servir la página de actualización
            import re
            # Reemplazar las directivas de proxy con las de actualización
            ssl_updating = re.sub(
                r'location\s+/\s*\{[^}]*\}',
                '''location / {
        root /apps;
        try_files /maintenance/updating.html =404;
    }
    
    # Allow access to maintenance directory for assets
    location ^~ /maintenance/ {
        root /apps;
        expires 30s;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }
    
    # Cache updating page briefly
    location ~* \\.(html)$ {
        expires 15s;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }''',
                ssl_config,
                flags=re.DOTALL
            )
            
            return base_config + "\n\n" + ssl_updating
        
        return base_config

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

    # Error pages for maintenance mode
    error_page 502 503 504 /maintenance/error502.html;
    error_page 500 /maintenance/error502.html;
    
    # Maintenance pages location
    location ^~ /maintenance/ {{
        root /apps;
        internal;
        expires 30s;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }}

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

    # Error pages for maintenance mode
    error_page 502 503 504 /maintenance/error502.html;
    error_page 500 /maintenance/error502.html;
    
    # Maintenance pages location
    location ^~ /maintenance/ {{
        root /apps;
        internal;
        expires 30s;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }}

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

    # Error pages for maintenance mode
    error_page 502 503 504 /maintenance/error502.html;
    error_page 500 /maintenance/error502.html;
    
    # Maintenance pages location
    location ^~ /maintenance/ {{
        root /apps;
        internal;
        expires 30s;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }}

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

    # Error pages for maintenance mode (for static sites, mainly for updates)
    error_page 502 503 504 /maintenance/error502.html;
    error_page 500 /maintenance/error502.html;
    
    # Maintenance pages location
    location ^~ /maintenance/ {{
        root /apps;
        internal;
        expires 30s;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }}

    location / {{
        try_files $uri $uri/ =404;
    }}

    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {{
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
}}"""

    def _get_maintenance_config(self, app_config: AppConfig, has_ssl: bool = False, ssl_config: str = "") -> str:
        """Configuración para modo mantenimiento con soporte SSL"""
        # Configuración base HTTP
        base_config = f"""# Maintenance Mode: {app_config.domain}
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

        # Si tiene SSL, preservar la configuración SSL
        if has_ssl and ssl_config:
            # Modificar el bloque SSL para servir la página de mantenimiento
            import re
            # Reemplazar las directivas de proxy con las de mantenimiento
            ssl_maintenance = re.sub(
                r'location\s+/\s*\{[^}]*\}',
                '''location / {
        root /var/www/maintenance;
        index index.html;
        try_files /index.html =404;
    }
    
    # Cache maintenance page briefly
    location ~* \\.(html)$ {
        expires 30s;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }''',
                ssl_config,
                flags=re.DOTALL
            )
            
            return base_config + "\n\n" + ssl_maintenance
        
        return base_config

    def _get_default_config(self, app_config: AppConfig) -> str:
        """Configuración por defecto"""
        return self._get_node_config(app_config)

