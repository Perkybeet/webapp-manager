"""
WebApp Manager - Sistema completo de gestión de aplicaciones web
Versión 3.0 - Arquitectura modular y escalable
"""

__version__ = "3.0.0"
__description__ = "Sistema completo de gestión de aplicaciones web con nginx proxy reverso"
__author__ = "WebApp Manager Team"

from .core.manager import WebAppManager
from .models.app_config import AppConfig
from .utils.colors import Colors

__all__ = ['WebAppManager', 'AppConfig', 'Colors']
