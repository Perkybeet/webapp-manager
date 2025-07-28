"""
Deployer específico para aplicaciones Next.js
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List
from .base_deployer import BaseDeployer
from ..models.app_config import AppConfig
from ..utils.colors import Colors


class NextJSDeployer(BaseDeployer):
    """Deployer para aplicaciones Next.js"""
    
    def get_app_type(self) -> str:
        return "nextjs"
    
    def get_required_files(self) -> List[str]:
        return ["package.json"]
    
    def get_optional_files(self) -> List[str]:
        return [".env.local", ".env.production", "next.config.js", "tailwind.config.js"]
    
    def validate_structure(self, app_dir: Path) -> bool:
        """Validar estructura Next.js"""
        package_json = app_dir / "package.json"
        if not package_json.exists():
            print(Colors.error("package.json no encontrado"))
            return False
        
        try:
            with open(package_json, "r") as f:
                package_data = json.load(f)
            
            # Verificar dependencias de Next.js
            dependencies = {
                **package_data.get("dependencies", {}),
                **package_data.get("devDependencies", {}),
            }
            
            if "next" not in dependencies:
                print(Colors.error("Next.js no encontrado en dependencias"))
                return False
            
            if "react" not in dependencies:
                print(Colors.error("React no encontrado en dependencias"))
                return False
            
            # Verificar scripts
            scripts = package_data.get("scripts", {})
            if "build" not in scripts:
                print(Colors.warning("Script 'build' no encontrado - se usará 'next build'"))
            
            if "start" not in scripts:
                print(Colors.warning("Script 'start' no encontrado - se usará 'next start'"))
            
            # Verificar estructura de directorios
            required_dirs = ["pages", "src", "app"]  # Next.js 13+ usa app/, versiones anteriores pages/
            has_required_dir = any((app_dir / dir_name).exists() for dir_name in required_dirs)
            
            if not has_required_dir:
                print(Colors.error("No se encontró estructura de Next.js (pages/, src/, o app/)"))
                return False
            
            print(Colors.success("Estructura Next.js válida"))
            return True
            
        except json.JSONDecodeError:
            print(Colors.error("package.json inválido"))
            return False
        except Exception as e:
            print(Colors.error(f"Error validando package.json: {e}"))
            return False
    
    def install_dependencies(self, app_dir: Path, app_config: AppConfig) -> bool:
        """Instalar dependencias Node.js"""
        print(Colors.info("Instalando dependencias Node.js..."))
        
        # Limpiar node_modules y package-lock.json existentes
        node_modules = app_dir / "node_modules"
        package_lock = app_dir / "package-lock.json"
        
        if node_modules.exists():
            shutil.rmtree(node_modules)
        
        if package_lock.exists():
            package_lock.unlink()
        
        # Instalar dependencias
        install_result = self.cmd.run(
            f"cd {app_dir} && npm install --production=false",
            check=False
        )
        
        if not install_result:
            print(Colors.error("Error instalando dependencias npm"))
            return False
        
        # Verificar que node_modules se creó
        if not node_modules.exists():
            print(Colors.error("node_modules no se creó correctamente"))
            return False
        
        print(Colors.success("Dependencias Node.js instaladas exitosamente"))
        return True
    
    def build_application(self, app_dir: Path, app_config: AppConfig) -> bool:
        """Construir aplicación Next.js"""
        print(Colors.info("Construyendo aplicación Next.js..."))
        
        # Usar comando personalizado o por defecto
        build_cmd = app_config.build_command or self.get_default_build_command(app_config)
        
        # Construir aplicación
        build_result = self.cmd.run(
            f"cd {app_dir} && {build_cmd}",
            check=False
        )
        
        if not build_result:
            print(Colors.error("Error construyendo aplicación Next.js"))
            return False
        
        # Verificar que .next se creó
        next_dir = app_dir / ".next"
        if not next_dir.exists():
            print(Colors.error("Construcción Next.js no generó directorio .next"))
            return False
        
        # Verificar archivos de build
        build_manifest = next_dir / "build-manifest.json"
        if not build_manifest.exists():
            print(Colors.warning("build-manifest.json no encontrado, pero .next existe"))
        
        print(Colors.success("Aplicación Next.js construida exitosamente"))
        return True
    
    def get_default_start_command(self, app_config: AppConfig) -> str:
        """Comando de inicio por defecto para Next.js"""
        return f"./node_modules/.bin/next start --port {app_config.port}"
    
    def get_default_build_command(self, app_config: AppConfig) -> str:
        """Comando de build por defecto para Next.js"""
        return "npm run build"
    
    def get_environment_variables(self, app_config: AppConfig) -> Dict[str, str]:
        """Variables de entorno para Next.js"""
        return {
            "NODE_ENV": "production",
            "PORT": str(app_config.port),
            "HOSTNAME": "localhost",
            "NEXT_TELEMETRY_DISABLED": "1"
        }
    
    def clean_build_artifacts(self, app_dir: Path):
        """Limpiar artefactos de build de Next.js"""
        artifacts = [
            app_dir / ".next",
            app_dir / "node_modules",
            app_dir / "package-lock.json",
            app_dir / ".next-cache"
        ]
        
        for artifact in artifacts:
            if artifact.exists():
                if artifact.is_dir():
                    shutil.rmtree(artifact)
                else:
                    artifact.unlink()
    
    def check_requirements(self) -> bool:
        """Verificar requerimientos para Next.js"""
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
        
        return True
    
    def get_health_check_command(self, app_config: AppConfig) -> str:
        """Comando de health check para Next.js"""
        return f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{app_config.port}"
    
    def get_log_files(self, app_config: AppConfig) -> List[str]:
        """Archivos de log específicos para Next.js"""
        return [
            f"/var/log/webapp-manager/{app_config.domain}.log",
            f"/var/log/{app_config.domain}.log",
            f"{self.apps_dir}/{app_config.domain}/.next/trace"
        ]
