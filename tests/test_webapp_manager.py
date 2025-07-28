"""
Pruebas unitarias para WebApp Manager
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from webapp_manager.models import AppConfig, GlobalConfig
from webapp_manager.utils import Validators, Colors
from webapp_manager.config import ConfigManager


class TestValidators:
    """Pruebas para validadores"""

    def test_validate_domain_valid(self):
        """Probar validación de dominio válido"""
        assert Validators.validate_domain("ejemplo.com") == True
        assert Validators.validate_domain("sub.ejemplo.com") == True
        assert Validators.validate_domain("app-test.ejemplo.com") == True

    def test_validate_domain_invalid(self):
        """Probar validación de dominio inválido"""
        assert Validators.validate_domain("") == False
        assert Validators.validate_domain("ejemplo") == False
        assert Validators.validate_domain("ejemplo.") == False
        assert Validators.validate_domain(".ejemplo.com") == False

    def test_validate_port_valid(self):
        """Probar validación de puerto válido"""
        assert Validators.validate_port(3000) == True
        assert Validators.validate_port("8080") == True
        assert Validators.validate_port(65535) == True

    def test_validate_port_invalid(self):
        """Probar validación de puerto inválido"""
        assert Validators.validate_port(80) == False
        assert Validators.validate_port(70000) == False
        assert Validators.validate_port("invalid") == False

    def test_validate_app_type(self):
        """Probar validación de tipo de aplicación"""
        assert Validators.validate_app_type("nextjs") == True
        assert Validators.validate_app_type("fastapi") == True
        assert Validators.validate_app_type("node") == True
        assert Validators.validate_app_type("static") == True
        assert Validators.validate_app_type("invalid") == False

    def test_validate_env_var(self):
        """Probar validación de variables de entorno"""
        valid, key, value = Validators.validate_env_var("NODE_ENV=production")
        assert valid == True
        assert key == "NODE_ENV"
        assert value == "production"

        valid, key, value = Validators.validate_env_var("invalid")
        assert valid == False


class TestAppConfig:
    """Pruebas para AppConfig"""

    def test_create_new(self):
        """Probar creación de nueva configuración"""
        config = AppConfig.create_new(
            domain="test.com",
            port=3000,
            app_type="nextjs",
            source="/path/to/app"
        )
        
        assert config.domain == "test.com"
        assert config.port == 3000
        assert config.app_type == "nextjs"
        assert config.source == "/path/to/app"
        assert config.status == "pending"
        assert config.env_vars == {}

    def test_to_dict_from_dict(self):
        """Probar serialización y deserialización"""
        config = AppConfig.create_new(
            domain="test.com",
            port=3000,
            app_type="nextjs",
            source="/path/to/app"
        )
        
        config_dict = config.to_dict()
        restored_config = AppConfig.from_dict(config_dict)
        
        assert restored_config.domain == config.domain
        assert restored_config.port == config.port
        assert restored_config.app_type == config.app_type

    def test_update_timestamp(self):
        """Probar actualización de timestamp"""
        config = AppConfig.create_new(
            domain="test.com",
            port=3000,
            app_type="nextjs",
            source="/path/to/app"
        )
        
        original_time = config.last_updated
        config.update_timestamp()
        
        assert config.last_updated != original_time

    def test_set_active(self):
        """Probar marcado como activo"""
        config = AppConfig.create_new(
            domain="test.com",
            port=3000,
            app_type="nextjs",
            source="/path/to/app"
        )
        
        config.set_active()
        assert config.status == "active"


class TestConfigManager:
    """Pruebas para ConfigManager"""

    def setup_method(self):
        """Configurar para cada prueba"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "config.json"
        self.backup_dir = self.temp_dir / "backup"
        self.config_manager = ConfigManager(self.config_file, self.backup_dir)

    def teardown_method(self):
        """Limpiar después de cada prueba"""
        shutil.rmtree(self.temp_dir)

    def test_load_config_new(self):
        """Probar carga de configuración nueva"""
        config = self.config_manager.load_config()
        
        assert "apps" in config
        assert "global" in config
        assert config["apps"] == {}

    def test_add_app(self):
        """Probar agregado de aplicación"""
        app_config = AppConfig.create_new(
            domain="test.com",
            port=3000,
            app_type="nextjs",
            source="/path/to/app"
        )
        
        self.config_manager.add_app(app_config)
        
        assert self.config_manager.app_exists("test.com")
        retrieved_config = self.config_manager.get_app("test.com")
        assert retrieved_config.domain == "test.com"

    def test_remove_app(self):
        """Probar remoción de aplicación"""
        app_config = AppConfig.create_new(
            domain="test.com",
            port=3000,
            app_type="nextjs",
            source="/path/to/app"
        )
        
        self.config_manager.add_app(app_config)
        assert self.config_manager.app_exists("test.com")
        
        self.config_manager.remove_app("test.com")
        assert not self.config_manager.app_exists("test.com")

    def test_is_port_in_use(self):
        """Probar verificación de puerto en uso"""
        app_config = AppConfig.create_new(
            domain="test.com",
            port=3000,
            app_type="nextjs",
            source="/path/to/app"
        )
        
        self.config_manager.add_app(app_config)
        
        assert self.config_manager.is_port_in_use(3000)
        assert not self.config_manager.is_port_in_use(4000)
        assert not self.config_manager.is_port_in_use(3000, exclude_domain="test.com")


class TestColors:
    """Pruebas para utilidades de colores"""

    def test_success(self):
        """Probar formato de éxito"""
        result = Colors.success("Test message")
        assert "✅" in result
        assert "Test message" in result

    def test_error(self):
        """Probar formato de error"""
        result = Colors.error("Error message")
        assert "❌" in result
        assert "Error message" in result

    def test_warning(self):
        """Probar formato de advertencia"""
        result = Colors.warning("Warning message")
        assert "⚠️" in result
        assert "Warning message" in result

    def test_info(self):
        """Probar formato informativo"""
        result = Colors.info("Info message")
        assert "ℹ️" in result
        assert "Info message" in result

    def test_step(self):
        """Probar formato de paso"""
        result = Colors.step(1, 5, "Step message")
        assert "[1/5]" in result
        assert "Step message" in result

    def test_header(self):
        """Probar formato de encabezado"""
        result = Colors.header("Header message")
        assert "Header message" in result
        assert "=" in result


if __name__ == "__main__":
    pytest.main([__file__])
