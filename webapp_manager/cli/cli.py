"""
Interfaz de línea de comandos para WebApp Manager con GUI y deployers modulares
"""

import argparse
import os
import sys
from typing import Dict, List, Optional

from ..utils import Colors, Validators
from ..core.manager import WebAppManager
from ..gui import DialogUI, TerminalUI
from ..deployers import DeployerFactory


class CLI:
    """Interfaz de línea de comandos con soporte para GUI"""
    
    def __init__(self):
        self.manager = None
    
    def run(self):
        """Ejecutar interfaz de línea de comandos"""
        # Verificar si se ejecuta en modo GUI
        if "--gui" in sys.argv or "-g" in sys.argv:
            self._run_gui_mode()
            return
        
        parser = self._create_parser()
        args = parser.parse_args()
        
        # Verificar permisos de root (solo en sistemas Unix)
        if os.name == 'posix' and os.geteuid() != 0:
            print(Colors.error("Este script requiere permisos de root en sistemas Unix"))
            print(Colors.info(f"Ejecuta: sudo {' '.join(sys.argv)}"))
            sys.exit(1)
        
        # Inicializar manager
        try:
            self.manager = WebAppManager()
        except Exception as e:
            print(Colors.error(f"Error inicializando WebApp Manager: {e}"))
            sys.exit(1)
        
        # Procesar variables de entorno
        env_vars = self._parse_env_vars(args.env or [])
        
        # Ejecutar comando
        try:
            success = self._execute_command(args, env_vars)
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print(Colors.warning("\nOperación cancelada por el usuario"))
            sys.exit(1)
        except Exception as e:
            print(Colors.error(f"Error inesperado: {e}"))
            sys.exit(1)
    
    def _run_gui_mode(self):
        """Ejecutar en modo GUI con Dialog"""
        try:
            # Verificar permisos de root para GUI (solo en sistemas Unix)
            if os.name == 'posix' and os.geteuid() != 0:
                print(Colors.error("El modo GUI requiere permisos de root en sistemas Unix"))
                print(Colors.info("Ejecuta: sudo python webapp-manager.py --gui"))
                sys.exit(1)
            
            # Verificar que dialog esté disponible
            try:
                import dialog
            except ImportError:
                print(Colors.error("pythondialog no está instalado"))
                print(Colors.info("Instala con: pip3 install pythondialog"))
                print(Colors.info("También necesitas: sudo apt install dialog"))
                sys.exit(1)
            
            # Crear y ejecutar GUI con Dialog
            gui = DialogUI()
            gui.run()
            
        except KeyboardInterrupt:
            print(Colors.info("\nGUI terminada por el usuario"))
        except Exception as e:
            print(Colors.error(f"Error en GUI: {e}"))
            # Fallback a la interfaz Rich si falla Dialog
            print(Colors.info("Intentando con interfaz Rich como fallback..."))
            try:
                from ..services import FileService, AppService
                from pathlib import Path
                
                config = {
                    "apps_dir": "/var/www/apps",
                    "config_file": "/etc/webapp-manager/apps.json",
                    "nginx_sites": "/etc/nginx/sites-available",
                    "systemd_services": "/etc/systemd/system"
                }
                
                file_service = FileService(config["config_file"])
                app_service = AppService(Path(config["apps_dir"]))
                
                gui = TerminalUI(file_service, app_service)
                gui.run()
            except Exception as fallback_error:
                print(Colors.error(f"Error en fallback: {fallback_error}"))
    
    def _handle_types(self, args):
        """Manejar comando types"""
        print(Colors.info("Tipos de deployers disponibles:"))
        
        deployers = DeployerFactory.list_all_deployers()
        
        for deployer in deployers:
            print(f"\n{Colors.BLUE}{deployer['type']}{Colors.ENDC}")
            print(f"  Descripción: {deployer['description']}")
            print(f"  Archivos requeridos: {', '.join(deployer['required_files'])}")
            if deployer['optional_files']:
                print(f"  Archivos opcionales: {', '.join(deployer['optional_files'])}")
            print(f"  Soportado: {'✓' if deployer['supported'] else '✗'}")
    
    def _handle_detect(self, args):
        """Manejar comando detect"""
        directory = args.directory or "."
        
        try:
            detected_type = DeployerFactory.detect_app_type(directory)
            print(Colors.info(f"Tipo detectado para {directory}: {Colors.BLUE}{detected_type}{Colors.ENDC}"))
            
            # Validar que la detección es correcta
            if DeployerFactory.validate_app_type(directory, detected_type):
                print(Colors.success("✓ Validación exitosa"))
            else:
                print(Colors.warning("⚠ Validación fallida - puede requerir ajustes"))
            
            # Mostrar información del deployer
            info = DeployerFactory.get_deployer_info(detected_type)
            print(f"\nInformación del deployer:")
            print(f"  Archivos requeridos: {', '.join(info['required_files'])}")
            if info['optional_files']:
                print(f"  Archivos opcionales: {', '.join(info['optional_files'])}")
            
        except Exception as e:
            print(Colors.error(f"Error detectando tipo: {e}"))
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Crear parser de argumentos"""
        parser = argparse.ArgumentParser(
            description="WebApp Manager v3.0 - Sistema modular de gestión de aplicaciones web",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_examples()
        )
        
        # Comando principal
        parser.add_argument(
            "command",
            choices=[
                "add", "remove", "list", "restart", "update", 
                "logs", "ssl", "diagnose", "repair", "status",
                "export", "import", "types", "detect", "gui", "fix-config"
            ],
            help="Comando a ejecutar"
        )
        
        # Argumentos principales
        parser.add_argument("--domain", "-d", help="Dominio de la aplicación")
        parser.add_argument("--source", "-s", help="Ruta o URL del código fuente")
        parser.add_argument("--port", "-p", type=int, help="Puerto de la aplicación")
        parser.add_argument(
            "--type", "-t",
            choices=DeployerFactory.get_supported_types(),
            default="nextjs",
            help="Tipo de aplicación (default: nextjs)"
        )
        parser.add_argument("--branch", "-b", default="main", help="Rama del repositorio (default: main)")
        
        # Opciones SSL y comandos
        parser.add_argument("--no-ssl", action="store_true", help="No configurar SSL")
        parser.add_argument("--build-command", help="Comando personalizado de construcción")
        parser.add_argument("--start-command", help="Comando personalizado de inicio")
        parser.add_argument("--env", action="append", help="Variables de entorno (KEY=VALUE)")
        
        # Opciones para logs
        parser.add_argument("--lines", "-l", type=int, default=50, help="Número de líneas de log (default: 50)")
        parser.add_argument("--follow", "-f", action="store_true", help="Seguir logs en tiempo real")
        
        # Opciones generales
        parser.add_argument("--detailed", action="store_true", help="Mostrar información detallada")
        parser.add_argument("--no-backup", action="store_true", help="No crear backup al remover")
        parser.add_argument("--email", help="Email para certificados SSL")
        parser.add_argument("--file", help="Archivo para importar/exportar configuración")
        parser.add_argument("--gui", "-g", action="store_true", help="Ejecutar en modo GUI")
        parser.add_argument("--directory", help="Directorio para detectar tipo de aplicación")
        
        return parser
    
    def _get_examples(self) -> str:
        """Obtener ejemplos de uso"""
        return """
