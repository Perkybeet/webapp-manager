"""
FastAPI Web Application for WebApp Manager SAAS
"""

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import secrets
import uvicorn
from pathlib import Path
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .database import DatabaseManager
from .auth import AuthManager
from .api import router as api_router
from .websockets import ws_router

# Get the web directory path
WEB_DIR = Path(__file__).parent
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"

# Ensure directories exist
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="WebApp Manager SAAS",
    description="Control Panel for WebApp Manager",
    version="1.0.0",
)

# Add middleware
app.add_middleware(
    SessionMiddleware, 
    secret_key=secrets.token_urlsafe(32)
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Initialize services
db_manager = DatabaseManager()
auth_manager = AuthManager(db_manager)

# Include API routes
app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and create default admin user"""
    db_manager.init_database()
    # Create default admin user if it doesn't exist
    if not auth_manager.get_user_by_username("admin"):
        auth_manager.create_user("admin", "admin123", is_admin=True)
        print("Created default admin user (username: admin, password: admin123)")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard"""
    # Check if user is logged in
    user = auth_manager.get_current_user_from_session(request.session)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request):
    """Process login"""
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")
    
    user = auth_manager.authenticate_user(username, password)
    if user:
        request.session["user_id"] = user["id"]
        request.session["username"] = user["username"]
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Invalid username or password"
    })


@app.get("/logout")
async def logout(request: Request):
    """Logout user"""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@app.get("/domains", response_class=HTMLResponse)
async def domains_page(request: Request):
    """Domains management page"""
    user = auth_manager.get_current_user_from_session(request.session)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("domains.html", {
        "request": request,
        "user": user
    })


@app.get("/monitoring", response_class=HTMLResponse)
async def monitoring_page(request: Request):
    """System monitoring page"""
    user = auth_manager.get_current_user_from_session(request.session)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("monitoring.html", {
        "request": request,
        "user": user
    })


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page"""
    user = auth_manager.get_current_user_from_session(request.session)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": user
    })


def run_web_server(host: str = "0.0.0.0", port: int = 8080, debug: bool = False):
    """Run the web server"""
    uvicorn.run(
        "webapp_manager.web.app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if debug else "warning"
    )


if __name__ == "__main__":
    run_web_server(debug=True)