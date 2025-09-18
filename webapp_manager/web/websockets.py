"""
WebSocket endpoints for real-time updates
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends
from fastapi.routing import APIRouter
import json
import asyncio
import logging
from typing import List, Dict, Any
import psutil
import time

from .database import DatabaseManager
from .auth import AuthManager

logger = logging.getLogger(__name__)

# Create WebSocket router
ws_router = APIRouter()

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.db_manager = DatabaseManager()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        message_str = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def get_system_metrics(self):
        """Get current system metrics"""
        try:
            return {
                "type": "system_metrics",
                "data": {
                    "cpu_usage": psutil.cpu_percent(interval=None),
                    "memory_usage": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0,
                    "load_avg": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0, 0, 0],
                    "network": {
                        "bytes_sent": psutil.net_io_counters().bytes_sent,
                        "bytes_recv": psutil.net_io_counters().bytes_recv
                    },
                    "timestamp": time.time()
                }
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {
                "type": "system_metrics",
                "data": {
                    "error": str(e),
                    "timestamp": time.time()
                }
            }

    async def get_application_status(self):
        """Get current application statuses"""
        try:
            applications = self.db_manager.get_all_applications()
            return {
                "type": "application_status",
                "data": {
                    "applications": applications,
                    "summary": {
                        "total": len(applications),
                        "active": len([app for app in applications if app.get('status') == 'active']),
                        "inactive": len([app for app in applications if app.get('status') == 'inactive']),
                        "error": len([app for app in applications if app.get('status') == 'error'])
                    },
                    "timestamp": time.time()
                }
            }
        except Exception as e:
            logger.error(f"Error getting application status: {e}")
            return {
                "type": "application_status",
                "data": {
                    "error": str(e),
                    "timestamp": time.time()
                }
            }

    async def get_recent_logs(self, limit: int = 10):
        """Get recent system logs"""
        try:
            logs = self.db_manager.get_system_logs(limit=limit)
            return {
                "type": "recent_logs",
                "data": {
                    "logs": logs,
                    "timestamp": time.time()
                }
            }
        except Exception as e:
            logger.error(f"Error getting recent logs: {e}")
            return {
                "type": "recent_logs",
                "data": {
                    "error": str(e),
                    "timestamp": time.time()
                }
            }

# Global connection manager
manager = ConnectionManager()

@ws_router.websocket("/ws/monitoring")
async def websocket_monitoring(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring updates"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Send system metrics every 5 seconds
            metrics = await manager.get_system_metrics()
            await manager.send_personal_message(json.dumps(metrics), websocket)
            
            # Send application status every 10 seconds
            app_status = await manager.get_application_status()
            await manager.send_personal_message(json.dumps(app_status), websocket)
            
            # Wait before next update
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@ws_router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for real-time log updates"""
    await manager.connect(websocket)
    last_log_id = 0
    
    try:
        while True:
            # Get recent logs
            logs = await manager.get_recent_logs(limit=50)
            
            # Filter new logs only
            new_logs = []
            if logs.get("data", {}).get("logs"):
                for log in logs["data"]["logs"]:
                    if log.get("id", 0) > last_log_id:
                        new_logs.append(log)
                        last_log_id = max(last_log_id, log.get("id", 0))
            
            if new_logs:
                await manager.send_personal_message(json.dumps({
                    "type": "new_logs",
                    "data": {
                        "logs": new_logs,
                        "timestamp": time.time()
                    }
                }), websocket)
            
            await asyncio.sleep(2)  # Check for new logs every 2 seconds
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket logs error: {e}")
        manager.disconnect(websocket)

@ws_router.websocket("/ws/applications")
async def websocket_applications(websocket: WebSocket):
    """WebSocket endpoint for application status updates"""
    await manager.connect(websocket)
    
    try:
        # Send initial application data
        app_status = await manager.get_application_status()
        await manager.send_personal_message(json.dumps(app_status), websocket)
        
        while True:
            # Listen for messages from client (e.g., requests for specific updates)
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "request_update":
                    # Send immediate update
                    app_status = await manager.get_application_status()
                    await manager.send_personal_message(json.dumps(app_status), websocket)
                    
            except asyncio.TimeoutError:
                # Send periodic updates even without client requests
                app_status = await manager.get_application_status()
                await manager.send_personal_message(json.dumps(app_status), websocket)
                
            await asyncio.sleep(10)  # Update every 10 seconds
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket applications error: {e}")
        manager.disconnect(websocket)

async def broadcast_system_event(event_type: str, data: Dict[str, Any]):
    """Broadcast system event to all connected clients"""
    message = {
        "type": "system_event",
        "event_type": event_type,
        "data": data,
        "timestamp": time.time()
    }
    await manager.broadcast(message)

async def broadcast_application_update(app_id: int, action: str, status: str = None):
    """Broadcast application update to all connected clients"""
    message = {
        "type": "application_update",
        "data": {
            "app_id": app_id,
            "action": action,
            "status": status,
            "timestamp": time.time()
        }
    }
    await manager.broadcast(message)