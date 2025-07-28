"""
Servicio para gestión de servicios systemd
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from ..utils import CommandRunner, Colors
from ..models import AppConfig


class SystemdService:
    """Servicio para gestión de systemd"""
    
    def __init__(self, systemd_dir: Path, apps_dir: Path):
        self.systemd_dir = systemd_dir
        self.apps_dir = apps_dir
        self.cmd = CommandRunner()
    
    def create_service(self, app_config: AppConfig, env_vars: Optional[Dict[str, str]] = None) -> bool:
        """Crear servicio systemd para aplicación"""
        try:
            app_dir = self.apps_dir / app_config.domain
            env_vars = env_vars or {}

            # Obtener comandos por defecto si no se especificaron
            build_command = app_config.build_command or self._get_default_build_command(app_config.app_type)
            start_command = app_config.start_command or self._get_default_start_command(app_config.app_type, app_config.port)

            # Configurar archivo de entorno
            env_file_success = self._setup_environment_file(app_config, app_dir, env_vars)
            if not env_file_success:
                return False

            # Configurar permisos específicos
            self._setup_permissions(app_config, app_dir)

            # Crear contenido del servicio
            service_content = self._get_service_content(app_config, app_dir, start_command)

            # Escribir archivo de servicio
            service_path = self.systemd_dir / f"{app_config.domain}.service"
            with open(service_path, "w") as f:
                f.write(service_content)

            self.cmd.run_sudo(f"chmod 644 {service_path}")
            self.cmd.run_sudo("systemctl daemon-reload")

            # Validar que el servicio se creó correctamente
            validation = self.cmd.run_sudo(f"systemctl status {app_config.domain}.service", check=False)
            if validation and "could not be found" in validation:
                print(Colors.error("Error en creación del servicio"))
                return False

            print(Colors.success(f"Servicio systemd creado para {app_config.domain}"))
            return True

        except Exception as e:
            print(Colors.error(f"Error creando servicio systemd: {e}"))
            return False

    def remove_service(self, domain: str) -> bool:
        """Remover servicio systemd"""
        try:
            # Detener y deshabilitar servicio
            self.cmd.run_sudo(f"systemctl stop {domain}.service", check=False)
            self.cmd.run_sudo(f"systemctl disable {domain}.service", check=False)

            # Remover archivo de servicio
            service_file = self.systemd_dir / f"{domain}.service"
            if service_file.exists():
                service_file.unlink()

            self.cmd.run_sudo("systemctl daemon-reload")
            return True

        except Exception as e:
            print(Colors.error(f"Error removiendo servicio: {e}"))
            return False

    def start_service(self, domain: str) -> bool:
        """Iniciar servicio"""
        try:
            self.cmd.run_sudo(f"systemctl enable {domain}.service")
            result = self.cmd.run_sudo(f"systemctl start {domain}.service", check=False)
            return result is not None
        except Exception:
            return False

    def stop_service(self, domain: str) -> bool:
        """Detener servicio"""
        try:
            result = self.cmd.run_sudo(f"systemctl stop {domain}.service", check=False)
            return result is not None
        except Exception:
            return False

    def restart_service(self, domain: str) -> bool:
        """Reiniciar servicio"""
        try:
            result = self.cmd.run_sudo(f"systemctl restart {domain}.service", check=False)
            return result is not None
        except Exception:
            return False

    def get_service_status(self, domain: str) -> str:
        """Obtener estado del servicio"""
        try:
            status = self.cmd.run_sudo(f"systemctl is-active {domain}.service", check=False)
            
            if status == "active":
                return f"{Colors.GREEN}🟢 Activo{Colors.END}"
            elif status == "inactive":
                return f"{Colors.RED}🔴 Inactivo{Colors.END}"
            elif status == "failed":
                return f"{Colors.RED}❌ Fallido{Colors.END}"
            elif status:
                return f"{Colors.YELLOW}🟡 {status.title()}{Colors.END}"
            else:
                return f"{Colors.YELLOW}🟡 Desconocido{Colors.END}"

        except Exception:
            return f"{Colors.YELLOW}🟡 Desconocido{Colors.END}"

    def is_service_active(self, domain: str) -> bool:
        """Verificar si el servicio está activo"""
        try:
            status = self.cmd.run_sudo(f"systemctl is-active {domain}.service", check=False)
            return status == "active"
        except Exception:
            return False

    def get_service_logs(self, domain: str, lines: int = 50) -> Optional[str]:
        """Obtener logs del servicio"""
        try:
            return self.cmd.run_sudo(f"journalctl -u {domain}.service -n {lines} --no-pager", check=False)
        except Exception:
            return None

    def start_and_verify(self, domain: str, port: int, timeout: int = 30) -> bool:
        """Iniciar servicio y verificar que funciona"""
        try:
            # Iniciar servicio
            if not self.start_service(domain):
                print(Colors.error("Error iniciando servicio"))
                return False

            # Esperar a que el servicio inicie
            time.sleep(5)

            # Verificar estado
            if not self.is_service_active(domain):
                print(Colors.error("Servicio no está activo"))
                # Mostrar logs para diagnóstico
                logs = self.get_service_logs(domain, 10)
                if logs:
                    print(Colors.error("Últimos logs del servicio:"))
                    print(logs[-500:])  # Últimos 500 caracteres
                return False

            # Verificar logs recientes en busca de errores
            recent_logs = self.cmd.run_sudo(
                f'journalctl -u {domain}.service --since="1 minute ago" --no-pager',
                check=False,
            )

            if recent_logs:
                success_indicators = ["Ready in", "server started", "listening on", "Started", "✓"]
                error_indicators = ["Error:", "ERROR", "Failed", "Exception", "Cannot"]

                has_success = any(indicator in recent_logs for indicator in success_indicators)
                has_errors = any(indicator in recent_logs for indicator in error_indicators)

                if has_success and not has_errors:
                    print(Colors.success("Servicio funcionando correctamente"))
                    return True
                elif has_errors:
                    print(Colors.error("Servicio con errores:"))
                    print(recent_logs[-500:])
                    return False

            print(Colors.success("Servicio iniciado correctamente"))
            return True

        except Exception as e:
            print(Colors.error(f"Error verificando servicio: {e}"))
            return False

    def _setup_environment_file(self, app_config: AppConfig, app_dir: Path, env_vars: Dict[str, str]) -> bool:
        """Configurar archivo de entorno"""
        try:
            # Determinar archivo de entorno según tipo de app
            if app_config.app_type == "fastapi":
                env_file = app_dir / ".env"
                env_file_name = ".env"
                default_env = {
                    "PYTHONPATH": str(app_dir),
                    "PORT": str(app_config.port),
                    "HOST": "0.0.0.0",
                    "ENVIRONMENT": "production",
                }
            else:
                env_file = app_dir / ".env.production"
                env_file_name = ".env.production"
                default_env = {
                    "NODE_ENV": "production",
                    "PORT": str(app_config.port),
                    "HOSTNAME": "localhost",
                }

            # Si el archivo .env ya existe para FastAPI, respetarlo completamente
            if app_config.app_type == "fastapi" and env_file.exists():
                print(Colors.info(f"Archivo {env_file_name} encontrado en el repositorio"))
                
                # Solo actualizar el PORT si es necesario
                try:
                    with open(env_file, "r") as f:
                        content = f.read()
                    
                    # Verificar si ya tiene PORT configurado
                    if "PORT=" in content:
                        print(Colors.info("Puerto ya configurado en .env, respetando configuración existente"))
                    else:
                        # Agregar PORT al final del archivo
                        with open(env_file, "a") as f:
                            f.write(f"\n# Port added by WebApp Manager\nPORT={app_config.port}\n")
                        print(Colors.success(f"Puerto {app_config.port} agregado al .env existente"))
                    
                    return True
                    
                except Exception as e:
                    print(Colors.warning(f"Error procesando {env_file_name} existente: {e}"))
                    # Continuar con el proceso normal si hay error
            
            # Para Node.js o si no existe .env en FastAPI, crear/actualizar archivo
            # Leer variables existentes si el archivo ya existe
            existing_env = {}
            if env_file.exists():
                print(Colors.info(f"Archivo {env_file_name} encontrado, preservando variables existentes..."))
                try:
                    with open(env_file, "r") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                key, value = line.split("=", 1)
                                existing_env[key.strip()] = value.strip()
                    print(Colors.success(f"Se preservaron {len(existing_env)} variables del archivo {env_file_name} original"))
                except Exception as e:
                    print(Colors.warning(f"Error leyendo {env_file_name} existente: {e}"))

            # Construir diccionario final de variables
            final_env = {}
            final_env.update(default_env)  # Variables por defecto
            final_env.update(env_vars)     # Variables pasadas como parámetro
            final_env.update(existing_env) # Variables existentes (máxima prioridad)
            final_env["PORT"] = str(app_config.port)  # Asegurar puerto correcto

            # Escribir archivo de entorno
            with open(env_file, "w") as f:
                f.write("# Environment variables processed by WebApp Manager\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n\n")

                # Variables del sistema primero
                if app_config.app_type == "fastapi":
                    system_vars = ["PYTHONPATH", "PORT", "HOST", "ENVIRONMENT"]
                else:
                    system_vars = ["NODE_ENV", "PORT", "HOSTNAME"]

                for key in system_vars:
                    if key in final_env:
                        f.write(f"{key}={final_env[key]}\n")

                # Variables personalizadas
                if any(key not in system_vars for key in final_env):
                    f.write("\n# Application specific variables\n")
                    for key, value in final_env.items():
                        if key not in system_vars:
                            f.write(f"{key}={value}\n")

            print(Colors.success(f"Archivo {env_file_name} configurado con {len(final_env)} variables"))

            # Configurar permisos
            self.cmd.run_sudo(f"chown www-data:www-data {env_file}")
            self.cmd.run_sudo(f"chmod 600 {env_file}")

            return True

        except Exception as e:
            print(Colors.error(f"Error configurando archivo de entorno: {e}"))
            return False

    def _setup_permissions(self, app_config: AppConfig, app_dir: Path):
        """Configurar permisos específicos según tipo de aplicación"""
        if app_config.app_type in ["nextjs", "node"]:
            self.cmd.run_sudo(f"chmod +x {app_dir}/node_modules/.bin/*", check=False)
        elif app_config.app_type == "fastapi":
            self.cmd.run_sudo(f"chmod +x {app_dir}/venv/bin/*", check=False)

    def _get_default_build_command(self, app_type: str) -> str:
        """Obtener comando de construcción por defecto"""
        commands = {
            "nextjs": "npm run build",
            "node": "npm install",
            "fastapi": "./venv/bin/pip install -r requirements.txt",
            "static": ""
        }
        return commands.get(app_type, "")

    def _get_default_start_command(self, app_type: str, port: int) -> str:
        """Obtener comando de inicio por defecto"""
        commands = {
            "nextjs": f"./node_modules/.bin/next start --port {port}",
            "node": "node server.js",
            "fastapi": f".venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port {port} --workers 1",
            "static": ""
        }
        return commands.get(app_type, "")

    def _get_service_content(self, app_config: AppConfig, app_dir: Path, start_command: str) -> str:
        """Obtener contenido del archivo de servicio"""
        if app_config.app_type == "fastapi":
            env_file = app_dir / ".env"
            return self._get_fastapi_service_content(app_config, app_dir, env_file, start_command)
        else:
            env_file = app_dir / ".env.production"
            return self._get_nodejs_service_content(app_config, app_dir, env_file, start_command)

    def _get_fastapi_service_content(self, app_config: AppConfig, app_dir: Path, env_file: Path, start_command: str) -> str:
        """Contenido de servicio para FastAPI"""
        return f"""# FastAPI Service: {app_config.domain}