Ejemplos de uso:

  # Aplicaciones Next.js
  webapp-manager add --domain app.ejemplo.com --source /ruta/app --port 3000
  webapp-manager add --domain mi-app.com --source https://github.com/usuario/mi-app.git --port 3001
  
  # APIs FastAPI
  webapp-manager add --domain api.ejemplo.com --source /ruta/api --port 8000 --type fastapi
  webapp-manager add --domain mi-api.com --source https://github.com/usuario/mi-api.git --port 8001 --type fastapi
  
  # Aplicaciones Node.js genéricas
  webapp-manager add --domain node-app.com --source https://github.com/usuario/node-app.git --port 4000 --type nodejs
  
  # Sitios estáticos
  webapp-manager add --domain sitio.com --source /ruta/sitio --type static
  
  # Gestión de aplicaciones
  webapp-manager list --detailed
  webapp-manager status --domain mi-app.com
  webapp-manager logs --domain mi-app.com --lines 100
  
  # Herramientas de deployers
  webapp-manager types
  webapp-manager detect --directory /ruta/app
  
  # Interfaz gráfica
  webapp-manager gui
  webapp-manager --gui
  
  # Gestión de aplicaciones
  webapp-manager status --domain app.ejemplo.com
  webapp-manager update --domain app.ejemplo.com
  webapp-manager restart --domain api.ejemplo.com
  webapp-manager logs --domain app.ejemplo.com --follow
  webapp-manager remove --domain old-app.com --no-backup
  
  # Diagnóstico y reparación
  webapp-manager diagnose
  webapp-manager diagnose --domain app.ejemplo.com
  webapp-manager repair --domain api.ejemplo.com
  
  # SSL
  webapp-manager ssl --domain app.ejemplo.com --email admin@ejemplo.com
  
  # Configuración
  webapp-manager export --file backup-config.json
  webapp-manager import --file backup-config.json
  webapp-manager fix-config
  
  # Herramientas
  webapp-manager types
  webapp-manager detect --directory /path/to/app
  webapp-manager gui

