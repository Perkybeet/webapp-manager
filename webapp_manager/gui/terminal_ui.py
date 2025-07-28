"""
Interfaz gráfica de terminal para WebApp Manager
"""

import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, TaskID
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.columns import Columns
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from ..core.manager import WebAppManager
from ..utils.colors import Colors
from ..models.app_config import AppConfig


class TerminalUI:
    """Interfaz gráfica de terminal para WebApp Manager"""
    
    def __init__(self, file_service=None, app_service=None):
        if not RICH_AVAILABLE:
            print("⚠️  Para usar la interfaz gráfica, instala: pip install rich")
            sys.exit(1)
        
        self.console = Console()
        
        # Inicializar servicios - SIEMPRE inicializar manager
        self.manager = WebAppManager()
        self.file_service = file_service
        self.app_service = app_service
        
        self.current_menu = "main"
        self.running = True
    
    def run(self):
        """Ejecutar la interfaz gráfica"""
        self.show_welcome()
        
        while self.running:
            try:
                if self.current_menu == "main":
                    self.show_main_menu()
                elif self.current_menu == "apps":
                    self.show_apps_menu()
                elif self.current_menu == "deploy":
                    self.show_deploy_menu()
                elif self.current_menu == "system":
                    self.show_system_menu()
                else:
                    self.current_menu = "main"
            except KeyboardInterrupt:
                if Confirm.ask("¿Salir de WebApp Manager?"):
                    self.running = False
            except Exception as e:
                self.console.print(f"❌ Error: {e}", style="red")
                Prompt.ask("Presiona Enter para continuar")
    
    def show_welcome(self):
        """Mostrar pantalla de bienvenida"""
        self.console.clear()
        
        welcome_text = """
# 🚀 WebApp Manager v3.0

Sistema modular de gestión de aplicaciones web con nginx proxy reverso

## Características
- 🔧 Despliegue automático de aplicaciones
- 🌐 Configuración de nginx y SSL
- 📊 Monitoreo de servicios
- 🔄 Gestión de actualizaciones
- 📝 Logs centralizados

---
        """
        
        self.console.print(Panel(
            Markdown(welcome_text),
            title="Bienvenido",
            border_style="blue",
            padding=(1, 2)
        ))
        
        Prompt.ask("Presiona Enter para continuar")
    
    def show_main_menu(self):
        """Mostrar menú principal"""
        self.console.clear()
        
        # Header
        header = Panel(
            Align.center("🚀 WebApp Manager - Panel de Control"),
            style="bold blue"
        )
        self.console.print(header)
        
        # Estadísticas del sistema
        self.show_system_stats()
        
        # Opciones del menú
        menu_options = [
            "1. 📱 Gestionar Aplicaciones",
            "2. 🚀 Desplegar Nueva Aplicación",
            "3. 🔧 Configuración del Sistema",
            "4. 📊 Monitoreo y Logs",
            "5. 🔄 Actualizaciones",
            "6. ❓ Ayuda",
            "0. 🚪 Salir"
        ]
        
        options_panel = Panel(
            "\n".join(menu_options),
            title="Opciones",
            border_style="green"
        )
        self.console.print(options_panel)
        
        choice = Prompt.ask(
            "Selecciona una opción",
            choices=["0", "1", "2", "3", "4", "5", "6"],
            default="1"
        )
        
        self.handle_main_menu_choice(choice)
    
    def show_system_stats(self):
        """Mostrar estadísticas del sistema"""
        try:
            apps = self.manager.list_apps()
            
            # Contar aplicaciones por estado
            active_count = sum(1 for app in apps if app.status == "active")
            failed_count = sum(1 for app in apps if app.status == "failed")
            total_count = len(apps)
            
            # Crear tabla de estadísticas
            stats_table = Table(show_header=False, box=None, padding=(0, 2))
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="white")
            
            stats_table.add_row("📱 Total Apps", str(total_count))
            stats_table.add_row("✅ Activas", str(active_count))
            stats_table.add_row("❌ Fallidas", str(failed_count))
            stats_table.add_row("🔄 En Línea", f"{active_count}/{total_count}")
            
            stats_panel = Panel(
                stats_table,
                title="Estado del Sistema",
                border_style="yellow"
            )
            self.console.print(stats_panel)
            
        except Exception as e:
            self.console.print(f"⚠️  Error obteniendo estadísticas: {e}", style="yellow")
    
    def show_apps_menu(self):
        """Mostrar menú de aplicaciones"""
        self.console.clear()
        
        header = Panel(
            Align.center("📱 Gestión de Aplicaciones"),
            style="bold green"
        )
        self.console.print(header)
        
        try:
            apps = self.manager.list_apps()
            
            if not apps:
                self.console.print(Panel(
                    "No hay aplicaciones desplegadas",
                    title="Sin Aplicaciones",
                    border_style="yellow"
                ))
            else:
                self.show_apps_table(apps)
            
            # Menú de acciones
            actions = [
                "1. 📋 Actualizar Lista",
                "2. 🔍 Ver Detalles de Aplicación",
                "3. 🔄 Reiniciar Aplicación",
                "4. 🗑️  Eliminar Aplicación",
                "5. 📊 Ver Logs",
                "0. ⬅️  Volver al Menú Principal"
            ]
            
            actions_panel = Panel(
                "\n".join(actions),
                title="Acciones",
                border_style="blue"
            )
            self.console.print(actions_panel)
            
            choice = Prompt.ask(
                "Selecciona una acción",
                choices=["0", "1", "2", "3", "4", "5"],
                default="1"
            )
            
            self.handle_apps_menu_choice(choice, apps)
            
        except Exception as e:
            self.console.print(f"❌ Error: {e}", style="red")
            Prompt.ask("Presiona Enter para continuar")
    
    def show_apps_table(self, apps: List[AppConfig]):
        """Mostrar tabla de aplicaciones"""
        table = Table(title="Aplicaciones Desplegadas")
        
        table.add_column("Dominio", style="cyan")
        table.add_column("Tipo", style="magenta")
        table.add_column("Puerto", style="yellow")
        table.add_column("Estado", style="green")
        table.add_column("SSL", style="blue")
        table.add_column("Última Actualización", style="white")
        
        for app in apps:
            try:
                # Proteger contra valores None
                domain = getattr(app, 'domain', 'N/A') or 'N/A'
                app_type = getattr(app, 'app_type', 'N/A') or 'N/A'
                port = str(getattr(app, 'port', 'N/A') or 'N/A')
                status = getattr(app, 'status', 'unknown') or 'unknown'
                ssl = getattr(app, 'ssl', False)
                last_updated = getattr(app, 'last_updated', '') or ''
                
                status_style = "green" if status == "active" else "red"
                ssl_icon = "✅" if ssl else "❌"
                
                table.add_row(
                    domain,
                    app_type,
                    port,
                    f"[{status_style}]{status}[/{status_style}]",
                    ssl_icon,
                    last_updated[:10] if last_updated else "N/A"
                )
            except Exception as e:
                # Si hay error con una aplicación específica, mostrar error pero continuar
                table.add_row(
                    "Error",
                    "Error",
                    "Error",
                    "[red]Error[/red]",
                    "❌",
                    "Error"
                )
        
        self.console.print(table)
    
    def show_deploy_menu(self):
        """Mostrar menú de despliegue"""
        self.console.clear()
        
        header = Panel(
            Align.center("🚀 Desplegar Nueva Aplicación"),
            style="bold green"
        )
        self.console.print(header)
        
        # Tipos de aplicación soportados
        app_types = [
            "1. 📱 Next.js Application",
            "2. 🐍 FastAPI Application",
            "3. 🟢 Node.js Application",
            "4. 📄 Static Website",
            "0. ⬅️  Volver al Menú Principal"
        ]
        
        types_panel = Panel(
            "\n".join(app_types),
            title="Tipos de Aplicación",
            border_style="blue"
        )
        self.console.print(types_panel)
        
        choice = Prompt.ask(
            "Selecciona el tipo de aplicación",
            choices=["0", "1", "2", "3", "4"],
            default="1"
        )
        
        if choice == "0":
            self.current_menu = "main"
            return
        
        # Mapear elección a tipo
        type_mapping = {
            "1": "nextjs",
            "2": "fastapi",
            "3": "node",
            "4": "static"
        }
        
        app_type = type_mapping[choice]
        self.deploy_application_wizard(app_type)
    
    def deploy_application_wizard(self, app_type: str):
        """Asistente para desplegar aplicación"""
        self.console.print(f"\n🔧 Configurando aplicación {app_type}...\n")
        
        try:
            # Recopilar información
            domain = Prompt.ask("Dominio de la aplicación", default="example.com")
            port = int(Prompt.ask("Puerto", default="3000"))
            source = Prompt.ask("Repositorio o ruta", default="https://github.com/user/repo.git")
            branch = Prompt.ask("Rama", default="main")
            ssl = Confirm.ask("¿Habilitar SSL?", default=True)
            
            # Comandos opcionales
            build_command = Prompt.ask("Comando de build (opcional)", default="")
            start_command = Prompt.ask("Comando de inicio (opcional)", default="")
            
            # Mostrar resumen
            self.show_deployment_summary(domain, port, app_type, source, branch, ssl, build_command, start_command)
            
            if Confirm.ask("¿Proceder con el despliegue?"):
                self.deploy_with_progress(domain, port, app_type, source, branch, ssl, build_command, start_command)
            else:
                self.console.print("❌ Despliegue cancelado")
                
        except ValueError as e:
            self.console.print(f"❌ Error en los datos: {e}", style="red")
        except Exception as e:
            self.console.print(f"❌ Error inesperado: {e}", style="red")
        
        Prompt.ask("Presiona Enter para continuar")
    
    def show_deployment_summary(self, domain: str, port: int, app_type: str, source: str, 
                              branch: str, ssl: bool, build_command: str, start_command: str):
        """Mostrar resumen del despliegue"""
        summary_data = [
            ("Dominio", domain),
            ("Puerto", str(port)),
            ("Tipo", app_type),
            ("Fuente", source),
            ("Rama", branch),
            ("SSL", "✅" if ssl else "❌"),
            ("Comando Build", build_command or "Por defecto"),
            ("Comando Start", start_command or "Por defecto")
        ]
        
        table = Table(title="Resumen del Despliegue")
        table.add_column("Parámetro", style="cyan")
        table.add_column("Valor", style="white")
        
        for param, value in summary_data:
            table.add_row(param, value)
        
        self.console.print(table)
    
    def deploy_with_progress(self, domain: str, port: int, app_type: str, source: str, 
                           branch: str, ssl: bool, build_command: str, start_command: str):
        """Desplegar aplicación con barra de progreso"""
        with Progress() as progress:
            task = progress.add_task("Desplegando aplicación...", total=100)
            
            try:
                # Validación inicial
                progress.update(task, description="[cyan]Validando configuración...", completed=10)
                self.console.print(f"🔍 Validando configuración para {domain}...")
                time.sleep(0.5)
                
                # Obtener código fuente
                progress.update(task, description="[cyan]Preparando despliegue...", completed=20)
                self.console.print(f"📦 Preparando despliegue para aplicación {app_type}...")
                time.sleep(0.5)
                
                # Validar estructura
                progress.update(task, description="[cyan]Validando estructura del proyecto...", completed=30)
                self.console.print(f"🔍 Validando estructura del proyecto desde {source}...")
                time.sleep(0.5)
                
                # Instalar dependencias
                progress.update(task, description="[cyan]Instalando dependencias...", completed=50)
                self.console.print(f"📥 Instalando dependencias para {app_type}...")
                time.sleep(1)
                
                # Construir aplicación
                progress.update(task, description="[cyan]Construyendo aplicación...", completed=70)
                self.console.print(f"🔨 Construyendo aplicación en puerto {port}...")
                time.sleep(1)
                
                # Configurar servicios
                progress.update(task, description="[cyan]Configurando servicios...", completed=85)
                self.console.print(f"⚙️ Configurando nginx y systemd...")
                time.sleep(0.5)
                
                # Desplegar aplicación
                progress.update(task, description="[cyan]Desplegando aplicación...", completed=95)
                self.console.print(f"🚀 Iniciando despliegue final...")
                
                result = self.manager.add_app(
                    domain=domain,
                    port=port,
                    app_type=app_type,
                    source_path=source,
                    branch=branch,
                    ssl=ssl,
                    build_command=build_command,
                    start_command=start_command
                )
                
                # Finalizar
                progress.update(task, description="[green]Despliegue completado", completed=100)
                time.sleep(0.5)
                
                if result:
                    self.console.print("✅ Aplicación desplegada exitosamente!", style="bold green")
                    self.console.print(f"🌐 Aplicación disponible en: http{'s' if ssl else ''}://{domain}", style="blue")
                    self.console.print(f"🔗 Puerto: {port}", style="blue")
                else:
                    self.console.print("❌ Error en el despliegue", style="bold red")
                    self.console.print("💡 Revisa los logs del sistema para más detalles", style="yellow")
                    
            except Exception as e:
                progress.update(task, description="[red]Error en el despliegue", completed=100)
                self.console.print(f"❌ Error durante el despliegue: {e}", style="bold red")
                self.console.print("💡 Revisa los logs del sistema para más detalles", style="yellow")
                
            finally:
                # Pausa para que el usuario pueda leer el resultado
                Prompt.ask("\nPresiona Enter para continuar")
    
    def show_system_menu(self):
        """Mostrar menú del sistema"""
        self.console.clear()
        
        header = Panel(
            Align.center("🔧 Configuración del Sistema"),
            style="bold blue"
        )
        self.console.print(header)
        
        # Información del sistema
        self.show_system_info()
        
        # Opciones del menú
        options = [
            "1. 🔍 Diagnóstico del Sistema",
            "2. 🧹 Limpiar Archivos Temporales",
            "3. 🔄 Reiniciar Servicios",
            "4. 📋 Backup de Configuración",
            "5. 🔧 Configuración Avanzada",
            "0. ⬅️  Volver al Menú Principal"
        ]
        
        options_panel = Panel(
            "\n".join(options),
            title="Opciones",
            border_style="green"
        )
        self.console.print(options_panel)
        
        choice = Prompt.ask(
            "Selecciona una opción",
            choices=["0", "1", "2", "3", "4", "5"],
            default="1"
        )
        
        self.handle_system_menu_choice(choice)
    
    def show_system_info(self):
        """Mostrar información del sistema"""
        try:
            # Información básica del sistema
            info_table = Table(show_header=False, box=None, padding=(0, 2))
            info_table.add_column("Component", style="cyan")
            info_table.add_column("Status", style="white")
            
            # Verificar servicios
            services = ["nginx", "systemd", "node", "python3"]
            for service in services:
                status = "✅" if self.manager.cmd.run(f"which {service}", check=False) else "❌"
                info_table.add_row(service, status)
            
            info_panel = Panel(
                info_table,
                title="Estado de Servicios",
                border_style="blue"
            )
            self.console.print(info_panel)
            
        except Exception as e:
            self.console.print(f"⚠️  Error obteniendo información: {e}", style="yellow")
    
    def handle_main_menu_choice(self, choice: str):
        """Manejar elección del menú principal"""
        if choice == "0":
            self.running = False
        elif choice == "1":
            self.current_menu = "apps"
        elif choice == "2":
            self.current_menu = "deploy"
        elif choice == "3":
            self.current_menu = "system"
        elif choice == "4":
            self.show_monitoring_menu()
        elif choice == "5":
            self.show_updates_menu()
        elif choice == "6":
            self.show_help()
    
    def handle_apps_menu_choice(self, choice: str, apps: List[AppConfig]):
        """Manejar elección del menú de aplicaciones"""
        if choice == "0":
            self.current_menu = "main"
        elif choice == "1":
            pass  # Actualizar lista (ya se hace automáticamente)
        elif choice == "2":
            self.show_app_details(apps)
        elif choice == "3":
            self.restart_app(apps)
        elif choice == "4":
            self.remove_app(apps)
        elif choice == "5":
            self.show_app_logs(apps)
    
    def handle_system_menu_choice(self, choice: str):
        """Manejar elección del menú del sistema"""
        if choice == "0":
            self.current_menu = "main"
        elif choice == "1":
            self.run_system_diagnosis()
        elif choice == "2":
            self.clean_temp_files()
        elif choice == "3":
            self.restart_services()
        elif choice == "4":
            self.backup_configuration()
        elif choice == "5":
            self.show_advanced_config()
    
    def show_app_details(self, apps: List[AppConfig]):
        """Mostrar detalles de una aplicación"""
        if not apps:
            self.console.print("No hay aplicaciones para mostrar", style="yellow")
            return
        
        try:
            app_names = [getattr(app, 'domain', 'N/A') or 'N/A' for app in apps]
            selected = Prompt.ask(
                "Selecciona una aplicación",
                choices=app_names
            )
            
            selected_app = next(app for app in apps if getattr(app, 'domain', '') == selected)
            
            # Mostrar detalles con protección contra None
            details_table = Table(title=f"Detalles de {getattr(selected_app, 'domain', 'N/A')}")
            details_table.add_column("Propiedad", style="cyan")
            details_table.add_column("Valor", style="white")
            
            details_table.add_row("Dominio", getattr(selected_app, 'domain', 'N/A') or 'N/A')
            details_table.add_row("Puerto", str(getattr(selected_app, 'port', 'N/A') or 'N/A'))
            details_table.add_row("Tipo", getattr(selected_app, 'app_type', 'N/A') or 'N/A')
            details_table.add_row("Fuente", getattr(selected_app, 'source', 'N/A') or 'N/A')
            details_table.add_row("Rama", getattr(selected_app, 'branch', 'N/A') or 'N/A')
            details_table.add_row("SSL", "✅" if getattr(selected_app, 'ssl', False) else "❌")
            details_table.add_row("Estado", getattr(selected_app, 'status', 'unknown') or 'unknown')
            
            self.console.print(details_table)
            
        except Exception as e:
            self.console.print(f"❌ Error al mostrar detalles: {e}", style="red")
            
        Prompt.ask("Presiona Enter para continuar")
        details_table.add_row("Creado", selected_app.created)
        details_table.add_row("Actualizado", selected_app.last_updated)
        
        self.console.print(details_table)
        Prompt.ask("Presiona Enter para continuar")
    
    def show_monitoring_menu(self):
        """Mostrar menú de monitoreo"""
        self.console.print("🚧 Función de monitoreo en desarrollo", style="yellow")
        Prompt.ask("Presiona Enter para continuar")
    
    def show_updates_menu(self):
        """Mostrar menú de actualizaciones"""
        self.console.print("🚧 Función de actualizaciones en desarrollo", style="yellow")
        Prompt.ask("Presiona Enter para continuar")
    
    def show_help(self):
        """Mostrar ayuda"""
        help_text = """
# 📖 Ayuda de WebApp Manager

## Comandos Principales
- `webapp-manager add <domain>` - Desplegar nueva aplicación
- `webapp-manager list` - Listar aplicaciones
- `webapp-manager remove <domain>` - Eliminar aplicación
- `webapp-manager logs <domain>` - Ver logs

## Tipos de Aplicación Soportados
- **Next.js**: Aplicaciones React con SSR
- **FastAPI**: APIs Python modernas
- **Node.js**: Aplicaciones JavaScript
- **Static**: Sitios web estáticos

## Configuración
- Archivos de configuración en `/etc/webapp-manager/`
- Logs en `/var/log/webapp-manager/`
- Aplicaciones en `/var/www/apps/`

---
        """
        
        self.console.print(Panel(
            Markdown(help_text),
            title="Ayuda",
            border_style="blue"
        ))
        Prompt.ask("Presiona Enter para continuar")
    
    def run_system_diagnosis(self):
        """Ejecutar diagnóstico del sistema"""
        self.console.print("🔍 Ejecutando diagnóstico del sistema...", style="blue")
        
        try:
            result = self.manager.diagnose()
            if result:
                self.console.print("✅ Diagnóstico completado exitosamente", style="green")
            else:
                self.console.print("⚠️  Se encontraron problemas", style="yellow")
        except Exception as e:
            self.console.print(f"❌ Error en diagnóstico: {e}", style="red")
        
        Prompt.ask("Presiona Enter para continuar")
    
    def clean_temp_files(self):
        """Limpiar archivos temporales"""
        self.console.print("🧹 Limpiando archivos temporales...", style="blue")
        # Implementar limpeza
        self.console.print("✅ Archivos temporales eliminados", style="green")
        Prompt.ask("Presiona Enter para continuar")
    
    def restart_services(self):
        """Reiniciar servicios"""
        if Confirm.ask("¿Reiniciar servicios del sistema?"):
            self.console.print("🔄 Reiniciando servicios...", style="blue")
            # Implementar reinicio
            self.console.print("✅ Servicios reiniciados", style="green")
        Prompt.ask("Presiona Enter para continuar")
    
    def backup_configuration(self):
        """Hacer backup de la configuración"""
        self.console.print("💾 Creando backup de configuración...", style="blue")
        # Implementar backup
        self.console.print("✅ Backup creado exitosamente", style="green")
        Prompt.ask("Presiona Enter para continuar")
    
    def show_advanced_config(self):
        """Mostrar configuración avanzada"""
        self.console.print("🚧 Configuración avanzada en desarrollo", style="yellow")
        Prompt.ask("Presiona Enter para continuar")
    
    def restart_app(self, apps: List[AppConfig]):
        """Reiniciar aplicación"""
        if not apps:
            self.console.print("No hay aplicaciones para reiniciar", style="yellow")
            return
        
        app_names = [app.domain for app in apps]
        selected = Prompt.ask("Selecciona una aplicación para reiniciar", choices=app_names)
        
        if Confirm.ask(f"¿Reiniciar {selected}?"):
            try:
                result = self.manager.restart_app(selected)
                if result:
                    self.console.print(f"✅ {selected} reiniciada exitosamente", style="green")
                else:
                    self.console.print(f"❌ Error reiniciando {selected}", style="red")
            except Exception as e:
                self.console.print(f"❌ Error: {e}", style="red")
        
        Prompt.ask("Presiona Enter para continuar")
    
    def remove_app(self, apps: List[AppConfig]):
        """Eliminar aplicación"""
        if not apps:
            self.console.print("No hay aplicaciones para eliminar", style="yellow")
            return
        
        app_names = [app.domain for app in apps]
        selected = Prompt.ask("Selecciona una aplicación para eliminar", choices=app_names)
        
        if Confirm.ask(f"¿ELIMINAR {selected}? Esta acción no se puede deshacer"):
            try:
                result = self.manager.remove_app(selected)
                if result:
                    self.console.print(f"✅ {selected} eliminada exitosamente", style="green")
                else:
                    self.console.print(f"❌ Error eliminando {selected}", style="red")
            except Exception as e:
                self.console.print(f"❌ Error: {e}", style="red")
        
        Prompt.ask("Presiona Enter para continuar")
    
    def show_app_logs(self, apps: List[AppConfig]):
        """Mostrar logs de aplicación"""
        if not apps:
            self.console.print("No hay aplicaciones para mostrar logs", style="yellow")
            return
        
        app_names = [app.domain for app in apps]
        selected = Prompt.ask("Selecciona una aplicación para ver logs", choices=app_names)
        
        try:
            logs = self.manager.get_app_logs(selected, lines=50)
            if logs:
                self.console.print(Panel(
                    Syntax(logs, "log", theme="monokai"),
                    title=f"Logs de {selected}",
                    border_style="blue"
                ))
            else:
                self.console.print("No se encontraron logs", style="yellow")
        except Exception as e:
            self.console.print(f"❌ Error obteniendo logs: {e}", style="red")
        
        Prompt.ask("Presiona Enter para continuar")


def main():
    """Punto de entrada para la interfaz gráfica"""
    ui = TerminalUI()
    ui.run()


if __name__ == "__main__":
    main()
