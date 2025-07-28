"""
Deployer específico para aplicaciones FastAPI
"""

import shutil
from pathlib import Path
from typing import Dict, List
from .base_deployer import BaseDeployer
from ..models.app_config import AppConfig
from ..utils.colors import Colors


class FastAPIDeployer(BaseDeployer):
    """Deployer para aplicaciones FastAPI"""
    
    def get_app_type(self) -> str:
        return "fastapi"
    
    def get_required_files(self) -> List[str]:
        return ["main.py"]
    
    def get_optional_files(self) -> List[str]:
        return ["requirements.txt", ".env", "pyproject.toml", "setup.py", "alembic.ini"]
    
    def validate_structure(self, app_dir: Path) -> bool:
        """Validar estructura FastAPI"""
        main_file = app_dir / "main.py"
        if not main_file.exists():
            print(Colors.error("main.py no encontrado"))
            return False
        
        try:
            # Verificar que main.py contiene FastAPI
            with open(main_file, "r") as f:
                main_content = f.read()
            
            if "from fastapi import" not in main_content and "import fastapi" not in main_content:
                print(Colors.warning("main.py no parece ser una aplicación FastAPI"))
            
            if "app = " not in main_content and "application = " not in main_content:
                print(Colors.warning("Variable de aplicación no encontrada en main.py"))
            
            # Verificar requirements.txt si existe
            requirements_file = app_dir / "requirements.txt"
            if requirements_file.exists():
                with open(requirements_file, "r") as f:
                    requirements_content = f.read().lower()
                
                if "fastapi" not in requirements_content:
                    print(Colors.warning("FastAPI no encontrado en requirements.txt"))
                
                if "uvicorn" not in requirements_content:
                    print(Colors.warning("Uvicorn no encontrado en requirements.txt"))
                
                print(Colors.success("requirements.txt encontrado y válido"))
            else:
                print(Colors.info("requirements.txt no encontrado - se instalarán dependencias básicas"))
            
            # Verificar archivo .env si existe
            env_file = app_dir / ".env"
            if env_file.exists():
                print(Colors.info("Archivo .env encontrado en el repositorio - será respetado"))
            
            print(Colors.success("Estructura FastAPI válida"))
            return True
            
        except Exception as e:
            print(Colors.error(f"Error validando estructura FastAPI: {e}"))
            return False
    
    def install_dependencies(self, app_dir: Path, app_config: AppConfig) -> bool:
        """Instalar dependencias Python"""
        print(Colors.info("Configurando entorno virtual Python..."))
        
        venv_dir = app_dir / ".venv"
        
        try:
            # Limpiar entorno virtual existente
            if venv_dir.exists():
                print(Colors.info("Eliminando entorno virtual existente..."))
                shutil.rmtree(venv_dir)
            
            # Crear nuevo entorno virtual
            print(Colors.info("Creando entorno virtual (.venv)..."))
            venv_result = self.cmd.run(f"cd {app_dir} && python3 -m venv .venv", check=False)
            if venv_result is None:
                print(Colors.error("Error creando entorno virtual"))
                return False
            
            print(Colors.success("Entorno virtual creado exitosamente"))
            
            # Actualizar pip
            print(Colors.info("Actualizando pip..."))
            pip_update = self.cmd.run(
                f"cd {app_dir} && .venv/bin/pip install --upgrade pip",
                check=False
            )
            if pip_update is None:
                print(Colors.warning("Error actualizando pip, continuando..."))
            
            # Instalar dependencias
            requirements_file = app_dir / "requirements.txt"
            if requirements_file.exists():
                print(Colors.info("Instalando dependencias desde requirements.txt..."))
                install_result = self.cmd.run(
                    f"cd {app_dir} && .venv/bin/pip install -r requirements.txt",
                    check=False
                )
                if install_result is None:
                    print(Colors.error("Error instalando dependencias desde requirements.txt"))
                    return False
                print(Colors.success("Dependencias instaladas desde requirements.txt"))
            else:
                print(Colors.info("requirements.txt no encontrado, instalando dependencias básicas..."))
                basic_deps = ["fastapi", "uvicorn[standard]", "python-multipart", "python-dotenv"]
                
                for dep in basic_deps:
                    print(Colors.info(f"Instalando {dep}..."))
                    install_result = self.cmd.run(
                        f"cd {app_dir} && .venv/bin/pip install {dep}",
                        check=False
                    )
                    if install_result is None:
                        print(Colors.error(f"Error instalando {dep}"))
                        return False
                
                print(Colors.success("Dependencias básicas instaladas"))
            
            # Verificar instalación
            print(Colors.info("Verificando instalación..."))
            check_fastapi = self.cmd.run(
                f"cd {app_dir} && .venv/bin/python -c 'import fastapi; print(\"FastAPI:\", fastapi.__version__)'",
                check=False
            )
            if check_fastapi is None:
                print(Colors.error("FastAPI no se instaló correctamente"))
                return False
            
            check_uvicorn = self.cmd.run(
                f"cd {app_dir} && .venv/bin/python -c 'import uvicorn; print(\"Uvicorn:\", uvicorn.__version__)'",
                check=False
            )
            if check_uvicorn is None:
                print(Colors.error("Uvicorn no se instaló correctamente"))
                return False
            
            print(Colors.success("Verificación completada - FastAPI y Uvicorn instalados"))
            return True
            
        except Exception as e:
            print(Colors.error(f"Error en instalación de dependencias: {e}"))
            return False
            print(Colors.info("Instalando dependencias desde requirements.txt..."))
            install_deps = self.cmd.run(
                f"cd {app_dir} && .venv/bin/pip install -r requirements.txt",
                check=False
            )
            if not install_deps:
                print(Colors.error("Error instalando dependencias desde requirements.txt"))
                return False
        else:
            print(Colors.info("Instalando dependencias básicas (FastAPI + Uvicorn)..."))
            install_basic = self.cmd.run(
                f"cd {app_dir} && .venv/bin/pip install fastapi uvicorn[standard]",
                check=False
            )
            if not install_basic:
                print(Colors.error("Error instalando dependencias básicas"))
                return False
        
        # Verificar que uvicorn está disponible
        self._ensure_uvicorn_installed(app_dir)
        
        # Configurar permisos
        self.cmd.run(f"chmod +x {app_dir}/.venv/bin/*", check=False)
        
        print(Colors.success("Entorno virtual Python configurado exitosamente"))
        return True
    
    def build_application(self, app_dir: Path, app_config: AppConfig) -> bool:
        """Construir aplicación FastAPI"""
        print(Colors.info("Preparando aplicación FastAPI..."))
        
        try:
            # FastAPI no requiere build step, pero podemos hacer validaciones
            venv_dir = app_dir / ".venv"
            if not venv_dir.exists():
                print(Colors.error("Entorno virtual no encontrado"))
                return False
            
            # Verificar que las dependencias están instaladas
            pip_list = self.cmd.run(f"cd {app_dir} && .venv/bin/pip list", check=False)
            if pip_list is None:
                print(Colors.error("Error verificando dependencias instaladas"))
                return False
            
            if "fastapi" not in pip_list.lower():
                print(Colors.error("FastAPI no está instalado en el entorno virtual"))
                return False
            
            if "uvicorn" not in pip_list.lower():
                print(Colors.error("Uvicorn no está instalado en el entorno virtual"))
                return False
            
            # Verificar que main.py es válido
            main_file = app_dir / "main.py"
            if not main_file.exists():
                print(Colors.error("main.py no encontrado"))
                return False
            
            # Verificar que main.py se puede compilar
            compile_result = self.cmd.run(
                f"cd {app_dir} && .venv/bin/python -m py_compile main.py",
                check=False
            )
            if compile_result is None:
                print(Colors.error("main.py tiene errores de sintaxis"))
                return False
            
            print(Colors.success("Aplicación FastAPI preparada exitosamente"))
            return True
            
        except Exception as e:
            print(Colors.error(f"Error preparando aplicación FastAPI: {e}"))
            return False
        if not main_file.exists():
            print(Colors.error("main.py no encontrado"))
            return False
        
        # Verificar sintaxis de Python
        syntax_check = self.cmd.run(
            f"cd {app_dir} && .venv/bin/python -m py_compile main.py",
            check=False
        )
        if not syntax_check:
            print(Colors.error("Error de sintaxis en main.py"))
            return False
        
        print(Colors.success("Aplicación FastAPI preparada exitosamente"))
        return True
    
    def get_default_start_command(self, app_config: AppConfig) -> str:
        """Comando de inicio por defecto para FastAPI"""
        return f".venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port {app_config.port} --workers 1"
    
    def get_default_build_command(self, app_config: AppConfig) -> str:
        """FastAPI no requiere build command"""
        return ""
    
    def get_environment_variables(self, app_config: AppConfig) -> Dict[str, str]:
        """Variables de entorno para FastAPI"""
        return {
            "PYTHONPATH": str(self.apps_dir / app_config.domain),
            "PORT": str(app_config.port),
            "HOST": "0.0.0.0",
            "ENVIRONMENT": "production",
            "PYTHONUNBUFFERED": "1"
        }
    
    def clean_build_artifacts(self, app_dir: Path):
        """Limpiar artefactos de build de FastAPI"""
        artifacts = [
            app_dir / ".venv",
            app_dir / "__pycache__",
            app_dir / "*.pyc",
            app_dir / ".pytest_cache"
        ]
        
        for artifact in artifacts:
            if artifact.exists():
                if artifact.is_dir():
                    shutil.rmtree(artifact)
                else:
                    artifact.unlink()
    
    def check_requirements(self) -> bool:
        """Verificar requerimientos para FastAPI"""
        requirements = ["python3", "pip3"]
        
        for req in requirements:
            if not self.cmd.run(f"which {req}", check=False):
                print(Colors.error(f"Requerimiento faltante: {req}"))
                return False
        
        # Verificar versiones
        python_version = self.cmd.run("python3 --version", check=False)
        if python_version:
            print(Colors.info(f"Python version: {python_version.strip()}"))
        
        pip_version = self.cmd.run("pip3 --version", check=False)
        if pip_version:
            print(Colors.info(f"pip version: {pip_version.strip()}"))
        
        return True
    
    def get_health_check_command(self, app_config: AppConfig) -> str:
        """Comando de health check para FastAPI"""
        return f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{app_config.port}/docs"
    
    def get_log_files(self, app_config: AppConfig) -> List[str]:
        """Archivos de log específicos para FastAPI"""
        return [
            f"/var/log/webapp-manager/{app_config.domain}.log",
            f"/var/log/{app_config.domain}.log",
            f"{self.apps_dir}/{app_config.domain}/app.log"
        ]
    
    def get_start_command(self, app_config: AppConfig) -> str:
        """Comando de inicio para FastAPI"""
        app_dir = self.apps_dir / app_config.domain
        
        # Buscar la aplicación FastAPI en main.py
        main_file = app_dir / "main.py"
        app_var = "app"
        
        if main_file.exists():
            try:
                with open(main_file, "r") as f:
                    main_content = f.read()
                
                # Buscar variable de aplicación
                if "application = " in main_content:
                    app_var = "application"
                elif "fastapi_app = " in main_content:
                    app_var = "fastapi_app"
                elif "api = " in main_content:
                    app_var = "api"
                
            except Exception:
                pass
        
        # Retornar comando usando el entorno virtual
        return f"cd {app_dir} && .venv/bin/uvicorn main:{app_var} --host 0.0.0.0 --port {app_config.port} --workers 1"
    
    def get_build_command(self, app_config: AppConfig) -> str:
        """Comando de build para FastAPI (no necesario, pero podemos validar)"""
        app_dir = self.apps_dir / app_config.domain
        return f"cd {app_dir} && .venv/bin/python -m py_compile main.py"
    
    def _ensure_uvicorn_installed(self, app_dir: Path):
        """Asegurar que uvicorn está instalado"""
        pip_list = self.cmd.run(f"cd {app_dir} && .venv/bin/pip list", check=False)
        if pip_list and "uvicorn" not in pip_list.lower():
            print(Colors.info("Uvicorn no encontrado, instalando..."))
            self.cmd.run(f"cd {app_dir} && .venv/bin/pip install uvicorn[standard]", check=False)
        else:
            print(Colors.success("Uvicorn ya está instalado"))
            print(Colors.success("Uvicorn ya está instalado"))
    
    def handle_environment_file(self, app_dir: Path, app_config: AppConfig) -> bool:
        """Manejar archivo .env respetando el existente"""
        env_file = app_dir / ".env"
        
        # Si existe .env, respetarlo completamente
        if env_file.exists():
            print(Colors.info("Archivo .env encontrado en el repositorio - será respetado"))
            
            try:
                with open(env_file, "r") as f:
                    content = f.read()
                
                # Solo agregar PORT si no existe
                if "PORT=" not in content:
                    with open(env_file, "a") as f:
                        f.write(f"\n# Port added by WebApp Manager\nPORT={app_config.port}\n")
                    print(Colors.success(f"Puerto {app_config.port} agregado al .env existente"))
                else:
                    print(Colors.info("Puerto ya configurado en .env"))
                
                return True
                
            except Exception as e:
                print(Colors.warning(f"Error procesando .env existente: {e}"))
                return False
        
        # Si no existe .env, crear uno básico
        print(Colors.info("Creando archivo .env básico..."))
        try:
            env_vars = self.get_environment_variables(app_config)
            
            with open(env_file, "w") as f:
                f.write("# Environment variables for FastAPI application\n")
                f.write(f"# Generated by WebApp Manager\n\n")
                
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            print(Colors.success("Archivo .env creado exitosamente"))
            return True
            
        except Exception as e:
            print(Colors.error(f"Error creando .env: {e}"))
            return False
