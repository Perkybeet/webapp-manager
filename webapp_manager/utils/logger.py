"""
Sistema de logging profesional y estructurado para WebApp Manager
"""

from enum import Enum
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.table import Table
from datetime import datetime


class LogLevel(Enum):
    """Niveles de log"""
    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Logger:
    """Logger profesional con formato estructurado"""
    
    # Iconos y estilos por nivel
    LEVEL_CONFIG = {
        LogLevel.DEBUG: {"icon": "🔍", "style": "dim cyan", "prefix": "DEBUG"},
        LogLevel.INFO: {"icon": "ℹ️", "style": "blue", "prefix": "INFO"},
        LogLevel.SUCCESS: {"icon": "✅", "style": "bold green", "prefix": "OK"},
        LogLevel.WARNING: {"icon": "⚠️", "style": "yellow", "prefix": "WARN"},
        LogLevel.ERROR: {"icon": "❌", "style": "bold red", "prefix": "ERROR"},
        LogLevel.CRITICAL: {"icon": "🔥", "style": "bold white on red", "prefix": "CRITICAL"},
    }
    
    def __init__(self, verbose: bool = False, quiet: bool = False, progress_manager=None):
        """
        Inicializar logger
        
        Args:
            verbose: Mostrar logs detallados (DEBUG level)
            quiet: Mostrar solo errores y críticos
            progress_manager: Progress manager para integración con barras de progreso
        """
        self.console = Console()
        self.verbose = verbose
        self.quiet = quiet
        self.indent_level = 0
        self.operation_start_time = None
        self.progress_manager = progress_manager
        
    def _should_log(self, level: LogLevel) -> bool:
        """Determinar si se debe mostrar el log según el nivel"""
        if self.quiet:
            return level in [LogLevel.ERROR, LogLevel.CRITICAL]
        if not self.verbose and level == LogLevel.DEBUG:
            return False
        return True
    
    def _format_message(self, message: str, level: LogLevel) -> str:
        """Formatear mensaje con indentación"""
        config = self.LEVEL_CONFIG[level]
        indent = "  " * self.indent_level
        
        # En modo verbose, incluir timestamp y nivel
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            return f"{indent}[{timestamp}] [{config['prefix']:8}] {message}"
        else:
            return f"{indent}{message}"
    
    def log(self, message: str, level: LogLevel = LogLevel.INFO):
        """Log genérico"""
        if not self._should_log(level):
            return
        
        config = self.LEVEL_CONFIG[level]
        formatted_msg = self._format_message(message, level)
        
        # Si hay progress_manager y no estamos en verbose, usar su sistema de logs
        if self.progress_manager and not self.verbose:
            if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                self.progress_manager.error(message)
            elif level == LogLevel.WARNING:
                self.progress_manager.warning(message)
            elif level == LogLevel.SUCCESS:
                self.progress_manager.success(message)
            else:
                self.progress_manager.log(message, "dim" if level == LogLevel.DEBUG else "white")
        else:
            # Fallback a impresión normal
            if self.verbose:
                self.console.print(f"[{config['style']}]{formatted_msg}[/{config['style']}]")
            else:
                self.console.print(f"[{config['style']}]{config['icon']} {formatted_msg}[/{config['style']}]")
    
    def debug(self, message: str):
        """Log de debug"""
        self.log(message, LogLevel.DEBUG)
    
    def info(self, message: str):
        """Log informativo"""
        self.log(message, LogLevel.INFO)
    
    def success(self, message: str):
        """Log de éxito"""
        self.log(message, LogLevel.SUCCESS)
    
    def warning(self, message: str):
        """Log de advertencia"""
        self.log(message, LogLevel.WARNING)
    
    def error(self, message: str):
        """Log de error"""
        self.log(message, LogLevel.ERROR)
    
    def critical(self, message: str):
        """Log crítico"""
        self.log(message, LogLevel.CRITICAL)
    
    def step(self, message: str, current: int = None, total: int = None):
        """
        Log de paso con contador opcional
        
        Args:
            message: Mensaje del paso
            current: Paso actual (opcional)
            total: Total de pasos (opcional)
        """
        if not self._should_log(LogLevel.INFO):
            return
        
        if current is not None and total is not None:
            prefix = f"[{current}/{total}]"
            self.console.print(f"[bold cyan]▶ {prefix}[/bold cyan] {message}")
        else:
            self.console.print(f"[bold cyan]▶[/bold cyan] {message}")
    
    def substep(self, message: str):
        """Log de sub-paso"""
        if not self._should_log(LogLevel.INFO):
            return
        
        # Si hay progress_manager y no estamos en verbose, usar su sistema de logs
        if self.progress_manager and not self.verbose:
            # Agregar el substep como un log en el progress manager
            self.progress_manager.log_lines.append(Text(f"  → {message}", style="cyan"))
            if len(self.progress_manager.log_lines) > self.progress_manager.max_log_lines:
                self.progress_manager.log_lines.pop(0)
            self.progress_manager._update_display()
        else:
            indent = "  " * (self.indent_level + 1)
            self.console.print(f"[cyan]{indent}→[/cyan] {message}")
    
    def command(self, command: str, show: bool = None):
        """
        Log de comando ejecutado
        
        Args:
            command: Comando ejecutado
            show: Forzar mostrar comando (None usa verbose)
        """
        should_show = show if show is not None else self.verbose
        
        if not should_show:
            return
        
        # Truncar comandos muy largos
        if len(command) > 100:
            command = command[:97] + "..."
        
        indent = "  " * (self.indent_level + 1)
        self.console.print(f"[dim]{indent}$ {command}[/dim]")
    
    def command_output(self, output: str, max_lines: int = 10):
        """
        Log de salida de comando
        
        Args:
            output: Salida del comando
            max_lines: Máximo de líneas a mostrar
        """
        if not self.verbose or not output:
            return
        
        lines = output.split('\n')
        indent = "  " * (self.indent_level + 2)
        
        # Mostrar solo las primeras y últimas líneas si es muy largo
        if len(lines) > max_lines:
            shown_lines = lines[:max_lines//2] + ["..."] + lines[-max_lines//2:]
        else:
            shown_lines = lines
        
        for line in shown_lines:
            if line.strip():
                self.console.print(f"[dim]{indent}{line}[/dim]")
    
    def header(self, title: str, subtitle: str = None):
        """
        Mostrar encabezado de sección
        
        Args:
            title: Título principal
            subtitle: Subtítulo opcional
        """
        separator = "━" * 80
        
        self.console.print()
        self.console.print(f"[bold cyan]{separator}[/bold cyan]")
        self.console.print(f"[bold white]{title.center(80)}[/bold white]")
        if subtitle:
            self.console.print(f"[dim]{subtitle.center(80)}[/dim]")
        self.console.print(f"[bold cyan]{separator}[/bold cyan]")
        self.console.print()
    
    def section(self, title: str):
        """Mostrar título de sección"""
        self.console.print()
        self.console.print(f"[bold magenta]╭─ {title}[/bold magenta]")
        self.indent_level += 1
    
    def end_section(self):
        """Finalizar sección"""
        if self.indent_level > 0:
            self.indent_level -= 1
        self.console.print(f"[bold magenta]╰─[/bold magenta]")
        self.console.print()
    
    def table(self, title: str, columns: List[str], rows: List[List[str]], 
              show_header: bool = True):
        """
        Mostrar tabla de datos
        
        Args:
            title: Título de la tabla
            columns: Nombres de columnas
            rows: Filas de datos
            show_header: Mostrar encabezado
        """
        table = Table(title=title, show_header=show_header, header_style="bold cyan")
        
        for col in columns:
            table.add_column(col)
        
        for row in rows:
            table.add_row(*row)
        
        self.console.print(table)
    
    def panel(self, content: str, title: str = None, style: str = "blue"):
        """
        Mostrar panel con contenido
        
        Args:
            content: Contenido del panel
            title: Título opcional
            style: Estilo del borde
        """
        self.console.print(Panel(content, title=title, border_style=style))
    
    def tree(self, root_label: str, items: dict):
        """
        Mostrar estructura de árbol
        
        Args:
            root_label: Etiqueta raíz
            items: Diccionario con items del árbol
        """
        tree = Tree(root_label)
        
        def add_items(parent, items_dict):
            for key, value in items_dict.items():
                if isinstance(value, dict):
                    branch = parent.add(key)
                    add_items(branch, value)
                else:
                    parent.add(f"{key}: {value}")
        
        add_items(tree, items)
        self.console.print(tree)
    
    def operation_start(self, operation: str):
        """Iniciar operación cronometrada"""
        self.operation_start_time = datetime.now()
        self.step(operation)
    
    def operation_end(self, success: bool = True, message: str = None):
        """Finalizar operación cronometrada"""
        if self.operation_start_time:
            elapsed = (datetime.now() - self.operation_start_time).total_seconds()
            elapsed_str = f"({elapsed:.2f}s)"
            
            if success:
                msg = message or "Operación completada"
                self.success(f"{msg} {elapsed_str}")
            else:
                msg = message or "Operación fallida"
                self.error(f"{msg} {elapsed_str}")
            
            self.operation_start_time = None
    
    def progress_bar(self, total: int, description: str = "Procesando"):
        """
        Crear barra de progreso
        
        Args:
            total: Total de items
            description: Descripción de la tarea
            
        Returns:
            Contexto de progreso Rich
        """
        from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
        
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        )
    
    def newline(self, count: int = 1):
        """Imprimir líneas en blanco"""
        for _ in range(count):
            self.console.print()
    
    def rule(self, title: str = None):
        """Imprimir línea separadora"""
        from rich.rule import Rule
        if title:
            self.console.print(Rule(title, style="cyan"))
        else:
            self.console.print(Rule(style="dim"))
    
    def summary(self, items: dict, title: str = "Resumen"):
        """
        Mostrar resumen de operación
        
        Args:
            items: Diccionario con items del resumen
            title: Título del resumen
        """
        self.console.print()
        self.console.print(Panel.fit(
            "\n".join([f"[cyan]{k}:[/cyan] [white]{v}[/white]" for k, v in items.items()]),
            title=f"[bold]{title}[/bold]",
            border_style="green"
        ))
        self.console.print()
