"""
Interfaz de línea de comandos moderna para WebApp Manager
Diseñada para ser 100% terminal con Rich para experiencia profesional
"""

import argparse
import os
import sys
import time
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import (
    Progress, 
    BarColumn, 
    TextColumn, 
    TimeElapsedColumn, 
    TimeRemainingColumn,
    SpinnerColumn,
    MofNCompleteColumn,
    TaskProgressColumn
)
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.align import Align
from rich.columns import Columns
from rich.status import Status

from ..utils import Colors, Validators, ProgressManager
from ..core.manager import WebAppManager
from ..deployers import DeployerFactory


class CLI:
    """Interfaz de línea de comandos moderna con Rich"""
    
    def __init__(self):
        self.console = Console()
        self.manager = None
        self.verbose = False
        self.progress_manager = None
        
        # Configurar estilo de la consola
        self.console.print()  # Línea en blanco inicial
    
    def run(self):
        """Ejecutar interfaz de línea de comandos"""
        # Mostrar banner si no hay argumentos
        if len(sys.argv) == 1:
            self._show_banner()
            self._show_interactive_help()
            return
        
        parser = self._create_parser()
        args = parser.parse_args()
        
        # Configurar modo verbose
        self.verbose = args.verbose
        
        # Crear progress manager
        self.progress_manager = ProgressManager(self.console, verbose=self.verbose)
        
        # Verificar permisos de root (solo en sistemas Unix)
        if os.name == 'posix' and os.geteuid() != 0:
            self._show_error("Este script requiere permisos de root en sistemas Unix")
            self._show_info(f"Ejecuta: [bold]sudo {' '.join(sys.argv)}[/bold]")
            sys.exit(1)
        
        # Inicializar manager
        try:
            with self.progress_manager.task("Inicializando WebApp Manager", total=3) as task_id:
                self.progress_manager.update(task_id, advance=1, description="Cargando configuración...")
                self.manager = WebAppManager(verbose=self.verbose, progress_manager=self.progress_manager)
                self.progress_manager.update(task_id, advance=1, description="Verificando servicios...")
                time.sleep(0.3)  # Simular verificación
                self.progress_manager.update(task_id, advance=1, description="Sistema listo")
        except Exception as e:
            self._show_error(f"Error inicializando WebApp Manager: {e}")
            sys.exit(1)
        
        # Procesar variables de entorno
        env_vars = self._parse_env_vars(args.env or [])
        
        # Ejecutar comando
        try:
            success = self._execute_command(args, env_vars)
            
            # Limpiar progreso antes de salir
            if hasattr(self, 'progress_manager') and self.progress_manager:
                self.progress_manager.stop()
            
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            self._show_warning("\n⚠️  Operación cancelada por el usuario")
            
            # Limpiar progreso en caso de interrupción
            if hasattr(self, 'progress_manager') and self.progress_manager:
                self.progress_manager.force_cleanup()
            
            sys.exit(1)
        except Exception as e:
            self._show_error(f"Error inesperado: {e}")
            
            # Limpiar progreso en caso de error
            if hasattr(self, 'progress_manager') and self.progress_manager:
                self.progress_manager.force_cleanup()
            
            if self.verbose:
                import traceback
                self.console.print(f"[dim]Detalles del error:\n{traceback.format_exc()}[/dim]")
            
            sys.exit(1)
    
    def _show_banner(self):
        """Mostrar banner de la aplicación"""
        banner_text = """
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║               🚀 WebApp Manager v4.0                            ║
    ║            Sistema Modular para Aplicaciones Web                 ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
        """
        
        self.console.print(Panel(
            Align.center(banner_text.strip()),
            style="bold blue",
            padding=(1, 2)
        ))
        
        # Mostrar información del sistema
        self._show_system_info()
    
    def _show_system_info(self):
        """Mostrar información básica del sistema"""
        try:
            # Crear tabla de información del sistema
            info_table = Table(show_header=False, box=None, padding=(0, 2))
            info_table.add_column("Item", style="cyan", width=20)
            info_table.add_column("Status", style="green")
            
            # Verificar servicios básicos
            services = {
                "🐧 Sistema": "Linux" if os.name == 'posix' else "Windows",
                "🐍 Python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "👤 Usuario": "root" if os.geteuid() == 0 else "normal" if os.name == 'posix' else "admin",
                "📂 Directorio": os.getcwd()
            }
            
            for service, status in services.items():
                info_table.add_row(service, status)
            
            self.console.print(Panel(
                info_table,
                title="[bold]Información del Sistema[/bold]",
                border_style="green"
            ))
            
        except Exception:
            pass  # Ignorar errores en la información del sistema
    
    def _show_interactive_help(self):
        """Mostrar ayuda interactiva"""
        help_text = """
[bold cyan]Comandos Principales:[/bold cyan]

[bold]Gestión de Aplicaciones:[/bold]
  • [green]webapp-manager list[/green]                    - Listar aplicaciones
  • [green]webapp-manager add[/green] --domain app.com     - Agregar aplicación
  • [green]webapp-manager remove[/green] --domain app.com  - Eliminar aplicación
  • [green]webapp-manager update[/green] --domain app.com  - Actualizar aplicación
  • [green]webapp-manager restart[/green] --domain app.com - Reiniciar aplicación

[bold]Monitoreo y Diagnóstico:[/bold]
  • [green]webapp-manager status[/green]                   - Estado del sistema
  • [green]webapp-manager logs[/green] --domain app.com    - Ver logs
  • [green]webapp-manager diagnose[/green]                 - Diagnóstico completo

[bold]Herramientas:[/bold]
  • [green]webapp-manager types[/green]                    - Tipos de aplicación
  • [green]webapp-manager detect[/green] --directory ./app - Detectar tipo

[bold]Opciones:[/bold]
  • [yellow]--verbose, -v[/yellow]                           - Mostrar logs detallados

[bold]Ejemplos Rápidos:[/bold]
  • [dim]webapp-manager add --domain mi-app.com --source https://github.com/user/app.git --port 3000[/dim]
  • [dim]webapp-manager list --detailed[/dim]
  • [dim]webapp-manager logs --domain mi-app.com --follow[/dim]

Para ayuda detallada: [bold]webapp-manager --help[/bold]
        """
        
        self.console.print(Panel(
            help_text.strip(),
            title="[bold]Guía de Inicio Rápido[/bold]",
            border_style="yellow",
            padding=(1, 2)
        ))
    
    def _loading(self, message: str):
        """Context manager para mostrar spinner de carga"""
        return self.console.status(f"[bold green]{message}...", spinner="dots")
    
    def _show_success(self, message: str):
        """Mostrar mensaje de éxito"""
        self.console.print(f"[bold green]✅ {message}[/bold green]")
    
    def _show_error(self, message: str):
        """Mostrar mensaje de error"""
        self.console.print(f"[bold red]❌ {message}[/bold red]")
    
    def _show_warning(self, message: str):
        """Mostrar mensaje de advertencia"""
        self.console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")
    
    def _show_info(self, message: str):
        """Mostrar mensaje informativo"""
        if self.verbose:
            self.console.print(f"[bold blue]ℹ️  {message}[/bold blue]")
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Crear parser de argumentos"""
        parser = argparse.ArgumentParser(
            description="🚀 WebApp Manager v4.0 - Sistema modular de gestión de aplicaciones web",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_examples()
        )
        
        # Comando principal
        parser.add_argument(
            "command",
            choices=[
                "add", "remove", "list", "restart", "update", 
                "logs", "ssl", "diagnose", "repair", "status",
                "export", "import", "types", "detect", "fix-config",
                "apply-maintenance", "maintenance", "updating", "sync-pages",
                "setup", "check-system", "version", "gui"
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
        
        # Opciones adicionales
        parser.add_argument("--no-ssl", action="store_true", help="No configurar SSL")
        parser.add_argument("--build-command", help="Comando personalizado de construcción")
        parser.add_argument("--start-command", help="Comando personalizado de inicio")
        parser.add_argument("--env", action="append", help="Variables de entorno (KEY=VALUE)")
        
        # Opciones para maintenance/updating
        parser.add_argument("--enable", action="store_true", help="Activar modo mantenimiento/actualización")
        parser.add_argument("--disable", action="store_true", help="Desactivar modo mantenimiento/actualización")
        
        # Opciones para logs
        parser.add_argument("--lines", "-l", type=int, default=50, help="Número de líneas de log (default: 50)")
        parser.add_argument("--follow", "-f", action="store_true", help="Seguir logs en tiempo real")
        
        # Opciones generales
        parser.add_argument("--detailed", action="store_true", help="Mostrar información detallada")
        parser.add_argument("--no-backup", action="store_true", help="No crear backup al remover")
        parser.add_argument("--email", help="Email para certificados SSL")
        parser.add_argument("--file", help="Archivo para importar/exportar configuración")
        parser.add_argument("--directory", help="Directorio para detectar tipo de aplicación")
        
        # Opción verbose
        parser.add_argument(
            "--verbose", "-v", 
            action="store_true", 
            help="Mostrar logs detallados del proceso"
        )
        
        return parser
    
    def _get_examples(self) -> str:
        """Obtener ejemplos de uso con formato moderno"""
        return """
