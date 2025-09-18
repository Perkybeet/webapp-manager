"""
Database Manager with SQLAlchemy and SQLite
"""

import os
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for the WebApp Manager SAAS"""
    
    def __init__(self, db_path: str = None):
        """Initialize database manager"""
        if db_path is None:
            db_path = self._get_default_db_path()
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Database initialized at: {self.db_path}")
    
    def _get_default_db_path(self) -> str:
        """Get default database path"""
        home_dir = Path.home()
        db_dir = home_dir / ".webapp-manager" / "data"
        db_dir.mkdir(parents=True, exist_ok=True)
        return str(db_dir / "webapp_manager.db")
    
    def init_database(self):
        """Initialize database with all tables"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(100),
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            
            # Applications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    domain VARCHAR(255) NOT NULL,
                    app_type VARCHAR(50) NOT NULL,
                    port INTEGER NOT NULL,
                    status VARCHAR(20) DEFAULT 'inactive',
                    directory_path TEXT NOT NULL,
                    git_url TEXT,
                    ssl_enabled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """)
            
            # System usage table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_id INTEGER,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    network_in REAL,
                    network_out REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (app_id) REFERENCES applications (id)
                )
            """)
            
            # System logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_id INTEGER,
                    level VARCHAR(20),
                    message TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (app_id) REFERENCES applications (id)
                )
            """)
            
            # Configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key VARCHAR(100) UNIQUE NOT NULL,
                    value TEXT,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            conn.commit()
            logger.info("Database tables created/verified successfully")
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dictionaries"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row  # This enables column access by name
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows count"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT query and return the last row ID"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    # User management methods
    def create_user(self, username: str, password_hash: str, email: str = None, is_admin: bool = False) -> int:
        """Create a new user"""
        query = """
            INSERT INTO users (username, password_hash, email, is_admin)
            VALUES (?, ?, ?, ?)
        """
        return self.execute_insert(query, (username, password_hash, email, is_admin))
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        query = "SELECT * FROM users WHERE username = ? AND is_active = 1"
        results = self.execute_query(query, (username,))
        return results[0] if results else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = ? AND is_active = 1"
        results = self.execute_query(query, (user_id,))
        return results[0] if results else None
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?"
        self.execute_update(query, (user_id,))
    
    # Application management methods
    def create_application(self, name: str, domain: str, app_type: str, port: int, 
                          directory_path: str, git_url: str = None, created_by: int = None) -> int:
        """Create a new application"""
        query = """
            INSERT INTO applications (name, domain, app_type, port, directory_path, git_url, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_insert(query, (name, domain, app_type, port, directory_path, git_url, created_by))
    
    def get_all_applications(self) -> List[Dict[str, Any]]:
        """Get all applications"""
        query = """
            SELECT a.*, u.username as created_by_username
            FROM applications a
            LEFT JOIN users u ON a.created_by = u.id
            ORDER BY a.created_at DESC
        """
        return self.execute_query(query)
    
    def get_application_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get application by name"""
        query = "SELECT * FROM applications WHERE name = ?"
        results = self.execute_query(query, (name,))
        return results[0] if results else None
    
    def update_application_status(self, app_id: int, status: str):
        """Update application status"""
        query = "UPDATE applications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        self.execute_update(query, (status, app_id))
    
    def delete_application(self, app_id: int):
        """Delete an application"""
        query = "DELETE FROM applications WHERE id = ?"
        self.execute_update(query, (app_id,))
    
    # Usage tracking methods
    def record_usage(self, app_id: int, cpu_usage: float, memory_usage: float, 
                    disk_usage: float, network_in: float = 0, network_out: float = 0):
        """Record system usage for an application"""
        query = """
            INSERT INTO system_usage (app_id, cpu_usage, memory_usage, disk_usage, network_in, network_out)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        self.execute_insert(query, (app_id, cpu_usage, memory_usage, disk_usage, network_in, network_out))
    
    def get_usage_history(self, app_id: int = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get usage history for the last N hours"""
        if app_id:
            query = """
                SELECT * FROM system_usage 
                WHERE app_id = ? AND timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp DESC
            """.format(hours)
            return self.execute_query(query, (app_id,))
        else:
            query = """
                SELECT * FROM system_usage 
                WHERE timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp DESC
            """.format(hours)
            return self.execute_query(query)
    
    # Configuration methods
    def set_config(self, key: str, value: str, description: str = None):
        """Set a configuration value"""
        query = """
            INSERT OR REPLACE INTO configuration (key, value, description, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """
        self.execute_update(query, (key, value, description))
    
    def get_config(self, key: str, default_value: str = None) -> str:
        """Get a configuration value"""
        query = "SELECT value FROM configuration WHERE key = ?"
        results = self.execute_query(query, (key,))
        return results[0]['value'] if results else default_value
    
    def get_all_config(self) -> Dict[str, str]:
        """Get all configuration values"""
        query = "SELECT key, value FROM configuration"
        results = self.execute_query(query)
        return {row['key']: row['value'] for row in results}
    
    # Logging methods
    def log_system_event(self, app_id: int, level: str, message: str, details: str = None):
        """Log a system event"""
        query = """
            INSERT INTO system_logs (app_id, level, message, details)
            VALUES (?, ?, ?, ?)
        """
        self.execute_insert(query, (app_id, level, message, details))
    
    def get_system_logs(self, app_id: int = None, level: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get system logs"""
        query = "SELECT * FROM system_logs WHERE 1=1"
        params = []
        
        if app_id:
            query += " AND app_id = ?"
            params.append(app_id)
        
        if level:
            query += " AND level = ?"
            params.append(level)
        
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        return self.execute_query(query, tuple(params))