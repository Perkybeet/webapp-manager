"""
Deployer específico para aplicaciones Node.js
"""

import shutil
from pathlib import Path
from typing import Dict, List
from .base_deployer import BaseDeployer
from ..models.app_config import AppConfig
from ..utils.colors import Colors


class NodeJSDeployer(BaseDeployer):
    """Deployer para aplicaciones Node.js"""
    
    def get_app_type(self) -> str:
        return "nodejs"
    
    def get_required_files(self) -> List[str]:
        return ["package.json"]
    
    def get_optional_files(self) -> List[str]:
        return ["package-lock.json", "yarn.lock", ".env", "server.js", "index.js", "app.js"]
    
    def validate_structure(self, app_dir: Path) -> bool:
        """Validar estructura Node.js"""
        package_json = app_dir / "package.json"
        if not package_json.exists():
            print(Colors.error("package.json no encontrado"))
            return False
        
        try:
            import json
            with open(package_json, "r") as f:
                package_data = json.load(f)
            
            # Verificar estructura básica
            if "name" not in package_data:
                print(Colors.error("Falta el campo 'name' en package.json"))
                return False
            
            if "version" not in package_data:
                print(Colors.warning("Falta el campo 'version' en package.json"))
            
            # Verificar script de inicio
            scripts = package_data.get("scripts", {})
            if "start" not in scripts:
                # Buscar archivo principal
                main_file = package_data.get("main", "index.js")
                main_path = app_dir / main_file
                
                if not main_path.exists():
                    # Buscar archivos comunes
                    common_files = ["server.js", "index.js", "app.js"]
                    found_main = False
                    
                    for file in common_files:
                        if (app_dir / file).exists():
                            print(Colors.info(f"Archivo principal encontrado: {file}"))
                            found_main = True
                            break
                    
                    if not found_main:
                        print(Colors.error("No se encontró archivo principal ni script de inicio"))
                        return False
                else:
                    print(Colors.info(f"Archivo principal encontrado: {main_file}"))
            else:
                print(Colors.success("Script de inicio encontrado en package.json"))
            
            # Verificar dependencias
            if "dependencies" not in package_data and "devDependencies" not in package_data:
                print(Colors.warning("No se encontraron dependencias en package.json"))
            else:
                deps_count = len(package_data.get("dependencies", {}))
                dev_deps_count = len(package_data.get("devDependencies", {}))
                print(Colors.info(f"Dependencias: {deps_count}, Dev dependencias: {dev_deps_count}"))
            
            # Verificar archivo .env si existe
            env_file = app_dir / ".env"
            if env_file.exists():
                print(Colors.info("Archivo .env encontrado en el repositorio - será respetado"))
            
            print(Colors.success("Estructura Node.js válida"))
            return True
            
        except json.JSONDecodeError:
            print(Colors.error("Error: package.json no es un JSON válido"))
            return False
        except Exception as e:
            print(Colors.error(f"Error validando estructura Node.js: {e}"))
            return False
    
    def install_dependencies(self, app_dir: Path, app_config: AppConfig) -> bool:
        """Instalar dependencias Node.js"""
        print(Colors.info("Instalando dependencias Node.js..."))
        
        # Limpiar instalación anterior
        node_modules = app_dir / "node_modules"
        if node_modules.exists():
            print(Colors.info("Eliminando node_modules existente..."))
            shutil.rmtree(node_modules)
        
        # Verificar si usar yarn o npm
        use_yarn = (app_dir / "yarn.lock").exists()
        package_manager = "yarn" if use_yarn else "npm"
        
        print(Colors.info(f"Usando {package_manager} para instalar dependencias..."))
        
        # Instalar dependencias
        if use_yarn:
            install_cmd = f"cd {app_dir} && yarn install --production"
        else:
            install_cmd = f"cd {app_dir} && npm install --production"
        
        result = self.cmd.run(install_cmd, check=False)
        if not result:
            print(Colors.error(f"Error instalando dependencias con {package_manager}"))
            return False
        
        # Verificar que node_modules se creó
        if not node_modules.exists():
            print(Colors.error("node_modules no fue creado"))
            return False
        
        print(Colors.success("Dependencias Node.js instaladas exitosamente"))
        return True
    
    def build_application(self, app_dir: Path, app_config: AppConfig) -> bool:
        """Construir aplicación Node.js"""
        print(Colors.info("Preparando aplicación Node.js..."))
        
        # Verificar que node_modules existe
        node_modules = app_dir / "node_modules"
        if not node_modules.exists():
            print(Colors.error("node_modules no encontrado"))
            return False
        
        # Verificar si hay script de build
        package_json = app_dir / "package.json"
        try:
            import json
            with open(package_json, "r") as f:
                package_data = json.load(f)
            
            scripts = package_data.get("scripts", {})
            
            if "build" in scripts:
                print(Colors.info("Ejecutando script de build..."))
                use_yarn = (app_dir / "yarn.lock").exists()
                
                if use_yarn:
                    build_cmd = f"cd {app_dir} && yarn build"
                else:
                    build_cmd = f"cd {app_dir} && npm run build"
                
                result = self.cmd.run(build_cmd, check=False)
                if not result:
                    print(Colors.error("Error ejecutando script de build"))
                    return False
                
                print(Colors.success("Build completado exitosamente"))
            else:
                print(Colors.info("No se encontró script de build - saltando paso"))
            
            # Verificar sintaxis básica del archivo principal
            main_file = package_data.get("main", "index.js")
            main_path = app_dir / main_file
            
            if not main_path.exists():
                # Buscar archivos comunes
                common_files = ["server.js", "index.js", "app.js"]
                for file in common_files:
                    if (app_dir / file).exists():
                        main_path = app_dir / file
                        break
            
            if main_path.exists():
                # Verificar sintaxis básica
                syntax_check = self.cmd.run(f"cd {app_dir} && node --check {main_path.name}", check=False)
                if not syntax_check:
                    print(Colors.error(f"Error de sintaxis en {main_path.name}"))
                    return False
                
                print(Colors.success(f"Sintaxis verificada en {main_path.name}"))
            
            return True
            
        except Exception as e:
            print(Colors.error(f"Error en build de Node.js: {e}"))
            return False
    
    def get_default_start_command(self, app_config: AppConfig) -> str:
        """Comando de inicio por defecto para Node.js"""
        app_dir = self.apps_dir / app_config.domain
        package_json = app_dir / "package.json"
        
        try:
            import json
            with open(package_json, "r") as f:
                package_data = json.load(f)
            
            scripts = package_data.get("scripts", {})
            
            if "start" in scripts:
                return "npm start"
            else:
                main_file = package_data.get("main", "index.js")
                return f"node {main_file}"
                
        except Exception:
            return "node index.js"
    
    def get_default_build_command(self, app_config: AppConfig) -> str:
        """Comando de build por defecto para Node.js"""
        app_dir = self.apps_dir / app_config.domain
        use_yarn = (app_dir / "yarn.lock").exists()
        
        if use_yarn:
            return "yarn build"
        else:
            return "npm run build"
    
    def get_environment_variables(self, app_config: AppConfig) -> Dict[str, str]:
        """Variables de entorno para Node.js"""
        return {
            "NODE_ENV": "production",
            "PORT": str(app_config.port),
            "HOST": "0.0.0.0"
        }
    
    def clean_build_artifacts(self, app_dir: Path):
        """Limpiar artefactos de build de Node.js"""
        artifacts = [
            app_dir / "node_modules",
            app_dir / "dist",
            app_dir / "build",
            app_dir / ".next",
            app_dir / ".cache"
        ]
        
        for artifact in artifacts:
            if artifact.exists():
                if artifact.is_dir():
                    shutil.rmtree(artifact)
                else:
                    artifact.unlink()
    
    def check_requirements(self) -> bool:
        """Verificar requerimientos para Node.js"""
        requirements = ["node", "npm"]
        
        for req in requirements:
            if not self.cmd.run(f"which {req}", check=False):
                print(Colors.error(f"Requerimiento faltante: {req}"))
                return False
        
        # Verificar versiones
        node_version = self.cmd.run("node --version", check=False)
        if node_version:
            print(Colors.info(f"Node.js version: {node_version.strip()}"))
        
        npm_version = self.cmd.run("npm --version", check=False)
        if npm_version:
            print(Colors.info(f"npm version: {npm_version.strip()}"))
        
        # Verificar si yarn está disponible
        yarn_version = self.cmd.run("yarn --version", check=False)
        if yarn_version:
            print(Colors.info(f"Yarn version: {yarn_version.strip()}"))
        
        return True
    
    def get_health_check_command(self, app_config: AppConfig) -> str:
        """Comando de health check para Node.js"""
        return f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{app_config.port}/"
    
    def get_log_files(self, app_config: AppConfig) -> List[str]:
        """Archivos de log específicos para Node.js"""
        return [
            f"/var/log/webapp-manager/{app_config.domain}.log",
            f"/var/log/{app_config.domain}.log",
            f"{self.apps_dir}/{app_config.domain}/app.log",
            f"{self.apps_dir}/{app_config.domain}/logs/app.log"
        ]
    
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
                f.write("# Environment variables for Node.js application\n")
                f.write(f"# Generated by WebApp Manager\n\n")
                
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            print(Colors.success("Archivo .env creado exitosamente"))
            return True
            
        except Exception as e:
            print(Colors.error(f"Error creando .env: {e}"))
            return False
