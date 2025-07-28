"""
Factory para crear deployers específicos según el tipo de aplicación
"""

from .base_deployer import BaseDeployer
from .nextjs_deployer import NextJSDeployer
from .fastapi_deployer import FastAPIDeployer
from .nodejs_deployer import NodeJSDeployer
from .static_deployer import StaticDeployer
from ..models.app_config import AppConfig
from ..utils.colors import Colors


class DeployerFactory:
    """Factory para crear deployers específicos"""
    
    _deployers = {
        "nextjs": NextJSDeployer,
        "fastapi": FastAPIDeployer,
        "nodejs": NodeJSDeployer,
        "static": StaticDeployer
    }
    
    @classmethod
    def create_deployer(cls, app_type: str, apps_dir: str, cmd_service) -> BaseDeployer:
        """Crear deployer específico para el tipo de aplicación"""
        if app_type not in cls._deployers:
            raise ValueError(f"Tipo de aplicación no soportado: {app_type}")
        
        deployer_class = cls._deployers[app_type]
        return deployer_class(apps_dir, cmd_service)
    
    @classmethod
    def get_supported_types(cls) -> list:
        """Obtener tipos de aplicación soportados"""
        return list(cls._deployers.keys())
    
    @classmethod
    def detect_app_type(cls, app_dir: str) -> str:
        """Detectar automáticamente el tipo de aplicación"""
        from pathlib import Path
        
        app_path = Path(app_dir)
        
        # Verificar archivos específicos para cada tipo
        if (app_path / "next.config.js").exists() or (app_path / "next.config.mjs").exists():
            return "nextjs"
        
        if (app_path / "main.py").exists():
            # Verificar si es FastAPI
            try:
                with open(app_path / "main.py", "r") as f:
                    content = f.read()
                if "fastapi" in content.lower() or "from fastapi import" in content:
                    return "fastapi"
            except:
                pass
        
        if (app_path / "package.json").exists():
            try:
                import json
                with open(app_path / "package.json", "r") as f:
                    package_data = json.load(f)
                
                # Verificar dependencias para Next.js
                deps = package_data.get("dependencies", {})
                if "next" in deps:
                    return "nextjs"
                
                # Verificar si es Node.js con servidor
                scripts = package_data.get("scripts", {})
                if "start" in scripts:
                    return "nodejs"
                
                # Si solo tiene build tools, probablemente sea estático
                if "build" in scripts and "start" not in scripts:
                    return "static"
                
                # Por defecto, si tiene package.json, es Node.js
                return "nodejs"
                
            except:
                pass
        
        # Si solo tiene index.html, es estático
        if (app_path / "index.html").exists():
            return "static"
        
        # Por defecto, retornar estático
        return "static"
    
    @classmethod
    def validate_app_type(cls, app_dir: str, app_type: str) -> bool:
        """Validar que el tipo de aplicación es correcto para el directorio"""
        if app_type not in cls._deployers:
            return False
        
        try:
            from ..services.cmd_service import CmdService
            cmd_service = CmdService()
            
            deployer = cls.create_deployer(app_type, "/tmp", cmd_service)
            from pathlib import Path
            return deployer.validate_structure(Path(app_dir))
            
        except Exception as e:
            print(Colors.error(f"Error validando tipo de aplicación: {e}"))
            return False
    
    @classmethod
    def get_deployer_info(cls, app_type: str) -> dict:
        """Obtener información sobre un deployer específico"""
        if app_type not in cls._deployers:
            return {}
        
        deployer_class = cls._deployers[app_type]
        
        # Crear instancia temporal para obtener información
        try:
            from ..services.cmd_service import CmdService
            cmd_service = CmdService()
            deployer = deployer_class("/tmp", cmd_service)
            
            return {
                "type": app_type,
                "name": deployer_class.__name__,
                "description": deployer_class.__doc__ or f"Deployer para {app_type}",
                "required_files": deployer.get_required_files(),
                "optional_files": deployer.get_optional_files(),
                "supported": True
            }
            
        except Exception as e:
            return {
                "type": app_type,
                "name": deployer_class.__name__,
                "description": f"Error obteniendo información: {e}",
                "required_files": [],
                "optional_files": [],
                "supported": False
            }
    
    @classmethod
    def list_all_deployers(cls) -> list:
        """Listar todos los deployers disponibles con su información"""
        deployers = []
        
        for app_type in cls._deployers:
            info = cls.get_deployer_info(app_type)
            deployers.append(info)
        
        return deployers
