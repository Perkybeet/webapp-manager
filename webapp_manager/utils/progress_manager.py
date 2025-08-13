"""
Gestor de progreso para mostrar barras de progreso con información real
"""

import time
from typing import Optional, Dict, Any
from contextlib import contextmanager
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn
)
from rich.live import Live
from rich.panel import Panel
from rich.text import Text


class ProgressManager:
    """Gestor centralizado de progreso con Rich"""
    
    def __init__(self, console: Console, verbose: bool = False):
        self.console = console
        self.verbose = verbose
        self.progress = None
        self.live = None
        self.tasks: Dict[str, Any] = {}
        self.log_buffer = []
        self.max_log_lines = 10
        
    def start(self):
        """Iniciar el sistema de progreso"""
        if not self.verbose:
            # En modo no verbose, usar Live display con barra de progreso
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=60),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=self.console,
                expand=True
            )
            self.live = Live(self.progress, console=self.console, refresh_per_second=10)
            self.live.start()
    
    def stop(self):
        """Detener el sistema de progreso"""
        try:
            if self.live:
                self.live.stop()
                self.live = None
        except Exception:
            # Si hay error deteniendo, simplemente continuar
            pass
        
        self.progress = None
        self.tasks.clear()
        self.log_buffer.clear()
    
    def force_cleanup(self):
        """Forzar limpieza del progreso en caso de error"""
        try:
            # Limpiar todas las tareas activas
            if self.progress:
                for task_id in list(self.tasks.values()):
                    try:
                        self.progress.remove_task(task_id)
                    except Exception:
                        pass
            
            # Detener el live display
            self.stop()
            
            # Limpiar la consola si es necesario
            self.console.print("\n[dim]Sistema de progreso reiniciado[/dim]")
            
        except Exception:
            # Si todo falla, al menos limpiar las variables
            self.progress = None
            self.live = None
            self.tasks.clear()
            self.log_buffer.clear()
    
    @contextmanager
    def task(self, description: str, total: Optional[int] = None):
        """Context manager para una tarea con progreso"""
        task_id = None
        try:
            # En modo verbose, solo mostrar el mensaje
            if self.verbose:
                self.console.print(f"[cyan]▶ {description}[/cyan]")
                yield None
            else:
                # En modo no verbose, crear tarea de progreso
                if not self.progress:
                    self.start()
                
                task_id = self.progress.add_task(description, total=total or 100)
                self.tasks[description] = task_id
                yield task_id
                
        except KeyboardInterrupt:
            # Manejar interrupción del usuario
            self.console.print("\n[bold red]⚠️  Operación cancelada por el usuario[/bold red]")
            raise
        except Exception as e:
            # Manejar errores
            self.console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
            raise
        finally:
            # Limpiar tarea - SIEMPRE se ejecuta
            if task_id is not None and self.progress:
                try:
                    self.progress.update(task_id, completed=total or 100)
                    self.progress.remove_task(task_id)
                except Exception:
                    # Si hay error removiendo la tarea, simplemente continuar
                    pass
            
            if description in self.tasks:
                del self.tasks[description]
    
    def update(self, task_id: Optional[str], advance: int = 1, description: Optional[str] = None):
        """Actualizar progreso de una tarea"""
        if self.verbose:
            # En modo verbose, mostrar descripción si se proporciona
            if description:
                self.console.print(f"  [dim]→ {description}[/dim]")
        else:
            # En modo no verbose, actualizar barra de progreso
            if task_id is not None and self.progress:
                update_kwargs = {"advance": advance}
                if description:
                    update_kwargs["description"] = description
                self.progress.update(task_id, **update_kwargs)
    
    def log(self, message: str, style: str = "dim"):
        """Agregar un log que se muestra según el modo"""
        if self.verbose:
            # En modo verbose, mostrar inmediatamente
            self.console.print(f"[{style}]{message}[/{style}]")
        else:
            # En modo no verbose, agregar al buffer
            self.log_buffer.append((message, style))
            if len(self.log_buffer) > self.max_log_lines:
                self.log_buffer.pop(0)
    
    def error(self, message: str):
        """Mostrar mensaje de error (siempre visible)"""
        self.console.print(f"[bold red]❌ {message}[/bold red]")
    
    def warning(self, message: str):
        """Mostrar mensaje de advertencia (siempre visible)"""
        self.console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")
    
    def success(self, message: str):
        """Mostrar mensaje de éxito (siempre visible)"""
        self.console.print(f"[bold green]✅ {message}[/bold green]")
    
    def info(self, message: str):
        """Mostrar mensaje informativo según el modo"""
        if self.verbose:
            self.console.print(f"[bold blue]ℹ️  {message}[/bold blue]")
        else:
            self.log(f"ℹ️  {message}", "blue")
    
    def step(self, current: int, total: int, description: str):
        """Mostrar un paso del proceso"""
        if self.verbose:
            percentage = int((current / total) * 100)
            self.console.print(f"[cyan][{current}/{total}] {description} ({percentage}%)[/cyan]")
        else:
            # En modo no verbose, actualizar la tarea principal si existe
            if self.tasks:
                # Obtener la primera tarea activa
                task_id = next(iter(self.tasks.values()), None)
                if task_id is not None:
                    self.progress.update(
                        task_id, 
                        completed=int((current / total) * 100),
                        description=f"[{current}/{total}] {description}"
                    )
    
    @contextmanager
    def live_display(self):
        """Context manager para usar Live display directamente"""
        if self.verbose:
            yield None
        else:
            with Live(console=self.console, refresh_per_second=4) as live:
                yield live