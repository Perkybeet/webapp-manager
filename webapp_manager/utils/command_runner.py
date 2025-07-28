"""
Utilidades para ejecutar comandos del sistema
"""

import logging
import subprocess
import sys
from typing import Optional

logger = logging.getLogger(__name__)


class CommandRunner:
    """Ejecutor de comandos del sistema"""
    
    @staticmethod
    def run(
        command: str,
        check: bool = True,
        capture_output: bool = True,
        timeout: int = 300
    ) -> Optional[str]:
        """
        Ejecutar comando del sistema con logging detallado
        
        Args:
            command: Comando a ejecutar
            check: Si debe fallar en caso de error
            capture_output: Si debe capturar la salida
            timeout: Timeout en segundos
            
        Returns:
            Output del comando o None en caso de error
        """
        logger.debug(f"Ejecutando comando: {command}")

        try:
            if capture_output:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=check,
                    timeout=timeout,
                )

                if result.stdout:
                    logger.debug(f"STDOUT: {result.stdout}")
                if result.stderr:
                    logger.debug(f"STDERR: {result.stderr}")

                return result.stdout.strip()
            else:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    check=check, 
                    timeout=timeout
                )
                return ""

        except subprocess.TimeoutExpired:
            logger.error(f"Comando timeout: {command}")
            if check:
                sys.exit(1)
            return None
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error ejecutando comando: {command}")
            logger.error(f"Código de salida: {e.returncode}")
            if e.stderr:
                logger.error(f"STDERR: {e.stderr}")
            if check:
                raise CommandExecutionError(f"Falló comando: {command}", e.stderr)
            return None
            
        except Exception as e:
            logger.error(f"Error inesperado ejecutando comando: {e}")
            if check:
                raise CommandExecutionError(f"Error inesperado: {command}", str(e))
            return None

    @staticmethod
    def run_sudo(
        command: str,
        check: bool = True,
        capture_output: bool = True,
        timeout: int = 300
    ) -> Optional[str]:
        """
        Ejecutar comando con sudo
        """
        sudo_command = f"sudo {command}"
        return CommandRunner.run(sudo_command, check, capture_output, timeout)

    @staticmethod
    def test_command_exists(command: str) -> bool:
        """
        Verificar si un comando existe en el sistema
        """
        result = CommandRunner.run(f"command -v {command}", check=False)
        return result is not None and result != ""


class CommandExecutionError(Exception):
    """Excepción para errores de ejecución de comandos"""
    
    def __init__(self, message: str, stderr: str = ""):
        super().__init__(message)
        self.stderr = stderr
