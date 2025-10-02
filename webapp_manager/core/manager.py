"""
Clase principal del WebApp Manager
"""

import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from ..config import ConfigManager
from ..models import AppConfig, GlobalConfig, SystemPaths
from ..services import AppService, NginxService, SystemdService, CmdService
from ..utils import Colors, CommandRunner, Validators, ProgressManager

# Configurar logging con manejo de errores
log_dir = Path("/var/log") if os.name == "posix" else Path("./logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "webapp-manager.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class WebAppManager:
    """Gestor principal de aplicaciones web"""
    
    def __init__(self, verbose: bool = False, progress_manager: Optional[ProgressManager] = None):
        # Configurar verbose y progress manager
        self.verbose = verbose
        self.progress = progress_manager
        
        # Inicializar rutas del sistema
        self.paths = SystemPaths()
        self._init_paths()
        
        # Inicializar servicios con modo verbose
        self.config_manager = ConfigManager(self.paths.config_file, self.paths.backup_dir)
        self.app_service = AppService(self.paths.apps_dir, verbose=verbose, progress_manager=progress_manager)
        self.nginx_service = NginxService(
            self.paths.nginx_sites, 
            self.paths.nginx_enabled, 
            self.paths.nginx_conf,
            verbose=verbose
        )
        self.systemd_service = SystemdService(
            self.paths.systemd_dir, 
            self.paths.apps_dir,
            verbose=verbose
        )
        
        # Utilidades
        self.cmd = CmdService(verbose=verbose)
        
        # Inicializar sistema
        self._ensure_directories()
        self._create_maintenance_page()
        self._check_prerequisites()
        
        # Cargar configuración
        self.config = self.config_manager.load_config()
    
    def _init_paths(self):
        """Inicializar rutas como objetos Path"""
        self.paths.apps_dir = Path(self.paths.apps_dir)
        self.paths.nginx_sites = Path(self.paths.nginx_sites)
        self.paths.nginx_enabled = Path(self.paths.nginx_enabled)
        self.paths.systemd_dir = Path(self.paths.systemd_dir)
        self.paths.log_dir = Path(self.paths.log_dir)
        self.paths.config_file = Path(self.paths.config_file)
        self.paths.backup_dir = Path(self.paths.backup_dir)
        self.paths.nginx_conf = Path(self.paths.nginx_conf)
        self.paths.maintenance_dir = Path(self.paths.maintenance_dir)
    
    def _ensure_directories(self):
        """Crear directorios necesarios"""
        dirs = [
            self.paths.apps_dir,
            self.paths.log_dir,
            self.paths.config_file.parent,
            self.paths.backup_dir,
            self.paths.maintenance_dir,
            Path("/var/log/nginx"),
        ]

        for directory in dirs:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                if directory in [self.paths.apps_dir, self.paths.log_dir, self.paths.maintenance_dir]:
                    self.cmd.run_sudo(f"chown -R www-data:www-data {directory}", check=False)
                elif directory == Path("/var/log/nginx"):
                    self.cmd.run_sudo(f"chown -R www-data:adm {directory}", check=False)
            except Exception as e:
                logger.error(f"Error creando directorio {directory}: {e}")
    
    def _create_maintenance_page(self):
        """Crear página de mantenimiento si no existe"""
        maintenance_file = self.paths.maintenance_dir / "index.html"
        if not maintenance_file.exists():
            html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Actualización en Progreso</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            color: #333;
        }
        .container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 500px;
            backdrop-filter: blur(10px);
        }
        .icon {
            font-size: 4rem;
            margin-bottom: 20px;
            color: #667eea;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
            font-size: 2.5rem;
            font-weight: 300;
        }
        p {
            color: #666;
            font-size: 1.1rem;
            line-height: 1.6;
            margin-bottom: 30px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .footer {
            margin-top: 30px;
            font-size: 0.9rem;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">🔄</div>
        <h1>Actualización en Progreso</h1>
        <div class="spinner"></div>
        <p>Estamos actualizando la aplicación para mejorar tu experiencia. Esto tomará solo unos momentos.</p>
        <p>Por favor, regresa en unos minutos.</p>
        <div class="footer">
            WebApp Manager - Mantenimiento Automático
        </div>
    </div>
</body>
</html>"""
            try:
                # Crear el archivo HTML legacy para compatibilidad
                with open(maintenance_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                # Cambiar permisos
                self.cmd.run_sudo(f"chown www-data:www-data {maintenance_file}", check=False)
                self.cmd.run_sudo(f"chmod 644 {maintenance_file}", check=False)
            except Exception as e:
                logger.error(f"Error creando página de mantenimiento: {e}")
        
        # Asegurar que las nuevas páginas de mantenimiento estén disponibles
        try:
            # Crear directorio /apps/maintenance si no existe
            apps_maintenance_dir = Path("/apps/maintenance")
            apps_maintenance_dir.mkdir(parents=True, exist_ok=True)
            
            # Copiar archivos desde el directorio templates del proyecto
            template_dir = Path(__file__).parent.parent.parent / "apps" / "maintenance"
            
            if template_dir.exists():
                for html_file in template_dir.glob("*.html"):
                    target_file = apps_maintenance_dir / html_file.name
                    if not target_file.exists():
                        shutil.copy2(html_file, target_file)
                        self.cmd.run_sudo(f"chown www-data:www-data {target_file}", check=False)
                        self.cmd.run_sudo(f"chmod 644 {target_file}", check=False)
                        if self.verbose:
                            print(Colors.info(f"Copiado archivo de mantenimiento: {html_file.name}"))
                            
        except Exception as e:
            logger.error(f"Error configurando páginas de mantenimiento: {e}")
            if self.verbose:
                print(Colors.error(f"Error configurando páginas de mantenimiento: {e}"))
    
    def _check_prerequisites(self, force_verbose: bool = False):
        """Verificar prerrequisitos del sistema"""
        # Solo verificar prerrequisitos en sistemas Unix para comandos que requieren despliegue
        if os.name != 'posix':
            return
            
        show_output = self.verbose or force_verbose
        if show_output:
            print(Colors.header("Verificando Prerrequisitos del Sistema"))

        required_commands = [
            ("nginx", "nginx -v"),
            ("systemctl", "systemctl --version"),
            ("node", "node --version"),
            ("npm", "npm --version"),
            ("git", "git --version"),
        ]

        missing = []
        for cmd, test_cmd in required_commands:
            if not self.cmd.test_command_exists(cmd):
                missing.append(cmd)
            else:
                if show_output:
                    version = self.cmd.run(test_cmd, check=False)
                    print(Colors.success(f"{cmd}: {version}"))

        if missing:
            if self.progress:
                self.progress.error(f"Comandos faltantes: {', '.join(missing)}")
            else:
                print(Colors.error(f"Comandos faltantes: {', '.join(missing)}"))
            print(Colors.info("Instala los prerrequisitos con:"))
            print(Colors.info("sudo apt update && sudo apt install -y nginx nodejs npm git"))
            sys.exit(1)

        # Configurar nginx (silencioso por defecto)
        self._setup_nginx_configuration(show_output)
    
    def _setup_nginx_configuration(self, show_output: bool = False):
        """Configurar nginx con todas las correcciones necesarias"""
        if self.progress:
            self.progress.info("Configurando nginx...")
        elif show_output:
            print(Colors.info("Configurando nginx..."))

        # Verificar que nginx.conf existe
        if not self.paths.nginx_conf.exists():
            if self.progress:
                self.progress.error("Archivo nginx.conf no encontrado")
            else:
                print(Colors.error("Archivo nginx.conf no encontrado"))
            return False

        # Verificar directorios de log
        nginx_log_dir = Path("/var/log/nginx")
        if not nginx_log_dir.exists():
            if show_output:
                print(Colors.warning("Directorio /var/log/nginx no existe, creándolo..."))
            nginx_log_dir.mkdir(parents=True, exist_ok=True)
            self.cmd.run_sudo("chown -R www-data:adm /var/log/nginx", check=False)

        # Asegurar que la zona webapp_global existe
        self._ensure_webapp_global_zone(show_output)

        # Limpiar configuraciones problemáticas
        self._cleanup_nginx_sites()

        # Verificar configuración
        if self.nginx_service.test_config():
            if show_output:
                print(Colors.success("Configuración de nginx válida"))
            return True
        else:
            if show_output:
                print(Colors.warning("Problemas en configuración nginx, intentando corregir..."))
            self._fix_common_nginx_issues()
            return self.nginx_service.test_config()
    
    def _ensure_webapp_global_zone(self, show_output: bool = False):
        """Asegurar que la zona webapp_global existe en nginx.conf"""
        try:
            # Leer nginx.conf actual
            with open(self.paths.nginx_conf, "r") as f:
                content = f.read()

            # Verificar si ya existe la zona webapp_global
            if "zone=webapp_global" in content:
                if show_output:
                    print(Colors.info("Zona webapp_global ya existe en nginx.conf"))
                return True

            # Agregar la zona
            import re
            http_pattern = r"(http\s*{[^}]*?)((?:\s*#[^\n]*\n)*\s*)(.*?)(})"
            match = re.search(http_pattern, content, re.DOTALL)

            if not match:
                if self.progress:
                    self.progress.error("No se pudo encontrar el bloque http en nginx.conf")
                else:
                    print(Colors.error("No se pudo encontrar el bloque http en nginx.conf"))
                return False

            # Insertar la zona webapp_global
            before_http = content[:match.start()]
            http_start = match.group(1)
            comments = match.group(2)
            http_content = match.group(3)
            http_end = match.group(4)
            after_http = content[match.end():]

            zone_definition = "\n    # Rate limiting zone for webapp-manager\n    limit_req_zone $binary_remote_addr zone=webapp_global:10m rate=50r/s;\n"

            new_content = (
                before_http + http_start + comments + zone_definition + 
                http_content + http_end + after_http
            )

            # Crear backup
            from datetime import datetime
            backup_path = f"{self.paths.nginx_conf}.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            shutil.copy2(self.paths.nginx_conf, backup_path)
            if self.verbose:
                print(Colors.info(f"Backup de nginx.conf creado: {backup_path}"))

            # Escribir nueva configuración
            with open(self.paths.nginx_conf, "w") as f:
                f.write(new_content)

            if self.verbose:
                print(Colors.success("Zona webapp_global agregada a nginx.conf"))
            return True

        except Exception as e:
            if self.progress:
                self.progress.error(f"Error configurando zona webapp_global: {e}")
            else:
                print(Colors.error(f"Error configurando zona webapp_global: {e}"))
            return False
    
    def _cleanup_nginx_sites(self):
        """Limpiar configuraciones problemáticas"""
        if self.paths.nginx_enabled.exists():
            for link in self.paths.nginx_enabled.iterdir():
                if link.is_symlink() and not link.resolve().exists():
                    if self.verbose:
                        print(Colors.info(f"Removiendo enlace huérfano: {link}"))
                    link.unlink()
    
    def _fix_common_nginx_issues(self):
        """Corregir problemas comunes de nginx"""
        if self.verbose:
            print(Colors.info("Intentando corregir problemas comunes..."))

        # Verificar permisos en logs
        self.cmd.run_sudo("chmod -R 755 /var/log/nginx", check=False)
        self.cmd.run_sudo("chown -R www-data:adm /var/log/nginx", check=False)

        # Crear archivos de log básicos si no existen
        basic_logs = ["/var/log/nginx/access.log", "/var/log/nginx/error.log"]
        for log_file in basic_logs:
            if not Path(log_file).exists():
                self.cmd.run_sudo(f"touch {log_file}", check=False)
                self.cmd.run_sudo(f"chown www-data:adm {log_file}", check=False)
    
    def check_prerequisites(self):
        """Verificar prerrequisitos del sistema (versión pública con output)"""
        self._check_prerequisites(force_verbose=True)
    
    def add_app(
        self,
        domain: str,
        source_path: str,
        port: int,
        app_type: str = "nextjs",
        branch: str = "main",
        ssl: bool = True,
        build_command: str = "",
        start_command: str = "",
        env_vars: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Agregar nueva aplicación con progreso real"""
        # Verificar prerrequisitos visiblemente para comandos de despliegue
        self.check_prerequisites()
        
        if self.verbose:
            print(Colors.header(f"Agregando Aplicación: {domain}"))

        # Total de pasos del proceso
        total_steps = 8
        
        # Usar progress manager si está disponible
        if self.progress:
            with self.progress.task(f"Desplegando {domain}", total=total_steps) as task_id:
                return self._add_app_with_progress(
                    task_id, domain, source_path, port, app_type, 
                    branch, ssl, build_command, start_command, env_vars
                )
        else:
            # Modo legacy sin progress manager
            return self._add_app_legacy(
                domain, source_path, port, app_type, 
                branch, ssl, build_command, start_command, env_vars
            )
    
    def _add_app_with_progress(
        self,
        task_id: str,
        domain: str,
        source_path: str,
        port: int,
        app_type: str = "nextjs",
        branch: str = "main",
        ssl: bool = True,
        build_command: str = "",
        start_command: str = "",
        env_vars: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Agregar aplicación con progress manager"""
        try:
            # Paso 1: Validaciones
            self.progress.update(task_id, advance=1, description="Validando parámetros")
            
            if not Validators.validate_domain(domain):
                self.progress.error(f"Dominio inválido: {domain}")
                return False

            if not Validators.validate_port(port):
                self.progress.error(f"Puerto inválido: {port}. Debe estar entre 1024-65535")
                return False

            if self.config_manager.is_port_in_use(port):
                self.progress.error(f"Puerto {port} ya está en uso")
                return False

            if self.config_manager.app_exists(domain):
                self.progress.error(f"Aplicación {domain} ya existe")
                return False

            if not Validators.validate_app_type(app_type):
                self.progress.error(f"Tipo de aplicación inválido: {app_type}")
                return False

            # Crear configuración de aplicación
            app_config = AppConfig.create_new(
                domain=domain,
                port=port,
                app_type=app_type,
                source=source_path,
                branch=branch,
                ssl=ssl,
                build_command=build_command,
                start_command=start_command,
                env_vars=env_vars
            )

            # Paso 2: Desplegar aplicación
            self.progress.update(task_id, advance=1, description="Desplegando aplicación")
            if not self.app_service.deploy_app(app_config):
                return False

            # Paso 3: Configurar nginx
            self.progress.update(task_id, advance=1, description="Configurando nginx")
            self.nginx_service.ensure_maintenance_directory()
            if not self.nginx_service.create_config(app_config):
                self.progress.warning("Problemas con nginx, pero continuando...")

            # Paso 4: Crear servicio systemd
            self.progress.update(task_id, advance=1, description="Creando servicio systemd")
            if not self.systemd_service.create_service(app_config, env_vars):
                return False

            # Paso 5: Iniciar servicio
            self.progress.update(task_id, advance=1, description="Iniciando servicio")
            if not self.systemd_service.start_and_verify(domain, port):
                return False

            # Paso 6: Recargar nginx
            self.progress.update(task_id, advance=1, description="Recargando nginx")
            self.nginx_service.reload()

            # Paso 7: Verificar conectividad
            self.progress.update(task_id, advance=1, description="Verificando conectividad")
            self.app_service.test_connectivity(domain, port)

            # Paso 8: SSL
            if ssl:
                self.progress.update(task_id, advance=1, description="Configurando SSL")
                ssl_success = self.setup_ssl(domain)
                if not ssl_success:
                    self.progress.warning("SSL no configurado, aplicación disponible solo en HTTP")
                    app_config.ssl = False
            else:
                self.progress.update(task_id, advance=1, description="Finalizando")

            # Marcar como activa y guardar configuración
            app_config.set_active()
            self.config_manager.add_app(app_config)

            self.progress.success(f"Aplicación {domain} agregada exitosamente")
            return True

        except Exception as e:
            self.progress.error(f"Error agregando aplicación: {e}")
            self._cleanup_failed_deployment(domain)
            return False
    
    def _add_app_legacy(
        self,
        domain: str,
        source_path: str,
        port: int,
        app_type: str = "nextjs",
        branch: str = "main",
        ssl: bool = True,
        build_command: str = "",
        start_command: str = "",
        env_vars: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Agregar aplicación modo legacy (compatibilidad)"""
        # Validaciones
        if self.verbose:
            print(Colors.info("→ Validando parámetros"))
        
        if not Validators.validate_domain(domain):
            print(Colors.error(f"Dominio inválido: {domain}"))
            return False

        if not Validators.validate_port(port):
            print(Colors.error(f"Puerto inválido: {port}. Debe estar entre 1024-65535"))
            return False

        if self.config_manager.is_port_in_use(port):
            print(Colors.error(f"Puerto {port} ya está en uso"))
            return False

        if self.config_manager.app_exists(domain):
            print(Colors.error(f"Aplicación {domain} ya existe"))
            return False

        if not Validators.validate_app_type(app_type):
            print(Colors.error(f"Tipo de aplicación inválido: {app_type}"))
            return False

        # Mostrar información solo en verbose
        if self.verbose:
            print(Colors.info(f"Dominio: {domain}"))
            print(Colors.info(f"Puerto: {port}"))
            print(Colors.info(f"Tipo: {app_type}"))
            print(Colors.info(f"Fuente: {source_path}"))
            print(Colors.info(f"SSL: {'Sí' if ssl else 'No'}"))

        try:
            # Crear configuración de aplicación
            app_config = AppConfig.create_new(
                domain=domain,
                port=port,
                app_type=app_type,
                source=source_path,
                branch=branch,
                ssl=ssl,
                build_command=build_command,
                start_command=start_command,
                env_vars=env_vars
            )

            # Desplegar aplicación
            if self.verbose:
                print(Colors.info("→ Desplegando aplicación"))
            if not self.app_service.deploy_app(app_config):
                return False

            # Configurar nginx
            if self.verbose:
                print(Colors.info("→ Configurando nginx"))
            # Asegurar que el directorio de mantenimiento existe
            self.nginx_service.ensure_maintenance_directory()
            if not self.nginx_service.create_config(app_config):
                print(Colors.warning("Problemas con nginx, pero continuando..."))

            # Crear servicio systemd
            if self.verbose:
                print(Colors.info("→ Creando servicio systemd"))
            if not self.systemd_service.create_service(app_config, env_vars):
                return False

            # Iniciar servicio
            if self.verbose:
                print(Colors.info("→ Iniciando servicio"))
            if not self.systemd_service.start_and_verify(domain, port):
                return False

            # Recargar nginx
            if self.verbose:
                print(Colors.info("→ Recargando nginx"))
            self.nginx_service.reload()

            # Verificar conectividad
            if self.verbose:
                print(Colors.info("→ Verificando conectividad"))
            self.app_service.test_connectivity(domain, port)

            # Configurar SSL si es necesario
            if ssl:
                if self.verbose:
                    print(Colors.info("→ Configurando SSL"))
                ssl_success = self.setup_ssl(domain)
                if not ssl_success:
                    print(Colors.warning("SSL no configurado, aplicación disponible solo en HTTP"))
                    app_config.ssl = False

            # Marcar como activa y guardar configuración
            app_config.set_active()
            self.config_manager.add_app(app_config)

            # Mostrar resumen
            print(Colors.success(f"\n✓ Aplicación {domain} agregada exitosamente"))
            if self.verbose:
                print(Colors.info(f"  HTTP: http://{domain}"))
                if app_config.ssl:
                    print(Colors.info(f"  HTTPS: https://{domain}"))
                print(Colors.info(f"  Puerto interno: {port}"))
                print(Colors.info(f"  Directorio: {self.paths.apps_dir}/{domain}"))
                print(Colors.info(f"  Servicio: {domain}.service"))

            return True

        except Exception as e:
            print(Colors.error(f"Error agregando aplicación: {e}"))
            self._cleanup_failed_deployment(domain)
            return False
    
    def remove_app(self, domain: str, backup: bool = True) -> bool:
        """Remover aplicación"""
        if self.verbose:
            print(Colors.header(f"Removiendo Aplicación: {domain}"))

        if not self.config_manager.app_exists(domain):
            if self.progress:
                self.progress.error(f"Aplicación {domain} no encontrada")
            else:
                print(Colors.error(f"Aplicación {domain} no encontrada"))
            return False

        try:
            total_steps = 6
            
            if self.progress:
                with self.progress.task(f"Removiendo {domain}", total=total_steps) as task_id:
                    if backup:
                        self.progress.update(task_id, advance=1, description="Creando backup...")
                        self._backup_app(domain)
                    else:
                        self.progress.update(task_id, advance=1, description="Omitiendo backup...")

                    self.progress.update(task_id, advance=1, description="Deteniendo servicio...")
                    self.systemd_service.stop_service(domain)

                    self.progress.update(task_id, advance=1, description="Removiendo servicio systemd...")
                    self.systemd_service.remove_service(domain)

                    self.progress.update(task_id, advance=1, description="Removiendo configuración nginx...")
                    self.nginx_service.remove_config(domain)

                    self.progress.update(task_id, advance=1, description="Removiendo certificado SSL...")
                    self.cmd.run_sudo(f"certbot delete --cert-name {domain}", check=False)

                    self.progress.update(task_id, advance=1, description="Removiendo aplicación...")
                    self.app_service.remove_app(domain)
            else:
                # Modo legacy
                if backup:
                    print(Colors.step(1, 6, "Creando backup"))
                    self._backup_app(domain)

                print(Colors.step(2, 6, "Deteniendo servicio"))
                self.systemd_service.stop_service(domain)

                print(Colors.step(3, 6, "Removiendo servicio systemd"))
                self.systemd_service.remove_service(domain)

                print(Colors.step(4, 6, "Removiendo configuración nginx"))
                self.nginx_service.remove_config(domain)

                print(Colors.step(5, 6, "Removiendo certificado SSL"))
                self.cmd.run_sudo(f"certbot delete --cert-name {domain}", check=False)

                print(Colors.step(6, 6, "Removiendo aplicación"))
                self.app_service.remove_app(domain)

            # Recargar servicios
            self.nginx_service.reload()

            # Remover de configuración
            self.config_manager.remove_app(domain)

            if self.progress:
                self.progress.success(f"Aplicación {domain} removida exitosamente!")
            else:
                print(Colors.success(f"Aplicación {domain} removida exitosamente!"))
            return True

        except Exception as e:
            if self.progress:
                self.progress.error(f"Error removiendo aplicación: {e}")
            else:
                print(Colors.error(f"Error removiendo aplicación: {e}"))
            return False
    
    def restart_app(self, domain: str) -> bool:
        """Reiniciar aplicación"""
        if self.verbose:
            print(Colors.header(f"Reiniciando Aplicación: {domain}"))

        if not self.config_manager.app_exists(domain):
            error_msg = f"Aplicación {domain} no encontrada"
            if self.progress:
                self.progress.error(error_msg)
            else:
                print(Colors.error(error_msg))
            return False

        try:
            app_config = self.config_manager.get_app(domain)

            if self.progress:
                with self.progress.task(f"Reiniciando {domain}", total=2) as task_id:
                    self.progress.update(task_id, advance=1, description="Reiniciando servicio")
                    if not self.systemd_service.restart_service(domain):
                        self.progress.error("Error reiniciando servicio")
                        return False

                    self.progress.update(task_id, advance=1, description="Verificando estado")
                    return self.systemd_service.start_and_verify(domain, app_config.port)
            else:
                if self.verbose:
                    print(Colors.info("→ Reiniciando servicio"))
                if not self.systemd_service.restart_service(domain):
                    print(Colors.error("Error reiniciando servicio"))
                    return False

                if self.verbose:
                    print(Colors.info("→ Verificando estado"))
                return self.systemd_service.start_and_verify(domain, app_config.port)

        except Exception as e:
            error_msg = f"Error reiniciando {domain}: {e}"
            if self.progress:
                self.progress.error(error_msg)
            else:
                print(Colors.error(error_msg))
            return False
    
    def update_app(self, domain: str) -> bool:
        """Actualizar aplicación"""
        # Verificar prerrequisitos
        self.check_prerequisites()
        
        if self.verbose:
            print(Colors.header(f"Actualizando Aplicación: {domain}"))

        if not self.config_manager.app_exists(domain):
            error_msg = f"Aplicación {domain} no encontrada"
            if self.progress:
                self.progress.error(error_msg)
            else:
                print(Colors.error(error_msg))
            return False

        try:
            app_config = self.config_manager.get_app(domain)

            if self.progress:
                with self.progress.task(f"Actualizando {domain}", total=4) as task_id:
                    # Verificar y aplicar configuración de mantenimiento
                    self.progress.update(task_id, advance=0.5, description="Verificando configuración")
                    self.nginx_service.update_config_with_maintenance(app_config)
                    
                    # Activar modo mantenimiento
                    self.progress.update(task_id, advance=0.5, description="Activando mantenimiento")
                    if not self.nginx_service.enable_maintenance_mode(app_config):
                        self.progress.error("Error activando modo mantenimiento")
                        return False

                    # Detener servicio
                    self.progress.update(task_id, advance=1, description="Deteniendo servicio")
                    self.systemd_service.stop_service(domain)

                    # Actualizar aplicación
                    self.progress.update(task_id, advance=1, description="Actualizando código")
                    if not self.app_service.update_app(domain, app_config):
                        self.systemd_service.start_service(domain)
                        self.nginx_service.disable_maintenance_mode(app_config)
                        return False

                    # Reiniciar servicio
                    self.progress.update(task_id, advance=1, description="Reiniciando servicio")
                    success = self.systemd_service.start_and_verify(domain, app_config.port)
                    
                    # Desactivar modo mantenimiento si fue exitoso
                    if success:
                        self.nginx_service.disable_maintenance_mode(app_config)
            else:
                # Modo verbose/legacy
                if self.verbose:
                    print(Colors.info("→ Verificando configuración de mantenimiento"))
                self.nginx_service.update_config_with_maintenance(app_config)
                
                if self.verbose:
                    print(Colors.info("→ Activando modo mantenimiento"))
                if not self.nginx_service.enable_maintenance_mode(app_config):
                    print(Colors.error("Error activando modo mantenimiento"))
                    return False

                if self.verbose:
                    print(Colors.info("→ Deteniendo servicio"))
                self.systemd_service.stop_service(domain)

                if self.verbose:
                    print(Colors.info("→ Actualizando código y reconstruyendo"))
                if not self.app_service.update_app(domain, app_config):
                    self.systemd_service.start_service(domain)
                    self.nginx_service.disable_maintenance_mode(app_config)
                    return False

                if self.verbose:
                    print(Colors.info("→ Reiniciando servicio"))
                success = self.systemd_service.start_and_verify(domain, app_config.port)
                
                if success:
                    self.nginx_service.disable_maintenance_mode(app_config)

            if success:
                app_config.update_timestamp()
                self.config_manager.update_app(domain, app_config)
                
                if self.progress:
                    self.progress.success(f"Aplicación {domain} actualizada exitosamente")
                else:
                    print(Colors.success(f"\n✓ Aplicación {domain} actualizada exitosamente"))
            else:
                error_msg = "Error verificando aplicación después de actualización"
                if self.progress:
                    self.progress.error(error_msg)
                else:
                    print(Colors.error(error_msg))

            return success

        except Exception as e:
            error_msg = f"Error actualizando {domain}: {e}"
            if self.progress:
                self.progress.error(error_msg)
            else:
                print(Colors.error(error_msg))
            return False
    
    def list_apps(self, detailed: bool = False):
        """Listar aplicaciones - versión que devuelve lista para GUI"""
        try:
            apps = self.config_manager.get_all_apps()
            if not apps:
                return []

            # Convertir el diccionario a lista y actualizar el estado
            app_list = []
            for domain, app_config in apps.items():
                try:
                    # Actualizar estado actual
                    app_config.status = self.systemd_service.get_service_status(domain)
                    app_list.append(app_config)
                except Exception as e:
                    logger.error(f"Error al procesar aplicación {domain}: {e}")
                    continue

            return app_list
        except Exception as e:
            logger.error(f"Error al listar aplicaciones: {e}")
            return []
    
    def logs(self, domain: str, lines: int = 50, follow: bool = False) -> bool:
        """Mostrar logs de aplicación"""
        if not self.config_manager.app_exists(domain):
            if self.progress:
                self.progress.error(f"Aplicación {domain} no encontrada")
            else:
                print(Colors.error(f"Aplicación {domain} no encontrada"))
            return False

        if self.verbose:
            print(Colors.header(f"Logs de {domain}"))

        try:
            if self.verbose:
                print(f"\n{Colors.bold(f'📋 Logs del Servicio ({lines} líneas):')}")
                print("-" * 80)

            if follow:
                if self.verbose:
                    print(Colors.info("Siguiendo logs en tiempo real (Ctrl+C para salir)..."))
                self.cmd.run_sudo(f"journalctl -u {domain}.service -f", capture_output=False)
            else:
                self.cmd.run_sudo(f"journalctl -u {domain}.service -n {lines} --no-pager", capture_output=False)

            # Mostrar logs de nginx si existen
            nginx_access = f"/var/log/apps/{domain}-access.log"
            nginx_error = f"/var/log/apps/{domain}-error.log"

            if os.path.exists(nginx_access):
                if self.verbose:
                    print(f"\n{Colors.bold('📊 Nginx Access Log (últimas 20 líneas):')}")
                    print("-" * 80)
                self.cmd.run(f"tail -n 20 {nginx_access}", capture_output=False)

            if os.path.exists(nginx_error) and os.path.getsize(nginx_error) > 0:
                if self.verbose:
                    print(f"\n{Colors.bold('⚠️ Nginx Error Log (últimas 20 líneas):')}")
                    print("-" * 80)
                self.cmd.run(f"tail -n 20 {nginx_error}", capture_output=False)

            return True

        except KeyboardInterrupt:
            if self.verbose:
                print(Colors.info("\nSaliendo de logs..."))
            return True
        except Exception as e:
            if self.progress:
                self.progress.error(f"Error mostrando logs: {e}")
            else:
                print(Colors.error(f"Error mostrando logs: {e}"))
            return False
    
    def setup_ssl(self, domain: str, email: str = None) -> bool:
        """Configurar SSL con certbot"""
        try:
            if not email:
                email = f"admin@{domain}"

            if self.progress:
                self.progress.info(f"Configurando SSL para {domain}...")
            elif self.verbose:
                print(Colors.info(f"Configurando SSL para {domain}..."))

            # Instalar certbot si no existe
            if not self.cmd.test_command_exists("certbot"):
                if self.verbose:
                    print(Colors.info("Instalando certbot..."))
                self.cmd.run_sudo("apt update")
                self.cmd.run_sudo("apt install -y certbot python3-certbot-nginx")

            # Configurar SSL
            cmd = f"certbot --nginx -d {domain} --non-interactive --agree-tos --email {email} --redirect"
            result = self.cmd.run_sudo(cmd, check=False)

            if result and "Congratulations" in result:
                if self.progress:
                    self.progress.success(f"SSL configurado exitosamente para {domain}")
                else:
                    print(Colors.success(f"SSL configurado exitosamente para {domain}"))
                return True
            else:
                if self.progress:
                    self.progress.error(f"Error configurando SSL: {result}")
                else:
                    print(Colors.error(f"Error configurando SSL: {result}"))
                return False

        except Exception as e:
            if self.progress:
                self.progress.error(f"Error configurando SSL: {e}")
            else:
                print(Colors.error(f"Error configurando SSL: {e}"))
            return False
    
    def diagnose(self, domain: str = None):
        """Diagnosticar problemas del sistema o aplicación"""
        if domain:
            self._diagnose_app(domain)
        else:
            self._diagnose_system()
    
    def _diagnose_app(self, domain: str):
        """Diagnosticar aplicación específica"""
        if self.verbose:
            print(Colors.header(f"Diagnóstico de {domain}"))

        if not self.config_manager.app_exists(domain):
            if self.progress:
                self.progress.error(f"Aplicación {domain} no encontrada")
            else:
                print(Colors.error(f"Aplicación {domain} no encontrada"))
            return

        app_config = self.config_manager.get_app(domain)
        issues = []

        # Verificar servicio
        if not self.systemd_service.is_service_active(domain):
            issues.append("❌ Servicio no activo")
        else:
            if self.verbose:
                print(Colors.success("Servicio activo"))

        # Verificar puerto
        port_check = self.cmd.run_sudo(f'netstat -tlnp | grep :{app_config.port}', check=False)
        if not port_check:
            issues.append(f"❌ Puerto {app_config.port} no está escuchando")
        else:
            if self.verbose:
                print(Colors.success(f"Puerto {app_config.port} activo"))

        # Verificar nginx
        nginx_config = self.paths.nginx_sites / domain
        if not nginx_config.exists():
            issues.append(f"❌ Configuración nginx no existe: {nginx_config}")
        else:
            if self.verbose:
                print(Colors.success("Configuración nginx existe"))

        # Verificar conectividad
        if not self.app_service.test_connectivity(domain, app_config.port):
            issues.append(f"❌ Aplicación no responde en puerto {app_config.port}")
        else:
            if self.verbose:
                print(Colors.success("Aplicación responde correctamente"))

        # Mostrar problemas encontrados
        if issues:
            print(f"\n{Colors.bold(Colors.RED + 'Problemas encontrados:' + Colors.END)}")
            for issue in issues:
                print(f"  {issue}")

            print(f"\n{Colors.bold('Sugerencias de solución:')}")
            print(f"  1. Revisar logs: webapp-manager logs --domain {domain}")
            print(f"  2. Reiniciar aplicación: webapp-manager restart --domain {domain}")
            print(f"  3. Verificar configuración nginx: sudo nginx -t")
            print(f"  4. Actualizar aplicación: webapp-manager update --domain {domain}")
        else:
            if self.verbose:
                print(Colors.success("No se encontraron problemas"))
    
    def _diagnose_system(self):
        """Diagnosticar sistema general"""
        if self.verbose:
            print(Colors.header("Diagnóstico General del Sistema"))

        issues = []

        # Verificar nginx
        nginx_status = self.cmd.run_sudo("systemctl is-active nginx", check=False)
        if nginx_status != "active":
            issues.append("❌ Nginx no está activo")
        else:
            if self.verbose:
                print(Colors.success("Nginx activo"))

        # Verificar configuración nginx
        if not self.nginx_service.test_config():
            issues.append("❌ Configuración nginx tiene errores")
        else:
            if self.verbose:
                print(Colors.success("Configuración nginx válida"))

        # Verificar espacio en disco
        disk_usage = self.cmd.run("df / | awk 'NR==2{print $5}' | sed 's/%//'", check=False)
        if disk_usage and int(disk_usage) > 90:
            issues.append(f"❌ Poco espacio en disco: {disk_usage}% usado")
        else:
            if self.verbose:
                print(Colors.success(f"Espacio en disco OK: {disk_usage}% usado"))

        # Verificar aplicaciones
        apps = self.config_manager.get_all_apps()
        for domain in apps:
            if not self.systemd_service.is_service_active(domain):
                issues.append(f"❌ Aplicación {domain} no activa")

        if issues:
            print(f"\n{Colors.bold(Colors.RED + 'Problemas del sistema:' + Colors.END)}")
            for issue in issues:
                print(f"  {issue}")
        else:
            if self.verbose:
                print(Colors.success("Sistema funcionando correctamente"))
    
    def repair_app(self, domain: str) -> bool:
        """Reparar aplicación con problemas"""
        print(Colors.header(f"Reparando Aplicación: {domain}"))
        
        if not self.config_manager.app_exists(domain):
            print(Colors.error(f"Aplicación {domain} no encontrada"))
            return False
        
        app_config = self.config_manager.get_app(domain)
        
        try:
            # Detener servicio
            print(Colors.step(1, 4, "Deteniendo servicio"))
            self.systemd_service.stop_service(domain)
            
            # Reparar según tipo de aplicación
            print(Colors.step(2, 4, "Reparando aplicación"))
            if app_config.app_type == "fastapi":
                success = self._repair_fastapi_app(domain, app_config)
            else:
                success = self._repair_nodejs_app(domain, app_config)
            
            if not success:
                return False
            
            # Recrear servicio
            print(Colors.step(3, 4, "Recreando servicio"))
            self.systemd_service.create_service(app_config)
            
            # Reiniciar servicio
            print(Colors.step(4, 4, "Reiniciando servicio"))
            return self.systemd_service.start_and_verify(domain, app_config.port)
            
        except Exception as e:
            print(Colors.error(f"Error reparando aplicación: {e}"))
            return False
    
    def _repair_fastapi_app(self, domain: str, app_config: AppConfig) -> bool:
        """Reparar aplicación FastAPI"""
        app_dir = self.paths.apps_dir / domain
        
        # Verificar entorno virtual
        venv_path = app_dir / "venv"
        if not venv_path.exists():
            print(Colors.info("Recreando entorno virtual..."))
            if not self.cmd.run(f"cd {app_dir} && python3 -m venv venv", check=False):
                return False
        
        # Reinstalar dependencias
        print(Colors.info("Reinstalando dependencias..."))
        if not self.cmd.run(f"cd {app_dir} && .venv/bin/pip install -r requirements.txt", check=False):
            return False
        
        # Asegurar uvicorn
        print(Colors.info("Verificando uvicorn..."))
        self.cmd.run(f"cd {app_dir} && .venv/bin/pip install uvicorn[standard]", check=False)
        
        # Configurar permisos
        self.cmd.run(f"chmod +x {app_dir}/.venv/bin/*", check=False)
        
        return True
    
    def _repair_nodejs_app(self, domain: str, app_config: AppConfig) -> bool:
        """Reparar aplicación Node.js"""
        app_dir = self.paths.apps_dir / domain
        
        # Limpiar dependencias
        print(Colors.info("Limpiando dependencias..."))
        self.cmd.run(f"cd {app_dir} && rm -rf node_modules package-lock.json", check=False)
        
        # Reinstalar
        print(Colors.info("Reinstalando dependencias..."))
        if not self.cmd.run(f"cd {app_dir} && npm install", check=False):
            return False
        
        # Reconstruir si es Next.js
        if app_config.app_type == "nextjs":
            print(Colors.info("Reconstruyendo aplicación..."))
            if not self.cmd.run(f"cd {app_dir} && npm run build", check=False):
                return False
        
        return True
    
    def show_app_status(self, domain: str) -> bool:
        """Mostrar estado de aplicación específica"""
        if not self.config_manager.app_exists(domain):
            print(Colors.error(f"Aplicación {domain} no encontrada"))
            return False
        
        app_config = self.config_manager.get_app(domain)
        
        print(Colors.header(f"Estado de {domain}"))
        print(f"Tipo: {app_config.app_type}")
        print(f"Puerto: {app_config.port}")
        print(f"Estado del servicio: {self.systemd_service.get_service_status(domain)}")
        print(f"SSL: {'Configurado' if app_config.ssl else 'No configurado'}")
        
        # Verificar conectividad
        connectivity = self.app_service.test_connectivity(domain, app_config.port)
        print(f"Conectividad: {'🟢 Activo' if connectivity else '🔴 No responde'}")
        
        return True
    
    def show_system_status(self) -> bool:
        """Mostrar estado general del sistema"""
        print(Colors.header("Estado del Sistema"))
        
        # Estado de nginx
        nginx_status = self.cmd.run_sudo("systemctl is-active nginx", check=False)
        print(f"Nginx: {'🟢 Activo' if nginx_status == 'active' else '🔴 Inactivo'}")
        
        # Configuración nginx
        nginx_config_ok = self.nginx_service.test_config()
        print(f"Configuración nginx: {'✅ Válida' if nginx_config_ok else '❌ Errores'}")
        
        # Aplicaciones
        apps = self.config_manager.get_all_apps()
        print(f"Aplicaciones instaladas: {len(apps)}")
        
        active_apps = 0
        for domain in apps:
            if self.systemd_service.is_service_active(domain):
                active_apps += 1
        
        print(f"Aplicaciones activas: {active_apps}/{len(apps)}")
        
        return True
    
    def export_config(self, file_path: str) -> bool:
        """Exportar configuración"""
        return self.config_manager.export_config(Path(file_path))
    
    def import_config(self, file_path: str) -> bool:
        """Importar configuración"""
        return self.config_manager.import_config(Path(file_path))
    
    def _backup_app(self, domain: str) -> bool:
        """Crear backup de aplicación"""
        try:
            app_dir = self.paths.apps_dir / domain
            if not app_dir.exists():
                return False
            
            from datetime import datetime
            backup_name = f"{domain}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.tar.gz"
            backup_path = self.paths.backup_dir / backup_name

            print(Colors.info(f"Creando backup: {backup_name}"))
            self.cmd.run_sudo(f"tar -czf {backup_path} -C {app_dir.parent} {app_dir.name}")

            # Limpiar backups antiguos (mantener solo 5)
            backups = sorted(self.paths.backup_dir.glob(f"{domain}-*.tar.gz"))
            if len(backups) > 5:
                for old_backup in backups[:-5]:
                    old_backup.unlink()

            print(Colors.success(f"Backup creado: {backup_path}"))
            return True

        except Exception as e:
            print(Colors.error(f"Error creando backup: {e}"))
            return False
    
    def _cleanup_failed_deployment(self, domain: str):
        """Limpiar recursos de despliegue fallido"""
        try:
            print(Colors.info("Limpiando recursos de despliegue fallido..."))

            # Detener y remover servicio
            self.systemd_service.stop_service(domain)
            self.systemd_service.remove_service(domain)

            # Remover configuración nginx
            self.nginx_service.remove_config(domain)

            # Remover aplicación
            self.app_service.remove_app(domain)

            # Recargar servicios
            self.nginx_service.reload()

            print(Colors.info("Limpieza completada"))

        except Exception as e:
            print(Colors.warning(f"Error en limpieza: {e}"))
