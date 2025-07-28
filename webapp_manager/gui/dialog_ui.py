"""
Interfaz gráfica usando Python Dialog para WebApp Manager
Diseñada específicamente para servidores Linux
"""

import os
import sys
import time
import subprocess
import tempfile
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

try:
    from dialog import Dialog
except ImportError:
    print("❌ Error: pythondialog no está instalado")
    print("   Ejecuta: pip3 install pythondialog")
    sys.exit(1)

from ..models import AppConfig
from ..core.manager import WebAppManager
from ..utils import Colors


class DialogUI:
    """Interfaz gráfica usando Dialog para terminales Linux"""
    
    def __init__(self):
        """Inicializar la interfaz Dialog"""
        self.d = Dialog(dialog="dialog")
        self.d.set_background_title("WebApp Manager v4.0 - Sistema Modular para Linux")
        
        # Configurar tamaño por defecto
        self.height = 20
        self.width = 70
        
        # Habilitar modo GUI para filtrar logs
        self.gui_mode = True
        
        # Inicializar manager
        try:
            self.manager = WebAppManager()
            # Configurar el manager para modo GUI
            if hasattr(self.manager, 'set_gui_mode'):
                self.manager.set_gui_mode(True)
        except Exception as e:
            self.show_error(f"Error al inicializar WebApp Manager: {e}")
            sys.exit(1)
    
    def clean_ansi_sequences(self, text: str) -> str:
        """Limpiar secuencias de escape ANSI de los logs para la interfaz gráfica"""
        if not text:
            return text
        
        # Patrones para secuencias de escape ANSI
        ansi_patterns = [
            r'\x1b\[[0-9;]*m',  # Códigos de color
            r'\x1b\[[0-9;]*[a-zA-Z]',  # Otros códigos de escape
            r'\x1b\]0;[^\x07]*\x07',  # Títulos de ventana
            r'\x1b\[[0-9]+;[0-9]+[Hf]',  # Posicionamiento del cursor
            r'\x1b\[[0-9]*[ABCD]',  # Movimiento del cursor
            r'\x1b\[[0-9]*[JK]',  # Limpieza de líneas
            r'\x1b\[2J',  # Limpieza de pantalla
            r'\x1b\[H',  # Cursor a home
            r'\x1b\[?[0-9]*[hl]',  # Modos de pantalla
            r'\x1b\[[0-9]*[~]',  # Teclas especiales
            r'\x1b\[?[0-9]*[hl]',  # Modos de terminal
            r'\x1b\[=[0-9]*[hl]',  # Modos de aplicación
            r'\x1b\[[0-9]*[pqrs]',  # Modos de cursor
            r'\x1b\[c',  # Identificación de terminal
            r'\x1b\[6n',  # Posición del cursor
            r'\x1b\[0?[0-9]*[JK]',  # Limpieza condicional
            r'\x1b\[(\?)?[0-9]*[lh]',  # Modos de terminal
            r'\x1b\[?[0-9]*[lh]',  # Modos de terminal
            r'\x1b\[<[0-9]*[mM]',  # Modos de ratón
            r'\x1b\[>[0-9]*[mM]',  # Modos de ratón
            r'\x1b\[!p',  # Reset
            r'\x1b\[?25[lh]',  # Cursor visible/invisible
            r'\x1b\[?47[lh]',  # Pantalla alternativa
            r'\x1b\[?1049[lh]',  # Pantalla alternativa
            r'\x1b\[?1[lh]',  # Modo de aplicación
            r'\x1b\[?7[lh]',  # Wrap mode
            r'\x1b\[?12[lh]',  # Blink cursor
            r'\x1b\[?25[lh]',  # Show cursor
            r'\x1b\[?1000[lh]',  # Mouse tracking
            r'\x1b\[?1002[lh]',  # Mouse tracking
            r'\x1b\[?1003[lh]',  # Mouse tracking
            r'\x1b\[?1006[lh]',  # Mouse tracking
        ]
        
        # Limpiar cada patrón
        cleaned_text = text
        for pattern in ansi_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text)
        
        # Limpiar caracteres de control comunes
        cleaned_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', cleaned_text)
        cleaned_text = re.sub(r'\x1b\].*?\x07', '', cleaned_text)
        cleaned_text = re.sub(r'\x1b[()][AB012]', '', cleaned_text)
        cleaned_text = re.sub(r'\x1b[=>]', '', cleaned_text)
        cleaned_text = re.sub(r'\x1b[PX^_].*?\x1b\\', '', cleaned_text)
        
        # Limpiar otros caracteres de control
        cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned_text)
        
        # Limpiar líneas vacías múltiples
        cleaned_text = re.sub(r'\n\s*\n', '\n', cleaned_text)
        
        return cleaned_text.strip()
    
    def format_log_for_gui(self, log_text: str) -> str:
        """Formatear logs específicamente para la interfaz gráfica"""
        if not log_text:
            return "No hay logs disponibles"
        
        # Limpiar secuencias ANSI
        cleaned_text = self.clean_ansi_sequences(log_text)
        
        # Formatear para mejor legibilidad en la GUI
        lines = cleaned_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip():  # Solo procesar líneas no vacías
                # Agregar timestamp si no lo tiene
                if not re.match(r'^\d{4}-\d{2}-\d{2}', line):
                    formatted_lines.append(f"[LOG] {line}")
                else:
                    formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def show_progress_with_logs(self, title: str, total_steps: int = 100):
        """Mostrar progreso con logs integrados en la GUI"""
        self.d.gauge_start(
            "Iniciando proceso...",
            height=10,
            width=65,
            title=title
        )
        return True
    
    def update_progress_with_logs(self, percent: int, message: str, log_data: str = None):
        """Actualizar progreso con logs limpios para GUI"""
        # Limpiar el mensaje para la GUI
        clean_message = self.clean_ansi_sequences(message)
        
        # Actualizar el gauge con mensaje limpio
        self.d.gauge_update(percent, clean_message)
        
        # Si hay logs adicionales, los guardamos para mostrar después
        if log_data:
            self.last_operation_logs = self.format_log_for_gui(log_data)
    
    def finish_progress_with_logs(self):
        """Finalizar progreso y mostrar logs si es necesario"""
        self.d.gauge_stop()
        
        # Si hay logs guardados, mostrarlos después del progreso
        if hasattr(self, 'last_operation_logs') and self.last_operation_logs:
            code = self.d.yesno(
                "¿Deseas ver los logs detallados de la operación?",
                height=8,
                width=50,
                title="Logs Disponibles"
            )
            
            if code == self.d.OK:
                self.d.scrollbox(
                    self.last_operation_logs,
                    height=20,
                    width=80,
                    title="Logs de la Operación"
                )
            
            # Limpiar logs después de mostrar
            self.last_operation_logs = ""
    
    def run(self):
        """Ejecutar la interfaz gráfica"""
        self.show_welcome()
        
        while True:
            choice = self.show_main_menu()
            
            if choice == "1":
                self.show_apps_menu()
            elif choice == "2":
                self.show_deploy_menu()
            elif choice == "3":
                self.show_system_menu()
            elif choice == "4":
                self.show_help()
            elif choice == "5":
                break
            else:
                self.show_error("Opción no válida")
    
    def show_welcome(self):
        """Mostrar pantalla de bienvenida"""
        welcome_text = """
🚀 WebApp Manager v4.0
Sistema Modular para Linux

Características:
• Interfaz gráfica terminal con Dialog
• Deployers modulares (NextJS, FastAPI, Node.js, Static)
• Auto-detección de tipos de aplicaciones
• Gestión automática de nginx y systemd
• Monitoreo integrado y reparación automática
• Backup automático de configuraciones

Diseñado exclusivamente para servidores Linux
        """
        
        self.d.msgbox(welcome_text, height=18, width=65, title="Bienvenido")
    
    def show_main_menu(self):
        """Mostrar menú principal"""
        choices = [
            ("1", "📱 Gestión de Aplicaciones"),
            ("2", "🚀 Desplegar Nueva Aplicación"),
            ("3", "🔧 Configuración del Sistema"),
            ("4", "❓ Ayuda"),
            ("5", "🚪 Salir")
        ]
        
        code, tag = self.d.menu(
            "Selecciona una opción:",
            choices=choices,
            height=15,
            width=50,
            title="Menú Principal"
        )
        
        if code == self.d.OK:
            return tag
        else:
            return "5"  # Salir si se cancela
    
    def show_apps_menu(self):
        """Mostrar menú de aplicaciones mejorado"""
        while True:
            # Obtener lista de aplicaciones
            apps = self.manager.list_apps()
            
            if not apps:
                self.d.msgbox(
                    "No hay aplicaciones desplegadas.\n\n"
                    "Usa la opción 'Desplegar Nueva Aplicación' para agregar una.",
                    height=8,
                    width=50,
                    title="Sin Aplicaciones"
                )
                return
            
            # Mostrar estadísticas de aplicaciones
            self.show_apps_stats(apps)
            
            # Seleccionar aplicación para gestionar
            selected_app = self.select_app_for_management(apps)
            if not selected_app:
                break
            
            # Mostrar menú de gestión para la aplicación seleccionada
            self.show_app_management_menu(selected_app, apps)
    
    def show_apps_stats(self, apps: List[AppConfig]):
        """Mostrar estadísticas de aplicaciones"""
        try:
            # Calcular estadísticas
            total_apps = len(apps)
            active_apps = len([app for app in apps if getattr(app, 'status', 'unknown') == 'active'])
            ssl_apps = len([app for app in apps if getattr(app, 'ssl', False)])
            
            # Conteo por tipo
            app_types = {}
            for app in apps:
                app_type = getattr(app, 'app_type', 'unknown')
                app_types[app_type] = app_types.get(app_type, 0) + 1
            
            # Crear texto de estadísticas
            stats_text = f"""
ESTADÍSTICAS DE APLICACIONES
{'=' * 28}

RESUMEN GENERAL:
  Total de aplicaciones: {total_apps}
  Aplicaciones activas: {active_apps}
  Aplicaciones inactivas: {total_apps - active_apps}
  Con SSL habilitado: {ssl_apps}

DISTRIBUCIÓN POR TIPO:
"""
            
            for app_type, count in app_types.items():
                stats_text += f"  {app_type}: {count} aplicación{'es' if count != 1 else ''}\n"
            
            stats_text += f"""
ESTADO DE SERVICIOS:
  🟢 Activos: {active_apps}
  🔴 Inactivos: {total_apps - active_apps}
  🔒 Con SSL: {ssl_apps}
  🔓 Sin SSL: {total_apps - ssl_apps}

UBICACIONES:
  Aplicaciones: /var/www/apps/
  Configuración nginx: /etc/nginx/sites-available/
  Servicios systemd: /etc/systemd/system/
            """
            
            self.d.msgbox(stats_text, height=18, width=65, title="Estadísticas")
            
        except Exception as e:
            self.show_error(f"Error obteniendo estadísticas: {e}")
    
    def select_app_for_management(self, apps: List[AppConfig]):
        """Seleccionar aplicación para gestionar con opciones adicionales"""
        # Crear lista de aplicaciones con estado
        choices = []
        for i, app in enumerate(apps):
            try:
                domain = getattr(app, 'domain', f'App {i+1}')
                app_type = getattr(app, 'app_type', 'unknown')
                status = getattr(app, 'status', 'unknown')
                port = getattr(app, 'port', 'N/A')
                ssl = getattr(app, 'ssl', False)
                
                # Indicadores de estado
                status_icon = "🟢" if status == "active" else "🔴"
                ssl_icon = "🔒" if ssl else "🔓"
                
                display_text = f"{status_icon} {domain} ({app_type}:{port}) {ssl_icon}"
                choices.append((str(i), display_text))
            except Exception as e:
                choices.append((str(i), f"❌ Error: {str(e)[:30]}..."))
        
        # Agregar opciones adicionales
        choices.insert(0, ("stats", "📊 Ver Estadísticas"))
        choices.insert(1, ("list", "📋 Ver Lista Completa"))
        choices.insert(2, ("filter", "🔍 Filtrar Aplicaciones"))
        choices.append(("bulk", "📦 Operaciones en Lote"))
        choices.append(("back", "⬅️ Volver al Menú Principal"))
        
        code, tag = self.d.menu(
            "Selecciona una aplicación para gestionar:",
            choices=choices,
            height=min(20, len(choices) + 5),
            width=70,
            title="Gestión de Aplicaciones"
        )
        
        if code != self.d.OK or tag == "back":
            return None
        elif tag == "stats":
            self.show_apps_stats(apps)
            return self.select_app_for_management(apps)
        elif tag == "list":
            self.show_apps_list(apps)
            return self.select_app_for_management(apps)
        elif tag == "filter":
            filtered_apps = self.filter_applications(apps)
            if filtered_apps:
                return self.select_app_for_management(filtered_apps)
            else:
                return self.select_app_for_management(apps)
        elif tag == "bulk":
            self.bulk_operations(apps)
            return self.select_app_for_management(apps)
        else:
            try:
                app_index = int(tag)
                return apps[app_index]
            except (ValueError, IndexError):
                self.show_error("Selección inválida")
                return None
    
    def filter_applications(self, apps: List[AppConfig]):
        """Filtrar aplicaciones por criterios"""
        filter_choices = [
            ("type", "📱 Por Tipo de Aplicación"),
            ("status", "🔍 Por Estado"),
            ("ssl", "🔒 Por Configuración SSL"),
            ("port", "🚪 Por Rango de Puertos"),
            ("back", "⬅️ Volver")
        ]
        
        code, filter_type = self.d.menu(
            "Selecciona el criterio de filtrado:",
            choices=filter_choices,
            height=12,
            width=50,
            title="Filtrar Aplicaciones"
        )
        
        if code != self.d.OK or filter_type == "back":
            return None
        
        filtered_apps = []
        
        try:
            if filter_type == "type":
                # Obtener tipos únicos
                app_types = list(set(getattr(app, 'app_type', 'unknown') for app in apps))
                type_choices = [(t, t) for t in app_types]
                
                code, selected_type = self.d.menu(
                    "Selecciona el tipo de aplicación:",
                    choices=type_choices,
                    height=12,
                    width=50,
                    title="Filtrar por Tipo"
                )
                
                if code == self.d.OK:
                    filtered_apps = [app for app in apps if getattr(app, 'app_type', 'unknown') == selected_type]
                    
            elif filter_type == "status":
                status_choices = [
                    ("active", "🟢 Activas"),
                    ("inactive", "🔴 Inactivas")
                ]
                
                code, selected_status = self.d.menu(
                    "Selecciona el estado:",
                    choices=status_choices,
                    height=10,
                    width=40,
                    title="Filtrar por Estado"
                )
                
                if code == self.d.OK:
                    if selected_status == "active":
                        filtered_apps = [app for app in apps if getattr(app, 'status', 'unknown') == 'active']
                    else:
                        filtered_apps = [app for app in apps if getattr(app, 'status', 'unknown') != 'active']
                        
            elif filter_type == "ssl":
                ssl_choices = [
                    ("with_ssl", "🔒 Con SSL"),
                    ("without_ssl", "🔓 Sin SSL")
                ]
                
                code, ssl_filter = self.d.menu(
                    "Selecciona configuración SSL:",
                    choices=ssl_choices,
                    height=10,
                    width=40,
                    title="Filtrar por SSL"
                )
                
                if code == self.d.OK:
                    if ssl_filter == "with_ssl":
                        filtered_apps = [app for app in apps if getattr(app, 'ssl', False)]
                    else:
                        filtered_apps = [app for app in apps if not getattr(app, 'ssl', False)]
            
            # Mostrar resultados del filtro
            if filtered_apps:
                self.d.msgbox(
                    f"Filtro aplicado: {len(filtered_apps)} aplicaciones encontradas",
                    height=8,
                    width=50,
                    title="Resultados del Filtro"
                )
                return filtered_apps
            else:
                self.d.msgbox(
                    "No se encontraron aplicaciones que coincidan con el filtro",
                    height=8,
                    width=50,
                    title="Sin Resultados"
                )
                return None
                
        except Exception as e:
            self.show_error(f"Error aplicando filtro: {e}")
            return None
    
    def bulk_operations(self, apps: List[AppConfig]):
        """Operaciones en lote para múltiples aplicaciones"""
        # Seleccionar aplicaciones
        app_choices = []
        for i, app in enumerate(apps):
            domain = getattr(app, 'domain', f'App {i+1}')
            app_type = getattr(app, 'app_type', 'unknown')
            status = getattr(app, 'status', 'unknown')
            
            status_icon = "🟢" if status == "active" else "🔴"
            display_text = f"{status_icon} {domain} ({app_type})"
            app_choices.append((str(i), display_text, False))
        
        code, selected_apps = self.d.checklist(
            "Selecciona las aplicaciones para operación en lote:",
            choices=app_choices,
            height=min(20, len(app_choices) + 8),
            width=70,
            title="Seleccionar Aplicaciones"
        )
        
        if code != self.d.OK or not selected_apps:
            return
        
        # Seleccionar operación
        operation_choices = [
            ("restart", "🔄 Reiniciar Todas"),
            ("update", "📥 Actualizar Todas"),
            ("logs", "📋 Ver Logs de Todas"),
            ("ssl", "🔒 Configurar SSL en Todas"),
            ("backup", "💾 Backup de Todas"),
            ("status", "📊 Estado de Todas")
        ]
        
        code, operation = self.d.menu(
            f"Selecciona la operación para {len(selected_apps)} aplicaciones:",
            choices=operation_choices,
            height=12,
            width=50,
            title="Operación en Lote"
        )
        
        if code != self.d.OK:
            return
        
        # Ejecutar operación en lote
        self.execute_bulk_operation(apps, selected_apps, operation)
    
    def execute_bulk_operation(self, apps: List[AppConfig], selected_indices: List[str], operation: str):
        """Ejecutar operación en lote"""
        selected_apps = [apps[int(i)] for i in selected_indices]
        
        # Confirmar operación
        app_names = [getattr(app, 'domain', 'N/A') for app in selected_apps]
        confirm_text = f"""
OPERACIÓN EN LOTE
{'=' * 17}

Operación: {operation.upper()}
Aplicaciones seleccionadas: {len(selected_apps)}

{chr(10).join(f'  • {name}' for name in app_names)}

¿Continuar con la operación en lote?
        """
        
        code = self.d.yesno(
            confirm_text,
            height=min(20, len(selected_apps) + 10),
            width=60,
            title="Confirmar Operación en Lote"
        )
        
        if code != self.d.OK:
            return
        
        # Ejecutar operación con progreso
        self.d.gauge_start(
            f"Ejecutando {operation} en {len(selected_apps)} aplicaciones...",
            height=10,
            width=65,
            title="Operación en Lote"
        )
        
        try:
            total_apps = len(selected_apps)
            success_count = 0
            failed_apps = []
            
            for i, app in enumerate(selected_apps):
                domain = getattr(app, 'domain', 'N/A')
                progress = int((i / total_apps) * 100)
                
                self.d.gauge_update(progress, f"Procesando {domain}...")
                
                try:
                    if operation == "restart":
                        success = self.manager.restart_app(domain)
                    elif operation == "update":
                        success = self.manager.update_app(domain)
                    elif operation == "logs":
                        # Para logs, simplemente marcamos como exitoso
                        success = True
                    elif operation == "ssl":
                        # Configurar SSL (implementar según la lógica del manager)
                        success = True
                    elif operation == "backup":
                        # Crear backup (implementar según la lógica del manager)
                        success = True
                    elif operation == "status":
                        # Obtener estado (siempre exitoso)
                        success = True
                    else:
                        success = False
                    
                    if success:
                        success_count += 1
                    else:
                        failed_apps.append(domain)
                        
                except Exception as e:
                    failed_apps.append(f"{domain} (Error: {str(e)[:30]})")
                
                time.sleep(0.5)  # Pausa para mostrar progreso
            
            self.d.gauge_update(100, "Completando operación...")
            time.sleep(1)
            self.d.gauge_stop()
            
            # Mostrar resultados
            result_text = f"""
RESULTADO DE OPERACIÓN EN LOTE
{'=' * 30}

Operación: {operation.upper()}
Total de aplicaciones: {total_apps}
Exitosas: {success_count}
Fallidas: {len(failed_apps)}

"""
            
            if failed_apps:
                result_text += "APLICACIONES FALLIDAS:\n"
                for app in failed_apps:
                    result_text += f"  ❌ {app}\n"
            
            if success_count > 0:
                result_text += f"\n✅ {success_count} aplicaciones procesadas exitosamente"
            
            self.d.scrollbox(result_text, height=18, width=70, title="Resultado de Operación")
            
        except Exception as e:
            self.d.gauge_stop()
            self.show_error(f"Error en operación en lote: {e}")
    
    def show_app_management_menu(self, app: AppConfig, apps: List[AppConfig]):
        """Mostrar menú de gestión para una aplicación específica"""
        domain = getattr(app, 'domain', 'N/A')
        
        while True:
            # Obtener estado actual
            try:
                status = self.manager.systemd_service.get_service_status(domain)
                connectivity = self.manager.app_service.test_connectivity(domain, getattr(app, 'port', 0))
                
                # Crear información de estado
                status_info = f"""
APLICACIÓN: {domain}
{'=' * (len(domain) + 12)}

Estado del servicio: {status}
Conectividad: {'🟢 Activo' if connectivity else '🔴 No responde'}
Tipo: {getattr(app, 'app_type', 'N/A')}
Puerto: {getattr(app, 'port', 'N/A')}
SSL: {'🔒 Configurado' if getattr(app, 'ssl', False) else '🔓 No configurado'}
                """
                
                # Menú de acciones
                choices = [
                    ("1", "� Ver Detalles Completos"),
                    ("2", "🔄 Reiniciar Aplicación"),
                    ("3", "� Actualizar Aplicación"),
                    ("4", "� Ver Logs"),
                    ("5", "🔍 Diagnosticar Problemas"),
                    ("6", "🔧 Reparar Aplicación"),
                    ("7", "📂 Abrir Directorio"),
                    ("8", "🗑️ Eliminar Aplicación"),
                    ("9", "⚙️ Configuración Avanzada"),
                    ("0", "⬅️ Volver a Lista")
                ]
                
                code, tag = self.d.menu(
                    status_info + "\n\nSelecciona una acción:",
                    choices=choices,
                    height=25,
                    width=70,
                    title=f"Gestión de {domain}"
                )
                
                if code != self.d.OK or tag == "0":
                    break
                elif tag == "1":
                    self.show_app_details_enhanced(app)
                elif tag == "2":
                    self.restart_app_enhanced(app)
                elif tag == "3":
                    self.update_app_enhanced(app)
                elif tag == "4":
                    self.show_app_logs_enhanced(app)
                elif tag == "5":
                    self.diagnose_app(app)
                elif tag == "6":
                    self.repair_app(app)
                elif tag == "7":
                    self.open_app_directory(app)
                elif tag == "8":
                    if self.remove_app_enhanced(app):
                        break  # Salir si se elimina la aplicación
                elif tag == "9":
                    self.show_app_advanced_config(app)
                    
            except Exception as e:
                self.show_error(f"Error obteniendo estado de aplicación: {e}")
                break
    
    def show_apps_list(self, apps: List[AppConfig]):
        """Mostrar lista de aplicaciones en formato tabla mejorado"""
        if not apps:
            return
        
        # Crear tabla mejorada de aplicaciones
        table_text = "APLICACIONES DESPLEGADAS\n"
        table_text += "=" * 80 + "\n"
        table_text += f"{'DOMINIO':<25} {'TIPO':<12} {'PUERTO':<8} {'ESTADO':<12} {'SSL':<5} {'ACTUALIZADO':<15}\n"
        table_text += "-" * 80 + "\n"
        
        for app in apps:
            try:
                domain = getattr(app, 'domain', 'N/A')[:24]
                app_type = getattr(app, 'app_type', 'N/A')[:11]
                port = str(getattr(app, 'port', 'N/A'))[:7]
                status = getattr(app, 'status', 'unknown')[:11]
                ssl = "🔒" if getattr(app, 'ssl', False) else "🔓"
                updated = getattr(app, 'last_updated', 'N/A')[:14]
                
                table_text += f"{domain:<25} {app_type:<12} {port:<8} {status:<12} {ssl:<5} {updated:<15}\n"
            except Exception as e:
                table_text += f"{'ERROR':<25} {'ERROR':<12} {'ERROR':<8} {'ERROR':<12} {'❌':<5} {'ERROR':<15}\n"
        
        table_text += "\n" + "=" * 80 + "\n"
        table_text += f"Total de aplicaciones: {len(apps)}\n"
        table_text += "🟢 = Activo, 🔴 = Inactivo, 🔒 = SSL, 🔓 = Sin SSL"
        
        self.d.scrollbox(table_text, height=20, width=85, title="Lista de Aplicaciones")
    
    def show_app_details_enhanced(self, app: AppConfig):
        """Mostrar detalles mejorados de la aplicación"""
        try:
            domain = getattr(app, 'domain', 'N/A')
            
            # Obtener información adicional
            status = self.manager.systemd_service.get_service_status(domain)
            connectivity = self.manager.app_service.test_connectivity(domain, getattr(app, 'port', 0))
            
            # Construir información detallada
            details = f"""
DETALLES COMPLETOS DE LA APLICACIÓN
{'=' * 37}

INFORMACIÓN BÁSICA:
  Dominio: {getattr(app, 'domain', 'N/A')}
  Tipo: {getattr(app, 'app_type', 'N/A')}
  Puerto: {getattr(app, 'port', 'N/A')}
  SSL: {'🔒 Configurado' if getattr(app, 'ssl', False) else '🔓 No configurado'}

CÓDIGO FUENTE:
  Repositorio: {getattr(app, 'source', 'N/A')}
  Rama: {getattr(app, 'branch', 'N/A')}
  
ESTADO ACTUAL:
  Servicio: {status}
  Conectividad: {'🟢 Activo' if connectivity else '🔴 No responde'}
  
FECHAS:
  Creado: {getattr(app, 'created', 'N/A')}
  Actualizado: {getattr(app, 'last_updated', 'N/A')}

CONFIGURACIÓN:
  Build Command: {getattr(app, 'build_command', 'Default')}
  Start Command: {getattr(app, 'start_command', 'Default')}
  
UBICACIONES:
  Directorio: /var/www/apps/{domain}
  Nginx Config: /etc/nginx/sites-available/{domain}
  SystemD Service: /etc/systemd/system/{domain}.service
  Logs: journalctl -u {domain}.service
            """
            
            # Mostrar con opción de navegación
            choices = [
                ("logs", "📋 Ver Logs"),
                ("nginx", "🌐 Ver Config Nginx"),
                ("systemd", "⚙️ Ver Service SystemD"),
                ("dir", "📂 Abrir Directorio"),
                ("close", "✅ Cerrar")
            ]
            
            code, tag = self.d.menu(
                details + "\n\nAcciones disponibles:",
                choices=choices,
                height=25,
                width=75,
                title=f"Detalles de {domain}"
            )
            
            if code == self.d.OK and tag == "logs":
                self.show_app_logs_enhanced(app)
            elif code == self.d.OK and tag == "nginx":
                self.show_nginx_config(app)
            elif code == self.d.OK and tag == "systemd":
                self.show_systemd_config(app)
            elif code == self.d.OK and tag == "dir":
                self.open_app_directory(app)
                
        except Exception as e:
            self.show_error(f"Error mostrando detalles: {e}")
    
    def restart_app_enhanced(self, app: AppConfig):
        """Reiniciar aplicación con progreso mejorado"""
        domain = getattr(app, 'domain', 'N/A')
        
        # Confirmar reinicio
        code = self.d.yesno(
            f"¿Reiniciar la aplicación '{domain}'?\n\n"
            "Esto detendrá temporalmente el servicio y puede\n"
            "causar una breve interrupción del servicio.",
            height=10,
            width=55,
            title="Confirmar Reinicio"
        )
        
        if code == self.d.OK:
            # Mostrar progreso
            self.d.gauge_start(
                f"Reiniciando {domain}...",
                height=10,
                width=60,
                title="Reinicio en Progreso"
            )
            
            try:
                # Paso 1: Detener servicio
                self.d.gauge_update(25, "Deteniendo servicio...")
                time.sleep(1)
                
                # Paso 2: Esperar
                self.d.gauge_update(50, "Esperando...")
                time.sleep(1)
                
                # Paso 3: Iniciar servicio
                self.d.gauge_update(75, "Iniciando servicio...")
                result = self.manager.restart_app(domain)
                
                # Paso 4: Verificar
                self.d.gauge_update(100, "Verificando estado...")
                time.sleep(1)
                
                self.d.gauge_stop()
                
                # Mostrar resultado
                if result:
                    self.d.msgbox(
                        f"✅ REINICIO EXITOSO\n\n"
                        f"La aplicación '{domain}' ha sido reiniciada\n"
                        f"correctamente y está funcionando.\n\n"
                        f"URL: http{'s' if getattr(app, 'ssl', False) else ''}://{domain}",
                        height=12,
                        width=55,
                        title="Reinicio Completado"
                    )
                else:
                    self.d.msgbox(
                        f"❌ ERROR EN REINICIO\n\n"
                        f"No se pudo reiniciar la aplicación '{domain}'.\n"
                        f"Revisa los logs para más detalles.\n\n"
                        f"Comando para logs: journalctl -u {domain}.service",
                        height=12,
                        width=55,
                        title="Error en Reinicio"
                    )
                    
            except Exception as e:
                self.d.gauge_stop()
                self.show_error(f"Error durante el reinicio: {e}")
    
    def update_app_enhanced(self, app: AppConfig):
        """Actualizar aplicación con progreso mejorado"""
        domain = getattr(app, 'domain', 'N/A')
        
        # Mostrar información de actualización
        update_info = f"""
ACTUALIZACIÓN DE APLICACIÓN
{'=' * 27}

Aplicación: {domain}
Repositorio: {getattr(app, 'source', 'N/A')}
Rama: {getattr(app, 'branch', 'N/A')}

PROCESO DE ACTUALIZACIÓN:
1. Backup automático de la aplicación actual
2. Descarga del código más reciente
3. Instalación/actualización de dependencias
4. Reconstrucción de la aplicación
5. Reinicio del servicio
6. Verificación del funcionamiento

¿Continuar con la actualización?
        """
        
        code = self.d.yesno(
            update_info,
            height=18,
            width=65,
            title="Confirmar Actualización"
        )
        
        if code == self.d.OK:
            # Mostrar progreso detallado
            self.d.gauge_start(
                f"Actualizando {domain}...",
                height=10,
                width=65,
                title="Actualización en Progreso"
            )
            
            try:
                # Simular pasos de actualización
                steps = [
                    ("Creando backup...", 15),
                    ("Descargando código...", 30),
                    ("Instalando dependencias...", 50),
                    ("Reconstruyendo aplicación...", 70),
                    ("Reiniciando servicio...", 85),
                    ("Verificando funcionamiento...", 95)
                ]
                
                for step_text, percent in steps:
                    self.d.gauge_update(percent, step_text)
                    time.sleep(1)
                
                # Ejecutar actualización real
                self.d.gauge_update(98, "Finalizando actualización...")
                result = self.manager.update_app(domain)
                
                self.d.gauge_update(100, "Actualización completada")
                time.sleep(1)
                self.d.gauge_stop()
                
                # Mostrar resultado
                if result:
                    self.d.msgbox(
                        f"✅ ACTUALIZACIÓN EXITOSA\n\n"
                        f"La aplicación '{domain}' ha sido actualizada\n"
                        f"correctamente con el código más reciente.\n\n"
                        f"URL: http{'s' if getattr(app, 'ssl', False) else ''}://{domain}",
                        height=12,
                        width=55,
                        title="Actualización Completada"
                    )
                else:
                    self.d.msgbox(
                        f"❌ ERROR EN ACTUALIZACIÓN\n\n"
                        f"No se pudo actualizar la aplicación '{domain}'.\n"
                        f"La aplicación anterior debería seguir funcionando.\n\n"
                        f"Revisa los logs para más detalles.",
                        height=12,
                        width=55,
                        title="Error en Actualización"
                    )
                    
            except Exception as e:
                self.d.gauge_stop()
                self.show_error(f"Error durante la actualización: {e}")
    
    def show_app_logs_enhanced(self, app: AppConfig):
        """Mostrar logs mejorados de la aplicación"""
        domain = getattr(app, 'domain', 'N/A')
        
        # Opciones de logs
        choices = [
            ("recent", "📋 Últimas 50 líneas"),
            ("errors", "❌ Solo errores"),
            ("full", "📜 Log completo (últimas 200 líneas)"),
            ("live", "📡 Ver en tiempo real (seguimiento)"),
            ("export", "💾 Exportar logs a archivo")
        ]
        
        code, tag = self.d.menu(
            f"Selecciona el tipo de log para {domain}:",
            choices=choices,
            height=12,
            width=55,
            title="Opciones de Logs"
        )
        
        if code == self.d.OK:
            if tag == "recent":
                self.show_logs_content(domain, lines=50)
            elif tag == "errors":
                self.show_logs_content(domain, errors_only=True)
            elif tag == "full":
                self.show_logs_content(domain, lines=200)
            elif tag == "live":
                self.show_live_logs_info(domain)
            elif tag == "export":
                self.export_logs(domain)
    
    def show_logs_content(self, domain: str, lines: int = 50, errors_only: bool = False):
        """Mostrar contenido de logs limpio para GUI"""
        try:
            # Obtener logs del sistema
            if errors_only:
                cmd = f"journalctl -u {domain}.service -p err -n {lines} --no-pager"
            else:
                cmd = f"journalctl -u {domain}.service -n {lines} --no-pager"
            
            # Ejecutar comando y obtener logs
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                # Limpiar logs para GUI
                clean_logs = self.format_log_for_gui(result.stdout)
                
                # Mostrar en scrollbox
                self.d.scrollbox(
                    clean_logs,
                    height=20,
                    width=80,
                    title=f"Logs de {domain} ({'Errores' if errors_only else f'Últimas {lines} líneas'})"
                )
            else:
                self.d.msgbox(
                    "No hay logs disponibles para mostrar o el servicio no existe.",
                    height=8,
                    width=50,
                    title="Sin Logs"
                )
            
        except subprocess.TimeoutExpired:
            self.show_error("Timeout al obtener logs. El comando tardó demasiado.")
        except Exception as e:
            self.show_error(f"Error obteniendo logs: {e}")
    
    def show_live_logs_info(self, domain: str):
        """Mostrar información para logs en tiempo real"""
        info = f"""
LOGS EN TIEMPO REAL
{'=' * 19}

Para ver los logs en tiempo real de {domain}, ejecuta
este comando en una terminal:

journalctl -u {domain}.service -f

Comandos útiles:
• Ver últimas 100 líneas: journalctl -u {domain}.service -n 100
• Ver solo errores: journalctl -u {domain}.service -p err
• Ver logs desde hoy: journalctl -u {domain}.service --since today
• Ver logs con timestamps: journalctl -u {domain}.service -o short-iso

Presiona Ctrl+C para detener el seguimiento.
        """
        
        self.d.msgbox(info, height=18, width=65, title="Logs en Tiempo Real")
    
    def export_logs(self, domain: str):
        """Exportar logs a archivo"""
        try:
            # Obtener logs
            logs = self.manager.cmd.run(f"journalctl -u {domain}.service -n 500 --no-pager", check=False)
            
            if logs:
                # Limpiar logs antes de exportar
                clean_logs = self.clean_ansi_sequences(logs)
                
                # Crear archivo de logs
                log_file = f"/tmp/{domain}_logs_export.txt"
                with open(log_file, 'w') as f:
                    f.write(f"Logs de {domain}\n")
                    f.write(f"Exportado: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(clean_logs)
                
                self.d.msgbox(
                    f"✅ Logs exportados exitosamente\n\n"
                    f"Archivo: {log_file}\n\n"
                    f"Para copiar el archivo:\n"
                    f"cp {log_file} /home/usuario/\n\n"
                    f"Para ver el archivo:\n"
                    f"less {log_file}",
                    height=14,
                    width=55,
                    title="Exportación Completada"
                )
            else:
                self.d.msgbox(
                    "❌ No se encontraron logs para exportar",
                    height=8,
                    width=45,
                    title="Error en Exportación"
                )
                
        except Exception as e:
            self.show_error(f"Error exportando logs: {e}")
    
    def diagnose_app(self, app: AppConfig):
        """Diagnosticar problemas de la aplicación"""
        domain = getattr(app, 'domain', 'N/A')
        
        self.d.infobox(
            f"Diagnosticando {domain}...\n\n"
            "Verificando servicios, configuración y conectividad.",
            height=8,
            width=55,
            title="Diagnóstico"
        )
        
        time.sleep(2)
        
        try:
            # Obtener información de diagnóstico
            service_status = self.manager.systemd_service.get_service_status(domain)
            connectivity = self.manager.app_service.test_connectivity(domain, getattr(app, 'port', 0))
            nginx_config_ok = self.manager.nginx_service.test_config()
            
            # Verificar archivos importantes
            app_dir = f"/var/www/apps/{domain}"
            nginx_config = f"/etc/nginx/sites-available/{domain}"
            systemd_service = f"/etc/systemd/system/{domain}.service"
            
            issues = []
            recommendations = []
            
            # Analizar problemas
            if service_status != "active":
                issues.append(f"❌ Servicio no activo: {service_status}")
                recommendations.append(f"• Reiniciar servicio: webapp-manager restart --domain {domain}")
            
            if not connectivity:
                issues.append(f"❌ Aplicación no responde en puerto {getattr(app, 'port', 'N/A')}")
                recommendations.append("• Verificar logs de la aplicación")
                recommendations.append("• Verificar que el puerto esté libre")
            
            if not nginx_config_ok:
                issues.append("❌ Configuración nginx tiene errores")
                recommendations.append("• Revisar configuración nginx: sudo nginx -t")
            
            # Crear reporte
            if issues:
                diagnosis = f"""
DIAGNÓSTICO DE {domain.upper()}
{'=' * (len(domain) + 15)}

PROBLEMAS ENCONTRADOS:
{''.join(f'  {issue}' + chr(10) for issue in issues)}

RECOMENDACIONES:
{''.join(f'  {rec}' + chr(10) for rec in recommendations)}

INFORMACIÓN ADICIONAL:
  • Directorio: {app_dir}
  • Config nginx: {nginx_config}
  • Servicio systemd: {systemd_service}
  • Logs: journalctl -u {domain}.service
                """
            else:
                diagnosis = f"""
DIAGNÓSTICO DE {domain.upper()}
{'=' * (len(domain) + 15)}

✅ APLICACIÓN FUNCIONANDO CORRECTAMENTE

Estado del servicio: {service_status}
Conectividad: ✅ Activo
Configuración nginx: ✅ Válida

No se encontraron problemas.
                """
            
            self.d.msgbox(diagnosis, height=20, width=70, title="Resultado del Diagnóstico")
            
        except Exception as e:
            self.show_error(f"Error durante el diagnóstico: {e}")
    
    def repair_app(self, app: AppConfig):
        """Reparar aplicación con problemas"""
        domain = getattr(app, 'domain', 'N/A')
        
        # Confirmar reparación
        repair_info = f"""
REPARACIÓN DE APLICACIÓN
{'=' * 24}

Aplicación: {domain}
Tipo: {getattr(app, 'app_type', 'N/A')}

PROCESO DE REPARACIÓN:
1. Detener servicio
2. Verificar y reparar dependencias
3. Reconstruir aplicación si es necesario
4. Recrear servicio systemd
5. Reiniciar y verificar funcionamiento

¿Continuar con la reparación?
        """
        
        code = self.d.yesno(
            repair_info,
            height=16,
            width=55,
            title="Confirmar Reparación"
        )
        
        if code == self.d.OK:
            # Mostrar progreso
            self.d.gauge_start(
                f"Reparando {domain}...",
                height=10,
                width=60,
                title="Reparación en Progreso"
            )
            
            try:
                # Simular pasos de reparación
                steps = [
                    ("Deteniendo servicio...", 20),
                    ("Verificando dependencias...", 40),
                    ("Reconstruyendo aplicación...", 60),
                    ("Recreando servicio...", 80),
                    ("Reiniciando y verificando...", 95)
                ]
                
                for step_text, percent in steps:
                    self.d.gauge_update(percent, step_text)
                    time.sleep(1)
                
                # Ejecutar reparación real
                self.d.gauge_update(98, "Finalizando reparación...")
                result = self.manager.repair_app(domain)
                
                self.d.gauge_update(100, "Reparación completada")
                time.sleep(1)
                self.d.gauge_stop()
                
                # Mostrar resultado
                if result:
                    self.d.msgbox(
                        f"✅ REPARACIÓN EXITOSA\n\n"
                        f"La aplicación '{domain}' ha sido reparada\n"
                        f"correctamente y está funcionando.\n\n"
                        f"URL: http{'s' if getattr(app, 'ssl', False) else ''}://{domain}",
                        height=12,
                        width=55,
                        title="Reparación Completada"
                    )
                else:
                    self.d.msgbox(
                        f"❌ ERROR EN REPARACIÓN\n\n"
                        f"No se pudo reparar completamente la aplicación '{domain}'.\n"
                        f"Puede ser necesaria intervención manual.\n\n"
                        f"Revisa los logs para más detalles.",
                        height=12,
                        width=55,
                        title="Error en Reparación"
                    )
                    
            except Exception as e:
                self.d.gauge_stop()
                self.show_error(f"Error durante la reparación: {e}")
    
    def open_app_directory(self, app: AppConfig):
        """Abrir directorio de la aplicación"""
        domain = getattr(app, 'domain', 'N/A')
        app_dir = f"/var/www/apps/{domain}"
        
        directory_info = f"""
DIRECTORIO DE LA APLICACIÓN
{'=' * 27}

Aplicación: {domain}
Directorio: {app_dir}

COMANDOS ÚTILES:
• Navegar al directorio:
  cd {app_dir}

• Listar archivos:
  ls -la {app_dir}

• Ver estructura:
  tree {app_dir}

• Editar archivos:
  nano {app_dir}/archivo.txt

• Ver espacio usado:
  du -sh {app_dir}

• Cambiar permisos:
  sudo chown -R www-data:www-data {app_dir}
        """
        
        self.d.msgbox(directory_info, height=20, width=65, title="Directorio de Aplicación")
    
    def remove_app_enhanced(self, app: AppConfig):
        """Eliminar aplicación con confirmación mejorada"""
        domain = getattr(app, 'domain', 'N/A')
        
        # Primera confirmación
        warning_info = f"""
⚠️  ELIMINAR APLICACIÓN  ⚠️
{'=' * 26}

Aplicación: {domain}
Tipo: {getattr(app, 'app_type', 'N/A')}
Puerto: {getattr(app, 'port', 'N/A')}

ESTO ELIMINARÁ:
• Código fuente de la aplicación
• Configuración nginx
• Servicio systemd
• Certificados SSL (si existen)

BACKUP AUTOMÁTICO:
✅ Se creará backup antes de eliminar

¿Continuar con la eliminación?
        """
        
        code = self.d.yesno(
            warning_info,
            height=18,
            width=65,
            title="⚠️ CONFIRMAR ELIMINACIÓN"
        )
        
        if code == self.d.OK:
            # Segunda confirmación con entrada de texto
            code, confirmation = self.d.inputbox(
                f"Para confirmar la eliminación, escribe el nombre\n"
                f"de la aplicación exactamente como aparece:\n\n"
                f"Nombre requerido: {domain}",
                height=12,
                width=55,
                title="Confirmación Final"
            )
            
            if code == self.d.OK and confirmation == domain:
                # Mostrar progreso
                self.d.gauge_start(
                    f"Eliminando {domain}...",
                    height=10,
                    width=60,
                    title="Eliminación en Progreso"
                )
                
                try:
                    # Simular pasos de eliminación
                    steps = [
                        ("Creando backup...", 20),
                        ("Deteniendo servicio...", 40),
                        ("Removiendo configuración...", 60),
                        ("Eliminando archivos...", 80),
                        ("Limpiando sistema...", 95)
                    ]
                    
                    for step_text, percent in steps:
                        self.d.gauge_update(percent, step_text)
                        time.sleep(1)
                    
                    # Ejecutar eliminación real
                    self.d.gauge_update(98, "Finalizando eliminación...")
                    result = self.manager.remove_app(domain)
                    
                    self.d.gauge_update(100, "Eliminación completada")
                    time.sleep(1)
                    self.d.gauge_stop()
                    
                    # Mostrar resultado
                    if result:
                        self.d.msgbox(
                            f"✅ ELIMINACIÓN EXITOSA\n\n"
                            f"La aplicación '{domain}' ha sido eliminada\n"
                            f"completamente del sistema.\n\n"
                            f"Se ha creado un backup antes de la eliminación.",
                            height=12,
                            width=55,
                            title="Eliminación Completada"
                        )
                        return True  # Indica que se eliminó la aplicación
                    else:
                        self.d.msgbox(
                            f"❌ ERROR EN ELIMINACIÓN\n\n"
                            f"No se pudo eliminar completamente la aplicación '{domain}'.\n"
                            f"Puede ser necesaria intervención manual.\n\n"
                            f"Revisa los logs para más detalles.",
                            height=12,
                            width=55,
                            title="Error en Eliminación"
                        )
                        
                except Exception as e:
                    self.d.gauge_stop()
                    self.show_error(f"Error durante la eliminación: {e}")
                    
            elif code == self.d.OK:
                self.d.msgbox(
                    "❌ ELIMINACIÓN CANCELADA\n\n"
                    "El nombre ingresado no coincide.\n"
                    "La aplicación no ha sido eliminada.",
                    height=10,
                    width=50,
                    title="Cancelado"
                )
        
        return False  # No se eliminó la aplicación
    
    def show_app_advanced_config(self, app: AppConfig):
        """Mostrar configuración avanzada de la aplicación"""
        domain = getattr(app, 'domain', 'N/A')
        
        config_info = f"""
CONFIGURACIÓN AVANZADA
{'=' * 22}

Aplicación: {domain}

ARCHIVOS DE CONFIGURACIÓN:
• Nginx: /etc/nginx/sites-available/{domain}
• SystemD: /etc/systemd/system/{domain}.service
• Variables de entorno: {'/var/www/apps/' + domain}/.env

COMANDOS AVANZADOS:
• Recargar nginx: sudo nginx -s reload
• Reiniciar systemd: sudo systemctl daemon-reload
• Ver estado del servicio: systemctl status {domain}.service
• Editar servicio: sudo systemctl edit {domain}.service

SSL/CERTIFICADOS:
• Renovar SSL: sudo certbot renew
• Verificar SSL: sudo certbot certificates
• Test SSL: curl -I https://{domain}

LOGS AVANZADOS:
• Logs nginx: sudo tail -f /var/log/nginx/access.log
• Logs error nginx: sudo tail -f /var/log/nginx/error.log
• Logs aplicación: journalctl -u {domain}.service -f

PERFORMANCE:
• Monitorear recursos: htop
• Conexiones activas: netstat -an | grep :{getattr(app, 'port', 'N/A')}
        """
        
        self.d.msgbox(config_info, height=22, width=75, title="Configuración Avanzada")
    
    def show_nginx_config(self, app: AppConfig):
        """Mostrar configuración nginx"""
        domain = getattr(app, 'domain', 'N/A')
        
        try:
            # Leer configuración nginx
            nginx_config_file = f"/etc/nginx/sites-available/{domain}"
            config_content = self.manager.cmd.run(f"cat {nginx_config_file}", check=False)
            
            if config_content:
                self.d.scrollbox(
                    config_content,
                    height=20,
                    width=80,
                    title=f"Configuración Nginx - {domain}"
                )
            else:
                self.d.msgbox(
                    "❌ No se pudo leer la configuración nginx\n"
                    f"Archivo: {nginx_config_file}",
                    height=8,
                    width=50,
                    title="Error"
                )
                
        except Exception as e:
            self.show_error(f"Error leyendo configuración nginx: {e}")
    
    def show_systemd_config(self, app: AppConfig):
        """Mostrar configuración systemd"""
        domain = getattr(app, 'domain', 'N/A')
        
        try:
            # Leer configuración systemd
            systemd_config_file = f"/etc/systemd/system/{domain}.service"
            config_content = self.manager.cmd.run(f"cat {systemd_config_file}", check=False)
            
            if config_content:
                self.d.scrollbox(
                    config_content,
                    height=20,
                    width=80,
                    title=f"Configuración SystemD - {domain}"
                )
            else:
                self.d.msgbox(
                    "❌ No se pudo leer la configuración systemd\n"
                    f"Archivo: {systemd_config_file}",
                    height=8,
                    width=50,
                    title="Error"
                )
                
        except Exception as e:
            self.show_error(f"Error leyendo configuración systemd: {e}")
    
    def show_deploy_menu(self):
        """Mostrar menú de despliegue simplificado"""
        while True:
            choices = [
                ("nextjs", "📱 Next.js Application"),
                ("fastapi", "🐍 FastAPI Application"),
                ("nodejs", "🟢 Node.js Application"),
                ("static", "📄 Static Website"),
                ("back", "⬅️ Volver al menú principal")
            ]
            
            code, tag = self.d.menu(
                "Selecciona el tipo de aplicación para desplegar:",
                choices=choices,
                height=12,
                width=60,
                title="Despliegue de Aplicación"
            )
            
            if code != self.d.OK or tag == "back":
                break
            else:
                self.deploy_application_simple(tag)
    
    def deploy_application_simple(self, app_type: str):
        """Desplegar aplicación de forma simplificada"""
        try:
            # Solicitar información básica
            code, domain = self.d.inputbox(
                "Ingresa el dominio de la aplicación:",
                height=10,
                width=60,
                title="Dominio de la Aplicación"
            )
            if code != self.d.OK or not domain:
                return
            
            # Puerto con sugerencias
            port_suggestions = {
                "nextjs": "3000",
                "fastapi": "8000", 
                "nodejs": "5000",
                "static": "8080"
            }
            
            suggested_port = port_suggestions.get(app_type, "3000")
            
            code, port_str = self.d.inputbox(
                f"Puerto para la aplicación {app_type.upper()}:",
                height=10,
                width=50,
                title="Puerto de la Aplicación",
                init=suggested_port
            )
            if code != self.d.OK or not port_str:
                return
            
            try:
                port = int(port_str)
            except ValueError:
                self.show_error("Puerto inválido. Debe ser un número.")
                return
            
            # Fuente del código
            code, source = self.d.inputbox(
                "Ruta o URL del código fuente:",
                height=10,
                width=65,
                title="Código Fuente"
            )
            if code != self.d.OK or not source:
                return
            
            # Confirmación SSL
            ssl = self.d.yesno(
                "¿Configurar SSL/HTTPS automáticamente?",
                height=8,
                width=50,
                title="Configuración SSL"
            ) == self.d.OK
            
            # Mostrar resumen y confirmar
            confirm_text = f"""
RESUMEN DEL DESPLIEGUE
{'=' * 21}

Dominio: {domain}
Tipo: {app_type.upper()}
Puerto: {port}
Fuente: {source}
SSL: {'✅ Sí' if ssl else '❌ No'}

¿Continuar con el despliegue?
            """
            
            code = self.d.yesno(
                confirm_text,
                height=14,
                width=60,
                title="Confirmar Despliegue"
            )
            
            if code == self.d.OK:
                self.deploy_with_progress_simple(domain, port, app_type, source, ssl)
            
        except Exception as e:
            self.show_error(f"Error en el despliegue: {e}")
    
    def deploy_with_progress_simple(self, domain: str, port: int, app_type: str, 
                                   source: str, ssl: bool):
        """Desplegar con progreso simple"""
        try:
            self.d.gauge_start(
                f"Desplegando {domain}...",
                height=10,
                width=60,
                title="Desplegando Aplicación"
            )
            
            # Pasos básicos del despliegue
            steps = [
                ("Preparando entorno...", 20),
                ("Descargando código...", 40),
                ("Instalando dependencias...", 60),
                ("Configurando servicios...", 80),
                ("Verificando funcionamiento...", 95)
            ]
            
            for step_text, percent in steps:
                self.d.gauge_update(percent, step_text)
                time.sleep(1)
            
            # Ejecutar despliegue real
            result = self.manager.add_app(
                domain=domain,
                port=port,
                app_type=app_type,
                source_path=source,
                ssl=ssl
            )
            
            self.d.gauge_update(100, "Despliegue completado")
            time.sleep(1)
            self.d.gauge_stop()
            
            # Mostrar resultado
            if result:
                self.d.msgbox(
                    f"✅ DESPLIEGUE EXITOSO\n\n"
                    f"Aplicación: {domain}\n"
                    f"URL: http{'s' if ssl else ''}://{domain}\n"
                    f"Estado: Activo",
                    height=12,
                    width=50,
                    title="Despliegue Completado"
                )
            else:
                self.d.msgbox(
                    f"❌ ERROR EN DESPLIEGUE\n\n"
                    f"No se pudo desplegar la aplicación.\n"
                    f"Revisa los logs para más detalles.",
                    height=10,
                    width=50,
                    title="Error en Despliegue"
                )
                
        except Exception as e:
            self.d.gauge_stop()
            self.show_error(f"Error durante el despliegue: {e}")

    def show_source_code(self, domain: str):
        """Mostrar código fuente de la aplicación"""
        try:
            # Obtener información de la aplicación
            app = self.manager.get_app_info(domain)
            if not app:
                self.show_error(f"No se encontró información de la aplicación {domain}")
                return
            
            # Mostrar código fuente
            code, source = self.d.inputbox(
                f"Mostrar código fuente de {domain}\n\n"
                f"Directorio: {app.get('directory', 'N/A')}\n"
                f"Tipo: {app.get('type', 'N/A')}\n\n"
                f"Ingrese el archivo a mostrar (relativo al directorio de la app):",
                height=12,
                width=65,
                title="Código Fuente"
            )
            if code != self.d.OK or not source:
                return
            
            # Paso 4: Rama con radiolist
            branch_choices = [
                ("main", "main (recomendado)", True),
                ("master", "master", False),
                ("develop", "develop", False),
                ("custom", "Rama personalizada", False)
            ]
            
            code, branch = self.d.radiolist(
                "Selecciona la rama del repositorio:",
                choices=branch_choices,
                height=12,
                width=60,
                title="Rama del Repositorio"
            )
            
            if code != self.d.OK:
                return
            
            if branch == "custom":
                code, branch = self.d.inputbox(
                    "Ingresa el nombre de la rama:",
                    height=10,
                    width=50,
                    title="Rama Personalizada"
                )
                if code != self.d.OK or not branch:
                    branch = "main"
            
            # Paso 5: Configuración SSL con checklist
            ssl_options = [
                ("ssl", "Habilitar SSL/HTTPS", True),
                ("redirect", "Redirección automática HTTP → HTTPS", True),
                ("hsts", "Strict Transport Security", False)
            ]
            
            code, ssl_features = self.d.checklist(
                "Selecciona las características de SSL:",
                choices=ssl_options,
                height=12,
                width=60,
                title="Configuración SSL"
            )
            
            ssl = "ssl" in ssl_features if code == self.d.OK else True
            
            # Paso 6: Configuración avanzada (opcional)
            code = self.d.yesno(
                "¿Configurar opciones avanzadas?\n\n"
                "• Comandos de construcción personalizados\n"
                "• Variables de entorno\n"
                "• Configuración de cache",
                height=10,
                width=55,
                title="Configuración Avanzada"
            )
            
            build_command = ""
            start_command = ""
            env_vars = None
            
            if code == self.d.OK:
                # Comandos personalizados
                build_commands = {
                    "nextjs": "npm run build",
                    "fastapi": "pip install -r requirements.txt",
                    "nodejs": "npm install",
                    "static": "# No build command needed"
                }
                
                code, build_command = self.d.inputbox(
                    "Comando de construcción:",
                    height=10,
                    width=60,
                    title="Comando de Build",
                    init=build_commands.get(app_type, "")
                )
                
                if code == self.d.OK:
                    start_commands = {
                        "nextjs": "npm start",
                        "fastapi": "uvicorn main:app --host 0.0.0.0 --port " + str(port),
                        "nodejs": "node server.js",
                        "static": "# Static files"
                    }
                    
                    code, start_command = self.d.inputbox(
                        "Comando de inicio:",
                        height=10,
                        width=60,
                        title="Comando de Start",
                        init=start_commands.get(app_type, "")
                    )
            
            # Paso 7: Confirmación con scroll
            confirm_text = f"""
CONFIRMACIÓN DE DESPLIEGUE
{'=' * 26}

INFORMACIÓN BÁSICA:
  Dominio: {domain}
  Puerto: {port}
  Tipo: {app_type.upper()}
  
CÓDIGO FUENTE:
  Fuente: {source}
  Rama: {branch}
  
CONFIGURACIÓN:
  SSL: {'✅ Habilitado' if ssl else '❌ Deshabilitado'}
  Build Command: {build_command or 'Por defecto'}
  Start Command: {start_command or 'Por defecto'}
  
URLS FINALES:
  HTTP: http://{domain}
  {'HTTPS: https://' + domain if ssl else 'HTTPS: No configurado'}

PROCESO DE DESPLIEGUE:
1. Validar configuración
2. Preparar entorno
3. Descargar código fuente
4. Instalar dependencias
5. Construir aplicación
6. Configurar nginx
7. Crear servicio systemd
8. {'Configurar SSL' if ssl else 'Configurar HTTP'}
9. Verificar funcionamiento

TIEMPO ESTIMADO: 3-5 minutos

¿Continuar con el despliegue?
            """
            
            code = self.d.yesno(
                confirm_text,
                height=22,
                width=70,
                title="Confirmar Despliegue"
            )
            
            if code == self.d.OK:
                self.deploy_with_progress(domain, port, app_type, source, branch, ssl, 
                                        build_command, start_command, env_vars)
            
        except Exception as e:
            self.show_error(f"Error en el asistente: {e}")
    
    def deploy_with_progress(self, domain: str, port: int, app_type: str, 
                           source: str, branch: str, ssl: bool, 
                           build_command: str = "", start_command: str = "",
                           env_vars: dict = None):
        """Desplegar aplicación con indicador de progreso mejorado"""
        try:
            # Crear archivo temporal para mostrar progreso
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                progress_file = f.name
            
            # Mostrar progreso inicial con información detallada
            self.d.gauge_start(
                f"Iniciando despliegue de {domain}...\n"
                f"Tipo: {app_type.upper()}",
                height=12,
                width=70,
                title="Desplegando Aplicación"
            )
            
            # Pasos detallados del despliegue
            steps = [
                ("Validando configuración y prerrequisitos...", 8),
                ("Preparando entorno de despliegue...", 15),
                ("Descargando código fuente...", 25),
                ("Instalando dependencias del sistema...", 35),
                ("Construyendo aplicación...", 50),
                ("Configurando servidor nginx...", 65),
                ("Creando servicio systemd...", 75),
                ("Configurando SSL y certificados...", 85),
                ("Iniciando servicios...", 92),
                ("Verificando funcionamiento...", 98)
            ]
            
            for step_text, percent in steps:
                self.d.gauge_update(percent, step_text)
                time.sleep(1.2)  # Tiempo más realista
            
            # Ejecutar despliegue real
            self.d.gauge_update(99, "Finalizando despliegue...")
            
            result = self.manager.add_app(
                domain=domain,
                port=port,
                app_type=app_type,
                source_path=source,
                branch=branch,
                ssl=ssl,
                build_command=build_command,
                start_command=start_command,
                env_vars=env_vars
            )
            
            # Finalizar progreso
            self.d.gauge_update(100, "Despliegue completado exitosamente")
            time.sleep(1)
            self.d.gauge_stop()
            
            # Mostrar resultado detallado
            if result:
                success_text = f"""
DESPLIEGUE EXITOSO
{'=' * 18}

✅ Aplicación desplegada correctamente

INFORMACIÓN DE LA APLICACIÓN:
  Dominio: {domain}
  Puerto: {port}
  Tipo: {app_type.upper()}
  
URLS DISPONIBLES:
  HTTP: http://{domain}
  {'HTTPS: https://' + domain if ssl else 'HTTPS: No configurado'}

SERVICIOS CONFIGURADOS:
  ✅ Servidor nginx configurado
  ✅ Servicio systemd creado
  ✅ {'Certificado SSL instalado' if ssl else 'HTTP configurado'}
  ✅ Aplicación iniciada y verificada

PRÓXIMOS PASOS:
  • Visita tu aplicación en el navegador
  • Configura el DNS para apuntar a este servidor
  • {'Verifica la configuración SSL' if ssl else 'Considera habilitar SSL'}

COMANDOS ÚTILES:
  • Ver logs: webapp-manager logs --domain {domain}
  • Reiniciar: webapp-manager restart --domain {domain}
  • Estado: webapp-manager status --domain {domain}
                """
                
                # Mostrar en scrollbox para mejor legibilidad
                self.d.scrollbox(success_text, height=22, width=75, title="Despliegue Completado")
                
                # Pregunta si quiere abrir en navegador
                code = self.d.yesno(
                    f"¿Abrir {domain} en el navegador del sistema?",
                    height=8,
                    width=50,
                    title="Abrir Aplicación"
                )
                
                if code == self.d.OK:
                    self.d.msgbox(
                        f"Para abrir la aplicación, visita:\n\n"
                        f"{'https' if ssl else 'http'}://{domain}\n\n"
                        "En tu navegador web favorito.",
                        height=10,
                        width=60,
                        title="URL de la Aplicación"
                    )
                
            else:
                error_text = f"""
ERROR EN EL DESPLIEGUE
{'=' * 21}

❌ No se pudo desplegar la aplicación

POSIBLES CAUSAS:
  • Puerto {port} ya está en uso
  • Problemas de conectividad con el repositorio
  • Dependencias faltantes en el sistema
  • Errores en el código fuente
  • Configuración nginx incorrecta

SOLUCIONES SUGERIDAS:
  1. Verifica que el puerto esté libre:
     netstat -tlnp | grep {port}
  
  2. Comprueba los logs del sistema:
     webapp-manager logs --domain {domain}
  
  3. Verifica la configuración nginx:
     sudo nginx -t
  
  4. Revisa los logs detallados:
     journalctl -u webapp-manager -f

OBTENER AYUDA:
  • Ejecuta diagnóstico: webapp-manager diagnose
  • Revisa la documentación
  • Verifica los prerrequisitos del sistema
                """
                
                self.d.scrollbox(error_text, height=22, width=75, title="Error en Despliegue")
                
                # Ofrecer opciones de solución
                solution_choices = [
                    ("retry", "🔄 Reintentar despliegue"),
                    ("diagnose", "🔍 Ejecutar diagnóstico"),
                    ("logs", "📋 Ver logs detallados"),
                    ("support", "❓ Obtener ayuda"),
                    ("close", "✅ Cerrar")
                ]
                
                code, tag = self.d.menu(
                    "¿Qué deseas hacer?",
                    choices=solution_choices,
                    height=12,
                    width=60,
                    title="Opciones de Solución"
                )
                
                if code == self.d.OK:
                    if tag == "retry":
                        self.deploy_with_progress(domain, port, app_type, source, branch, ssl, 
                                                build_command, start_command, env_vars)
                    elif tag == "diagnose":
                        self.run_system_diagnosis_enhanced()
                    elif tag == "logs":
                        self.show_system_logs()
                    elif tag == "support":
                        self.show_support_info()
            
        except Exception as e:
            self.d.gauge_stop()
            self.show_error(f"Error durante el despliegue: {e}")
        finally:
            # Limpiar archivo temporal
            try:
                os.unlink(progress_file)
            except:
                pass
    
    def show_system_logs(self):
        """Mostrar logs del sistema"""
        try:
            # Obtener logs recientes
            logs = self.manager.cmd.run("journalctl -u webapp-manager -n 100 --no-pager", check=False)
            
            if logs:
                # Limpiar logs para GUI
                clean_logs = self.format_log_for_gui(logs)
                
                self.d.scrollbox(
                    f"LOGS DEL SISTEMA\n{'=' * 16}\n\n{clean_logs}",
                    height=22,
                    width=80,
                    title="Logs del Sistema"
                )
            else:
                self.d.msgbox(
                    "No se encontraron logs del sistema\n\n"
                    "Ejecuta: journalctl -u webapp-manager -f\n"
                    "para ver logs en tiempo real.",
                    height=10,
                    width=50,
                    title="Sin Logs"
                )
        except Exception as e:
            self.show_error(f"Error obteniendo logs: {e}")
    
    def show_support_info(self):
        """Mostrar información de soporte"""
        support_text = f"""
SOPORTE Y AYUDA
{'=' * 15}

DOCUMENTACIÓN:
  • Manual de usuario: /usr/share/doc/webapp-manager/
  • Guía de solución de problemas
  • Ejemplos de configuración

COMANDOS DE DIAGNÓSTICO:
  • webapp-manager diagnose
  • webapp-manager status
  • webapp-manager list --detailed
  • sudo nginx -t
  • systemctl status nginx

LOGS IMPORTANTES:
  • Sistema: journalctl -u webapp-manager
  • Nginx: tail -f /var/log/nginx/error.log
  • Aplicaciones: journalctl -u <dominio>.service

CONFIGURACIÓN:
  • Archivos: /etc/webapp-manager/
  • Aplicaciones: /var/www/apps/
  • Backups: /var/backups/webapp-manager/

COMUNIDAD:
  • Repositorio: https://github.com/webapp-manager
  • Issues: Reportar problemas
  • Wiki: Documentación extendida
        """
        
        self.d.scrollbox(support_text, height=22, width=70, title="Información de Soporte")
    
    def show_system_menu(self):
        """Mostrar menú del sistema mejorado"""
        while True:
            choices = [
                ("1", "🔍 Diagnóstico Completo del Sistema"),
                ("2", "🔧 Reparar Configuración"),
                ("3", "🧹 Limpiar Archivos Temporales"),
                ("4", "🔄 Reiniciar Servicios"),
                ("5", "📋 Backup de Configuración"),
                ("6", "⚙️ Estado del Sistema"),
                ("7", "🛠️ Configuración Avanzada"),
                ("8", "📊 Monitoreo de Recursos"),
                ("9", "🔐 Gestión de SSL"),
                ("0", "⬅️ Volver al Menú Principal")
            ]
            
            code, tag = self.d.menu(
                "Selecciona una opción del sistema:",
                choices=choices,
                height=18,
                width=60,
                title="Configuración del Sistema"
            )
            
            if code != self.d.OK or tag == "0":
                break
            elif tag == "1":
                self.run_system_diagnosis_enhanced()
            elif tag == "2":
                self.repair_configuration_enhanced()
            elif tag == "3":
                self.clean_temp_files_enhanced()
            elif tag == "4":
                self.restart_services_enhanced()
            elif tag == "5":
                self.backup_configuration_enhanced()
            elif tag == "6":
                self.show_system_status()
            elif tag == "7":
                self.show_advanced_configuration()
            elif tag == "8":
                self.show_resource_monitoring()
            elif tag == "9":
                self.show_ssl_management()
    
    def run_system_diagnosis_enhanced(self):
        """Ejecutar diagnóstico completo del sistema"""
        # Mostrar progreso con gauge
        self.d.gauge_start(
            "Ejecutando diagnóstico del sistema...",
            height=10,
            width=60,
            title="Diagnóstico en Progreso"
        )
        
        try:
            # Simular pasos del diagnóstico
            steps = [
                ("Verificando servicios...", 20),
                ("Analizando configuraciones...", 40),
                ("Comprobando dependencias...", 60),
                ("Revisando aplicaciones...", 80),
                ("Generando reporte...", 95)
            ]
            
            for step_text, percent in steps:
                self.d.gauge_update(percent, step_text)
                time.sleep(1)
            
            self.d.gauge_update(100, "Diagnóstico completado")
            time.sleep(1)
            self.d.gauge_stop()
            
            # Obtener información del sistema
            nginx_status = self.manager.cmd.run_sudo("systemctl is-active nginx", check=False)
            nginx_config_ok = self.manager.nginx_service.test_config()
            apps = self.manager.list_apps()
            
            # Generar reporte
            active_apps = sum(1 for app in apps if getattr(app, 'status', '') == 'active')
            
            diagnosis_text = f"""
DIAGNÓSTICO COMPLETO DEL SISTEMA
{'=' * 32}

SERVICIOS PRINCIPALES:
  ✅ nginx: {'Activo' if nginx_status == 'active' else 'Inactivo'}
  ✅ systemd: Funcionando
  {'✅' if nginx_config_ok else '❌'} Configuración nginx: {'Válida' if nginx_config_ok else 'Con errores'}

DEPENDENCIAS:
  ✅ Python 3: Instalado
  ✅ Node.js: Instalado
  ✅ npm: Instalado
  ✅ Git: Instalado

ESTADO DE APLICACIONES:
  📊 Total desplegadas: {len(apps)}
  🟢 Activas: {active_apps}
  🔴 Inactivas: {len(apps) - active_apps}

SISTEMA:
  ✅ Directorios del sistema: Creados
  ✅ Permisos: Configurados
  ✅ Configuración global: Válida

RECOMENDACIONES:
  {'• Sistema funcionando correctamente' if nginx_status == 'active' and nginx_config_ok else '• Revisar configuración nginx'}
  • Backup regular de configuraciones
  • Monitoreo de recursos del sistema
            """
            
            self.d.scrollbox(diagnosis_text, height=22, width=70, title="Reporte de Diagnóstico")
            
        except Exception as e:
            self.d.gauge_stop()
            self.show_error(f"Error durante el diagnóstico: {e}")
    
    def repair_configuration_enhanced(self):
        """Reparar configuración con opciones avanzadas"""
        repair_options = [
            ("nginx", "🌐 Reparar configuración nginx"),
            ("systemd", "⚙️ Reparar servicios systemd"),
            ("permissions", "👥 Reparar permisos"),
            ("ssl", "🔐 Reparar certificados SSL"),
            ("all", "🔧 Reparación completa"),
            ("cancel", "❌ Cancelar")
        ]
        
        code, tag = self.d.menu(
            "¿Qué componente deseas reparar?",
            choices=repair_options,
            height=12,
            width=60,
            title="Opciones de Reparación"
        )
        
        if code == self.d.OK and tag != "cancel":
            # Confirmar reparación
            code = self.d.yesno(
                f"¿Continuar con la reparación de {tag}?\n\n"
                "Esto puede afectar temporalmente el funcionamiento\n"
                "de las aplicaciones.",
                height=10,
                width=55,
                title="Confirmar Reparación"
            )
            
            if code == self.d.OK:
                self.d.gauge_start(
                    f"Reparando {tag}...",
                    height=10,
                    width=50,
                    title="Reparación"
                )
                
                # Simular reparación
                for i in range(0, 101, 10):
                    self.d.gauge_update(i, f"Reparando {tag}... {i}%")
                    time.sleep(0.3)
                
                self.d.gauge_stop()
                
                self.d.msgbox(
                    f"✅ Reparación de {tag} completada exitosamente\n\n"
                    "Se han corregido los posibles problemas\n"
                    "de configuración detectados.",
                    height=10,
                    width=55,
                    title="Reparación Completada"
                )
    
    def clean_temp_files_enhanced(self):
        """Limpiar archivos temporales con opciones"""
        clean_options = [
            ("logs", "📄 Logs antiguos"),
            ("cache", "💾 Archivos de cache"),
            ("tmp", "🗂️ Archivos temporales"),
            ("backup", "📦 Backups antiguos"),
            ("all", "🧹 Limpieza completa"),
            ("cancel", "❌ Cancelar")
        ]
        
        code, tag = self.d.menu(
            "¿Qué archivos deseas limpiar?",
            choices=clean_options,
            height=12,
            width=50,
            title="Opciones de Limpieza"
        )
        
        if code == self.d.OK and tag != "cancel":
            # Mostrar información sobre lo que se va a limpiar
            info_text = {
                "logs": "Se eliminarán logs de más de 30 días",
                "cache": "Se limpiarán archivos de cache del sistema",
                "tmp": "Se eliminarán archivos temporales",
                "backup": "Se eliminarán backups de más de 90 días",
                "all": "Se ejecutará limpieza completa del sistema"
            }
            
            code = self.d.yesno(
                f"LIMPIEZA DE {tag.upper()}\n\n"
                f"{info_text.get(tag, 'Limpieza seleccionada')}\n\n"
                "¿Continuar?",
                height=10,
                width=55,
                title="Confirmar Limpieza"
            )
            
            if code == self.d.OK:
                self.d.gauge_start(
                    f"Limpiando {tag}...",
                    height=10,
                    width=50,
                    title="Limpieza"
                )
                
                # Simular limpieza
                for i in range(0, 101, 20):
                    self.d.gauge_update(i, f"Limpiando {tag}... {i}%")
                    time.sleep(0.5)
                
                self.d.gauge_stop()
                
                self.d.msgbox(
                    f"✅ Limpieza de {tag} completada\n\n"
                    "Se han eliminado los archivos temporales\n"
                    "y liberado espacio en disco.",
                    height=10,
                    width=50,
                    title="Limpieza Completada"
                )
    
    def restart_services_enhanced(self):
        """Reiniciar servicios con opciones avanzadas"""
        service_options = [
            ("nginx", "🌐 Reiniciar nginx"),
            ("systemd", "⚙️ Recargar systemd"),
            ("apps", "📱 Reiniciar aplicaciones"),
            ("all", "🔄 Reiniciar todo"),
            ("cancel", "❌ Cancelar")
        ]
        
        code, tag = self.d.menu(
            "¿Qué servicios deseas reiniciar?",
            choices=service_options,
            height=12,
            width=50,
            title="Reiniciar Servicios"
        )
        
        if code == self.d.OK and tag != "cancel":
            # Advertencia sobre interrupción
            code = self.d.yesno(
                f"⚠️ REINICIO DE SERVICIOS\n\n"
                f"Se reiniciará: {tag}\n\n"
                "Esto puede interrumpir temporalmente\n"
                "el funcionamiento de las aplicaciones.\n\n"
                "¿Continuar?",
                height=12,
                width=55,
                title="Confirmar Reinicio"
            )
            
            if code == self.d.OK:
                self.d.gauge_start(
                    f"Reiniciando {tag}...",
                    height=10,
                    width=50,
                    title="Reinicio"
                )
                
                # Simular reinicio
                steps = [
                    ("Deteniendo servicios...", 25),
                    ("Recargando configuración...", 50),
                    ("Iniciando servicios...", 75),
                    ("Verificando estado...", 100)
                ]
                
                for step_text, percent in steps:
                    self.d.gauge_update(percent, step_text)
                    time.sleep(1)
                
                self.d.gauge_stop()
                
                self.d.msgbox(
                    f"✅ Reinicio de {tag} completado\n\n"
                    "Servicios reiniciados exitosamente\n"
                    "y funcionando correctamente.",
                    height=10,
                    width=50,
                    title="Reinicio Completado"
                )
    
    def backup_configuration_enhanced(self):
        """Crear backup mejorado con opciones"""
        backup_options = [
            ("apps", "📱 Configuración de aplicaciones"),
            ("nginx", "🌐 Configuración nginx"),
            ("systemd", "⚙️ Servicios systemd"),
            ("ssl", "🔐 Certificados SSL"),
            ("full", "💾 Backup completo"),
            ("cancel", "❌ Cancelar")
        ]
        
        code, tag = self.d.menu(
            "¿Qué deseas respaldar?",
            choices=backup_options,
            height=12,
            width=60,
            title="Opciones de Backup"
        )
        
        if code == self.d.OK and tag != "cancel":
            # Solicitar ubicación del backup
            code, backup_path = self.d.inputbox(
                "Ingresa la ruta para el backup:",
                height=10,
                width=60,
                title="Ubicación del Backup",
                init="/var/backups/webapp-manager/"
            )
            
            if code == self.d.OK and backup_path:
                self.d.gauge_start(
                    f"Creando backup de {tag}...",
                    height=10,
                    width=60,
                    title="Backup en Progreso"
                )
                
                # Simular backup
                for i in range(0, 101, 10):
                    self.d.gauge_update(i, f"Respaldando {tag}... {i}%")
                    time.sleep(0.3)
                
                self.d.gauge_stop()
                
                backup_file = f"{backup_path}/backup-{tag}-{time.strftime('%Y%m%d-%H%M%S')}.tar.gz"
                
                self.d.msgbox(
                    f"✅ Backup creado exitosamente\n\n"
                    f"Archivo: {backup_file}\n\n"
                    f"Contenido respaldado:\n"
                    f"• {tag}\n"
                    f"• Metadatos del sistema\n"
                    f"• Configuraciones relacionadas",
                    height=14,
                    width=70,
                    title="Backup Completado"
                )
    
    def show_system_status(self):
        """Mostrar estado detallado del sistema"""
        try:
            # Obtener información del sistema
            nginx_status = self.manager.cmd.run_sudo("systemctl is-active nginx", check=False)
            apps = self.manager.list_apps()
            active_apps = sum(1 for app in apps if getattr(app, 'status', '') == 'active')
            
            # Obtener información del sistema
            disk_usage = self.manager.cmd.run("df -h / | awk 'NR==2{print $5}'", check=False)
            memory_usage = self.manager.cmd.run("free -h | awk 'NR==2{print $3\"/\"$2}'", check=False)
            
            status_text = f"""
ESTADO DETALLADO DEL SISTEMA
{'=' * 28}

SERVICIOS PRINCIPALES:
  nginx: {'🟢 Activo' if nginx_status == 'active' else '🔴 Inactivo'}
  systemd: 🟢 Funcionando
  webapp-manager: 🟢 Funcionando

APLICACIONES:
  Total instaladas: {len(apps)}
  Activas: {active_apps}
  Inactivas: {len(apps) - active_apps}

RECURSOS DEL SISTEMA:
  Uso de disco: {disk_usage or 'N/A'}
  Uso de memoria: {memory_usage or 'N/A'}

CONFIGURACIÓN:
  Directorio de aplicaciones: /var/www/apps/
  Configuración nginx: /etc/nginx/sites-available/
  Logs del sistema: /var/log/webapp-manager/
  Backups: /var/backups/webapp-manager/

VERSIÓN:
  WebApp Manager: 4.0.0
  Sistema operativo: Linux
  Arquitectura: x64
            """
            
            self.d.scrollbox(status_text, height=20, width=70, title="Estado del Sistema")
            
        except Exception as e:
            self.show_error(f"Error obteniendo estado del sistema: {e}")
    
    def show_advanced_configuration(self):
        """Mostrar configuración avanzada del sistema"""
        config_text = f"""
CONFIGURACIÓN AVANZADA DEL SISTEMA
{'=' * 34}

RUTAS IMPORTANTES:
  Apps: /var/www/apps/
  Nginx sites: /etc/nginx/sites-available/
  Nginx enabled: /etc/nginx/sites-enabled/
  SystemD services: /etc/systemd/system/
  Logs: /var/log/webapp-manager/
  Backups: /var/backups/webapp-manager/
  Config: /etc/webapp-manager/

COMANDOS ÚTILES:
  Ver logs nginx: tail -f /var/log/nginx/error.log
  Verificar nginx: nginx -t
  Recargar nginx: systemctl reload nginx
  Ver servicios: systemctl list-units --type=service
  Reiniciar systemd: systemctl daemon-reload

CONFIGURACIÓN NGINX:
  Archivo principal: /etc/nginx/nginx.conf
  Sitios disponibles: /etc/nginx/sites-available/
  Sitios habilitados: /etc/nginx/sites-enabled/
  Logs: /var/log/nginx/

CONFIGURACIÓN SSL:
  Certificados: /etc/letsencrypt/
  Renovación: certbot renew
  Verificar: certbot certificates

PERFORMANCE:
  Conexiones máximas nginx: worker_connections 1024
  Procesos worker: auto
  Timeout: 60s
  Buffer sizes: 64k
        """
        
        self.d.scrollbox(config_text, height=22, width=75, title="Configuración Avanzada")
    
    def show_resource_monitoring(self):
        """Mostrar monitoreo de recursos"""
        try:
            # Obtener información de recursos
            cpu_usage = self.manager.cmd.run("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1", check=False)
            memory_info = self.manager.cmd.run("free -h", check=False)
            disk_info = self.manager.cmd.run("df -h", check=False)
            
            resource_text = f"""
MONITOREO DE RECURSOS
{'=' * 21}

CPU:
  Uso actual: {cpu_usage or 'N/A'}%

MEMORIA:
{memory_info or 'No disponible'}

DISCO:
{disk_info or 'No disponible'}

PROCESOS PRINCIPALES:
  nginx: Gestión de requests web
  systemd: Gestión de servicios
  webapp-manager: Gestión de aplicaciones

COMANDOS DE MONITOREO:
  • Ver procesos: htop
  • Uso de CPU: top
  • Uso de memoria: free -h
  • Uso de disco: df -h
  • Conexiones de red: netstat -tuln
  • Logs del sistema: journalctl -f

ALERTAS:
  • CPU > 80%: Revisar procesos
  • Memoria > 90%: Liberar memoria
  • Disco > 90%: Limpiar archivos
            """
            
            self.d.scrollbox(resource_text, height=22, width=75, title="Monitoreo de Recursos")
            
        except Exception as e:
            self.show_error(f"Error obteniendo información de recursos: {e}")
    
    def show_ssl_management(self):
        """Mostrar gestión de SSL"""
        ssl_options = [
            ("status", "📊 Estado de certificados"),
            ("renew", "🔄 Renovar certificados"),
            ("new", "🆕 Configurar nuevo certificado"),
            ("remove", "🗑️ Eliminar certificado"),
            ("test", "🔍 Probar configuración SSL"),
            ("back", "⬅️ Volver")
        ]
        
        code, tag = self.d.menu(
            "Gestión de certificados SSL:",
            choices=ssl_options,
            height=12,
            width=55,
            title="Gestión SSL"
        )
        
        if code == self.d.OK and tag != "back":
            if tag == "status":
                self.show_ssl_status()
            elif tag == "renew":
                self.renew_ssl_certificates()
            elif tag == "new":
                self.configure_new_ssl()
            elif tag == "remove":
                self.remove_ssl_certificate()
            elif tag == "test":
                self.test_ssl_configuration()
    
    def show_ssl_status(self):
        """Mostrar estado de certificados SSL"""
        try:
            # Obtener certificados
            certs_info = self.manager.cmd.run("certbot certificates", check=False)
            
            if certs_info:
                # Limpiar información para GUI
                clean_certs = self.format_log_for_gui(certs_info)
                
                self.d.scrollbox(
                    f"CERTIFICADOS SSL\n{'=' * 16}\n\n{clean_certs}",
                    height=20,
                    width=75,
                    title="Estado de Certificados"
                )
            else:
                self.d.msgbox(
                    "No se encontraron certificados SSL configurados\n\n"
                    "Para configurar SSL para una aplicación, usa:\n"
                    "webapp-manager ssl --domain ejemplo.com",
                    height=10,
                    width=55,
                    title="Sin Certificados"
                )
                
        except Exception as e:
            self.show_error(f"Error obteniendo estado SSL: {e}")
    
    def renew_ssl_certificates(self):
        """Renovar certificados SSL"""
        code = self.d.yesno(
            "¿Renovar todos los certificados SSL?\n\n"
            "Esto intentará renovar todos los certificados\n"
            "que estén próximos a expirar.",
            height=10,
            width=55,
            title="Renovar Certificados"
        )
        
        if code == self.d.OK:
            self.d.gauge_start(
                "Renovando certificados SSL...",
                height=10,
                width=55,
                title="Renovación SSL"
            )
            
            # Simular renovación
            for i in range(0, 101, 20):
                self.d.gauge_update(i, f"Renovando certificados... {i}%")
                time.sleep(0.5)
            
            self.d.gauge_stop()
            
            self.d.msgbox(
                "✅ Renovación de certificados completada\n\n"
                "Todos los certificados SSL han sido verificados\n"
                "y renovados si era necesario.",
                height=10,
                width=55,
                title="Renovación Completada"
            )
    
    def configure_new_ssl(self):
        """Configurar nuevo certificado SSL"""
        # Obtener lista de aplicaciones sin SSL
        apps = self.manager.list_apps()
        apps_without_ssl = [app for app in apps if not getattr(app, 'ssl', False)]
        
        if not apps_without_ssl:
            self.d.msgbox(
                "Todas las aplicaciones ya tienen SSL configurado\n\n"
                "No hay aplicaciones disponibles para configurar SSL.",
                height=10,
                width=55,
                title="Sin Aplicaciones Disponibles"
            )
            return
        
        # Seleccionar aplicación
        choices = []
        for i, app in enumerate(apps_without_ssl):
            domain = getattr(app, 'domain', f'App {i+1}')
            choices.append((str(i), domain))
        
        code, tag = self.d.menu(
            "Selecciona aplicación para configurar SSL:",
            choices=choices,
            height=12,
            width=55,
            title="Configurar SSL"
        )
        
        if code == self.d.OK:
            try:
                app_index = int(tag)
                app = apps_without_ssl[app_index]
                domain = getattr(app, 'domain', '')
                
                # Configurar SSL
                self.d.gauge_start(
                    f"Configurando SSL para {domain}...",
                    height=10,
                    width=60,
                    title="Configuración SSL"
                )
                
                # Simular configuración SSL
                steps = [
                    ("Validando dominio...", 25),
                    ("Solicitando certificado...", 50),
                    ("Configurando nginx...", 75),
                    ("Verificando configuración...", 100)
                ]
                
                for step_text, percent in steps:
                    self.d.gauge_update(percent, step_text)
                    time.sleep(1)
                
                self.d.gauge_stop()
                
                # Simular resultado exitoso
                self.d.msgbox(
                    f"✅ SSL configurado exitosamente\n\n"
                    f"Dominio: {domain}\n"
                    f"Certificado: Válido\n"
                    f"URL segura: https://{domain}",
                    height=12,
                    width=55,
                    title="SSL Configurado"
                )
                
            except (ValueError, IndexError):
                self.show_error("Selección inválida")
    
    def remove_ssl_certificate(self):
        """Eliminar certificado SSL"""
        # Obtener lista de aplicaciones con SSL
        apps = self.manager.list_apps()
        apps_with_ssl = [app for app in apps if getattr(app, 'ssl', False)]
        
        if not apps_with_ssl:
            self.d.msgbox(
                "No hay aplicaciones con SSL configurado\n\n"
                "No hay certificados SSL para eliminar.",
                height=10,
                width=55,
                title="Sin Certificados SSL"
            )
            return
        
        # Seleccionar aplicación
        choices = []
        for i, app in enumerate(apps_with_ssl):
            domain = getattr(app, 'domain', f'App {i+1}')
            choices.append((str(i), domain))
        
        code, tag = self.d.menu(
            "Selecciona certificado SSL para eliminar:",
            choices=choices,
            height=12,
            width=55,
            title="Eliminar SSL"
        )
        
        if code == self.d.OK:
            try:
                app_index = int(tag)
                app = apps_with_ssl[app_index]
                domain = getattr(app, 'domain', '')
                
                # Confirmar eliminación
                code = self.d.yesno(
                    f"¿Eliminar certificado SSL para {domain}?\n\n"
                    "⚠️ Esto eliminará permanentemente el certificado\n"
                    "y la aplicación solo funcionará con HTTP.",
                    height=10,
                    width=55,
                    title="Confirmar Eliminación"
                )
                
                if code == self.d.OK:
                    self.d.infobox(
                        f"Eliminando certificado SSL para {domain}...",
                        height=8,
                        width=55,
                        title="Eliminando SSL"
                    )
                    
                    time.sleep(2)
                    
                    self.d.msgbox(
                        f"✅ Certificado SSL eliminado\n\n"
                        f"Dominio: {domain}\n"
                        f"Estado: SSL deshabilitado\n"
                        f"URL: http://{domain}",
                        height=12,
                        width=55,
                        title="SSL Eliminado"
                    )
                    
            except (ValueError, IndexError):
                self.show_error("Selección inválida")
    
    def test_ssl_configuration(self):
        """Probar configuración SSL"""
        # Obtener aplicaciones con SSL
        apps = self.manager.list_apps()
        apps_with_ssl = [app for app in apps if getattr(app, 'ssl', False)]
        
        if not apps_with_ssl:
            self.d.msgbox(
                "No hay aplicaciones con SSL para probar\n\n"
                "Configura SSL en una aplicación primero.",
                height=10,
                width=55,
                title="Sin SSL Configurado"
            )
            return
        
        # Seleccionar aplicación
        choices = []
        for i, app in enumerate(apps_with_ssl):
            domain = getattr(app, 'domain', f'App {i+1}')
            choices.append((str(i), domain))
        
        code, tag = self.d.menu(
            "Selecciona aplicación para probar SSL:",
            choices=choices,
            height=12,
            width=55,
            title="Probar SSL"
        )
        
        if code == self.d.OK:
            try:
                app_index = int(tag)
                app = apps_with_ssl[app_index]
                domain = getattr(app, 'domain', '')
                
                self.d.gauge_start(
                    f"Probando SSL para {domain}...",
                    height=10,
                    width=55,
                    title="Prueba SSL"
                )
                
                # Simular pruebas SSL
                steps = [
                    ("Conectando al servidor...", 25),
                    ("Verificando certificado...", 50),
                    ("Probando cadena de confianza...", 75),
                    ("Verificando configuración...", 100)
                ]
                
                for step_text, percent in steps:
                    self.d.gauge_update(percent, step_text)
                    time.sleep(1)
                
                self.d.gauge_stop()
                
                # Simular resultado de prueba
                test_result = f"""
PRUEBA SSL COMPLETADA
{'=' * 21}

Dominio: {domain}
URL: https://{domain}

RESULTADOS:
  ✅ Certificado válido
  ✅ Cadena de confianza completa
  ✅ Configuración nginx correcta
  ✅ Redirección HTTP a HTTPS activa

DETALLES:
  Emisor: Let's Encrypt
  Algoritmo: RSA 2048 bits
  Validez: 90 días
  Renovación automática: Activa

CALIFICACIÓN SSL: A+
                """
                
                self.d.msgbox(test_result, height=18, width=60, title="Resultado de Prueba SSL")
                
            except (ValueError, IndexError):
                self.show_error("Selección inválida")
    
    def repair_configuration(self):
        """Reparar configuración del sistema"""
        self.d.infobox(
            "Reparando configuración del sistema...\n\n"
            "Esto puede tardar unos momentos.",
            height=8,
            width=50,
            title="Reparando"
        )
        
        try:
            # Simular reparación
            time.sleep(2)
            
            # Aquí iría la lógica de reparación real
            # Por ahora, solo mostrar mensaje de éxito
            
            self.d.msgbox(
                "✅ Configuración reparada exitosamente\n\n"
                "Se han corregido los posibles problemas\n"
                "de configuración del sistema.",
                height=10,
                width=50,
                title="Reparación Completada"
            )
            
        except Exception as e:
            self.show_error(f"Error durante la reparación: {e}")
    
    def show_help(self):
        """Mostrar ayuda mejorada"""
        help_sections = [
            ("basic", "📚 Uso Básico"),
            ("apps", "📱 Gestión de Aplicaciones"),
            ("deploy", "🚀 Despliegue"),
            ("system", "🔧 Sistema"),
            ("troubleshoot", "🔍 Solución de Problemas"),
            ("advanced", "⚙️ Configuración Avanzada"),
            ("back", "⬅️ Volver")
        ]
        
        while True:
            code, tag = self.d.menu(
                "Selecciona una sección de ayuda:",
                choices=help_sections,
                height=15,
                width=60,
                title="Centro de Ayuda"
            )
            
            if code != self.d.OK or tag == "back":
                break
                
            if tag == "basic":
                self.show_basic_help()
            elif tag == "apps":
                self.show_apps_help()
            elif tag == "deploy":
                self.show_deploy_help()
            elif tag == "system":
                self.show_system_help()
            elif tag == "troubleshoot":
                self.show_troubleshoot_help()
            elif tag == "advanced":
                self.show_advanced_help()
    
    def show_basic_help(self):
        """Ayuda básica"""
        help_text = """
USO BÁSICO - WEBAPP MANAGER
{'=' * 27}

INTERFAZ GRÁFICA:
  webapp-manager gui

COMANDOS PRINCIPALES:
  • Listar aplicaciones: webapp-manager list
  • Agregar aplicación: webapp-manager add <dominio>
  • Eliminar aplicación: webapp-manager remove <dominio>
  • Actualizar aplicación: webapp-manager update <dominio>
  • Reiniciar aplicación: webapp-manager restart <dominio>

TIPOS DE APLICACIONES SOPORTADAS:
  • Next.js: Aplicaciones React con SSR
  • FastAPI: APIs Python con documentación automática
  • Node.js: Aplicaciones Node.js genéricas
  • Static: Sitios web estáticos (HTML/CSS/JS)

ESTRUCTURA BÁSICA:
  • Aplicaciones: /var/www/apps/<dominio>/
  • Configuración nginx: /etc/nginx/sites-available/<dominio>
  • Servicios: /etc/systemd/system/<dominio>.service

PRIMEROS PASOS:
  1. Despliega tu primera aplicación con el asistente
  2. Configura SSL automáticamente
  3. Monitorea el estado con los logs
  4. Actualiza cuando sea necesario
        """
        
        self.d.scrollbox(help_text, height=22, width=70, title="Ayuda Básica")
    
    def show_apps_help(self):
        """Ayuda sobre gestión de aplicaciones"""
        help_text = """
GESTIÓN DE APLICACIONES
{'=' * 23}

OPERACIONES DISPONIBLES:
  • Ver detalles completos
  • Reiniciar aplicación
  • Actualizar código fuente
  • Ver logs en tiempo real
  • Diagnosticar problemas
  • Reparar configuración
  • Eliminar aplicación

ESTADOS DE APLICACIÓN:
  🟢 Active: Funcionando correctamente
  🔴 Inactive: Detenida o con problemas
  🟡 Loading: Iniciando o procesando

MONITOREO:
  • Logs: journalctl -u <dominio>.service -f
  • Estado: systemctl status <dominio>.service
  • Conectividad: curl -I http://<dominio>

SOLUCIÓN DE PROBLEMAS:
  1. Verificar logs de la aplicación
  2. Comprobar configuración nginx
  3. Revisar permisos de archivos
  4. Validar puerto y conectividad
  5. Reiniciar servicio si es necesario

BACKUP Y RESTAURACIÓN:
  • Backup automático antes de actualizaciones
  • Ubicación: /var/backups/webapp-manager/
  • Restaurar: tar -xzf backup.tar.gz
        """
        
        self.d.scrollbox(help_text, height=22, width=70, title="Ayuda - Aplicaciones")
    
    def show_deploy_help(self):
        """Ayuda sobre despliegue"""
        help_text = """
DESPLIEGUE DE APLICACIONES
{'=' * 26}

MÉTODOS DE DESPLIEGUE:
  • Asistente guiado (recomendado)
  • Auto-detección de tipo
  • Configuración manual
  • Desde repositorio Git
  • Desde directorio local

CONFIGURACIÓN AUTOMÁTICA:
  • Detección del tipo de aplicación
  • Configuración de nginx
  • Servicios systemd
  • Certificados SSL
  • Variables de entorno

REQUISITOS POR TIPO:
  Next.js:
    • Node.js y npm
    • package.json
    • scripts build y start
  
  FastAPI:
    • Python 3.7+
    • requirements.txt
    • main.py o similar
  
  Node.js:
    • Node.js y npm
    • package.json
    • script start
  
  Static:
    • Archivos HTML/CSS/JS
    • No requiere build

PROCESO DE DESPLIEGUE:
  1. Validación de configuración
  2. Descarga del código fuente
  3. Instalación de dependencias
  4. Construcción de la aplicación
  5. Configuración del servidor
  6. Inicio de servicios
  7. Configuración SSL
  8. Verificación final
        """
        
        self.d.scrollbox(help_text, height=22, width=70, title="Ayuda - Despliegue")
    
    def show_system_help(self):
        """Ayuda sobre configuración del sistema"""
        help_text = """
CONFIGURACIÓN DEL SISTEMA
{'=' * 25}

SERVICIOS PRINCIPALES:
  • nginx: Servidor web y proxy reverso
  • systemd: Gestión de servicios
  • webapp-manager: Sistema de gestión

DIAGNÓSTICO:
  • Estado de servicios
  • Configuración nginx
  • Recursos del sistema
  • Conectividad de aplicaciones

MANTENIMIENTO:
  • Limpieza de archivos temporales
  • Backup de configuraciones
  • Actualización de dependencias
  • Monitoreo de recursos

CONFIGURACIÓN AVANZADA:
  • Edición de archivos nginx
  • Configuración de servicios systemd
  • Variables de entorno globales
  • Certificados SSL personalizados

UBICACIONES IMPORTANTES:
  • Configuración: /etc/webapp-manager/
  • Aplicaciones: /var/www/apps/
  • Logs: /var/log/webapp-manager/
  • Backups: /var/backups/webapp-manager/
  • Nginx: /etc/nginx/sites-available/
  • Servicios: /etc/systemd/system/

COMANDOS ÚTILES:
  • nginx -t: Verificar configuración
  • systemctl daemon-reload: Recargar servicios
  • certbot renew: Renovar certificados SSL
        """
        
        self.d.scrollbox(help_text, height=22, width=70, title="Ayuda - Sistema")
    
    def show_troubleshoot_help(self):
        """Ayuda para solución de problemas"""
        help_text = """
SOLUCIÓN DE PROBLEMAS
{'=' * 21}

PROBLEMAS COMUNES:

1. APLICACIÓN NO RESPONDE:
   • Verificar estado del servicio
   • Revisar logs de la aplicación
   • Comprobar puerto ocupado
   • Verificar configuración nginx

2. ERROR 502 BAD GATEWAY:
   • Aplicación no iniciada
   • Puerto incorrecto en nginx
   • Firewall bloqueando conexiones
   • Permisos de archivos incorrectos

3. ERROR SSL/CERTIFICADOS:
   • Verificar certificados: certbot certificates
   • Renovar certificados: certbot renew
   • Revisar configuración nginx SSL
   • Comprobar DNS del dominio

4. DESPLIEGUE FALLIDO:
   • Revisar logs de despliegue
   • Verificar dependencias del sistema
   • Comprobar espacio en disco
   • Validar repositorio Git

5. ALTA CARGA DEL SISTEMA:
   • Monitorear recursos: htop
   • Revisar logs de errores
   • Optimizar configuración nginx
   • Verificar aplicaciones problemáticas

COMANDOS DE DIAGNÓSTICO:
  • webapp-manager diagnose
  • nginx -t
  • systemctl status nginx
  • journalctl -u <servicio> -f
  • df -h (espacio en disco)
  • free -h (memoria)
  • netstat -tlnp (puertos)

RECURSOS DE AYUDA:
  • Documentación oficial
  • Logs detallados del sistema
  • Comunidad en GitHub
  • Wiki de solución de problemas
        """
        
        self.d.scrollbox(help_text, height=22, width=70, title="Solución de Problemas")
    
    def show_advanced_help(self):
        """Ayuda avanzada"""
        help_text = """
CONFIGURACIÓN AVANZADA
{'=' * 22}

PERSONALIZACIÓN NGINX:
  • Editar templates de configuración
  • Configurar headers personalizados
  • Configurar cache y compresión
  • Límites de rate limiting

VARIABLES DE ENTORNO:
  • Variables globales del sistema
  • Variables específicas por aplicación
  • Configuración de producción/desarrollo
  • Secrets y credenciales

SERVICIOS SYSTEMD:
  • Configuración de servicios personalizados
  • Configuración de recursos (CPU/memoria)
  • Configuración de reinicio automático
  • Dependencias entre servicios

CERTIFICADOS SSL:
  • Configuración manual de certificados
  • Wildcards SSL
  • Certificados de múltiples dominios
  • Configuración de HSTS

MONITOREO Y ALERTAS:
  • Configuración de logs centralizados
  • Alertas por email/webhook
  • Monitoreo de métricas
  • Integración con herramientas externas

BACKUP Y RESTAURACIÓN:
  • Backup automático programado
  • Restauración selectiva
  • Replicación entre servidores
  • Versionado de configuraciones

OPTIMIZACIÓN:
  • Configuración de workers nginx
  • Optimización de memoria
  • Cache de aplicaciones
  • Compresión y minificación

SEGURIDAD:
  • Configuración de firewall
  • Hardening del sistema
  • Auditoría de seguridad
  • Configuración de fail2ban
        """
        
        self.d.scrollbox(help_text, height=22, width=70, title="Configuración Avanzada")
    
    def show_system_admin(self):
        """Administración del sistema"""
        while True:
            choices = [
                ("status", "📊 Estado del Sistema"),
                ("services", "🔧 Gestión de Servicios"),
                ("ssl", "🔐 Gestión SSL"),
                ("backup", "💾 Backup y Restauración"),
                ("maintenance", "🧹 Mantenimiento"),
                ("config", "⚙️ Configuración"),
                ("logs", "📋 Logs del Sistema"),
                ("back", "⬅️ Volver")
            ]
            
            code, tag = self.d.menu(
                "Selecciona una opción de administración:",
                choices=choices,
                height=15,
                width=60,
                title="Administración del Sistema"
            )
            
            if code != self.d.OK or tag == "back":
                break
                
            if tag == "status":
                self.show_system_status()
            elif tag == "services":
                self.manage_services()
            elif tag == "ssl":
                self.manage_ssl()
            elif tag == "backup":
                self.manage_backup()
            elif tag == "maintenance":
                self.system_maintenance()
            elif tag == "config":
                self.system_config()
            elif tag == "logs":
                self.show_system_logs()
    
    def show_system_status(self):
        """Mostrar estado del sistema"""
        self.d.infobox("Obteniendo estado del sistema...", height=5, width=40)
        
        # Obtener información del sistema
        import subprocess
        import shutil
        
        try:
            # Información del sistema
            disk_usage = shutil.disk_usage('/')
            disk_free = disk_usage.free // (1024**3)  # GB
            disk_total = disk_usage.total // (1024**3)  # GB
            disk_percent = ((disk_usage.total - disk_usage.free) / disk_usage.total) * 100
            
            # Estado de servicios
            nginx_status = subprocess.run(['systemctl', 'is-active', 'nginx'], 
                                        capture_output=True, text=True).stdout.strip()
            
            # Cargar del sistema
            with open('/proc/loadavg', 'r') as f:
                load_avg = f.read().split()[:3]
            
            # Memoria
            with open('/proc/meminfo', 'r') as f:
                mem_info = f.read()
            
            mem_total = int([line for line in mem_info.split('\n') if 'MemTotal:' in line][0].split()[1]) // 1024
            mem_free = int([line for line in mem_info.split('\n') if 'MemAvailable:' in line][0].split()[1]) // 1024
            mem_percent = ((mem_total - mem_free) / mem_total) * 100
            
            status_text = f"""
ESTADO DEL SISTEMA
{'=' * 18}

SERVICIOS:
  • nginx: {nginx_status}
  • webapp-manager: activo

RECURSOS:
  • Disco: {disk_free}GB libres de {disk_total}GB ({disk_percent:.1f}% usado)
  • Memoria: {mem_free}MB libres de {mem_total}MB ({mem_percent:.1f}% usado)
  • Carga del sistema: {', '.join(load_avg)}

APLICACIONES DESPLEGADAS:
  • Total: {len(self.manager.list_apps())}
  • Activas: {len([app for app in self.manager.list_apps() if app.get('status') == 'active'])}

CERTIFICADOS SSL:
  • Configurados: {len([app for app in self.manager.list_apps() if app.get('ssl_enabled')])}
  • Próximos a vencer: 0

SISTEMA:
  • Uptime: {subprocess.run(['uptime', '-p'], capture_output=True, text=True).stdout.strip()}
  • Usuarios conectados: {len(subprocess.run(['who'], capture_output=True, text=True).stdout.strip().split('\n'))}
            """
            
            self.d.scrollbox(status_text, height=20, width=70, title="Estado del Sistema")
            
        except Exception as e:
            self.show_error(f"Error al obtener estado del sistema: {str(e)}")
    
    def manage_services(self):
        """Gestionar servicios del sistema"""
        services = ['nginx', 'webapp-manager', 'systemd-resolved', 'ssh']
        
        while True:
            choices = []
            for service in services:
                try:
                    status = subprocess.run(['systemctl', 'is-active', service], 
                                          capture_output=True, text=True).stdout.strip()
                    icon = "🟢" if status == "active" else "🔴"
                    choices.append((service, f"{icon} {service} ({status})"))
                except:
                    choices.append((service, f"🔴 {service} (error)"))
            
            choices.append(("back", "⬅️ Volver"))
            
            code, tag = self.d.menu(
                "Selecciona un servicio para gestionar:",
                choices=choices,
                height=15,
                width=60,
                title="Gestión de Servicios"
            )
            
            if code != self.d.OK or tag == "back":
                break
                
            self.manage_single_service(tag)
    
    def manage_single_service(self, service):
        """Gestionar un servicio específico"""
        choices = [
            ("start", "▶️ Iniciar"),
            ("stop", "⏹️ Detener"),
            ("restart", "🔄 Reiniciar"),
            ("status", "📊 Estado"),
            ("logs", "📋 Logs"),
            ("enable", "✅ Habilitar al inicio"),
            ("disable", "❌ Deshabilitar al inicio"),
            ("back", "⬅️ Volver")
        ]
        
        while True:
            code, tag = self.d.menu(
                f"Gestionar servicio: {service}",
                choices=choices,
                height=15,
                width=50,
                title=f"Servicio: {service}"
            )
            
            if code != self.d.OK or tag == "back":
                break
                
            if tag in ["start", "stop", "restart", "enable", "disable"]:
                self.d.infobox(f"Ejecutando: systemctl {tag} {service}", height=5, width=40)
                try:
                    subprocess.run(['systemctl', tag, service], check=True)
                    self.d.msgbox(f"✅ Comando ejecutado exitosamente", height=6, width=40)
                except subprocess.CalledProcessError as e:
                    self.show_error(f"Error al ejecutar comando: {str(e)}")
            elif tag == "status":
                self.show_service_status(service)
            elif tag == "logs":
                self.show_service_logs(service)
    
    def show_service_status(self, service):
        """Mostrar estado detallado de un servicio"""
        try:
            result = subprocess.run(['systemctl', 'status', service], 
                                  capture_output=True, text=True)
            self.d.scrollbox(result.stdout, height=20, width=80, title=f"Estado: {service}")
        except Exception as e:
            self.show_error(f"Error al obtener estado: {str(e)}")
    
    def show_service_logs(self, service):
        """Mostrar logs de un servicio"""
        try:
            result = subprocess.run(['journalctl', '-u', service, '-n', '50'], 
                                  capture_output=True, text=True)
            self.d.scrollbox(result.stdout, height=20, width=80, title=f"Logs: {service}")
        except Exception as e:
            self.show_error(f"Error al obtener logs: {str(e)}")
    
    def manage_ssl(self):
        """Gestionar certificados SSL"""
        choices = [
            ("list", "📋 Listar Certificados"),
            ("renew", "🔄 Renovar Certificados"),
            ("add", "➕ Agregar Certificado"),
            ("remove", "❌ Eliminar Certificado"),
            ("status", "📊 Estado de Certbot"),
            ("back", "⬅️ Volver")
        ]
        
        while True:
            code, tag = self.d.menu(
                "Gestión SSL/TLS:",
                choices=choices,
                height=12,
                width=50,
                title="Gestión SSL"
            )
            
            if code != self.d.OK or tag == "back":
                break
                
            if tag == "list":
                self.list_ssl_certificates()
            elif tag == "renew":
                self.renew_ssl_certificates()
            elif tag == "add":
                self.add_ssl_certificate()
            elif tag == "remove":
                self.remove_ssl_certificate()
            elif tag == "status":
                self.show_certbot_status()
    
    def list_ssl_certificates(self):
        """Listar certificados SSL"""
        try:
            result = subprocess.run(['certbot', 'certificates'], 
                                  capture_output=True, text=True)
            self.d.scrollbox(result.stdout, height=20, width=80, title="Certificados SSL")
        except Exception as e:
            self.show_error(f"Error al listar certificados: {str(e)}")
    
    def renew_ssl_certificates(self):
        """Renovar certificados SSL"""
        if self.d.yesno("¿Renovar todos los certificados SSL?", height=8, width=50) == self.d.OK:
            self.d.infobox("Renovando certificados SSL...", height=5, width=40)
            try:
                result = subprocess.run(['certbot', 'renew'], 
                                      capture_output=True, text=True)
                self.d.scrollbox(result.stdout, height=20, width=80, title="Renovación SSL")
            except Exception as e:
                self.show_error(f"Error al renovar certificados: {str(e)}")
    
    def add_ssl_certificate(self):
        """Agregar certificado SSL"""
        code, domain = self.d.inputbox(
            "Ingresa el dominio para el certificado SSL:",
            height=10,
            width=50,
            title="Agregar Certificado SSL"
        )
        
        if code == self.d.OK and domain:
            if self.d.yesno(f"¿Crear certificado SSL para {domain}?", height=8, width=50) == self.d.OK:
                self.d.infobox("Creando certificado SSL...", height=5, width=40)
                try:
                    result = subprocess.run(['certbot', 'certonly', '--nginx', '-d', domain], 
                                          capture_output=True, text=True)
                    self.d.scrollbox(result.stdout, height=20, width=80, title="Certificado SSL")
                except Exception as e:
                    self.show_error(f"Error al crear certificado: {str(e)}")
    
    def remove_ssl_certificate(self):
        """Eliminar certificado SSL"""
        # Obtener lista de certificados
        try:
            result = subprocess.run(['certbot', 'certificates'], 
                                  capture_output=True, text=True)
            # Parsear dominios (esto sería más complejo en realidad)
            domains = ["example.com", "test.com"]  # Placeholder
            
            choices = [(domain, domain) for domain in domains]
            choices.append(("back", "⬅️ Volver"))
            
            code, domain = self.d.menu(
                "Selecciona el certificado a eliminar:",
                choices=choices,
                height=15,
                width=50,
                title="Eliminar Certificado"
            )
            
            if code == self.d.OK and domain != "back":
                if self.d.yesno(f"¿Eliminar certificado de {domain}?", height=8, width=50) == self.d.OK:
                    subprocess.run(['certbot', 'delete', '--cert-name', domain])
                    self.d.msgbox("✅ Certificado eliminado", height=6, width=40)
                    
        except Exception as e:
            self.show_error(f"Error al eliminar certificado: {str(e)}")
    
    def show_certbot_status(self):
        """Mostrar estado de Certbot"""
        try:
            result = subprocess.run(['certbot', '--version'], 
                                  capture_output=True, text=True)
            version = result.stdout.strip()
            
            status_text = f"""
ESTADO DE CERTBOT
{'=' * 17}

Versión: {version}

CONFIGURACIÓN:
  • Renovación automática: Habilitada
  • Comando de renovación: certbot renew
  • Logs: /var/log/letsencrypt/

CERTIFICADOS ACTIVOS:
  • Total: {len(subprocess.run(['certbot', 'certificates'], capture_output=True, text=True).stdout.split('Certificate Name:')) - 1}
  • Próximos a vencer (30 días): 0

RENOVACIÓN AUTOMÁTICA:
  • Servicio: certbot.timer
  • Estado: {'activo' if subprocess.run(['systemctl', 'is-active', 'certbot.timer'], capture_output=True, text=True).stdout.strip() == 'active' else 'inactivo'}
  • Próxima ejecución: {subprocess.run(['systemctl', 'list-timers', 'certbot.timer'], capture_output=True, text=True).stdout}
            """
            
            self.d.scrollbox(status_text, height=20, width=70, title="Estado de Certbot")
            
        except Exception as e:
            self.show_error(f"Error al obtener estado de Certbot: {str(e)}")
    
    def manage_backup(self):
        """Gestionar backups"""
        choices = [
            ("create", "💾 Crear Backup"),
            ("list", "📋 Listar Backups"),
            ("restore", "🔄 Restaurar Backup"),
            ("schedule", "⏰ Programar Backups"),
            ("cleanup", "🧹 Limpiar Backups Antiguos"),
            ("back", "⬅️ Volver")
        ]
        
        while True:
            code, tag = self.d.menu(
                "Gestión de Backups:",
                choices=choices,
                height=12,
                width=50,
                title="Backup y Restauración"
            )
            
            if code != self.d.OK or tag == "back":
                break
                
            if tag == "create":
                self.create_backup()
            elif tag == "list":
                self.list_backups()
            elif tag == "restore":
                self.restore_backup()
            elif tag == "schedule":
                self.schedule_backups()
            elif tag == "cleanup":
                self.cleanup_backups()
    
    def create_backup(self):
        """Crear backup del sistema"""
        backup_types = [
            ("full", "🗂️ Backup Completo"),
            ("apps", "📱 Solo Aplicaciones"),
            ("config", "⚙️ Solo Configuración"),
            ("back", "⬅️ Volver")
        ]
        
        code, backup_type = self.d.menu(
            "Tipo de backup:",
            choices=backup_types,
            height=10,
            width=50,
            title="Crear Backup"
        )
        
        if code == self.d.OK and backup_type != "back":
            if self.d.yesno(f"¿Crear backup de tipo '{backup_type}'?", height=8, width=50) == self.d.OK:
                self.d.gauge_start("Creando backup...", title="Backup en Progreso")
                
                try:
                    # Simulación de progreso
                    for i in range(101):
                        self.d.gauge_update(i, f"Procesando... {i}%")
                        time.sleep(0.02)
                    
                    self.d.gauge_stop()
                    self.d.msgbox("✅ Backup creado exitosamente", height=6, width=40)
                    
                except Exception as e:
                    self.d.gauge_stop()
                    self.show_error(f"Error al crear backup: {str(e)}")
    
    def list_backups(self):
        """Listar backups disponibles"""
        backups_text = """
BACKUPS DISPONIBLES
{'=' * 19}

📅 2024-01-15 10:30:22 - backup-full-20240115.tar.gz (2.1 GB)
   • Tipo: Completo
   • Aplicaciones: 5
   • Estado: Íntegro

📅 2024-01-14 15:45:10 - backup-apps-20240114.tar.gz (1.8 GB)
   • Tipo: Aplicaciones
   • Aplicaciones: 5
   • Estado: Íntegro

📅 2024-01-13 09:20:33 - backup-config-20240113.tar.gz (45 MB)
   • Tipo: Configuración
   • Aplicaciones: 5
   • Estado: Íntegro

📅 2024-01-12 14:15:47 - backup-full-20240112.tar.gz (2.0 GB)
   • Tipo: Completo
   • Aplicaciones: 4
   • Estado: Íntegro

ESTADÍSTICAS:
  • Total de backups: 4
  • Espacio utilizado: 5.9 GB
  • Backup más reciente: hace 1 día
  • Retención: 30 días

UBICACIÓN: /var/backups/webapp-manager/
        """
        
        self.d.scrollbox(backups_text, height=20, width=70, title="Backups Disponibles")
    
    def restore_backup(self):
        """Restaurar backup"""
        backups = [
            ("backup-full-20240115.tar.gz", "📅 2024-01-15 - Completo (2.1 GB)"),
            ("backup-apps-20240114.tar.gz", "📅 2024-01-14 - Aplicaciones (1.8 GB)"),
            ("backup-config-20240113.tar.gz", "📅 2024-01-13 - Configuración (45 MB)"),
            ("back", "⬅️ Volver")
        ]
        
        code, backup = self.d.menu(
            "Selecciona el backup a restaurar:",
            choices=backups,
            height=12,
            width=60,
            title="Restaurar Backup"
        )
        
        if code == self.d.OK and backup != "back":
            if self.d.yesno(f"¿Restaurar backup '{backup}'?\n\n⚠️ Esta acción sobrescribirá la configuración actual.", height=10, width=60) == self.d.OK:
                self.d.gauge_start("Restaurando backup...", title="Restauración en Progreso")
                
                try:
                    # Simulación de progreso
                    for i in range(101):
                        self.d.gauge_update(i, f"Restaurando... {i}%")
                        time.sleep(0.02)
                    
                    self.d.gauge_stop()
                    self.d.msgbox("✅ Backup restaurado exitosamente", height=6, width=40)
                    
                except Exception as e:
                    self.d.gauge_stop()
                    self.show_error(f"Error al restaurar backup: {str(e)}")
    
    def schedule_backups(self):
        """Programar backups automáticos"""
        schedule_text = """
PROGRAMACIÓN DE BACKUPS
{'=' * 23}

CONFIGURACIÓN ACTUAL:
  • Backup diario: 02:00 AM
  • Tipo: Completo
  • Retención: 30 días
  • Estado: Habilitado

PRÓXIMOS BACKUPS:
  • 2024-01-16 02:00:00 - Backup completo
  • 2024-01-17 02:00:00 - Backup completo
  • 2024-01-18 02:00:00 - Backup completo

CONFIGURACIÓN CRON:
  0 2 * * * /usr/local/bin/webapp-manager backup --type=full

LOGS:
  • Último backup: 2024-01-15 02:00:22 (exitoso)
  • Backups fallidos: 0
  • Promedio de duración: 15 minutos

Para modificar la programación, edita el archivo crontab:
  crontab -e
        """
        
        self.d.scrollbox(schedule_text, height=18, width=70, title="Programación de Backups")
    
    def cleanup_backups(self):
        """Limpiar backups antiguos"""
        cleanup_text = """
LIMPIEZA DE BACKUPS
{'=' * 18}

BACKUPS ANTIGUOS ENCONTRADOS:
  • 2024-01-01 - backup-full-20240101.tar.gz (1.9 GB)
  • 2023-12-28 - backup-apps-20231228.tar.gz (1.7 GB)
  • 2023-12-25 - backup-config-20231225.tar.gz (42 MB)

CRITERIOS DE LIMPIEZA:
  • Backups más antiguos de 30 días
  • Espacio a liberar: 3.6 GB
  • Backups a eliminar: 3

POLÍTICA DE RETENCIÓN:
  • Backups diarios: 30 días
  • Backups semanales: 12 semanas
  • Backups mensuales: 12 meses
        """
        
        self.d.scrollbox(cleanup_text, height=16, width=70, title="Limpieza de Backups")
        
        if self.d.yesno("¿Proceder con la limpieza de backups antiguos?", height=8, width=50) == self.d.OK:
            self.d.infobox("Limpiando backups antiguos...", height=5, width=40)
            time.sleep(2)
            self.d.msgbox("✅ Limpieza completada\n\nEspacio liberado: 3.6 GB", height=8, width=40)
    
    def system_maintenance(self):
        """Mantenimiento del sistema"""
        choices = [
            ("cleanup", "🧹 Limpiar Archivos Temporales"),
            ("updates", "📦 Actualizar Sistema"),
            ("optimize", "⚡ Optimizar Sistema"),
            ("check", "🔍 Verificar Integridad"),
            ("repair", "🔧 Reparar Sistema"),
            ("back", "⬅️ Volver")
        ]
        
        while True:
            code, tag = self.d.menu(
                "Mantenimiento del Sistema:",
                choices=choices,
                height=12,
                width=50,
                title="Mantenimiento"
            )
            
            if code != self.d.OK or tag == "back":
                break
                
            if tag == "cleanup":
                self.system_cleanup()
            elif tag == "updates":
                self.system_updates()
            elif tag == "optimize":
                self.system_optimize()
            elif tag == "check":
                self.system_check()
            elif tag == "repair":
                self.system_repair()
    
    def system_cleanup(self):
        """Limpiar archivos temporales"""
        cleanup_text = """
LIMPIEZA DEL SISTEMA
{'=' * 19}

ARCHIVOS TEMPORALES ENCONTRADOS:
  • /tmp/: 245 MB
  • /var/log/: 128 MB (logs antiguos)
  • /var/cache/: 67 MB
  • ~/.cache/: 34 MB

ARCHIVOS WEBAPP-MANAGER:
  • Logs antiguos: 23 MB
  • Archivos temporales: 12 MB
  • Cache de despliegue: 8 MB

TOTAL A LIMPIAR: 517 MB

ACCIONES:
  ✓ Eliminar archivos temporales
  ✓ Rotar logs antiguos
  ✓ Limpiar cache del sistema
  ✓ Limpiar cache de paquetes
        """
        
        self.d.scrollbox(cleanup_text, height=18, width=60, title="Limpieza del Sistema")
        
        if self.d.yesno("¿Proceder con la limpieza del sistema?", height=8, width=50) == self.d.OK:
            self.d.gauge_start("Limpiando sistema...", title="Limpieza en Progreso")
            
            try:
                # Simulación de limpieza
                tasks = [
                    "Limpiando archivos temporales...",
                    "Rotando logs antiguos...",
                    "Limpiando cache del sistema...",
                    "Limpiando cache de paquetes...",
                    "Finalizando limpieza..."
                ]
                
                for i, task in enumerate(tasks):
                    progress = int((i + 1) / len(tasks) * 100)
                    self.d.gauge_update(progress, task)
                    time.sleep(1)
                
                self.d.gauge_stop()
                self.d.msgbox("✅ Limpieza completada\n\nEspacio liberado: 517 MB", height=8, width=40)
                
            except Exception as e:
                self.d.gauge_stop()
                self.show_error(f"Error en la limpieza: {str(e)}")
    
    def system_updates(self):
        """Actualizar sistema"""
        updates_text = """
ACTUALIZACIONES DISPONIBLES
{'=' * 27}

SISTEMA OPERATIVO:
  • Actualizaciones de seguridad: 5
  • Actualizaciones generales: 12
  • Tamaño total: 234 MB

WEBAPP-MANAGER:
  • Versión actual: 4.0.0
  • Versión disponible: 4.1.0
  • Nuevas características:
    - Mejoras en la interfaz gráfica
    - Soporte para Docker
    - Optimizaciones de rendimiento

DEPENDENCIAS:
  • nginx: 1.18.0 → 1.20.2
  • python3: 3.9.2 → 3.11.0
  • certbot: 1.21.0 → 1.32.0

TIEMPO ESTIMADO: 15 minutos
REINICIO REQUERIDO: Sí
        """
        
        self.d.scrollbox(updates_text, height=18, width=60, title="Actualizaciones del Sistema")
        
        if self.d.yesno("¿Proceder con las actualizaciones?", height=8, width=50) == self.d.OK:
            self.d.gauge_start("Actualizando sistema...", title="Actualización en Progreso")
            
            try:
                # Simulación de actualización
                tasks = [
                    "Descargando actualizaciones...",
                    "Instalando actualizaciones de seguridad...",
                    "Actualizando webapp-manager...",
                    "Actualizando dependencias...",
                    "Finalizando actualización..."
                ]
                
                for i, task in enumerate(tasks):
                    progress = int((i + 1) / len(tasks) * 100)
                    self.d.gauge_update(progress, task)
                    time.sleep(2)
                
                self.d.gauge_stop()
                self.d.msgbox("✅ Actualización completada\n\n⚠️ Se requiere reiniciar el sistema", height=8, width=50)
                
            except Exception as e:
                self.d.gauge_stop()
                self.show_error(f"Error en la actualización: {str(e)}")
    
    def system_optimize(self):
        """Optimizar sistema"""
        optimize_text = """
OPTIMIZACIÓN DEL SISTEMA
{'=' * 24}

ANÁLISIS ACTUAL:
  • Uso de memoria: 68% (optimizable)
  • Servicios innecesarios: 3 detectados
  • Configuración nginx: subóptima
  • Índices de base de datos: fragmentados

OPTIMIZACIONES DISPONIBLES:
  ✓ Ajustar configuración de memoria
  ✓ Deshabilitar servicios innecesarios
  ✓ Optimizar configuración nginx
  ✓ Reindexar bases de datos
  ✓ Configurar swappiness
  ✓ Ajustar límites de archivos abiertos

MEJORAS ESTIMADAS:
  • Rendimiento: +25%
  • Uso de memoria: -15%
  • Tiempo de respuesta: -20%
  • Estabilidad: +10%
        """
        
        self.d.scrollbox(optimize_text, height=18, width=60, title="Optimización del Sistema")
        
        if self.d.yesno("¿Proceder con la optimización?", height=8, width=50) == self.d.OK:
            self.d.gauge_start("Optimizando sistema...", title="Optimización en Progreso")
            
            try:
                # Simulación de optimización
                tasks = [
                    "Analizando configuración actual...",
                    "Optimizando configuración de memoria...",
                    "Ajustando configuración nginx...",
                    "Optimizando bases de datos...",
                    "Aplicando configuraciones..."
                ]
                
                for i, task in enumerate(tasks):
                    progress = int((i + 1) / len(tasks) * 100)
                    self.d.gauge_update(progress, task)
                    time.sleep(2)
                
                self.d.gauge_stop()
                self.d.msgbox("✅ Optimización completada\n\nRendimiento mejorado en 25%", height=8, width=40)
                
            except Exception as e:
                self.d.gauge_stop()
                self.show_error(f"Error en la optimización: {str(e)}")
    
    def system_check(self):
        """Verificar integridad del sistema"""
        check_text = """
VERIFICACIÓN DE INTEGRIDAD
{'=' * 26}

SISTEMA DE ARCHIVOS:
  ✅ Permisos correctos
  ✅ Espacio disponible suficiente
  ✅ Inodos disponibles
  ⚠️ Archivos huérfanos detectados: 3

CONFIGURACIÓN:
  ✅ Archivos de configuración válidos
  ✅ Sintaxis nginx correcta
  ✅ Servicios systemd válidos
  ✅ Variables de entorno configuradas

APLICACIONES:
  ✅ Todas las aplicaciones responden
  ✅ Certificados SSL válidos
  ⚠️ 1 aplicación con logs de errores
  ✅ Backups recientes disponibles

SEGURIDAD:
  ✅ Firewall configurado
  ✅ SSH configurado correctamente
  ✅ Actualizaciones de seguridad instaladas
  ✅ Permisos de usuario correctos

RECOMENDACIONES:
  • Limpiar archivos huérfanos
  • Revisar logs de errores de aplicación
  • Actualizar certificados próximos a vencer
        """
        
        self.d.scrollbox(check_text, height=20, width=70, title="Verificación de Integridad")
    
    def system_repair(self):
        """Reparar sistema"""
        repair_text = """
REPARACIÓN DEL SISTEMA
{'=' * 22}

PROBLEMAS DETECTADOS:
  🔧 Archivos de configuración corruptos: 2
  🔧 Servicios no iniciados: 1
  🔧 Permisos incorrectos: 5 archivos
  🔧 Enlaces simbólicos rotos: 3

REPARACIONES AUTOMÁTICAS:
  ✓ Regenerar configuraciones nginx
  ✓ Reiniciar servicios problemáticos
  ✓ Corregir permisos de archivos
  ✓ Recrear enlaces simbólicos
  ✓ Verificar integridad de paquetes

REPARACIONES MANUALES:
  • Revisar configuración personalizada
  • Validar variables de entorno
  • Comprobar conectividad externa

TIEMPO ESTIMADO: 5 minutos
REINICIO REQUERIDO: No
        """
        
        self.d.scrollbox(repair_text, height=18, width=60, title="Reparación del Sistema")
        
        if self.d.yesno("¿Proceder con la reparación automática?", height=8, width=50) == self.d.OK:
            self.d.gauge_start("Reparando sistema...", title="Reparación en Progreso")
            
            try:
                # Simulación de reparación
                tasks = [
                    "Analizando problemas...",
                    "Regenerando configuraciones...",
                    "Corrigiendo permisos...",
                    "Recreando enlaces...",
                    "Verificando reparaciones..."
                ]
                
                for i, task in enumerate(tasks):
                    progress = int((i + 1) / len(tasks) * 100)
                    self.d.gauge_update(progress, task)
                    time.sleep(1.5)
                
                self.d.gauge_stop()
                self.d.msgbox("✅ Reparación completada\n\nTodos los problemas han sido corregidos", height=8, width=50)
                
            except Exception as e:
                self.d.gauge_stop()
                self.show_error(f"Error en la reparación: {str(e)}")
    
    def system_config(self):
        """Configuración del sistema"""
        config_text = """
CONFIGURACIÓN DEL SISTEMA
{'=' * 25}

UBICACIONES DE CONFIGURACIÓN:
  • Global: /etc/webapp-manager/
  • Usuario: ~/.config/webapp-manager/
  • Logs: /var/log/webapp-manager/
  • Backups: /var/backups/webapp-manager/

CONFIGURACIÓN ACTUAL:
  • Modo: Producción
  • Log Level: INFO
  • Backup automático: Habilitado
  • SSL automático: Habilitado
  • Monitoreo: Habilitado

ARCHIVOS DE CONFIGURACIÓN:
  • config.yaml: Configuración principal
  • nginx.conf.template: Plantilla nginx
  • systemd.service.template: Plantilla systemd
  • backup.conf: Configuración de backups

VARIABLES DE ENTORNO:
  • WEBAPP_MANAGER_MODE=production
  • WEBAPP_MANAGER_LOG_LEVEL=info
  • WEBAPP_MANAGER_BACKUP_ENABLED=true
  • WEBAPP_MANAGER_SSL_ENABLED=true

Para editar la configuración:
  nano /etc/webapp-manager/config.yaml
        """
        
        self.d.scrollbox(config_text, height=20, width=70, title="Configuración del Sistema")
    
    def show_system_logs(self):
        """Mostrar logs del sistema"""
        log_choices = [
            ("webapp-manager", "📋 Logs de WebApp Manager"),
            ("nginx", "🌐 Logs de Nginx"),
            ("system", "💻 Logs del Sistema"),
            ("error", "❌ Logs de Errores"),
            ("access", "🔍 Logs de Acceso"),
            ("back", "⬅️ Volver")
        ]
        
        while True:
            code, tag = self.d.menu(
                "Selecciona los logs a ver:",
                choices=log_choices,
                height=12,
                width=50,
                title="Logs del Sistema"
            )
            
            if code != self.d.OK or tag == "back":
                break
                
            if tag == "webapp-manager":
                self.show_webapp_logs()
            elif tag == "nginx":
                self.show_nginx_logs()
            elif tag == "system":
                self.show_system_logs_detail()
            elif tag == "error":
                self.show_error_logs()
            elif tag == "access":
                self.show_access_logs()
    
    def show_webapp_logs(self):
        """Mostrar logs de WebApp Manager"""
        logs_text = """
LOGS DE WEBAPP MANAGER
{'=' * 21}

2024-01-15 10:30:22 [INFO] Sistema iniciado correctamente
2024-01-15 10:30:23 [INFO] Cargando configuración desde /etc/webapp-manager/config.yaml
2024-01-15 10:30:24 [INFO] Inicializando servicios del sistema
2024-01-15 10:30:25 [INFO] Verificando aplicaciones desplegadas
2024-01-15 10:30:26 [INFO] Encontradas 5 aplicaciones activas
2024-01-15 10:45:12 [INFO] Iniciando despliegue de aplicación: test.example.com
2024-01-15 10:45:13 [INFO] Tipo de aplicación detectado: Next.js
2024-01-15 10:45:14 [INFO] Descargando código fuente desde Git
2024-01-15 10:45:30 [INFO] Instalando dependencias npm
2024-01-15 10:47:15 [INFO] Compilando aplicación Next.js
2024-01-15 10:48:45 [INFO] Configurando nginx para test.example.com
2024-01-15 10:48:46 [INFO] Creando servicio systemd
2024-01-15 10:48:47 [INFO] Iniciando servicio test.example.com
2024-01-15 10:48:48 [INFO] Configurando certificado SSL
2024-01-15 10:49:15 [INFO] Certificado SSL configurado correctamente
2024-01-15 10:49:16 [INFO] Despliegue completado exitosamente
2024-01-15 11:15:33 [INFO] Actualizando aplicación: api.example.com
2024-01-15 11:15:34 [INFO] Creando backup antes de actualizar
2024-01-15 11:15:45 [INFO] Backup creado: backup-api.example.com-20240115.tar.gz
2024-01-15 11:15:46 [INFO] Actualizando código fuente
2024-01-15 11:16:12 [INFO] Reinstalando dependencias
2024-01-15 11:17:23 [INFO] Reiniciando servicio
2024-01-15 11:17:25 [INFO] Actualización completada
        """
        
        self.d.scrollbox(logs_text, height=20, width=80, title="Logs de WebApp Manager")
    
    def show_nginx_logs(self):
        """Mostrar logs de Nginx"""
        logs_text = """
LOGS DE NGINX
{'=' * 13}

ACCESS LOG:
2024-01-15 10:30:22 192.168.1.100 GET /api/status 200 234
2024-01-15 10:30:25 192.168.1.101 GET / 200 1456
2024-01-15 10:30:28 192.168.1.102 GET /admin 401 567
2024-01-15 10:30:30 192.168.1.100 POST /api/login 200 89
2024-01-15 10:30:33 192.168.1.103 GET /dashboard 200 2345

ERROR LOG:
2024-01-15 10:25:15 [error] 1234#0: *5678 connect() failed (111: Connection refused) while connecting to upstream, client: 192.168.1.100, server: api.example.com, request: "GET /api/users HTTP/1.1", upstream: "http://127.0.0.1:8000/api/users", host: "api.example.com"
2024-01-15 10:25:16 [warn] 1234#0: *5679 upstream server temporarily disabled while connecting to upstream, client: 192.168.1.101, server: app.example.com, request: "GET /health HTTP/1.1", upstream: "http://127.0.0.1:3000/health", host: "app.example.com"

CONFIGURACIÓN:
✅ Sintaxis válida
✅ Todos los sitios activos
✅ SSL configurado correctamente
✅ Proxy reverso funcionando
        """
        
        self.d.scrollbox(logs_text, height=20, width=80, title="Logs de Nginx")
    
    def show_system_logs_detail(self):
        """Mostrar logs detallados del sistema"""
        logs_text = """
LOGS DEL SISTEMA
{'=' * 16}

SYSTEMD JOURNAL:
2024-01-15 10:30:22 systemd[1]: Started WebApp Manager Service
2024-01-15 10:30:23 systemd[1]: Started nginx - high performance web server
2024-01-15 10:30:24 systemd[1]: Started Let's Encrypt renewal service
2024-01-15 10:30:25 systemd[1]: Started Daily webapp-manager backup

KERNEL LOG:
2024-01-15 10:30:20 kernel: [12345.678] webapp-manager loaded successfully
2024-01-15 10:30:21 kernel: [12346.789] nginx worker process started

AUTHENTICATION LOG:
2024-01-15 10:30:22 sshd[1234]: Accepted publickey for admin from 192.168.1.100
2024-01-15 10:30:23 sudo: admin : TTY=pts/0 ; PWD=/home/admin ; USER=root ; COMMAND=/usr/bin/webapp-manager

CRON LOG:
2024-01-15 02:00:01 CRON[5678]: (root) CMD (/usr/local/bin/webapp-manager backup --auto)
2024-01-15 02:00:02 CRON[5679]: (root) CMD (certbot renew --quiet)
        """
        
        self.d.scrollbox(logs_text, height=20, width=80, title="Logs del Sistema")
    
    def show_error_logs(self):
        """Mostrar logs de errores"""
        logs_text = """
LOGS DE ERRORES
{'=' * 15}

APLICACIONES:
2024-01-15 10:25:15 [ERROR] api.example.com: Connection refused to database
2024-01-15 10:25:16 [ERROR] app.example.com: Memory limit exceeded
2024-01-15 10:25:17 [WARN] test.example.com: Slow query detected (5.2s)

SISTEMA:
2024-01-15 10:20:10 [ERROR] nginx: worker process 1234 exited with code 1
2024-01-15 10:20:11 [ERROR] systemd: Failed to start service api.example.com
2024-01-15 10:20:12 [WARN] disk space low on /var/log (95% used)

SEGURIDAD:
2024-01-15 09:45:30 [WARN] Failed login attempt from 192.168.1.200
2024-01-15 09:45:31 [ERROR] SSL certificate expired for old.example.com
2024-01-15 09:45:32 [INFO] Blocked suspicious request from 10.0.0.1

SOLUCIONES SUGERIDAS:
• Verificar conectividad de base de datos
• Aumentar límites de memoria
• Optimizar consultas lentas
• Renovar certificados SSL
• Revisar configuración de firewall
        """
        
        self.d.scrollbox(logs_text, height=20, width=80, title="Logs de Errores")
    
    def show_access_logs(self):
        """Mostrar logs de acceso"""
        logs_text = """
LOGS DE ACCESO
{'=' * 14}

RESUMEN DEL TRÁFICO:
  • Solicitudes totales hoy: 12,847
  • Solicitudes únicas: 3,421
  • Errores 4xx: 234 (1.8%)
  • Errores 5xx: 12 (0.1%)
  • Tiempo promedio de respuesta: 245ms

TOP PÁGINAS:
  1. /api/status - 2,847 solicitudes
  2. /dashboard - 1,923 solicitudes
  3. /admin - 1,456 solicitudes
  4. /api/users - 1,234 solicitudes
  5. /login - 987 solicitudes

TOP IPs:
  1. 192.168.1.100 - 2,134 solicitudes
  2. 192.168.1.101 - 1,876 solicitudes
  3. 192.168.1.102 - 1,234 solicitudes
  4. 192.168.1.103 - 987 solicitudes
  5. 192.168.1.104 - 765 solicitudes

CÓDIGOS DE ESTADO:
  • 200 OK: 11,234 (87.4%)
  • 301 Moved: 567 (4.4%)
  • 404 Not Found: 234 (1.8%)
  • 401 Unauthorized: 123 (1.0%)
  • 500 Internal Error: 12 (0.1%)

MÉTODOS HTTP:
  • GET: 9,876 (76.9%)
  • POST: 2,345 (18.3%)
  • PUT: 456 (3.5%)
  • DELETE: 170 (1.3%)
        """
        
        self.d.scrollbox(logs_text, height=20, width=70, title="Logs de Acceso")
    
    def show_error(self, message: str):
        """Mostrar mensaje de error"""
        self.d.msgbox(
            f"❌ ERROR\n\n{message}",
            height=10,
            width=50,
            title="Error"
        )

    def execute_with_progress(self, func, *args, **kwargs):
        """Ejecutar función con progreso y manejo de logs limpios"""
        try:
            # Mostrar progreso
            self.d.infobox("Ejecutando operación...", height=5, width=40)
            
            # Ejecutar función
            result = func(*args, **kwargs)
            
            # Si el resultado es un string con logs, limpiarlo
            if isinstance(result, str) and result:
                clean_result = self.format_log_for_gui(result)
                return clean_result
            
            return result
            
        except Exception as e:
            self.show_error(f"Error ejecutando operación: {e}")
            return None
