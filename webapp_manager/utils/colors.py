"""
Colores y estilos para output terminal moderno con Rich
"""

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from typing import Optional


class Colors:
    """Colores y utilidades de formato modernas con Rich"""
    
    # Mantener compatibilidad con códigos ANSI básicos
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    DIM = "\033[2m"
    END = "\033[0m"
    ENDC = "\033[0m"
    
    # Console global para uso en toda la aplicación
    console = Console()
    
    @classmethod
    def success(cls, text: str) -> str:
        """Texto de éxito en verde - compatibilidad legacy"""
        return f"{cls.GREEN}✅ {text}{cls.END}"
    
    @classmethod
    def error(cls, text: str) -> str:
        """Texto de error en rojo - compatibilidad legacy"""
        return f"{cls.RED}❌ {text}{cls.END}"
    
    @classmethod
    def warning(cls, text: str) -> str:
        """Texto de advertencia en amarillo - compatibilidad legacy"""
        return f"{cls.YELLOW}⚠️  {text}{cls.END}"
    
    @classmethod
    def info(cls, text: str) -> str:
        """Texto informativo en azul - compatibilidad legacy"""
        return f"{cls.BLUE}ℹ️  {text}{cls.END}"
    
    @classmethod
    def step(cls, step: int, total: int, text: str) -> str:
        """Texto de paso - versión mejorada"""
        percentage = int((step / total) * 100)
        progress_bar = "█" * (percentage // 10) + "░" * (10 - percentage // 10)
        return f"{cls.CYAN}[{step:2d}/{total:2d}] {progress_bar} {percentage:3d}% {text}{cls.END}"
    
    @classmethod
    def header(cls, text: str) -> str:
        """Crear encabezado moderno"""
        separator = "═" * 80
        return f"""{cls.BOLD}{cls.CYAN}{separator}{cls.END}
{cls.BOLD}{cls.CYAN}{text.center(80)}{cls.END}
{cls.BOLD}{cls.CYAN}{separator}{cls.END}"""
    
    @classmethod
    def bold(cls, text: str) -> str:
        """Texto en negrita"""
        return f"{cls.BOLD}{text}{cls.END}"
    
    @classmethod
    def dim(cls, text: str) -> str:
        """Texto atenuado"""
        return f"{cls.DIM}{text}{cls.END}"
    
    # Nuevos métodos con Rich
    @classmethod
    def print_success(cls, text: str, title: Optional[str] = None):
        """Imprimir mensaje de éxito con Rich"""
        cls.console.print(f"[bold green]✅ {text}[/bold green]")
    
    @classmethod
    def print_error(cls, text: str, title: Optional[str] = None):
        """Imprimir mensaje de error con Rich"""
        cls.console.print(f"[bold red]❌ {text}[/bold red]")
    
    @classmethod
    def print_warning(cls, text: str, title: Optional[str] = None):
        """Imprimir mensaje de advertencia con Rich"""
        cls.console.print(f"[bold yellow]⚠️  {text}[/bold yellow]")
    
    @classmethod
    def print_info(cls, text: str, title: Optional[str] = None):
        """Imprimir mensaje informativo con Rich"""
        cls.console.print(f"[bold blue]ℹ️  {text}[/bold blue]")
    
    @classmethod
    def print_panel(cls, content: str, title: str, style: str = "blue"):
        """Imprimir panel con Rich"""
        cls.console.print(Panel(content, title=title, border_style=style))
    
    @classmethod
    def create_progress(cls, description: str = "Procesando..."):
        """Crear barra de progreso moderna"""
        return Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=cls.console,
            expand=True
        )