"""
Authentication Manager for WebApp Manager SAAS
"""

import hashlib
import secrets
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AuthManager:
    """Handles user authentication and session management"""
    
    def __init__(self, db_manager):
        """Initialize auth manager with database"""
        self.db = db_manager
    
    def hash_password(self, password: str) -> str:
        """Hash a password with salt"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password against stored hash"""
        try:
            salt, password_hash = stored_hash.split(':')
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return computed_hash == password_hash
        except ValueError:
            return False
    
    def create_user(self, username: str, password: str, email: str = None, is_admin: bool = False) -> int:
        """Create a new user"""
        try:
            password_hash = self.hash_password(password)
            user_id = self.db.create_user(username, password_hash, email, is_admin)
            logger.info(f"User created: {username} (ID: {user_id})")
            return user_id
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with username and password"""
        try:
            user = self.db.get_user_by_username(username)
            if not user:
                logger.warning(f"Authentication failed for username: {username} (user not found)")
                return None
            
            if not self.verify_password(password, user['password_hash']):
                logger.warning(f"Authentication failed for username: {username} (invalid password)")
                return None
            
            # Update last login
            self.db.update_last_login(user['id'])
            
            # Remove password hash from returned user data
            user_data = dict(user)
            del user_data['password_hash']
            
            logger.info(f"User authenticated successfully: {username}")
            return user_data
            
        except Exception as e:
            logger.error(f"Error authenticating user {username}: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username (without password hash)"""
        try:
            user = self.db.get_user_by_username(username)
            if user:
                user_data = dict(user)
                del user_data['password_hash']
                return user_data
            return None
        except Exception as e:
            logger.error(f"Error getting user {username}: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID (without password hash)"""
        try:
            user = self.db.get_user_by_id(user_id)
            if user:
                user_data = dict(user)
                del user_data['password_hash']
                return user_data
            return None
        except Exception as e:
            logger.error(f"Error getting user with ID {user_id}: {e}")
            return None
    
    def get_current_user_from_session(self, session: Dict) -> Optional[Dict[str, Any]]:
        """Get current user from session data"""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return None
            
            return self.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Error getting current user from session: {e}")
            return None
    
    def update_password(self, user_id: int, new_password: str) -> bool:
        """Update user password"""
        try:
            password_hash = self.hash_password(new_password)
            query = "UPDATE users SET password_hash = ? WHERE id = ?"
            affected_rows = self.db.execute_update(query, (password_hash, user_id))
            
            if affected_rows > 0:
                logger.info(f"Password updated for user ID: {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating password for user ID {user_id}: {e}")
            return False
    
    def is_admin(self, user: Dict[str, Any]) -> bool:
        """Check if user is admin"""
        return user.get('is_admin', False)
    
    def require_admin(self, user: Dict[str, Any]) -> bool:
        """Require user to be admin (raises exception if not)"""
        if not self.is_admin(user):
            raise PermissionError("Admin access required")
        return True
    
    def generate_session_token(self) -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)
    
    def create_session(self, user_id: int, expires_hours: int = 24) -> str:
        """Create a new session for user"""
        token = self.generate_session_token()
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        query = """
            INSERT INTO user_sessions (user_id, session_token, expires_at)
            VALUES (?, ?, ?)
        """
        self.db.execute_insert(query, (user_id, token, expires_at.isoformat()))
        return token
    
    def validate_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate session token and return user if valid"""
        try:
            query = """
                SELECT u.* FROM users u
                JOIN user_sessions s ON u.id = s.user_id
                WHERE s.session_token = ? AND s.expires_at > datetime('now')
                AND u.is_active = 1
            """
            results = self.db.execute_query(query, (token,))
            
            if results:
                user_data = dict(results[0])
                del user_data['password_hash']
                return user_data
            return None
            
        except Exception as e:
            logger.error(f"Error validating session token: {e}")
            return None
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions from database"""
        try:
            query = "DELETE FROM user_sessions WHERE expires_at < datetime('now')"
            deleted_count = self.db.execute_update(query)
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired sessions")
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
    
    def revoke_session(self, token: str):
        """Revoke a specific session token"""
        try:
            query = "DELETE FROM user_sessions WHERE session_token = ?"
            self.db.execute_update(query, (token,))
            logger.info("Session revoked successfully")
        except Exception as e:
            logger.error(f"Error revoking session: {e}")
    
    def revoke_all_user_sessions(self, user_id: int):
        """Revoke all sessions for a specific user"""
        try:
            query = "DELETE FROM user_sessions WHERE user_id = ?"
            deleted_count = self.db.execute_update(query, (user_id,))
            logger.info(f"Revoked {deleted_count} sessions for user ID: {user_id}")
        except Exception as e:
            logger.error(f"Error revoking all sessions for user ID {user_id}: {e}")