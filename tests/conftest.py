"""
Configuración de pruebas para pytest
"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Fixture para directorio temporal"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_app_config():
    """Fixture para configuración de aplicación mock"""
    from webapp_manager.models import AppConfig
    
    return AppConfig.create_new(
        domain="test.example.com",
        port=3000,
        app_type="nextjs",
        source="/path/to/test/app",
        branch="main",
        ssl=True
    )