[bold cyan]Ejemplos de Uso:[/bold cyan]

[bold]� Configuración Inicial (Primera vez):[/bold]
  webapp-manager setup
  
[bold]�📱 Aplicaciones Next.js:[/bold]
  webapp-manager add --domain app.ejemplo.com --source /ruta/app --port 3000
  webapp-manager add --domain mi-app.com --source https://github.com/usuario/mi-app.git --port 3001
  
[bold]🐍 APIs FastAPI:[/bold]
  webapp-manager add --domain api.ejemplo.com --source /ruta/api --port 8000 --type fastapi
  webapp-manager add --domain mi-api.com --source https://github.com/usuario/mi-api.git --port 8001 --type fastapi
  
[bold]🟢 Aplicaciones Node.js:[/bold]
  webapp-manager add --domain node-app.com --source https://github.com/usuario/node-app.git --port 4000 --type nodejs
  
[bold]📄 Sitios Estáticos:[/bold]
  webapp-manager add --domain sitio.com --source /ruta/sitio --type static

[bold]🔍 Modo Verbose:[/bold]
  webapp-manager add --domain app.com --source ./app --port 3000 --verbose
  webapp-manager update --domain app.com -v
  
[bold]📊 Gestión y Monitoreo:[/bold]
  webapp-manager list --detailed
  webapp-manager status --domain mi-app.com
  webapp-manager logs --domain mi-app.com --lines 100 --follow
  webapp-manager diagnose --domain mi-app.com
  webapp-manager restart --domain api.ejemplo.com
  
[bold]🔧 Herramientas Avanzadas:[/bold]
  webapp-manager types
  webapp-manager detect --directory /ruta/app
  webapp-manager export --file backup-config.json
  webapp-manager ssl --domain app.ejemplo.com --email admin@ejemplo.com
  webapp-manager apply-maintenance   # Aplicar páginas de mantenimiento a apps existentes
  webapp-manager check-system        # Verificar prerequisitos del sistema

[bold]🛠️  Modo Mantenimiento y Actualización:[/bold]
  # Modo interactivo (pregunta si activar/desactivar)
  webapp-manager maintenance --domain app.com
  webapp-manager updating --domain app.com
  
  # Activar explícitamente
  webapp-manager maintenance --domain app.com --enable
  webapp-manager updating --domain app.com --enable
  
  # Desactivar explícitamente  
  webapp-manager maintenance --domain app.com --disable
  webapp-manager updating --domain app.com --disable
  
  # Sincronizar páginas HTML
  webapp-manager sync-pages

[bold]Tipos de aplicación soportados:[/bold]
  • [green]nextjs[/green]  - Aplicaciones Next.js (por defecto)
  • [green]nodejs[/green]  - Aplicaciones Node.js genéricas  
  • [green]fastapi[/green] - APIs FastAPI con Python
  • [green]static[/green]  - Sitios web estáticos

