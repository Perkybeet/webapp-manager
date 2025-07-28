"""
Deployer específico para sitios web estáticos
"""

import shutil
from pathlib import Path
from typing import Dict, List
from .base_deployer import BaseDeployer
from ..models.app_config import AppConfig
from ..utils.colors import Colors


class StaticDeployer(BaseDeployer):
    """Deployer para sitios web estáticos"""
    
    def get_app_type(self) -> str:
        return "static"
    
    def get_required_files(self) -> List[str]:
        return ["index.html"]
    
    def get_optional_files(self) -> List[str]:
        return ["package.json", "gulpfile.js", "webpack.config.js", "index.css", "styles.css", "main.css"]
    
    def validate_structure(self, app_dir: Path) -> bool:
        """Validar estructura de sitio estático"""
        index_html = app_dir / "index.html"
        if not index_html.exists():
            print(Colors.error("index.html no encontrado"))
            return False
        
        try:
            # Verificar que index.html es válido
            with open(index_html, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            if "<html" not in html_content.lower():
                print(Colors.warning("index.html no parece ser un archivo HTML válido"))
            
            if "<title>" not in html_content.lower():
                print(Colors.warning("Etiqueta <title> no encontrada en index.html"))
            
            # Verificar archivos comunes
            common_files = ["style.css", "styles.css", "main.css", "app.css"]
            css_found = False
            
            for css_file in common_files:
                if (app_dir / css_file).exists():
                    print(Colors.info(f"Archivo CSS encontrado: {css_file}"))
                    css_found = True
                    break
            
            if not css_found:
                print(Colors.info("No se encontraron archivos CSS principales"))
            
            # Verificar archivos JavaScript
            js_files = ["script.js", "main.js", "app.js", "index.js"]
            js_found = False
            
            for js_file in js_files:
                if (app_dir / js_file).exists():
                    print(Colors.info(f"Archivo JavaScript encontrado: {js_file}"))
                    js_found = True
                    break
            
            if not js_found:
                print(Colors.info("No se encontraron archivos JavaScript principales"))
            
            # Verificar si hay build tools
            build_tools = ["package.json", "gulpfile.js", "webpack.config.js", "rollup.config.js"]
            build_tool_found = False
            
            for tool in build_tools:
                if (app_dir / tool).exists():
                    print(Colors.info(f"Herramienta de build encontrada: {tool}"))
                    build_tool_found = True
            
            if not build_tool_found:
                print(Colors.info("No se encontraron herramientas de build - sitio estático puro"))
            
            print(Colors.success("Estructura de sitio estático válida"))
            return True
            
        except Exception as e:
            print(Colors.error(f"Error validando estructura estática: {e}"))
            return False
    
    def install_dependencies(self, app_dir: Path, app_config: AppConfig) -> bool:
        """Instalar dependencias para sitio estático"""
        package_json = app_dir / "package.json"
        
        # Si no hay package.json, no hay dependencias que instalar
        if not package_json.exists():
            print(Colors.info("No se encontró package.json - sitio estático puro"))
            return True
        
        print(Colors.info("Instalando dependencias para build tools..."))
        
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
            install_cmd = f"cd {app_dir} && yarn install"
        else:
            install_cmd = f"cd {app_dir} && npm install"
        
        result = self.cmd.run(install_cmd, check=False)
        if not result:
            print(Colors.error(f"Error instalando dependencias con {package_manager}"))
            return False
        
        # Verificar que node_modules se creó
        if not node_modules.exists():
            print(Colors.error("node_modules no fue creado"))
            return False
        
        print(Colors.success("Dependencias instaladas exitosamente"))
        return True
    
    def build_application(self, app_dir: Path, app_config: AppConfig) -> bool:
        """Construir sitio estático"""
        print(Colors.info("Preparando sitio estático..."))
        
        package_json = app_dir / "package.json"
        
        # Si no hay package.json, no hay build que hacer
        if not package_json.exists():
            print(Colors.info("No se encontró package.json - sitio estático puro"))
            
            # Verificar que index.html existe
            index_html = app_dir / "index.html"
            if not index_html.exists():
                print(Colors.error("index.html no encontrado"))
                return False
            
            print(Colors.success("Sitio estático listo"))
            return True
        
        # Si hay package.json, verificar si hay script de build
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
                
                # Verificar si se generó una carpeta de build
                common_build_dirs = ["build", "dist", "public", "output"]
                build_dir_found = False
                
                for build_dir in common_build_dirs:
                    if (app_dir / build_dir).exists():
                        print(Colors.info(f"Carpeta de build encontrada: {build_dir}"))
                        build_dir_found = True
                        break
                
                if not build_dir_found:
                    print(Colors.warning("No se encontró carpeta de build específica"))
                
            else:
                print(Colors.info("No se encontró script de build - sitio estático sin build"))
            
            return True
            
        except Exception as e:
            print(Colors.error(f"Error en build estático: {e}"))
            return False
    
    def get_default_start_command(self, app_config: AppConfig) -> str:
        """Comando de inicio por defecto para sitio estático"""
        # Los sitios estáticos no necesitan comando de inicio
        # nginx servirá los archivos directamente
        return ""
    
    def get_default_build_command(self, app_config: AppConfig) -> str:
        """Comando de build por defecto para sitio estático"""
        app_dir = self.apps_dir / app_config.domain
        package_json = app_dir / "package.json"
        
        if not package_json.exists():
            return ""
        
        use_yarn = (app_dir / "yarn.lock").exists()
        
        if use_yarn:
            return "yarn build"
        else:
            return "npm run build"
    
    def get_environment_variables(self, app_config: AppConfig) -> Dict[str, str]:
        """Variables de entorno para sitio estático"""
        return {
            "NODE_ENV": "production",
            "PORT": str(app_config.port)
        }
    
    def clean_build_artifacts(self, app_dir: Path):
        """Limpiar artefactos de build estático"""
        artifacts = [
            app_dir / "node_modules",
            app_dir / "build",
            app_dir / "dist",
            app_dir / "public",
            app_dir / "output",
            app_dir / ".cache"
        ]
        
        for artifact in artifacts:
            if artifact.exists():
                if artifact.is_dir():
                    shutil.rmtree(artifact)
                else:
                    artifact.unlink()
    
    def check_requirements(self) -> bool:
        """Verificar requerimientos para sitio estático"""
        # Para sitios estáticos puros, no se necesitan requerimientos especiales
        # Solo nginx que ya está instalado
        print(Colors.info("Sitio estático - no se requieren herramientas adicionales"))
        
        # Verificar si hay herramientas de build disponibles
        tools = ["node", "npm", "yarn"]
        
        for tool in tools:
            if self.cmd.run(f"which {tool}", check=False):
                version = self.cmd.run(f"{tool} --version", check=False)
                if version:
                    print(Colors.info(f"{tool} version: {version.strip()}"))
        
        return True
    
    def get_health_check_command(self, app_config: AppConfig) -> str:
        """Comando de health check para sitio estático"""
        return f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{app_config.port}/"
    
    def get_log_files(self, app_config: AppConfig) -> List[str]:
        """Archivos de log específicos para sitio estático"""
        return [
            f"/var/log/nginx/{app_config.domain}.access.log",
            f"/var/log/nginx/{app_config.domain}.error.log",
            f"/var/log/webapp-manager/{app_config.domain}.log"
        ]
    
    def get_nginx_config_template(self, app_config: AppConfig) -> str:
        """Configuración específica de nginx para sitio estático"""
        app_dir = self.apps_dir / app_config.domain
        
        # Determinar directorio de archivos estáticos
        static_dirs = ["build", "dist", "public", "output"]
        document_root = str(app_dir)
        
        for static_dir in static_dirs:
            if (app_dir / static_dir).exists():
                document_root = str(app_dir / static_dir)
                break
        
        return f"""
server {{
    listen 80;
    server_name {app_config.domain};
    
    root {document_root};
    index index.html index.htm;
    
    # Configuración para sitio estático
    location / {{
        try_files $uri $uri/ /index.html;
    }}
    
    # Configuración para assets estáticos
    location ~* \\.(css|js|jpg|jpeg|png|gif|ico|svg|woff|woff2|ttf|eot)$ {{
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }}
    
    # Configuración para archivos HTML
    location ~* \\.html$ {{
        expires -1;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        try_files $uri =404;
    }}
    
    # Logs
    access_log /var/log/nginx/{app_config.domain}.access.log;
    error_log /var/log/nginx/{app_config.domain}.error.log;
}}
"""
    
    def handle_environment_file(self, app_dir: Path, app_config: AppConfig) -> bool:
        """Manejar archivo .env para sitio estático"""
        # Los sitios estáticos no necesitan archivos .env en runtime
        # Pero si tienen build tools, pueden necesitarlo
        
        package_json = app_dir / "package.json"
        if not package_json.exists():
            print(Colors.info("Sitio estático puro - no se requiere archivo .env"))
            return True
        
        env_file = app_dir / ".env"
        
        # Si existe .env, respetarlo
        if env_file.exists():
            print(Colors.info("Archivo .env encontrado en el repositorio - será respetado"))
            return True
        
        # Si no existe .env y hay build tools, crear uno básico
        print(Colors.info("Creando archivo .env básico para build..."))
        try:
            env_vars = self.get_environment_variables(app_config)
            
            with open(env_file, "w") as f:
                f.write("# Environment variables for static site build\n")
                f.write(f"# Generated by WebApp Manager\n\n")
                
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            print(Colors.success("Archivo .env creado exitosamente"))
            return True
            
        except Exception as e:
            print(Colors.error(f"Error creando .env: {e}"))
            return False
