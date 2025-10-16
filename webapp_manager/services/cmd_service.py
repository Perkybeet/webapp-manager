"""
Servicio para ejecutar comandos del sistema
"""

import subprocess
import sys
import os
from typing import Optional


class CmdService:
    """Servicio para ejecutar comandos del sistema"""
    
    def __init__(self, verbose: bool = False, logger=None):
        self.encoding = 'utf-8'
        self.verbose = verbose
        self.logger = logger
    
    def run(self, command: str, check: bool = True, timeout: Optional[int] = None, 
            capture_output: bool = True, show_command: bool = None) -> Optional[str]:
        """
        Ejecutar comando del sistema
        
        Args:
            command: Comando a ejecutar
            check: Si debe lanzar excepción en caso de error
            timeout: Timeout en segundos
            capture_output: Si debe capturar la salida
            show_command: Mostrar comando ejecutado (None usa verbose)
            
        Returns:
            Salida del comando o None si falló
        """
        # Usar logger si está disponible, sino usar print
        if self.logger:
            self.logger.command(command, show=show_command)
        elif self.verbose:
            print(f"🔧 Ejecutando: {command}")
        
        try:
            if capture_output:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding=self.encoding,
                    timeout=timeout,
                    check=check
                )
                
                output = result.stdout.strip() if result.stdout else ""
                
                # Mostrar output solo si hay error o en verbose
                if self.logger:
                    if result.stderr and result.returncode != 0:
                        self.logger.command_output(result.stderr)
                    elif output and self.verbose:
                        self.logger.command_output(output, max_lines=5)
                elif self.verbose:
                    if output:
                        print(f"📤 Salida: {output}")
                    if result.stderr:
                        print(f"⚠️  Error: {result.stderr}")
                
                return output
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    timeout=timeout,
                    check=check
                )
                
                return ""
            
        except subprocess.CalledProcessError as e:
            if self.logger:
                if check:
                    self.logger.debug(f"Comando falló con código {e.returncode}")
                if e.stderr:
                    self.logger.command_output(e.stderr)
            elif self.verbose:
                print(f"❌ Error ejecutando comando: {command}")
                print(f"📊 Código de salida: {e.returncode}")
                if e.stderr:
                    print(f"⚠️  STDERR: {e.stderr}")
            
            if check:
                return None
            return e.stdout.strip() if e.stdout else ""
        except subprocess.TimeoutExpired:
            if self.logger:
                self.logger.error(f"Timeout ejecutando comando (>{timeout}s)")
            elif self.verbose:
                print(f"⏰ Timeout ejecutando comando: {command}")
            return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Excepción: {str(e)}")
            elif self.verbose:
                print(f"💥 Excepción ejecutando comando: {e}")
            return None
    
    def run_sudo(self, command: str, check: bool = True, timeout: Optional[int] = None, 
                 capture_output: bool = True, show_command: bool = None) -> Optional[str]:
        """
        Ejecutar comando con sudo (solo en sistemas Unix)
        
        Args:
            command: Comando a ejecutar
            check: Si debe lanzar excepción en caso de error
            timeout: Timeout en segundos
            capture_output: Si debe capturar la salida
            show_command: Mostrar comando ejecutado (None usa verbose)
            
        Returns:
            Salida del comando o None si falló
        """
        if os.name == 'nt':  # Windows
            # En Windows ejecutar sin sudo
            return self.run(command, check=check, timeout=timeout, 
                          capture_output=capture_output, show_command=show_command)
        else:
            # En Unix/Linux usar sudo
            sudo_command = f"sudo {command}"
            return self.run(sudo_command, check=check, timeout=timeout, 
                          capture_output=capture_output, show_command=show_command)
    
    def test_command_exists(self, command: str) -> bool:
        """
        Verificar si un comando existe en el sistema
        
        Args:
            command: Comando a verificar
            
        Returns:
            True si el comando existe
        """
        if self.logger:
            self.logger.debug(f"Verificando comando: {command}")
        elif self.verbose:
            print(f"🔍 Verificando si existe comando: {command}")
        
        try:
            if os.name == 'nt':  # Windows
                result = self.run(f"where {command}", check=False, show_command=False)
            else:  # Unix/Linux
                result = self.run(f"command -v {command}", check=False, show_command=False)
            
            exists = result is not None and result.strip() != ""
            
            if self.logger:
                if exists:
                    self.logger.debug(f"Comando '{command}' encontrado")
                else:
                    self.logger.debug(f"Comando '{command}' no encontrado")
            elif self.verbose:
                if exists:
                    print(f"✅ Comando '{command}' encontrado: {result}")
                else:
                    print(f"❌ Comando '{command}' no encontrado")
            
            return exists
            
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Error verificando comando '{command}': {e}")
            elif self.verbose:
                print(f"❌ Error verificando comando '{command}': {e}")
            return False
    
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