# Generated by WebApp Manager v3.0
# Date: {datetime.now().isoformat()}

[Unit]
Description={app_config.domain} FastAPI Application
After=network.target mysql.service postgresql.service
Wants=network.target
Documentation=https://github.com/webapp-manager

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory={app_dir}

EnvironmentFile={env_file}
Environment=PYTHONPATH={app_dir}
Environment=PORT={app_config.port}
Environment=HOST=0.0.0.0
Environment=ENVIRONMENT=production
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:{app_dir}/.venv/bin

ExecStartPre=/bin/sleep 5
ExecStart=/bin/bash -c 'cd {app_dir} && source .venv/bin/activate && {start_command}'
ExecReload=/bin/kill -USR1 $MAINPID
ExecStop=/bin/kill -TERM $MAINPID
KillMode=mixed
KillSignal=SIGTERM
TimeoutStartSec=60
TimeoutStopSec=30

Restart=always
RestartSec=10
StartLimitInterval=120
StartLimitBurst=3

StandardOutput=journal
StandardError=journal
SyslogIdentifier={app_config.domain}

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={app_dir}
ReadWritePaths=/var/log/apps
ReadWritePaths=/tmp

LimitNOFILE=65536
LimitNPROC=32768

OOMScoreAdjust=500

[Install]
WantedBy=multi-user.target"""

    def _get_nodejs_service_content(self, app_config: AppConfig, app_dir: Path, env_file: Path, start_command: str) -> str:
        """Contenido de servicio para Node.js/Next.js"""
        return f"""# WebApp Service: {app_config.domain}
# Generated by WebApp Manager v3.0
# Date: {datetime.now().isoformat()}

[Unit]
Description={app_config.domain} Application ({app_config.app_type})
After=network.target mysql.service postgresql.service
Wants=network.target
Documentation=https://github.com/webapp-manager

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory={app_dir}

EnvironmentFile={env_file}
Environment=NODE_ENV=production
Environment=PORT={app_config.port}
Environment=HOSTNAME=localhost
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:{app_dir}/node_modules/.bin

ExecStartPre=/bin/sleep 5
ExecStart=/bin/bash -c 'cd {app_dir} && {start_command}'
ExecReload=/bin/kill -USR1 $MAINPID
ExecStop=/bin/kill -TERM $MAINPID
KillMode=mixed
KillSignal=SIGTERM
TimeoutStartSec=60
TimeoutStopSec=30

Restart=always
RestartSec=10
StartLimitInterval=120
StartLimitBurst=3

StandardOutput=journal
StandardError=journal
SyslogIdentifier={app_config.domain}

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={app_dir}
ReadWritePaths=/var/log/apps
ReadWritePaths=/tmp

LimitNOFILE=65536
LimitNPROC=32768

OOMScoreAdjust=500

[Install]
WantedBy=multi-user.target"""