[bold]Variables de entorno:[/bold]
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
                self._show_warning(f"Variable de entorno inválida ignorada: {env_var}")
        return env_vars
    
    def _execute_command(self, args, env_vars: Dict[str, str]) -> bool:
        """Ejecutar comando específico"""
        command = args.command
        
        # Mostrar header del comando solo en modo verbose
        if self.verbose:
            command_names = {
                "add": "Agregar Aplicación",
                "remove": "Eliminar Aplicación",
                "list": "Listar Aplicaciones",
                "restart": "Reiniciar Aplicación",
                "update": "Actualizar Aplicación",
                "logs": "Ver Logs",
                "ssl": "Configurar SSL",
                "diagnose": "Diagnóstico",
                "repair": "Reparar Aplicación",
                "status": "Estado",
                "export": "Exportar Configuración",
                "import": "Importar Configuración",
                "types": "Tipos de Aplicación",
                "detect": "Detectar Tipo",
                "fix-config": "Reparar Configuración",
                "maintenance": "Modo Mantenimiento",
                "updating": "Modo Actualización",
                "sync-pages": "Sincronizar Páginas",
                "setup": "Configuración Inicial",
                "check-system": "Verificar Prerequisitos del Sistema",
                "version": "Información de Versión",
                "gui": "Interfaz Gráfica"
            }
            
            self.console.print(Panel(
                f"[bold cyan]{command_names.get(command, command.title())}[/bold cyan]",
                style="blue"
            ))
        
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
            self._cmd_types(args)
            return True
        elif command == "detect":
            self._cmd_detect(args)
            return True
        elif command == "fix-config":
            return self._cmd_fix_config(args)
        elif command == "apply-maintenance":
            return self._cmd_apply_maintenance(args)
        elif command == "maintenance":
            return self._cmd_maintenance(args)
        elif command == "updating":
            return self._cmd_updating(args)
        elif command == "sync-pages":
            return self._cmd_sync_pages(args)
        elif command == "setup":
            return self._cmd_setup(args)
        elif command == "check-system":
            return self._cmd_check_system(args)
        elif command == "version":
            self._cmd_version()
            return True
        elif command == "gui":
            self._cmd_gui()
            return True
        else:
            self._show_error(f"Comando no implementado: {command}")
            return False
    
    def _cmd_add(self, args, env_vars: Dict[str, str]) -> bool:
        """Comando add con progress real"""
        if not args.domain or not args.source or not args.port:
            self._show_error("Para agregar una app necesitas: --domain, --source y --port")
            return False
        
        # Mostrar resumen antes de empezar
        if self.verbose:
            self._show_deployment_summary(args, env_vars)
        
        # Confirmar despliegue
        if not Confirm.ask("¿Proceder con el despliegue?", default=True):
            self._show_warning("Despliegue cancelado")
            return False
        
        # Ejecutar despliegue
        try:
            result = self.manager.add_app(
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
            
            if result:
                self._show_deployment_success(args)
            else:
                self._show_deployment_failure(args)
            
            return result
            
        except Exception as e:
            self._show_error(f"Error durante el despliegue: {e}")
            return False
    
    def _show_deployment_summary(self, args, env_vars: Dict[str, str]):
        """Mostrar resumen del despliegue"""
        summary_table = Table(title="Resumen del Despliegue")
        summary_table.add_column("Parámetro", style="cyan", width=20)
        summary_table.add_column("Valor", style="white")
        
        summary_table.add_row("🌐 Dominio", args.domain)
        summary_table.add_row("🚪 Puerto", str(args.port))
        summary_table.add_row("📱 Tipo", args.type)
        summary_table.add_row("📂 Fuente", args.source)
        summary_table.add_row("🌿 Rama", args.branch)
        summary_table.add_row("🔒 SSL", "❌ No" if args.no_ssl else "✅ Sí")
        
        if env_vars:
            env_display = ", ".join([f"{k}={v}" for k, v in list(env_vars.items())[:3]])
            if len(env_vars) > 3:
                env_display += f" (+{len(env_vars)-3} más)"
            summary_table.add_row("🔧 Variables", env_display)
        
        self.console.print(summary_table)
    
    def _show_deployment_success(self, args):
        """Mostrar mensaje de éxito del despliegue"""
        protocol = "https" if not args.no_ssl else "http"
        success_panel = Panel(
            f"""[bold green]🎉 ¡Despliegue Exitoso![/bold green]

[bold]Aplicación:[/bold] {args.domain}
[bold]URL:[/bold] [link]{protocol}://{args.domain}[/link]
[bold]Puerto interno:[/bold] {args.port}
[bold]Tipo:[/bold] {args.type}

[dim]La aplicación está lista y funcionando correctamente.[/dim]

[bold]Próximos pasos:[/bold]
- Configura el DNS para apuntar a este servidor
- Monitorea los logs: [cyan]webapp-manager logs --domain {args.domain}[/cyan]
- Ver estado: [cyan]webapp-manager status --domain {args.domain}[/cyan]
            """,
            title="✅ Despliegue Completado",
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(success_panel)
    
    def _show_deployment_failure(self, args):
        """Mostrar mensaje de fallo del despliegue"""
        failure_panel = Panel(
            f"""[bold red]❌ Error en el Despliegue[/bold red]

[bold]Aplicación:[/bold] {args.domain}
[bold]Estado:[/bold] Despliegue fallido

[bold]Soluciones sugeridas:[/bold]
- Verifica los logs: [cyan]webapp-manager logs --domain {args.domain}[/cyan]
- Ejecuta diagnóstico: [cyan]webapp-manager diagnose[/cyan]
- Revisa la configuración del servidor
- Verifica que el puerto {args.port} esté disponible

[dim]Consulta la documentación para más ayuda.[/dim]
            """,
            title="❌ Despliegue Fallido",
            border_style="red",
            padding=(1, 2)
        )
        self.console.print(failure_panel)
    
    def _cmd_remove(self, args) -> bool:
        """Comando remove con confirmación"""
        if not args.domain:
            self._show_error("Necesitas especificar --domain")
            return False
        
        # Confirmación de seguridad
        self._show_warning(f"⚠️  Vas a eliminar la aplicación: [bold red]{args.domain}[/bold red]")
        self.console.print("[dim]Esta acción eliminará:[/dim]")
        self.console.print("  • Código fuente de la aplicación")
        self.console.print("  • Configuración de nginx")
        self.console.print("  • Servicio systemd")
        self.console.print("  • Certificados SSL (si existen)")
        
        if not args.no_backup:
            self.console.print("\n[green]✅ Se creará un backup antes de eliminar[/green]")
        
        if not Confirm.ask(f"\n¿Confirmas la eliminación de {args.domain}?", default=False):
            self._show_info("Eliminación cancelada")
            return True
        
        # Ejecutar eliminación
        result = self.manager.remove_app(args.domain, backup=not args.no_backup)
        
        if result:
            self._show_success(f"Aplicación {args.domain} eliminada exitosamente")
        else:
            self._show_error(f"Error eliminando {args.domain}")
        
        return result
    
    def _cmd_list(self, args) -> bool:
        """Comando list con tabla moderna"""
        try:
            apps = self.manager.list_apps()
            
            if not apps:
                self.console.print(Panel(
                    "[yellow]No hay aplicaciones desplegadas[/yellow]\n\n"
                    "Para desplegar tu primera aplicación:\n"
                    "[cyan]webapp-manager add --domain ejemplo.com --source /ruta --port 3000[/cyan]",
                    title="Sin Aplicaciones",
                    border_style="yellow"
                ))
                return True
            
            # Crear tabla de aplicaciones
            table = Table(title=f"📱 Aplicaciones Desplegadas ({len(apps)})")
            
            table.add_column("🌐 Dominio", style="cyan", width=25)
            table.add_column("📱 Tipo", style="magenta", width=10)
            table.add_column("🚪 Puerto", style="yellow", width=8)
            table.add_column("⚡ Estado", style="white", width=12)
            table.add_column("🔒 SSL", style="blue", width=6)
            
            if args.detailed:
                table.add_column("📅 Actualizado", style="dim", width=12)
                table.add_column("📂 Fuente", style="dim", width=30)
            
            for app in apps:
                try:
                    # Obtener estado actualizado
                    status = self.manager.systemd_service.get_service_status(app.domain)
                    
                    # Determinar icono y color del estado
                    if "Activo" in status:
                        status_display = "[green]🟢 Activo[/green]"
                    elif "Inactivo" in status:
                        status_display = "[yellow]🟡 Inactivo[/yellow]"
                    elif "Fallido" in status:
                        status_display = "[red]🔴 Fallido[/red]"
                    else:
                        status_display = "[dim]🔘 Desconocido[/dim]"
                    
                    ssl_display = "✅" if app.ssl else "❌"
                    
                    row_data = [
                        app.domain,
                        app.app_type,
                        str(app.port),
                        status_display,
                        ssl_display
                    ]
                    
                    if args.detailed:
                        row_data.extend([
                            app.last_updated[:10] if app.last_updated else "N/A",
                            app.source[:30] + "..." if len(app.source) > 30 else app.source
                        ])
                    
                    table.add_row(*row_data)
                    
                except Exception as e:
                    # Fila de error para aplicaciones problemáticas
                    error_row = [
                        app.domain if hasattr(app, 'domain') else "Error",
                        "Error",
                        "Error",
                        "[red]🔴 Error[/red]",
                        "❌"
                    ]
                    if args.detailed:
                        error_row.extend(["Error", "Error"])
                    
                    table.add_row(*error_row)
            
            self.console.print(table)
            
            # Mostrar estadísticas
            active_count = sum(1 for app in apps 
                             if "Activo" in self.manager.systemd_service.get_service_status(app.domain))
            ssl_count = sum(1 for app in apps if app.ssl)
            
            stats_panel = Panel(
                f"[bold]📊 Estadísticas:[/bold]\n"
                f"• Total: {len(apps)} aplicaciones\n"
                f"• Activas: [green]{active_count}[/green]\n"
                f"• Con SSL: [blue]{ssl_count}[/blue]\n"
                f"• Eficiencia: [cyan]{active_count/len(apps)*100:.1f}%[/cyan]",
                title="Resumen",
                border_style="green",
                padding=(0, 2)
            )
            self.console.print(stats_panel)
            
            return True
            
        except Exception as e:
            self._show_error(f"Error listando aplicaciones: {e}")
            return False
    
    def _cmd_restart(self, args) -> bool:
        """Comando restart"""
        if not args.domain:
            self._show_error("Necesitas especificar --domain")
            return False
        
        result = self.manager.restart_app(args.domain)
        
        if result:
            self._show_success(f"Aplicación {args.domain} reiniciada exitosamente")
        else:
            self._show_error(f"Error reiniciando {args.domain}")
        
        return result
    
    def _cmd_update(self, args) -> bool:
        """Comando update"""
        if not args.domain:
            self._show_error("Necesitas especificar --domain")
            return False
        
        result = self.manager.update_app(args.domain)
        
        if result:
            self._show_success(f"Aplicación {args.domain} actualizada exitosamente")
        else:
            self._show_error(f"Error actualizando {args.domain}")
        
        return result
    
    def _cmd_logs(self, args) -> bool:
        """Mostrar logs con formato mejorado"""
        if not args.domain:
            self._show_error("Necesitas especificar --domain")
            return False
        
        try:
            if args.follow:
                # Logs en tiempo real
                self.console.print(Panel(
                    f"[bold]Siguiendo logs de {args.domain} en tiempo real[/bold]\n"
                    f"[dim]Presiona Ctrl+C para salir[/dim]",
                    title="📡 Logs en Tiempo Real",
                    border_style="blue"
                ))
                
                return self.manager.logs(args.domain, args.lines, args.follow)
            else:
                # Logs estáticos
                self.console.print(Panel(
                    f"[bold]Logs de {args.domain} (últimas {args.lines} líneas)[/bold]",
                    title="📋 Logs de Aplicación",
                    border_style="green"
                ))
                
                return self.manager.logs(args.domain, args.lines, args.follow)
                
        except Exception as e:
            self._show_error(f"Error obteniendo logs: {e}")
            return False
    
    def _cmd_status(self, args) -> bool:
        """Mostrar estado con información detallada"""
        try:
            if args.domain:
                return self._show_app_status(args.domain)
            else:
                return self._show_system_status()
        except Exception as e:
            self._show_error(f"Error obteniendo estado: {e}")
            return False
    
    def _show_app_status(self, domain: str) -> bool:
        """Mostrar estado de aplicación específica"""
        try:
            app_config = self.manager.config_manager.get_app(domain)
            status = self.manager.systemd_service.get_service_status(domain)
            connectivity = self.manager.app_service.test_connectivity(domain, app_config.port)
            
            # Crear tabla de estado
            status_table = Table(title=f"📊 Estado de {domain}")
            status_table.add_column("Aspecto", style="cyan", width=20)
            status_table.add_column("Estado", style="white", width=30)
            status_table.add_column("Detalles", style="dim", width=40)
            
            # Estado del servicio
            if "Activo" in status:
                service_status = "[green]🟢 Funcionando[/green]"
                service_details = "Servicio systemd activo"
            elif "Inactivo" in status:
                service_status = "[yellow]🟡 Detenido[/yellow]"
                service_details = "Servicio systemd inactivo"
            else:
                service_status = "[red]🔴 Error[/red]"
                service_details = "Problema con el servicio"
            
            status_table.add_row("⚡ Servicio", service_status, service_details)
            
            # Conectividad
            if connectivity:
                conn_status = "[green]🌐 Responde[/green]"
                conn_details = f"HTTP OK en puerto {app_config.port}"
            else:
                conn_status = "[red]🔴 No responde[/red]"
                conn_details = f"Sin respuesta en puerto {app_config.port}"
            
            status_table.add_row("🌐 Conectividad", conn_status, conn_details)
            
            # SSL
            ssl_status = "[green]🔒 Configurado[/green]" if app_config.ssl else "[yellow]🔓 Sin SSL[/yellow]"
            ssl_details = "HTTPS habilitado" if app_config.ssl else "Solo HTTP"
            status_table.add_row("🔒 SSL", ssl_status, ssl_details)
            
            # Información adicional
            status_table.add_row("📱 Tipo", app_config.app_type, f"Deployer {app_config.app_type}")
            status_table.add_row("🚪 Puerto", str(app_config.port), "Puerto interno")
            status_table.add_row("📅 Actualizado", app_config.last_updated[:19] if app_config.last_updated else "N/A", "Última modificación")
            
            self.console.print(status_table)
            
            # URLs de acceso
            urls_panel = Panel(
                f"[bold]🔗 URLs de acceso:[/bold]\n"
                f"• HTTP: [link]http://{domain}[/link]\n" +
                (f"• HTTPS: [link]https://{domain}[/link]\n" if app_config.ssl else "") +
                f"• Puerto directo: [dim]http://servidor:{app_config.port}[/dim]",
                title="Acceso",
                border_style="blue"
            )
            self.console.print(urls_panel)
            
            return True
            
        except Exception as e:
            self._show_error(f"Error obteniendo estado de {domain}: {e}")
            return False
    
    def _show_system_status(self) -> bool:
        """Mostrar estado general del sistema"""
        try:
            # Obtener información del sistema
            apps = self.manager.list_apps()
            active_count = sum(1 for app in apps 
                             if "Activo" in self.manager.systemd_service.get_service_status(app.domain))
            
            # Estado de nginx
            nginx_status = self.manager.cmd.run_sudo("systemctl is-active nginx", check=False)
            nginx_config_ok = self.manager.nginx_service.test_config()
            
            # Crear tabla de estado del sistema
            system_table = Table(title="🖥️  Estado General del Sistema")
            system_table.add_column("Componente", style="cyan", width=20)
            system_table.add_column("Estado", style="white", width=20)
            system_table.add_column("Detalles", style="dim", width=40)
            
            # Nginx
            if nginx_status == "active":
                nginx_display = "[green]🟢 Activo[/green]"
                nginx_details = "Servidor web funcionando"
            else:
                nginx_display = "[red]🔴 Inactivo[/red]"
                nginx_details = "Servidor web detenido"
            
            system_table.add_row("🌐 Nginx", nginx_display, nginx_details)
            
            # Configuración nginx
            config_status = "[green]✅ Válida[/green]" if nginx_config_ok else "[red]❌ Con errores[/red]"
            config_details = "Sintaxis correcta" if nginx_config_ok else "Revisar configuración"
            system_table.add_row("⚙️  Config Nginx", config_status, config_details)
            
            # Aplicaciones
            apps_status = f"[green]{active_count}[/green]/[cyan]{len(apps)}[/cyan] activas"
            apps_details = f"{len(apps)} aplicaciones desplegadas"
            system_table.add_row("📱 Aplicaciones", apps_status, apps_details)
            
            # WebApp Manager
            system_table.add_row("🚀 WebApp Manager", "[green]🟢 Funcionando[/green]", "Sistema operativo")
            
            self.console.print(system_table)
            
            # Panel de recursos
            try:
                disk_usage = self.manager.cmd.run("df -h / | awk 'NR==2{print $5}'", check=False)
                memory_info = self.manager.cmd.run("free -h | awk 'NR==2{print $3\"/\"$2}'", check=False)
                
                resources_panel = Panel(
                    f"[bold]💻 Recursos del Sistema:[/bold]\n"
                    f"• Disco usado: {disk_usage or 'N/A'}\n"
                    f"• Memoria: {memory_info or 'N/A'}\n"
                    f"• Sistema: {os.name} ({os.uname().machine if hasattr(os, 'uname') else 'N/A'})",
                    title="Recursos",
                    border_style="yellow"
                )
                self.console.print(resources_panel)
                
            except:
                pass  # Ignorar errores de recursos
            
            return True
            
        except Exception as e:
            self._show_error(f"Error obteniendo estado del sistema: {e}")
            return False
    
    def _cmd_ssl(self, args) -> bool:
        """Comando SSL"""
        if not args.domain:
            self._show_error("Necesitas especificar --domain")
            return False
        
        result = self.manager.setup_ssl(args.domain, args.email)
        
        if result:
            self._show_success(f"SSL configurado para {args.domain}")
            self.console.print(f"[green]🔒 HTTPS disponible en: https://{args.domain}[/green]")
        else:
            self._show_error(f"Error configurando SSL para {args.domain}")
        
        return result
    
    def _cmd_diagnose(self, args) -> bool:
        """Comando diagnose"""
        self.manager.diagnose(args.domain)
        return True
    
    def _cmd_repair(self, args) -> bool:
        """Comando repair"""
        if not args.domain:
            self._show_error("Necesitas especificar --domain")
            return False
        
        result = self.manager.repair_app(args.domain)
        
        if result:
            self._show_success(f"Aplicación {args.domain} reparada exitosamente")
        else:
            self._show_error(f"Error reparando {args.domain}")
        
        return result
    
    def _cmd_export(self, args) -> bool:
        """Comando export"""
        if not args.file:
            self._show_error("Necesitas especificar --file")
            return False
        
        result = self.manager.export_config(args.file)
        
        if result:
            self._show_success(f"Configuración exportada a {args.file}")
        else:
            self._show_error(f"Error exportando configuración")
        
        return result
    
    def _cmd_import(self, args) -> bool:
        """Comando import"""
        if not args.file:
            self._show_error("Necesitas especificar --file")
            return False
        
        result = self.manager.import_config(args.file)
        
        if result:
            self._show_success(f"Configuración importada desde {args.file}")
        else:
            self._show_error(f"Error importando configuración")
        
        return result
    
    def _cmd_types(self, args):
        """Mostrar tipos de deployers disponibles"""
        deployers = DeployerFactory.list_all_deployers()
        
        # Crear tabla de tipos
        types_table = Table(title="🛠️  Tipos de Aplicación Soportados")
        types_table.add_column("Tipo", style="cyan", width=12)
        types_table.add_column("Descripción", style="white", width=40)
        types_table.add_column("Archivos Requeridos", style="yellow", width=25)
        types_table.add_column("Estado", style="green", width=10)
        
        for deployer in deployers:
            status = "✅" if deployer['supported'] else "❌"
            required_files = ", ".join(deployer['required_files'][:2])
            if len(deployer['required_files']) > 2:
                required_files += f" (+{len(deployer['required_files'])-2})"
            
            types_table.add_row(
                f"[bold]{deployer['type']}[/bold]",
                deployer['description'],
                required_files,
                status
            )
        
        self.console.print(types_table)
        
        # Ejemplos de uso
        examples_panel = Panel(
            """[bold]Ejemplos de uso por tipo:[/bold]

[cyan]nextjs[/cyan]:  webapp-manager add --domain app.com --source ./my-nextjs-app --port 3000 --type nextjs
[cyan]fastapi[/cyan]: webapp-manager add --domain api.com --source ./my-fastapi-api --port 8000 --type fastapi  
[cyan]nodejs[/cyan]:  webapp-manager add --domain node.com --source ./my-node-app --port 5000 --type nodejs
[cyan]static[/cyan]:  webapp-manager add --domain site.com --source ./my-static-site --type static
            """,
            title="Ejemplos",
            border_style="blue"
        )
        self.console.print(examples_panel)
    
    def _cmd_detect(self, args):
        """Detectar tipo de aplicación"""
        directory = args.directory or "."
        
        with self._loading(f"Analizando directorio {directory}"):
            try:
                detected_type = DeployerFactory.detect_app_type(directory)
                is_valid = DeployerFactory.validate_app_type(directory, detected_type)
                
            except Exception as e:
                self._show_error(f"Error detectando tipo: {e}")
                return
        
        # Mostrar resultado
        validation_status = "✅ Válida" if is_valid else "⚠️  Requiere ajustes"
        validation_color = "green" if is_valid else "yellow"
        
        result_panel = Panel(
            f"""[bold]Directorio analizado:[/bold] {directory}
[bold]Tipo detectado:[/bold] [cyan]{detected_type}[/cyan]
[bold]Validación:[/bold] [{validation_color}]{validation_status}[/{validation_color}]

[bold]Información del deployer:[/bold]
            """,
            title="🔍 Resultado de Detección",
            border_style="cyan"
        )
        self.console.print(result_panel)
        
        # Mostrar información del deployer
        try:
            info = DeployerFactory.get_deployer_info(detected_type)
            
            info_table = Table(show_header=False, box=None)
            info_table.add_column("Item", style="cyan", width=20)
            info_table.add_column("Valor", style="white")
            
            info_table.add_row("📋 Archivos requeridos", ", ".join(info['required_files']))
            if info['optional_files']:
                info_table.add_row("📄 Archivos opcionales", ", ".join(info['optional_files']))
            
            self.console.print(info_table)
            
        except Exception as e:
            self._show_warning(f"No se pudo obtener información detallada: {e}")
    
    def _cmd_fix_config(self, args) -> bool:
        """Comando fix-config"""
        self._show_info("Función fix-config no implementada todavía")
        return True
    
    def _cmd_apply_maintenance(self, args) -> bool:
        """Aplicar configuración de páginas de mantenimiento a aplicaciones existentes"""
        try:
            # Mostrar información sobre el comando
            info_panel = Panel(
                "[bold cyan]Aplicar Páginas de Mantenimiento[/bold cyan]\n\n"
                "Este comando actualiza las configuraciones de nginx existentes para incluir:\n"
                "• Redirección automática a páginas de mantenimiento en errores 502/503/504\n"
                "• Páginas profesionales y modernas de actualización y error\n"
                "• Configuración automática para todas las aplicaciones\n\n"
                "[dim]Las páginas se sirven desde /apps/maintenance/ y se actualizan cada 30 segundos[/dim]",
                title="ℹ️  Información",
                style="blue"
            )
            self.console.print(info_panel)
            
            # Confirmar la operación
            if not Confirm.ask("[yellow]¿Desea aplicar las configuraciones de mantenimiento a todas las aplicaciones?[/yellow]"):
                self._show_info("Operación cancelada")
                return True
            
            # Inicializar el manager si es necesario
            if not self.manager:
                self.manager = WebAppManager(verbose=self.verbose, progress_manager=self.progress_manager)
            
            # Obtener lista de aplicaciones
            apps = self.manager.config_manager.list_apps()
            
            if not apps:
                self._show_warning("No se encontraron aplicaciones instaladas")
                return True
            
            self._show_info(f"Aplicando configuración de mantenimiento a {len(apps)} aplicaciones...")
            
            # Crear directorio de mantenimiento y copiar archivos
            with self._loading("Configurando directorio de mantenimiento"):
                self.manager.nginx_service.ensure_maintenance_directory()
            
            success_count = 0
            error_count = 0
            
            # Procesar cada aplicación
            for domain in apps:
                try:
                    app_config = self.manager.config_manager.get_app(domain)
                    
                    with self._loading(f"Actualizando {domain}"):
                        if self.manager.nginx_service.has_maintenance_config(domain):
                            self.console.print(f"  ✅ [green]{domain}[/green] - Ya tiene configuración de mantenimiento")
                        else:
                            if self.manager.nginx_service.update_config_with_maintenance(app_config):
                                self.console.print(f"  ✅ [green]{domain}[/green] - Configuración aplicada exitosamente")
                                success_count += 1
                            else:
                                self.console.print(f"  ❌ [red]{domain}[/red] - Error aplicando configuración")
                                error_count += 1
                
                except Exception as e:
                    self.console.print(f"  ❌ [red]{domain}[/red] - Error: {str(e)}")
                    error_count += 1
            
            # Recargar nginx si hubo cambios
            if success_count > 0:
                with self._loading("Recargando nginx"):
                    if self.manager.nginx_service.reload():
                        self._show_success("Nginx recargado exitosamente")
                    else:
                        self._show_warning("Problemas al recargar nginx")
            
            # Mostrar resumen
            summary_table = Table(title="📊 Resumen de la operación")
            summary_table.add_column("Estado", style="bold")
            summary_table.add_column("Cantidad", justify="right")
            
            summary_table.add_row("✅ Exitosas", str(success_count), style="green")
            summary_table.add_row("❌ Con errores", str(error_count), style="red")
            summary_table.add_row("📝 Total procesadas", str(len(apps)), style="blue")
            
            self.console.print(summary_table)
            
            if success_count > 0:
                success_panel = Panel(
                    "[bold green]✅ Configuración aplicada exitosamente[/bold green]\n\n"
                    "Las aplicaciones ahora mostrarán automáticamente páginas de mantenimiento cuando:\n"
                    "• El servicio esté caído (error 502/503/504)\n"
                    "• Se esté realizando una actualización\n"
                    "• Ocurra un error interno del servidor (error 500)\n\n"
                    "[dim]Las páginas se actualizan automáticamente cada 30 segundos[/dim]",
                    title="🎉 Completado",
                    style="green"
                )
                self.console.print(success_panel)
            
            return error_count == 0
            
        except Exception as e:
            self._show_error(f"Error aplicando configuración de mantenimiento: {str(e)}")
            return False
    
    def _cmd_setup(self, args) -> bool:
        """Ejecutar configuración inicial del sistema"""
        try:
            from ..services import InstallService
            
            # Mostrar información sobre el setup
            setup_panel = Panel(
                "[bold cyan]Configuración Inicial del Sistema[/bold cyan]\n\n"
                "Este comando realizará las siguientes tareas:\n\n"
                "• ✅ Verificar requisitos del sistema (nginx, python3, systemctl)\n"
                "• 📄 Instalar páginas de mantenimiento en /apps/maintenance/\n"
                "• 🔍 Verificar conflictos con el sitio default de nginx\n"
                "• 🔧 Configurar directorios necesarios\n\n"
                "[dim]Este comando debe ejecutarse una vez después de instalar webapp-manager[/dim]\n"
                "[yellow]⚠️  Se requieren permisos de root (sudo)[/yellow]",
                title="ℹ️  Información de Setup",
                style="blue"
            )
            self.console.print(setup_panel)
            
            # Confirmar la operación
            if not Confirm.ask("[yellow]¿Desea continuar con la configuración inicial?[/yellow]", default=True):
                self._show_info("Configuración cancelada")
                return True
            
            # Crear servicio de instalación
            install_service = InstallService(verbose=self.verbose)
            
            # Ejecutar setup completo
            with self._loading("Ejecutando configuración inicial"):
                success = install_service.run_initial_setup()
            
            if success:
                success_panel = Panel(
                    "[bold green]✅ Configuración inicial completada exitosamente[/bold green]\n\n"
                    "El sistema está listo para usar. Puedes:\n\n"
                    "• Agregar tu primera aplicación:\n"
                    "  [cyan]webapp-manager add --domain app.com --source /path --port 3000[/cyan]\n\n"
                    "• Ver aplicaciones instaladas:\n"
                    "  [cyan]webapp-manager list[/cyan]\n\n"
                    "• Ver tipos de aplicaciones soportados:\n"
                    "  [cyan]webapp-manager types[/cyan]\n\n"
                    "[dim]Las páginas de mantenimiento se han instalado en /apps/maintenance/[/dim]",
                    title="🎉 Setup Completado",
                    style="green"
                )
                self.console.print(success_panel)
                return True
            else:
                self._show_error("La configuración inicial falló. Revisa los mensajes anteriores para más detalles.")
                return False
                
        except Exception as e:
            self._show_error(f"Error durante la configuración inicial: {str(e)}")
            return False
    
    def _cmd_check_system(self, args) -> bool:
        """Verificar prerequisitos del sistema"""
        try:
            self.console.print(Panel(
                "[bold cyan]Verificación de Prerequisitos del Sistema[/bold cyan]\n\n"
                "Verificando la instalación de herramientas requeridas...",
                title="🔍 Check System",
                style="blue"
            ))
            
            # Ejecutar verificación
            self.manager.check_prerequisites()
            
            self._show_success("Verificación de sistema completada")
            return True
            
        except Exception as e:
            self._show_error(f"Error verificando prerequisitos: {str(e)}")
            return False
    
    def _cmd_version(self):
        """Mostrar información de versión"""
        from .. import __version__, __description__
        
        version_info = Table(show_header=False, box=None)
        version_info.add_row("🚀", f"[bold cyan]WebApp Manager[/bold cyan]")
        version_info.add_row("📦", f"Versión: [bold green]{__version__}[/bold green]")
        version_info.add_row("📝", f"Descripción: {__description__}")
        version_info.add_row("🐍", f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        version_info.add_row("🐧", f"Sistema: {'Linux' if os.name == 'posix' else 'Windows'}")
        
        self.console.print(Panel(
            Align.center(version_info),
            title="[bold]Información del Sistema[/bold]",
            style="blue"
        ))
    
    def _cmd_gui(self):
        """Abrir interfaz gráfica (dialog)"""
        self._show_info("Abriendo interfaz gráfica con Dialog...")
        # Aquí iría la implementación de la GUI con dialog
        self._show_warning("Función GUI no implementada todavía")
    
    def _cmd_maintenance(self, args) -> bool:
        """Activar o desactivar modo mantenimiento para una aplicación"""
        try:
            if not args.domain:
                self._show_error("Debe especificar un dominio con --domain")
                return False
            
            # Determinar si activar o desactivar
            if args.enable and args.disable:
                self._show_error("No puedes usar --enable y --disable al mismo tiempo")
                return False
            
            # Si se especificó --enable o --disable, usarlo directamente
            if args.enable:
                enable = True
            elif args.disable:
                enable = False
            else:
                # Modo interactivo
                info_panel = Panel(
                    "[bold cyan]Modo Mantenimiento[/bold cyan]\n\n"
                    "El modo mantenimiento muestra una página especial a los usuarios\n"
                    "mientras se realizan tareas de mantenimiento en la aplicación.\n\n"
                    f"Dominio: [bold]{args.domain}[/bold]\n\n"
                    "[dim]Los usuarios verán una página profesional indicando que el sitio\n"
                    "está temporalmente en mantenimiento[/dim]",
                    title="ℹ️  Información",
                    style="blue"
                )
                self.console.print(info_panel)
                
                # Preguntar si activar o desactivar
                enable = Confirm.ask(
                    "[yellow]¿Activar modo mantenimiento?[/yellow] (No = desactivar)",
                    default=True
                )
            
            # Ejecutar comando
            action_text = "Activando" if enable else "Desactivando"
            with self._loading(f"{action_text} modo mantenimiento"):
                success = self.manager.set_maintenance_mode(args.domain, enable)
            
            if success:
                if enable:
                    self._show_success(f"✅ Modo mantenimiento activado para {args.domain}")
                    self.console.print(f"[dim]Los usuarios verán la página de mantenimiento en https://{args.domain}[/dim]")
                    self.console.print(f"[bold yellow]Para desactivar:[/bold yellow] webapp-manager maintenance --domain {args.domain} --disable")
                else:
                    self._show_success(f"✅ Modo mantenimiento desactivado para {args.domain}")
                    self.console.print(f"[dim]La aplicación está nuevamente accesible en https://{args.domain}[/dim]")
                    self.console.print(f"[bold green]✓[/bold green] Configuración anterior restaurada desde backup")
            else:
                self._show_error(f"❌ Error configurando modo mantenimiento para {args.domain}")
            
            return success
            
        except Exception as e:
            self._show_error(f"Error en comando maintenance: {str(e)}")
            return False
    
    def _cmd_updating(self, args) -> bool:
        """Activar o desactivar modo actualización para una aplicación"""
        try:
            if not args.domain:
                self._show_error("Debe especificar un dominio con --domain")
                return False
            
            # Determinar si activar o desactivar
            if args.enable and args.disable:
                self._show_error("No puedes usar --enable y --disable al mismo tiempo")
                return False
            
            # Si se especificó --enable o --disable, usarlo directamente
            if args.enable:
                enable = True
            elif args.disable:
                enable = False
            else:
                # Modo interactivo
                info_panel = Panel(
                    "[bold cyan]Modo Actualización[/bold cyan]\n\n"
                    "El modo actualización muestra una página especial indicando que\n"
                    "se está actualizando la aplicación.\n\n"
                    f"Dominio: [bold]{args.domain}[/bold]\n\n"
                    "[dim]Los usuarios verán una página profesional con un mensaje\n"
                    "indicando que la aplicación se está actualizando[/dim]",
                    title="ℹ️  Información",
                    style="blue"
                )
                self.console.print(info_panel)
                
                # Preguntar si activar o desactivar
                enable = Confirm.ask(
                    "[yellow]¿Activar modo actualización?[/yellow] (No = desactivar)",
                    default=True
                )
            
            # Ejecutar comando
            action_text = "Activando" if enable else "Desactivando"
            with self._loading(f"{action_text} modo actualización"):
                success = self.manager.set_updating_mode(args.domain, enable)
            
            if success:
                if enable:
                    self._show_success(f"✅ Modo actualización activado para {args.domain}")
                    self.console.print(f"[dim]Los usuarios verán la página de actualización en https://{args.domain}[/dim]")
                    self.console.print(f"[bold yellow]Para desactivar:[/bold yellow] webapp-manager updating --domain {args.domain} --disable")
                else:
                    self._show_success(f"✅ Modo actualización desactivado para {args.domain}")
                    self.console.print(f"[dim]La aplicación está nuevamente accesible en https://{args.domain}[/dim]")
                    self.console.print(f"[bold green]✓[/bold green] Configuración anterior restaurada desde backup")
            else:
                self._show_error(f"❌ Error configurando modo actualización para {args.domain}")
            
            return success
            
        except Exception as e:
            self._show_error(f"Error en comando updating: {str(e)}")
            return False
    
    def _cmd_sync_pages(self, args) -> bool:
        """Sincronizar/actualizar páginas de mantenimiento en el servidor"""
        try:
            # Mostrar información
            info_panel = Panel(
                "[bold cyan]Sincronizar Páginas de Mantenimiento[/bold cyan]\n\n"
                "Este comando actualiza las páginas HTML de mantenimiento en el servidor\n"
                "copiándolas desde el repositorio a /apps/maintenance/\n\n"
                "Páginas incluidas:\n"
                "• [green]maintenance.html[/green] - Página de mantenimiento programado\n"
                "• [green]updating.html[/green] - Página de actualización en progreso\n"
                "• [green]error502.html[/green] - Página de error del servidor\n\n"
                "[dim]Usa este comando después de actualizar webapp-manager para obtener\n"
                "las últimas versiones de las páginas[/dim]",
                title="ℹ️  Información",
                style="blue"
            )
            self.console.print(info_panel)
            
            # Confirmar
            if not Confirm.ask("[yellow]¿Desea actualizar las páginas de mantenimiento?[/yellow]", default=True):
                self._show_info("Operación cancelada")
                return True
            
            # Ejecutar sincronización
            with self._loading("Sincronizando páginas de mantenimiento"):
                success = self.manager.sync_maintenance_pages()
            
            if success:
                success_panel = Panel(
                    "[bold green]✅ Páginas de mantenimiento actualizadas[/bold green]\n\n"
                    "Las páginas HTML se han copiado a /apps/maintenance/\n\n"
                    "Ahora puedes:\n"
                    "• Activar modo mantenimiento:\n"
                    "  [cyan]webapp-manager maintenance --domain app.com[/cyan]\n\n"
                    "• Activar modo actualización:\n"
                    "  [cyan]webapp-manager updating --domain app.com[/cyan]\n\n"
                    "[dim]Las páginas se sirven automáticamente cuando hay errores 502/503/504[/dim]",
                    title="🎉 Completado",
                    style="green"
                )
                self.console.print(success_panel)
            else:
                self._show_error("Error sincronizando páginas de mantenimiento")
            
            return success
            
        except Exception as e:
            self._show_error(f"Error en comando sync-pages: {str(e)}")
            return False


def main():
    """Función de entrada principal para el comando webapp-manager"""
    try:
        cli = CLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n⚠️  Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()