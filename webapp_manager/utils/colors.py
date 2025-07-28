"""
Colores y estilos para output terminal
"""


class Colors:
    """Códigos de color ANSI para terminal"""
    
    # Colores básicos
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    
    # Estilos
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    DIM = "\033[2m"
    
    # Reset
    END = "\033[0m"
    ENDC = "\033[0m"  # Alias para compatibilidad
    
    @classmethod
    def success(cls, text: str) -> str:
        """Texto de éxito en verde"""
        return f"{cls.GREEN}✅ {text}{cls.END}"
    
    @classmethod
    def error(cls, text: str) -> str:
        """Texto de error en rojo"""
        return f"{cls.RED}❌ {text}{cls.END}"
    
    @classmethod
    def warning(cls, text: str) -> str:
        """Texto de advertencia en amarillo"""
        return f"{cls.YELLOW}⚠️  {text}{cls.END}"
    
    @classmethod
    def info(cls, text: str) -> str:
        """Texto informativo en azul"""
        return f"{cls.BLUE}ℹ️  {text}{cls.END}"
    
    @classmethod
    def step(cls, step: int, total: int, text: str) -> str:
        """Texto de paso en magenta"""
        return f"{cls.MAGENTA}[{step}/{total}] {text}{cls.END}"
    
    @classmethod
    def header(cls, text: str) -> str:
        """Crear encabezado con estilo simple y compatible"""
        separator = "=" * 80
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
