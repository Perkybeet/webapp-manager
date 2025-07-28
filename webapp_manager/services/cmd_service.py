"""
Servicio para ejecutar comandos del sistema
"""

import subprocess
import sys
import os
from typing import Optional


class CmdService:
    """Servicio para ejecutar comandos del sistema"""
    
    def __init__(self):
        self.encoding = 'utf-8'
    
    def run(self, command: str, check: bool = True, timeout: Optional[int] = None) -> Optional[str]:
        """
        Ejecutar comando del sistema
        
        Args:
            command: Comando a ejecutar
            check: Si debe lanzar excepción en caso de error
            timeout: Timeout en segundos
            
        Returns:
            Salida del comando o None si falló
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding=self.encoding,
                timeout=timeout,
                check=check
            )
            
            return result.stdout.strip() if result.stdout else ""
            
        except subprocess.CalledProcessError as e:
            if check:
                return None
            return e.stdout.strip() if e.stdout else ""
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None
    
    def run_interactive(self, command: str) -> int:
        """
        Ejecutar comando interactivo
        
        Args:
            command: Comando a ejecutar
            
        Returns:
            Código de salida
        """
        try:
            return subprocess.run(command, shell=True).returncode
        except Exception:
            return 1
    
    def run_background(self, command: str) -> Optional[subprocess.Popen]:
        """
        Ejecutar comando en background
        
        Args:
            command: Comando a ejecutar
            
        Returns:
            Proceso o None si falló
        """
        try:
            return subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        except Exception:
            return None
    
    def is_command_available(self, command: str) -> bool:
        """
        Verificar si un comando está disponible
        
        Args:
            command: Comando a verificar
            
        Returns:
            True si está disponible
        """
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(
                    f"where {command}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
            else:  # Unix/Linux
                result = subprocess.run(
                    f"which {command}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
            
            return result.returncode == 0
            
        except Exception:
            return False
