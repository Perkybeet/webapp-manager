"""
API Routes for WebApp Manager SAAS
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import sys
import os
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..core.manager import WebAppManager
from ..models.app_config import AppConfig
from .database import DatabaseManager
from .auth import AuthManager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["api"])

# Initialize services
db_manager = DatabaseManager()
auth_manager = AuthManager(db_manager)

# Pydantic models for API requests/responses
class LoginRequest(BaseModel):
    username: str
    password: str

class CreateAppRequest(BaseModel):
    name: str
    domain: str
    app_type: str
    port: int
    directory_path: str
    git_url: Optional[str] = None

class UpdateAppRequest(BaseModel):
    domain: Optional[str] = None
    port: Optional[int] = None
    status: Optional[str] = None

class SystemUsageResponse(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_in: float
    network_out: float
    timestamp: str

class AppResponse(BaseModel):
    id: int
    name: str
    domain: str
    app_type: str
    port: int
    status: str
    directory_path: str
    git_url: Optional[str]
    ssl_enabled: bool
    created_at: str
    updated_at: str
    created_by_username: Optional[str]


def get_current_user(request: Request) -> Dict[str, Any]:
    """Dependency to get current user from session"""
    user = auth_manager.get_current_user_from_session(request.session)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# Authentication endpoints
@router.post("/auth/login")
async def api_login(login_data: LoginRequest, request: Request):
    """API login endpoint"""
    user = auth_manager.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session
    request.session["user_id"] = user["id"]
    request.session["username"] = user["username"]
    
    return {"message": "Login successful", "user": user}


@router.post("/auth/logout")
async def api_logout(request: Request):
    """API logout endpoint"""
    request.session.clear()
    return {"message": "Logout successful"}


@router.get("/auth/me")
async def get_current_user_info(user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return user


# Application management endpoints
@router.get("/applications", response_model=List[AppResponse])
async def get_applications(user: Dict[str, Any] = Depends(get_current_user)):
    """Get all applications"""
    try:
        applications = db_manager.get_all_applications()
        return applications
    except Exception as e:
        logger.error(f"Error getting applications: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/applications")
async def create_application(
    app_data: CreateAppRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new application"""
    try:
        # Check if application already exists
        existing_app = db_manager.get_application_by_name(app_data.name)
        if existing_app:
            raise HTTPException(status_code=400, detail="Application already exists")
        
        # Create application in database
        app_id = db_manager.create_application(
            name=app_data.name,
            domain=app_data.domain,
            app_type=app_data.app_type,
            port=app_data.port,
            directory_path=app_data.directory_path,
            git_url=app_data.git_url,
            created_by=user["id"]
        )
        
        # Try to deploy the application using the existing WebApp Manager
        try:
            webapp_manager = WebAppManager(verbose=True)
            
            # Create AppConfig object
            app_config = AppConfig(
                name=app_data.name,
                domain=app_data.domain,
                app_type=app_data.app_type,
                port=app_data.port,
                directory=app_data.directory_path,
                git_url=app_data.git_url if app_data.git_url else None
            )
            
            # Deploy the application
            result = webapp_manager.add_application(app_config)
            
            if result:
                # Update application status in database
                db_manager.update_application(app_id, {"status": "active"})
                
                # Add success log
                db_manager.add_system_log(
                    level="info",
                    component="deployment",
                    message=f"Application '{app_data.name}' deployed successfully"
                )
            else:
                # Update application status to error
                db_manager.update_application(app_id, {"status": "error"})
                
                # Add error log
                db_manager.add_system_log(
                    level="error",
                    component="deployment",
                    message=f"Failed to deploy application '{app_data.name}'"
                )
                
        except Exception as deploy_error:
            logger.error(f"Deployment error: {deploy_error}")
            # Update status to error but don't fail the request
            db_manager.update_application(app_id, {"status": "error"})
            db_manager.add_system_log(
                level="error",
                component="deployment",
                message=f"Deployment failed for '{app_data.name}': {str(deploy_error)}"
            )
        
        # Return the created application
        app = db_manager.get_application(app_id)
        return JSONResponse(
            status_code=201,
            content={"message": "Application created successfully", "application": app}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/applications/{app_id}")
async def get_application(
    app_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific application"""
    try:
        query = "SELECT * FROM applications WHERE id = ?"
        results = db_manager.execute_query(query, (app_id,))
        
        if not results:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return results[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/applications/{app_id}")
async def update_application(
    app_id: int,
    update_data: UpdateAppRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Update an application"""
    try:
        # Check if application exists
        app = db_manager.get_application_by_name("")  # We need the app by ID
        query = "SELECT * FROM applications WHERE id = ?"
        results = db_manager.execute_query(query, (app_id,))
        
        if not results:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Update fields
        update_fields = []
        params = []
        
        if update_data.domain:
            update_fields.append("domain = ?")
            params.append(update_data.domain)
        
        if update_data.port:
            update_fields.append("port = ?")
            params.append(update_data.port)
        
        if update_data.status:
            update_fields.append("status = ?")
            params.append(update_data.status)
        
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(app_id)
            
            query = f"UPDATE applications SET {', '.join(update_fields)} WHERE id = ?"
            db_manager.execute_update(query, tuple(params))
            
            db_manager.log_system_event(app_id, "INFO", f"Application updated by {user['username']}")
        
        return {"message": "Application updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating application: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/applications/{app_id}")
async def delete_application(
    app_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete an application"""
    try:
        # Check if application exists
        query = "SELECT * FROM applications WHERE id = ?"
        results = db_manager.execute_query(query, (app_id,))
        
        if not results:
            raise HTTPException(status_code=404, detail="Application not found")
        
        app = results[0]
        
        # Try to remove the application using WebApp Manager
        try:
            webapp_manager = WebAppManager(verbose=True)
            
            # Create AppConfig object from database data
            app_config = AppConfig(
                name=app['name'],
                domain=app['domain'],
                app_type=app['app_type'],
                port=app['port'],
                directory=app['directory_path']
            )
            
            # Remove the application
            success = webapp_manager.remove_application(app_config)
            
            if success:
                db_manager.add_system_log(
                    level="info",
                    component="deployment",
                    message=f"Application '{app['name']}' removed successfully from system"
                )
            else:
                db_manager.add_system_log(
                    level="warning",
                    component="deployment",
                    message=f"Failed to remove application '{app['name']}' from system"
                )
                
        except Exception as remove_error:
            logger.error(f"Error removing application from system: {remove_error}")
            db_manager.add_system_log(
                level="error",
                component="deployment",
                message=f"Error removing '{app['name']}' from system: {str(remove_error)}"
            )
        
        # Remove from database
        db_manager.delete_application(app_id)
        
        return {"message": "Application deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting application: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
        # Delete from database
        db_manager.delete_application(app_id)
        db_manager.log_system_event(app_id, "INFO", f"Application {app['name']} deleted by {user['username']}")
        
        return {"message": "Application deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting application: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/applications/{app_id}/start")
async def start_application(
    app_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Start an application"""
    try:
        # Get application
        query = "SELECT * FROM applications WHERE id = ?"
        results = db_manager.execute_query(query, (app_id,))
        
        if not results:
            raise HTTPException(status_code=404, detail="Application not found")
        
        app = results[0]
        
        # Start the application using WebApp Manager
        try:
            webapp_manager = WebAppManager(verbose=True)
            
            # Try to start the systemd service
            from webapp_manager.services.systemd_service import SystemdService
            systemd_service = SystemdService()
            
            service_name = f"{app['name']}-webapp"
            success = systemd_service.start_service(service_name)
            
            if success:
                db_manager.update_application(app_id, {"status": "active"})
                db_manager.add_system_log(
                    level="info",
                    component="service",
                    message=f"Application '{app['name']}' started successfully"
                )
                return {"message": "Application started successfully"}
            else:
                db_manager.update_application(app_id, {"status": "error"})
                db_manager.add_system_log(
                    level="error",
                    component="service",
                    message=f"Failed to start application '{app['name']}'"
                )
                raise HTTPException(status_code=500, detail="Failed to start application")
                
        except Exception as start_error:
            logger.error(f"Error starting application: {start_error}")
            db_manager.update_application(app_id, {"status": "error"})
            db_manager.add_system_log(
                level="error",
                component="service",
                message=f"Error starting '{app['name']}': {str(start_error)}"
            )
            raise HTTPException(status_code=500, detail=f"Failed to start application: {str(start_error)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/applications/{app_id}/stop")
async def stop_application(
    app_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Stop an application"""
    try:
        # Get application
        query = "SELECT * FROM applications WHERE id = ?"
        results = db_manager.execute_query(query, (app_id,))
        
        if not results:
            raise HTTPException(status_code=404, detail="Application not found")
        
        app = results[0]
        
        # Stop the application using WebApp Manager
        try:
            from webapp_manager.services.systemd_service import SystemdService
            systemd_service = SystemdService()
            
            service_name = f"{app['name']}-webapp"
            success = systemd_service.stop_service(service_name)
            
            if success:
                db_manager.update_application(app_id, {"status": "inactive"})
                db_manager.add_system_log(
                    level="info",
                    component="service",
                    message=f"Application '{app['name']}' stopped successfully"
                )
                return {"message": "Application stopped successfully"}
            else:
                db_manager.add_system_log(
                    level="error",
                    component="service",
                    message=f"Failed to stop application '{app['name']}'"
                )
                raise HTTPException(status_code=500, detail="Failed to stop application")
                
        except Exception as stop_error:
            logger.error(f"Error stopping application: {stop_error}")
            db_manager.add_system_log(
                level="error",
                component="service",
                message=f"Error stopping '{app['name']}': {str(stop_error)}"
            )
            raise HTTPException(status_code=500, detail=f"Failed to stop application: {str(stop_error)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping application: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/applications/{app_id}/restart")
async def restart_application(
    app_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Restart an application"""
    try:
        # Get application
        app = db_manager.get_application(app_id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Restart the application using systemd
        try:
            from webapp_manager.services.systemd_service import SystemdService
            systemd_service = SystemdService()
            
            service_name = f"{app['name']}-webapp"
            success = systemd_service.restart_service(service_name)
            
            if success:
                db_manager.update_application(app_id, {"status": "active"})
                db_manager.add_system_log(
                    level="info",
                    component="service",
                    message=f"Application '{app['name']}' restarted successfully"
                )
                return {"message": "Application restarted successfully"}
            else:
                db_manager.update_application(app_id, {"status": "error"})
                db_manager.add_system_log(
                    level="error",
                    component="service",
                    message=f"Failed to restart application '{app['name']}'"
                )
                raise HTTPException(status_code=500, detail="Failed to restart application")
                
        except Exception as restart_error:
            logger.error(f"Error restarting application: {restart_error}")
            db_manager.update_application(app_id, {"status": "error"})
            db_manager.add_system_log(
                level="error",
                component="service",
                message=f"Error restarting '{app['name']}': {str(restart_error)}"
            )
            raise HTTPException(status_code=500, detail=f"Failed to restart application: {str(restart_error)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting application: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# System monitoring endpoints
@router.get("/system/stats")
async def get_system_stats(user: Dict[str, Any] = Depends(get_current_user)):
    """Get overall system statistics"""
    try:
        # Get application counts
        applications = db_manager.get_all_applications()
        total_apps = len(applications)
        active_apps = len([app for app in applications if app['status'] == 'active'])
        
        # Get system resource usage using Linux commands
        import psutil
        import shutil
        
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Disk usage for root partition
        disk_usage = psutil.disk_usage('/')
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        
        # Network stats
        network = psutil.net_io_counters()
        
        # Process count
        process_count = len(psutil.pids())
        
        # Load average (Linux specific)
        try:
            load_avg = os.getloadavg()
        except AttributeError:
            load_avg = [0, 0, 0]  # Windows doesn't have loadavg
        
        return {
            "applications": {
                "total": total_apps,
                "active": active_apps,
                "inactive": total_apps - active_apps,
                "error": len([app for app in applications if app['status'] == 'error'])
            },
            "system": {
                "cpu_usage": round(cpu_usage, 2),
                "memory_usage": round(memory_usage, 2),
                "memory_total": round(memory.total / (1024**3), 2),  # GB
                "memory_available": round(memory.available / (1024**3), 2),  # GB
                "disk_usage": round(disk_percent, 2),
                "disk_total": round(disk_usage.total / (1024**3), 2),  # GB
                "disk_free": round(disk_usage.free / (1024**3), 2),  # GB
                "load_avg": [round(avg, 2) for avg in load_avg],
                "process_count": process_count,
                "uptime": get_system_uptime()
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_received": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_received": network.packets_recv
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        # Return basic stats if detailed stats fail
        return {
            "applications": {
                "total": len(db_manager.get_all_applications()),
                "active": 0,
                "inactive": 0,
                "error": 0
            },
            "system": {
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0,
                "error": str(e)
            }
        }

def get_system_uptime():
    """Get system uptime in seconds"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        return uptime_seconds
    except:
        return 0


@router.get("/system/usage/{app_id}")
async def get_application_usage(
    app_id: int,
    hours: int = 24,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get usage history for a specific application"""
    try:
        usage_history = db_manager.get_usage_history(app_id, hours)
        return {"usage_history": usage_history}
        
    except Exception as e:
        logger.error(f"Error getting application usage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/system/logs")
async def get_system_logs(
    app_id: Optional[int] = None,
    level: Optional[str] = None,
    limit: int = 100,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get system logs"""
    try:
        logs = db_manager.get_system_logs(app_id, level, limit)
        return {"logs": logs}
        
    except Exception as e:
        logger.error(f"Error getting system logs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Configuration endpoints
@router.get("/config")
async def get_configuration(user: Dict[str, Any] = Depends(get_current_user)):
    """Get all configuration settings"""
    try:
        config = db_manager.get_all_config()
        return {"config": config}
        
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/config")
async def update_configuration(
    config_data: Dict[str, str],
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Update configuration settings"""
    try:
        # Require admin for config changes
        auth_manager.require_admin(user)
        
        for key, value in config_data.items():
            db_manager.set_config(key, value)
        
        db_manager.log_system_event(None, "INFO", f"Configuration updated by {user['username']}")
        return {"message": "Configuration updated successfully"}
        
    except PermissionError:
        raise HTTPException(status_code=403, detail="Admin access required")
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")