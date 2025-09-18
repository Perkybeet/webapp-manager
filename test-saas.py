#!/usr/bin/env python3
"""
WebApp Manager SAAS - Test Script
Tests the basic functionality of the SAAS system
"""

import sys
import os
import asyncio
import sqlite3
import subprocess
from pathlib import Path

# Add the webapp_manager to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import fastapi
        print(f"  ✅ FastAPI: {fastapi.__version__}")
    except ImportError as e:
        print(f"  ❌ FastAPI: {e}")
        return False
    
    try:
        import uvicorn
        print(f"  ✅ Uvicorn: {uvicorn.__version__}")
    except ImportError as e:
        print(f"  ❌ Uvicorn: {e}")
        return False
    
    try:
        import jinja2
        print(f"  ✅ Jinja2: {jinja2.__version__}")
    except ImportError as e:
        print(f"  ❌ Jinja2: {e}")
        return False
    
    try:
        import passlib
        print(f"  ✅ Passlib: {passlib.__version__}")
    except ImportError as e:
        print(f"  ❌ Passlib: {e}")
        return False
    
    try:
        from webapp_manager.web import app, database, auth
        print("  ✅ WebApp Manager Web modules")
    except ImportError as e:
        print(f"  ❌ WebApp Manager Web modules: {e}")
        return False
    
    return True

def test_database():
    """Test database functionality"""
    print("\n🗃️  Testing database...")
    
    try:
        from webapp_manager.web.database import DatabaseManager
        
        # Test database creation
        test_db_path = "test_webapp_manager.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        db = DatabaseManager(test_db_path)
        print("  ✅ Database manager created")
        
        # Test user operations
        user_id = db.create_user("testuser", "testpass123", "test@example.com")
        print(f"  ✅ User created with ID: {user_id}")
        
        user = db.get_user_by_username("testuser")
        print(f"  ✅ User retrieved: {user['username']}")
        
        # Test application operations
        app_data = {
            "domain": "test.example.com",
            "app_type": "static",
            "status": "active",
            "config": {"port": 3000}
        }
        app_id = db.create_application(**app_data)
        print(f"  ✅ Application created with ID: {app_id}")
        
        # Test system log
        db.add_system_log("info", "test", "Test log message")
        print("  ✅ System log added")
        
        # Cleanup
        os.remove(test_db_path)
        print("  ✅ Test database cleaned up")
        
        return True
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        return False

def test_auth():
    """Test authentication functionality"""
    print("\n🔐 Testing authentication...")
    
    try:
        from webapp_manager.web.auth import hash_password, verify_password
        
        password = "testpassword123"
        hashed = hash_password(password)
        print("  ✅ Password hashed")
        
        # Test correct password
        if verify_password(password, hashed):
            print("  ✅ Password verification (correct) works")
        else:
            print("  ❌ Password verification (correct) failed")
            return False
        
        # Test wrong password
        if not verify_password("wrongpassword", hashed):
            print("  ✅ Password verification (incorrect) works")
        else:
            print("  ❌ Password verification (incorrect) failed")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ Authentication test failed: {e}")
        return False

def test_web_app():
    """Test FastAPI app creation"""
    print("\n🌐 Testing web application...")
    
    try:
        from webapp_manager.web.app import create_app
        
        app = create_app()
        print("  ✅ FastAPI app created")
        
        # Check routes
        routes = [route.path for route in app.routes]
        expected_routes = ["/", "/login", "/dashboard", "/domains", "/monitoring", "/settings"]
        
        for route in expected_routes:
            if route in routes:
                print(f"  ✅ Route {route} exists")
            else:
                print(f"  ❌ Route {route} missing")
                return False
        
        return True
    except Exception as e:
        print(f"  ❌ Web app test failed: {e}")
        return False

def test_directories():
    """Test required directories exist"""
    print("\n📁 Testing directory structure...")
    
    required_dirs = [
        "webapp_manager/web",
        "webapp_manager/web/templates",
        "webapp_manager/web/static"
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✅ Directory exists: {dir_path}")
        else:
            print(f"  ❌ Directory missing: {dir_path}")
            return False
    
    required_files = [
        "webapp_manager/web/app.py",
        "webapp_manager/web/database.py",
        "webapp_manager/web/auth.py",
        "webapp_manager/web/api.py",
        "webapp_manager/web/templates/base.html",
        "webapp_manager/web/templates/login.html",
        "webapp_manager/web/static/main.css",
        "webapp_manager/web/static/main.js"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ File exists: {file_path}")
        else:
            print(f"  ❌ File missing: {file_path}")
            return False
    
    return True

def test_entry_point():
    """Test the main entry point"""
    print("\n🚀 Testing entry point...")
    
    try:
        # Test that the main script exists
        if not os.path.exists("webapp-manager-saas.py"):
            print("  ❌ webapp-manager-saas.py not found")
            return False
        
        print("  ✅ webapp-manager-saas.py exists")
        
        # Test help command
        result = subprocess.run([
            sys.executable, "webapp-manager-saas.py", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "usage:" in result.stdout.lower():
            print("  ✅ Help command works")
        else:
            print(f"  ❌ Help command failed: {result.stderr}")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ Entry point test failed: {e}")
        return False

def test_configuration():
    """Test configuration files"""
    print("\n⚙️  Testing configuration...")
    
    try:
        config_files = [
            "webapp_manager/web/requirements-web.txt",
            "README-SAAS.md",
            "QUICKSTART.md"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                print(f"  ✅ Config file exists: {config_file}")
            else:
                print(f"  ❌ Config file missing: {config_file}")
                return False
        
        # Test requirements file content
        with open("webapp_manager/web/requirements-web.txt", "r") as f:
            requirements = f.read()
            if "fastapi" in requirements and "uvicorn" in requirements:
                print("  ✅ Requirements file has core dependencies")
            else:
                print("  ❌ Requirements file missing core dependencies")
                return False
        
        return True
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🧪 WebApp Manager SAAS - Test Suite")
    print("====================================")
    
    tests = [
        ("Imports", test_imports),
        ("Database", test_database),
        ("Authentication", test_auth),
        ("Web App", test_web_app),
        ("Directories", test_directories),
        ("Entry Point", test_entry_point),
        ("Configuration", test_configuration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"\n❌ Test '{test_name}' failed")
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The SAAS system is ready to use.")
        print("\n🚀 Next steps:")
        print("  1. Run: python webapp-manager-saas.py web")
        print("  2. Open: http://localhost:8080")
        print("  3. Login: admin / admin123")
        print("  4. Change the default password!")
        return True
    else:
        print("❌ Some tests failed. Please check the installation.")
        print("\n🔧 Troubleshooting:")
        print("  1. Install missing dependencies: pip install -r webapp_manager/web/requirements-web.txt")
        print("  2. Check file permissions")
        print("  3. Verify Python version >= 3.8")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)