Tipos de aplicación soportados:
  - nextjs: Aplicaciones Next.js (por defecto)
  - nodejs: Aplicaciones Node.js genéricas  
  - fastapi: APIs FastAPI con Python
  - static: Sitios web estáticos

Variables de entorno:
  --env NODE_ENV=production --env API_KEY=abc123 --env DATABASE_URL=postgresql://...
        """
    
    def _parse_env_vars(self, env_list: List[str]) -> Dict[str, str]:
        """Parsear variables de entorno"""
        env_vars = {}
        for env_var in env_list:
            is_valid, key, value = Validators.validate_env_var(env_var)
            if is_valid:
                env_vars[key] = value
            else:
                print(Colors.warning(f"Variable de entorno inválida ignorada: {env_var}"))
        return env_vars
    
    def _execute_command(self, args, env_vars: Dict[str, str]) -> bool:
        """Ejecutar comando específico"""
        command = args.command
        
        if command == "add":
            return self._cmd_add(args, env_vars)
        elif command == "remove":
            return self._cmd_remove(args)
        elif command == "list":
            return self._cmd_list(args)
        elif command == "restart":
            return self._cmd_restart(args)
        elif command == "update":
            return self._cmd_update(args)
        elif command == "logs":
            return self._cmd_logs(args)
        elif command == "ssl":
            return self._cmd_ssl(args)
        elif command == "diagnose":
            return self._cmd_diagnose(args)
        elif command == "repair":
            return self._cmd_repair(args)
        elif command == "status":
            return self._cmd_status(args)
        elif command == "export":
            return self._cmd_export(args)
        elif command == "import":
            return self._cmd_import(args)
        elif command == "types":
            self._handle_types(args)
            return True
        elif command == "detect":
            self._handle_detect(args)
            return True
        elif command == "gui":
            self._run_gui_mode()
            return True
        elif command == "fix-config":
            return self._cmd_fix_config(args)
        else:
            print(Colors.error(f"Comando no implementado: {command}"))
            return False
    
    def _cmd_add(self, args, env_vars: Dict[str, str]) -> bool:
        """Comando add"""
        if not args.domain or not args.source or not args.port:
            print(Colors.error("Para agregar una app necesitas: --domain, --source y --port"))
            return False
        
        return self.manager.add_app(
            domain=args.domain,
            source_path=args.source,
            port=args.port,
            app_type=args.type,
            branch=args.branch,
            ssl=not args.no_ssl,
            build_command=args.build_command or "",
            start_command=args.start_command or "",
            env_vars=env_vars,
        )
    
    def _cmd_remove(self, args) -> bool:
        """Comando remove"""
        if not args.domain:
            print(Colors.error("Necesitas especificar --domain"))
            return False
        
        return self.manager.remove_app(args.domain, backup=not args.no_backup)
    
    def _cmd_list(self, args) -> bool:
        """Comando list"""
        self.manager.list_apps_console(detailed=args.detailed)
        return True
    
    def _cmd_restart(self, args) -> bool:
        """Comando restart"""
        if not args.domain:
            print(Colors.error("Necesitas especificar --domain"))
            return False
        
        return self.manager.restart_app(args.domain)
    
    def _cmd_update(self, args) -> bool:
        """Comando update"""
        if not args.domain:
            print(Colors.error("Necesitas especificar --domain"))
            return False
        
        return self.manager.update_app(args.domain)
    
    def _cmd_logs(self, args) -> bool:
        """Comando logs"""
        if not args.domain:
            print(Colors.error("Necesitas especificar --domain"))
            return False
        
        return self.manager.logs(args.domain, args.lines, args.follow)
    
    def _cmd_ssl(self, args) -> bool:
        """Comando ssl"""
        if not args.domain:
            print(Colors.error("Necesitas especificar --domain"))
            return False
        
        return self.manager.setup_ssl(args.domain, args.email)
    
    def _cmd_diagnose(self, args) -> bool:
        """Comando diagnose"""
        self.manager.diagnose(args.domain)
        return True
    
    def _cmd_repair(self, args) -> bool:
        """Comando repair"""
        if not args.domain:
            print(Colors.error("Necesitas especificar --domain"))
            return False
        
        return self.manager.repair_app(args.domain)
    
    def _cmd_status(self, args) -> bool:
        """Comando status"""
        if args.domain:
            return self.manager.show_app_status(args.domain)
        else:
            return self.manager.show_system_status()
    
    def _cmd_export(self, args) -> bool:
        """Comando export"""
        if not args.file:
            print(Colors.error("Necesitas especificar --file para exportar"))
            return False
        
        return self.manager.export_config(args.file)
    
    def _cmd_import(self, args) -> bool:
        """Comando import"""
        if not args.file:
            print(Colors.error("Necesitas especificar --file para importar"))
            return False
        
        return self.manager.import_config(args.file)
    
    def _cmd_fix_config(self, args) -> bool:
        """Comando fix-config para reparar configuraciones corruptas"""
        print(Colors.header("🔧 Reparando archivo de configuración"))
        
        try:
            # Usar el archivo de configuración del manager
            config_path = self.manager.config_manager.config_file
            
            print(f"📁 Archivo de configuración: {config_path}")
            
            if not config_path.exists():
                print(Colors.info("ℹ️  Archivo de configuración no existe, creando nuevo..."))
                self.manager.config_manager.load_config()  # Esto creará el archivo
                print(Colors.success("✅ Archivo de configuración creado"))
                return True
            
            # Crear backup
            import shutil
            from datetime import datetime
            backup_path = config_path.with_suffix(f".backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            print(f"📦 Creando backup: {backup_path}")
            shutil.copy2(config_path, backup_path)
            
            # Intentar cargar y reparar
            print("🔍 Analizando archivo de configuración...")
            
            try:
                apps = self.manager.config_manager.get_all_apps()
                print(f"✅ Configuración válida: {len(apps)} aplicaciones encontradas")
                
                for domain, app_config in apps.items():
                    print(f"   - {domain}: {app_config.app_type}")
                    
            except Exception as e:
                print(f"❌ Error en configuración: {e}")
                
                # Intentar reparar
                print("🔧 Intentando reparar...")
                
                try:
                    import json
                    
                    # Leer archivo raw
                    with open(config_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parsear JSON
                    config_data = json.loads(content)
                    
                    # Reparar estructura
                    if "apps" not in config_data:
                        config_data["apps"] = {}
                    
                    # Validar aplicaciones
                    valid_apps = {}
                    for domain, app_data in config_data.get("apps", {}).items():
                        if isinstance(app_data, dict) and app_data:
                            required_fields = ['domain', 'port', 'app_type', 'source', 'branch', 'ssl', 'created']
                            missing_fields = [field for field in required_fields if field not in app_data]
                            
                            if missing_fields:
                                print(f"⚠️  Aplicación {domain} con campos faltantes: {missing_fields}")
                                print(f"   Eliminando aplicación corrupta...")
                            else:
                                valid_apps[domain] = app_data
                                print(f"✅ Aplicación {domain} válida")
                    
                    # Actualizar configuración
                    config_data["apps"] = valid_apps
                    config_data["version"] = "4.0"
                    config_data["last_modified"] = datetime.now().isoformat()
                    
                    # Escribir archivo reparado
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ Archivo reparado: {len(valid_apps)} aplicaciones válidas")
                    return True
                    
                except json.JSONDecodeError:
                    print("❌ JSON completamente corrupto, creando archivo nuevo...")
                    
                    # Crear archivo nuevo
                    new_config = {
                        "version": "4.0",
                        "apps": {},
                        "created_at": datetime.now().isoformat(),
                        "last_modified": datetime.now().isoformat()
                    }
                    
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(new_config, f, indent=2, ensure_ascii=False)
                    
                    print("✅ Archivo de configuración nuevo creado")
                    return True
            
            return True
            
        except Exception as e:
            print(Colors.error(f"❌ Error al reparar configuración: {e}"))
            return False
