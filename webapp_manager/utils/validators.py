"""
Utilidades para validación de datos
"""

import re
from typing import Union


class Validators:
    """Validadores de datos comunes"""
    
    @staticmethod
    def validate_domain(domain: str) -> bool:
        """Validar formato de dominio"""
        if not domain or len(domain) > 253:
            return False
        
        pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
        return bool(re.match(pattern, domain))
    
    @staticmethod
    def validate_port(port: Union[int, str]) -> bool:
        """Validar puerto"""
        try:
            port_int = int(port)
            return 1024 <= port_int <= 65535
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_app_type(app_type: str) -> bool:
        """Validar tipo de aplicación"""
        valid_types = ["nextjs", "node", "static", "fastapi"]
        return app_type in valid_types
    
    @staticmethod
    def validate_branch_name(branch: str) -> bool:
        """Validar nombre de rama git"""
        if not branch or len(branch) > 255:
            return False
        
        # Patrones no permitidos en nombres de rama
        invalid_patterns = [
            r"^\.",      # No puede empezar con punto
            r"\.\.",     # No puede contener doble punto
            r"[@{~^:]",  # Caracteres especiales no permitidos
            r"\\",       # No puede contener backslash
            r"\s",       # No puede contener espacios
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, branch):
                return False
        
        return True
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validar formato de email"""
        if not email:
            return False
        
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_env_var(env_var: str) -> tuple[bool, str, str]:
        """
        Validar variable de entorno
        Returns: (is_valid, key, value)
        """
        if not env_var or "=" not in env_var:
            return False, "", ""
        
        key, value = env_var.split("=", 1)
        key = key.strip()
        value = value.strip()
        
        # Validar clave
        if not key or not re.match(r"^[A-Z_][A-Z0-9_]*$", key):
            return False, key, value
        
        return True, key, value
