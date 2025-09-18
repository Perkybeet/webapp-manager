#!/bin/bash

# WebApp Manager SAAS - Deployment Script para Linux
# Este script automatiza la instalación y configuración del sistema SAAS

set -e

echo "🚀 WebApp Manager SAAS - Linux Deployment Script"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration variables
WEB_PORT=${WEBAPP_MANAGER_WEB_PORT:-8080}
WEB_HOST=${WEBAPP_MANAGER_WEB_HOST:-0.0.0.0}
DOMAIN=${WEBAPP_MANAGER_DOMAIN:-""}
SERVICE_USER=${SERVICE_USER:-webapp-manager}
INSTALL_DIR=${INSTALL_DIR:-/opt/webapp-manager}
UNATTENDED=${UNATTENDED:-false}
ENABLE_SSL=${ENABLE_SSL:-false}
ENABLE_FIREWALL=${ENABLE_FIREWALL:-false}

# Global variable for Python executable path
PYTHON_EXEC=""

# Global variables for actual installation paths (set by install_dependencies and verify_installation)
ACTUAL_WORKING_DIR=""
ACTUAL_VENV_DIR=""
ACTUAL_MAIN_SCRIPT=""
ACTUAL_PYTHON_EXEC=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unattended)
            UNATTENDED=true
            shift
            ;;
        --enable-ssl)
            ENABLE_SSL=true
            shift
            ;;
        --enable-firewall)
            ENABLE_FIREWALL=true
            shift
            ;;
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --port)
            WEB_PORT="$2"
            shift 2
            ;;
        --user)
            SERVICE_USER="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

show_help() {
    echo "WebApp Manager SAAS - Linux Deployment Script"
    echo "=============================================="
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --unattended          Run in unattended mode (no prompts)"
    echo "  --enable-ssl          Enable SSL certificate with Let's Encrypt"
    echo "  --enable-firewall     Enable and activate firewall (UFW/firewalld)"
    echo "  --domain DOMAIN       Set domain for the SAAS panel"
    echo "  --port PORT           Set web server port (default: 8080)"
    echo "  --user USER           Set service user (default: webapp-manager)"
    echo "  --help                Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  WEBAPP_MANAGER_WEB_PORT    Web server port"
    echo "  WEBAPP_MANAGER_WEB_HOST    Web server host"
    echo "  WEBAPP_MANAGER_DOMAIN      Domain name for the panel"
    echo ""
    echo "Examples:"
    echo "  $0"
    echo "  $0 --unattended --domain panel.example.com --enable-ssl"
    echo "  $0 --port 9000 --user myuser"
}

# Check if running as root or has sudo privileges
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root user"
        log_info "Script will install system-wide with root privileges"
        # Set different defaults for root installation
        if [[ "$SERVICE_USER" == "webapp-manager" ]]; then
            SERVICE_USER="root"
        fi
        if [[ "$INSTALL_DIR" == "/opt/webapp-manager" ]]; then
            INSTALL_DIR="/root/webapp-manager"
        fi
        # Set command prefixes for root
        CMD_PREFIX=""
        SYSTEMCTL_CMD="systemctl"
        return 0
    fi
    
    # Check if user has sudo privileges
    if ! sudo -n true 2>/dev/null; then
        log_error "This script requires sudo privileges or must be run as root"
        log_info "Please run with sudo or as root user"
        exit 1
    fi
    
    log_info "Running with sudo privileges"
    # Set command prefixes for sudo
    CMD_PREFIX="sudo"
    SYSTEMCTL_CMD="sudo systemctl"
}

# Detect Linux distribution
detect_distro() {
    log_step "Detecting Linux distribution..."
    
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    elif [[ -f /etc/debian_version ]]; then
        DISTRO="debian"
        VERSION=$(cat /etc/debian_version)
    elif [[ -f /etc/redhat-release ]]; then
        DISTRO="rhel"
        VERSION=$(rpm -q --qf "%{VERSION}" $(rpm -q --whatprovides redhat-release))
    else
        log_error "Unable to detect Linux distribution"
        exit 1
    fi
    
    log_success "Detected: $PRETTY_NAME"
    
    case $DISTRO in
        ubuntu|debian)
            PKG_MANAGER="apt"
            if [[ $EUID -eq 0 ]]; then
                PKG_UPDATE="apt update"
                PKG_INSTALL="apt install -y"
            else
                PKG_UPDATE="sudo apt update"
                PKG_INSTALL="sudo apt install -y"
            fi
            NGINX_SITES="/etc/nginx/sites-available"
            NGINX_ENABLED="/etc/nginx/sites-enabled"
            ;;
        centos|rhel|fedora|almalinux|rocky)
            PKG_MANAGER="dnf"
            if [[ $EUID -eq 0 ]]; then
                PKG_UPDATE="dnf update -y"
                PKG_INSTALL="dnf install -y"
            else
                PKG_UPDATE="sudo dnf update -y"
                PKG_INSTALL="sudo dnf install -y"
            fi
            NGINX_SITES="/etc/nginx/conf.d"
            NGINX_ENABLED="/etc/nginx/conf.d"
            ;;
        arch|manjaro)
            PKG_MANAGER="pacman"
            if [[ $EUID -eq 0 ]]; then
                PKG_UPDATE="pacman -Sy"
                PKG_INSTALL="pacman -S --noconfirm"
            else
                PKG_UPDATE="sudo pacman -Sy"
                PKG_INSTALL="sudo pacman -S --noconfirm"
            fi
            NGINX_SITES="/etc/nginx/sites-available"
            NGINX_ENABLED="/etc/nginx/sites-enabled"
            ;;
        *)
            log_warning "Unsupported distribution: $DISTRO"
            log_info "Proceeding with generic installation..."
            PKG_MANAGER="unknown"
            ;;
    esac
}

# Check system requirements
check_requirements() {
    log_step "Checking system requirements..."
    
    local missing_packages=()
    
    # Check Python 3.8+
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        local python_major=$(echo $python_version | cut -d. -f1)
        local python_minor=$(echo $python_version | cut -d. -f2)
        
        if [[ $python_major -ge 3 && $python_minor -ge 8 ]]; then
            log_success "Python $python_version found"
        else
            log_error "Python 3.8+ required, found $python_version"
            exit 1
        fi
    else
        missing_packages+=("python3")
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        missing_packages+=("python3-pip")
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        missing_packages+=("git")
    fi
    
    # Install missing packages
    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        log_info "Installing missing packages: ${missing_packages[*]}"
        $PKG_UPDATE
        
        case $PKG_MANAGER in
            apt)
                $CMD_PREFIX $PKG_INSTALL python3 python3-pip python3-venv git nginx sqlite3 curl wget
                ;;
            dnf)
                $CMD_PREFIX $PKG_INSTALL python3 python3-pip git nginx sqlite curl wget
                ;;
            pacman)
                $CMD_PREFIX $PKG_INSTALL python python-pip git nginx sqlite curl wget
                ;;
            *)
                log_error "Cannot install packages automatically"
                log_info "Please install: ${missing_packages[*]}"
                exit 1
                ;;
        esac
    fi
    
    log_success "System requirements check completed"
}

# Create system user
create_service_user() {
    log_step "Setting up service user '$SERVICE_USER'..."
    
    if [[ "$SERVICE_USER" == "root" ]]; then
        log_info "Using root user for service execution"
        # Ensure install directory exists with correct permissions
        $CMD_PREFIX mkdir -p "$INSTALL_DIR"
        return 0
    fi
    
    if id "$SERVICE_USER" &>/dev/null; then
        log_info "User '$SERVICE_USER' already exists"
    else
        $CMD_PREFIX useradd -r -s /bin/bash -d "$INSTALL_DIR" -m "$SERVICE_USER"
        log_success "Created user '$SERVICE_USER'"
    fi
    
    # Ensure install directory exists with correct permissions
    $CMD_PREFIX mkdir -p "$INSTALL_DIR"
    $CMD_PREFIX chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
}

# Install Python dependencies in virtual environment
install_dependencies() {
    log_step "Installing Python dependencies..."
    
    # Determine the correct working directory and setup
    cd "$INSTALL_DIR"
    
    # Clone or update repository
    if [[ -d "app" ]]; then
        log_info "App directory already exists, updating..."
        cd app
        git pull origin main || log_warning "Could not update repository"
        cd ..
    elif [[ -f "../webapp-manager-saas.py" && -d "../webapp_manager" ]]; then
        # Running from repo directory, create symlink
        ln -sf .. app
        log_info "Using parent directory as app source"
    elif [[ -f "webapp-manager-saas.py" && -d "webapp_manager" ]]; then
        # Already in the repository directory, create symlink
        ln -sf . app
        log_info "Using current directory as app"
    else
        log_info "Cloning repository..."
        git clone https://github.com/Perkybeet/webapp-manager.git app
    fi
    
    # Determine actual working paths
    if [[ -f "webapp-manager-saas.py" && -d "webapp_manager" ]]; then
        # Main files are in root directory
        ACTUAL_WORKING_DIR="$INSTALL_DIR"
        ACTUAL_VENV_DIR="$INSTALL_DIR/venv"
        ACTUAL_MAIN_SCRIPT="$INSTALL_DIR/webapp-manager-saas.py"
        log_info "Using root directory structure"
    elif [[ -f "app/webapp-manager-saas.py" && -d "app/webapp_manager" ]]; then
        # Main files are in app subdirectory
        ACTUAL_WORKING_DIR="$INSTALL_DIR/app"
        ACTUAL_VENV_DIR="$INSTALL_DIR/app/venv"
        ACTUAL_MAIN_SCRIPT="$INSTALL_DIR/app/webapp-manager-saas.py"
        log_info "Using app subdirectory structure"
        cd app
    else
        log_error "Could not find webapp-manager-saas.py or webapp_manager directory"
        log_info "Directory contents:"
        ls -la "$INSTALL_DIR"
        if [[ -d "$INSTALL_DIR/app" ]]; then
            echo "App directory contents:"
            ls -la "$INSTALL_DIR/app"
        fi
        exit 1
    fi
    
    # Create virtual environment
    log_info "Creating virtual environment in: $ACTUAL_VENV_DIR"
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    if [[ -f "webapp_manager/web/requirements-web.txt" ]]; then
        log_info "Installing from webapp_manager/web/requirements-web.txt"
        pip install -r webapp_manager/web/requirements-web.txt
    else
        log_warning "requirements-web.txt not found, installing basic dependencies"
        pip install fastapi uvicorn jinja2 python-multipart 'passlib[bcrypt]' 'python-jose[cryptography]' psutil
    fi
    
    # Install core dependencies if available
    if [[ -f "requirements.txt" ]]; then
        log_info "Installing from requirements.txt"
        pip install -r requirements.txt
    fi
    
    # Additional verification and fix for virtual environment
    if [[ ! -f "venv/bin/python" ]]; then
        log_warning "venv/bin/python not found, creating symlink"
        if [[ -f "venv/bin/python3" ]]; then
            ln -sf python3 venv/bin/python
        fi
    fi
    
    # Ensure we have a working Python executable
    local test_python=""
    for py_exec in python python3; do
        if [[ -x "venv/bin/$py_exec" ]]; then
            test_python="venv/bin/$py_exec"
            break
        fi
    done
    
    if [[ -z "$test_python" ]]; then
        log_error "No working Python executable found in virtual environment"
        log_info "Contents of venv/bin directory:"
        ls -la venv/bin/ || echo "venv/bin directory does not exist"
        exit 1
    fi
    
    # Test the Python executable
    if ! "$test_python" --version; then
        log_error "Python executable test failed: $test_python"
        exit 1
    fi
    
    # Verify main script exists
    if [[ ! -f "$ACTUAL_MAIN_SCRIPT" ]]; then
        log_error "Main script not found: $ACTUAL_MAIN_SCRIPT"
        exit 1
    fi
    
    # Test main script syntax
    if ! "$test_python" -m py_compile "$ACTUAL_MAIN_SCRIPT"; then
        log_error "Main script syntax check failed: $ACTUAL_MAIN_SCRIPT"
        exit 1
    fi
    
    # Set ownership if not root
    if [[ "$SERVICE_USER" != "root" ]]; then
        $CMD_PREFIX chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    fi
    
    log_success "Python dependencies installed and verified"
    log_info "Working directory: $ACTUAL_WORKING_DIR"
    log_info "Virtual environment: $ACTUAL_VENV_DIR"
    log_info "Main script: $ACTUAL_MAIN_SCRIPT"
}

# Verify installation integrity and determine paths
verify_installation() {
    log_step "Verifying installation integrity and determining paths..."
    
    # These variables should be set by install_dependencies()
    if [[ -z "$ACTUAL_WORKING_DIR" || -z "$ACTUAL_VENV_DIR" || -z "$ACTUAL_MAIN_SCRIPT" ]]; then
        log_error "Installation paths not properly set. Re-running path detection..."
        
        # Fallback path detection
        if [[ -f "$INSTALL_DIR/webapp-manager-saas.py" && -d "$INSTALL_DIR/webapp_manager" ]]; then
            ACTUAL_WORKING_DIR="$INSTALL_DIR"
            ACTUAL_VENV_DIR="$INSTALL_DIR/venv"
            ACTUAL_MAIN_SCRIPT="$INSTALL_DIR/webapp-manager-saas.py"
        elif [[ -f "$INSTALL_DIR/app/webapp-manager-saas.py" && -d "$INSTALL_DIR/app/webapp_manager" ]]; then
            ACTUAL_WORKING_DIR="$INSTALL_DIR/app"
            ACTUAL_VENV_DIR="$INSTALL_DIR/app/venv"
            ACTUAL_MAIN_SCRIPT="$INSTALL_DIR/app/webapp-manager-saas.py"
        else
            log_error "Cannot determine installation paths"
            exit 1
        fi
    fi
    
    log_info "Verifying paths:"
    log_info "  Working directory: $ACTUAL_WORKING_DIR"
    log_info "  Virtual environment: $ACTUAL_VENV_DIR"
    log_info "  Main script: $ACTUAL_MAIN_SCRIPT"
    
    # Check if directories exist
    if [[ ! -d "$ACTUAL_WORKING_DIR" ]]; then
        log_error "Working directory does not exist: $ACTUAL_WORKING_DIR"
        exit 1
    fi
    
    if [[ ! -d "$ACTUAL_VENV_DIR" ]]; then
        log_error "Virtual environment directory does not exist: $ACTUAL_VENV_DIR"
        exit 1
    fi
    
    if [[ ! -f "$ACTUAL_MAIN_SCRIPT" ]]; then
        log_error "Main script does not exist: $ACTUAL_MAIN_SCRIPT"
        exit 1
    fi
    
    # Find and verify Python executable
    ACTUAL_PYTHON_EXEC=""
    venv_python="$ACTUAL_VENV_DIR/bin/python"
    
    # Always prefer the virtual environment Python over resolved system paths
    if [[ -f "$venv_python" ]]; then
        # Use the virtual environment Python directly (even if it's a symlink)
        ACTUAL_PYTHON_EXEC="$venv_python"
        log_info "Using virtual environment Python: $ACTUAL_PYTHON_EXEC"
    elif [[ -L "$venv_python" ]]; then
        # If it's a symlink but the target is within the venv, keep the symlink path
        ACTUAL_PYTHON_EXEC="$venv_python"
        log_info "Using virtual environment Python symlink: $ACTUAL_PYTHON_EXEC"
    else
        # Try alternative paths within the venv
        for py_exec in python3 python3.12 python3.11 python3.10 python3.9 python3.8; do
            if [[ -f "$ACTUAL_VENV_DIR/bin/$py_exec" ]]; then
                ACTUAL_PYTHON_EXEC="$ACTUAL_VENV_DIR/bin/$py_exec"
                log_info "Using virtual environment Python: $ACTUAL_PYTHON_EXEC"
                break
            fi
        done
    fi
    
    # Final validation
    if [[ ! -f "$ACTUAL_PYTHON_EXEC" ]]; then
        log_error "Cannot find a valid Python executable"
        log_info "Searched in: $ACTUAL_VENV_DIR/bin/"
        ls -la "$ACTUAL_VENV_DIR/bin/" 2>/dev/null || echo "bin directory not found"
        exit 1
    fi
    
    if [[ ! -x "$ACTUAL_PYTHON_EXEC" ]]; then
        log_error "Python executable is not executable: $ACTUAL_PYTHON_EXEC"
        $CMD_PREFIX chmod +x "$ACTUAL_PYTHON_EXEC"
    fi
    
    # Test Python executable
    log_info "Testing Python executable..."
    if ! "$ACTUAL_PYTHON_EXEC" --version; then
        log_error "Python executable test failed: $ACTUAL_PYTHON_EXEC"
        exit 1
    fi
    
    # Test that Python can access virtual environment packages
    log_info "Testing virtual environment package access..."
    if ! "$ACTUAL_PYTHON_EXEC" -c "import sys; print('Python path:', sys.executable); import site; print('Site packages:', site.getsitepackages() if hasattr(site, 'getsitepackages') else 'N/A')"; then
        log_warning "Python executable may not have proper virtual environment setup"
    fi
    
    # Test for required packages in the virtual environment
    log_info "Testing for required packages..."
    if ! "$ACTUAL_PYTHON_EXEC" -c "import fastapi, uvicorn; print('FastAPI and Uvicorn are available')" 2>/dev/null; then
        log_warning "Required packages (FastAPI, Uvicorn) may not be available in virtual environment"
        log_info "Attempting to install missing packages..."
        cd "$ACTUAL_WORKING_DIR"
        source venv/bin/activate
        pip install fastapi uvicorn jinja2 python-multipart 'passlib[bcrypt]' 'python-jose[cryptography]' psutil
    fi
    
    # Test main script syntax
    log_info "Testing main script syntax..."
    if ! "$ACTUAL_PYTHON_EXEC" -m py_compile "$ACTUAL_MAIN_SCRIPT"; then
        log_error "Main script syntax check failed: $ACTUAL_MAIN_SCRIPT"
        exit 1
    fi
    
    log_success "Installation verification completed successfully"
    log_info "Final configuration:"
    log_info "  Working Directory: $ACTUAL_WORKING_DIR"
    log_info "  Python Executable: $ACTUAL_PYTHON_EXEC" 
    log_info "  Main Script: $ACTUAL_MAIN_SCRIPT"
    log_info "  Virtual Environment: $ACTUAL_VENV_DIR"
}

# Create configuration
create_configuration() {
    log_step "Creating configuration files..."
    
    # Generate secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Create configuration directory
    $CMD_PREFIX mkdir -p "$INSTALL_DIR/.webapp-manager/"{data,logs,backups,config}
    
    # Create main configuration file
    $CMD_PREFIX tee "$INSTALL_DIR/.webapp-manager/config.env" > /dev/null << EOF
# WebApp Manager SAAS Configuration
WEBAPP_MANAGER_WEB_PORT=$WEB_PORT
WEBAPP_MANAGER_WEB_HOST=$WEB_HOST
WEBAPP_MANAGER_SECRET_KEY=$SECRET_KEY
WEBAPP_MANAGER_DEBUG=false
WEBAPP_MANAGER_DATA_DIR=$INSTALL_DIR/.webapp-manager/data
WEBAPP_MANAGER_LOG_DIR=$INSTALL_DIR/.webapp-manager/logs
WEBAPP_MANAGER_BACKUP_DIR=$INSTALL_DIR/.webapp-manager/backups

# System paths
NGINX_SITES_PATH=$NGINX_SITES
NGINX_ENABLED_PATH=$NGINX_ENABLED
SYSTEMD_PATH=/etc/systemd/system
WEBAPP_BASE_DIR=/var/www

# Logging configuration
LOG_LEVEL=INFO
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5

# Security settings
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=300
EOF
    
    # Set secure permissions
    $CMD_PREFIX chmod 600 "$INSTALL_DIR/.webapp-manager/config.env"
    
    # Set ownership if not root
    if [[ "$SERVICE_USER" != "root" ]]; then
        $CMD_PREFIX chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.webapp-manager"
    fi
    
    log_success "Configuration created"
}

# Create startup wrapper script
create_startup_script() {
    log_step "Creating startup wrapper script..."
    
    # Verify that we have all the required paths from verification
    if [[ -z "$ACTUAL_WORKING_DIR" || -z "$ACTUAL_PYTHON_EXEC" || -z "$ACTUAL_MAIN_SCRIPT" || -z "$ACTUAL_VENV_DIR" ]]; then
        log_error "Missing required installation paths. Run verify_installation first."
        exit 1
    fi
    
    # Create the startup script
    local startup_script="$ACTUAL_WORKING_DIR/start-webapp-manager.sh"
    
    $CMD_PREFIX tee "$startup_script" > /dev/null << EOF
#!/bin/bash
# WebApp Manager SAAS Startup Script
# This script ensures the virtual environment is properly activated

set -e

echo "🚀 Starting WebApp Manager SAAS..."
echo "Working Directory: $ACTUAL_WORKING_DIR"
echo "Virtual Environment: $ACTUAL_VENV_DIR"
echo "Main Script: $ACTUAL_MAIN_SCRIPT"

# Change to the working directory
cd "$ACTUAL_WORKING_DIR"
echo "✅ Changed to working directory: \$(pwd)"

# Verify virtual environment exists
if [[ ! -d "$ACTUAL_VENV_DIR" ]]; then
    echo "❌ Virtual environment not found: $ACTUAL_VENV_DIR"
    exit 1
fi

# Activate the virtual environment
echo "🔄 Activating virtual environment..."
source "$ACTUAL_VENV_DIR/bin/activate"

# Verify activation worked
if [[ "\$VIRTUAL_ENV" == "$ACTUAL_VENV_DIR" ]]; then
    echo "✅ Virtual environment activated: \$VIRTUAL_ENV"
else
    echo "❌ Virtual environment activation failed"
    echo "Expected: $ACTUAL_VENV_DIR"
    echo "Actual: \$VIRTUAL_ENV"
    exit 1
fi

# Show Python executable being used
echo "🐍 Python executable: \$(which python)"
echo "🐍 Python version: \$(python --version)"

# Export additional environment variables
export PYTHONPATH="$ACTUAL_WORKING_DIR:\$PYTHONPATH"
export PYTHONUNBUFFERED=1

# Verify main script exists
if [[ ! -f "$ACTUAL_MAIN_SCRIPT" ]]; then
    echo "❌ Main script not found: $ACTUAL_MAIN_SCRIPT"
    exit 1
fi

# Test critical imports before starting
echo "🔍 Testing critical imports..."
python -c "
try:
    import rich
    print('✅ rich imported successfully')
except ImportError as e:
    print(f'❌ rich import failed: {e}')
    exit(1)

try:
    import fastapi
    print('✅ fastapi imported successfully')
except ImportError as e:
    print(f'❌ fastapi import failed: {e}')
    exit(1)

try:
    from fastapi.middleware.cors import CORSMiddleware
    print('✅ fastapi.middleware.cors imported successfully')
except ImportError as e:
    print(f'❌ fastapi.middleware.cors import failed: {e}')
    exit(1)

try:
    import uvicorn
    print('✅ uvicorn imported successfully')
except ImportError as e:
    print(f'❌ uvicorn import failed: {e}')
    exit(1)
"

if [[ \$? -ne 0 ]]; then
    echo "❌ Critical import test failed. Exiting."
    exit 1
fi

echo "✅ All critical imports successful. Starting application..."

# Start the application
exec python "$ACTUAL_MAIN_SCRIPT" web --host \$WEBAPP_MANAGER_WEB_HOST --port \$WEBAPP_MANAGER_WEB_PORT
EOF
    
    # Make the script executable
    $CMD_PREFIX chmod +x "$startup_script"
    
    # Set ownership if not root
    if [[ "$SERVICE_USER" != "root" ]]; then
        $CMD_PREFIX chown "$SERVICE_USER:$SERVICE_USER" "$startup_script"
    fi
    
    log_success "Startup wrapper script created: $startup_script"
    
    # Store the script path for use in systemd service
    STARTUP_SCRIPT="$startup_script"
}

# Create systemd service
create_systemd_service() {
    log_step "Creating systemd service..."
    
    # Verify that we have all the required paths from verification
    if [[ -z "$ACTUAL_WORKING_DIR" || -z "$ACTUAL_PYTHON_EXEC" || -z "$ACTUAL_MAIN_SCRIPT" || -z "$ACTUAL_VENV_DIR" ]]; then
        log_error "Missing required installation paths. Run verify_installation first."
        exit 1
    fi
    
    # Ensure startup script exists
    if [[ -z "$STARTUP_SCRIPT" || ! -f "$STARTUP_SCRIPT" ]]; then
        log_error "Startup script not found. Run create_startup_script first."
        exit 1
    fi
    
    # Debug information
    log_info "Systemd service configuration:"
    log_info "  Service User: $SERVICE_USER"
    log_info "  Working Directory: $ACTUAL_WORKING_DIR"
    log_info "  Python Executable: $ACTUAL_PYTHON_EXEC"
    log_info "  Main Script: $ACTUAL_MAIN_SCRIPT"
    log_info "  Virtual Environment: $ACTUAL_VENV_DIR"
    
    # Determine security settings based on installation location
    if [[ "$INSTALL_DIR" == /root/* ]] || [[ "$SERVICE_USER" == "root" ]]; then
        log_info "  Security Profile: Relaxed (root installation detected)"
    else
        log_info "  Security Profile: Standard (non-root installation)"
    fi
    
    # Final verification before creating service
    if [[ ! -f "$ACTUAL_PYTHON_EXEC" ]]; then
        log_error "Python executable not found: $ACTUAL_PYTHON_EXEC"
        exit 1
    fi
    
    if [[ ! -f "$ACTUAL_MAIN_SCRIPT" ]]; then
        log_error "Main script not found: $ACTUAL_MAIN_SCRIPT"
        exit 1
    fi
    
    if [[ ! -d "$ACTUAL_WORKING_DIR" ]]; then
        log_error "Working directory not found: $ACTUAL_WORKING_DIR"
        exit 1
    fi
    
    # Critical: Verify that the Python executable is from the virtual environment
    if [[ "$ACTUAL_PYTHON_EXEC" != "$ACTUAL_VENV_DIR"* ]]; then
        log_error "CRITICAL: Python executable is not from virtual environment!"
        log_error "Expected path to start with: $ACTUAL_VENV_DIR"
        log_error "Actual path: $ACTUAL_PYTHON_EXEC"
        log_error "This will cause missing package errors in systemd service"
        exit 1
    fi
    
    log_info "✅ Python executable verification passed - using venv Python"
    
    # Create the systemd service file
    $CMD_PREFIX tee /etc/systemd/system/webapp-manager-saas.service > /dev/null << EOF
[Unit]
Description=WebApp Manager SAAS Control Panel
Documentation=https://github.com/Perkybeet/webapp-manager
After=network.target nginx.service
Wants=nginx.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$ACTUAL_WORKING_DIR
EnvironmentFile=$INSTALL_DIR/.webapp-manager/config.env
ExecStart=$STARTUP_SCRIPT
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=webapp-manager-saas

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Security settings - Adjusted for root installations
NoNewPrivileges=true
EOF

    # Add conditional security settings based on installation location
    if [[ "$INSTALL_DIR" == /root/* ]] || [[ "$SERVICE_USER" == "root" ]]; then
        # More permissive settings for root installations
        $CMD_PREFIX tee -a /etc/systemd/system/webapp-manager-saas.service > /dev/null << EOF
# Root installation - relaxed security settings
ProtectSystem=false
ProtectHome=false
ReadWritePaths=$INSTALL_DIR
ReadWritePaths=$INSTALL_DIR/.webapp-manager
ReadWritePaths=/var/www
ReadWritePaths=/tmp
ReadWritePaths=/var/log
ReadWritePaths=/etc/nginx
EOF
    else
        # Standard security settings for non-root installations
        $CMD_PREFIX tee -a /etc/systemd/system/webapp-manager-saas.service > /dev/null << EOF
# Non-root installation - standard security settings
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR/.webapp-manager
ReadWritePaths=/var/www
ReadWritePaths=/tmp
ReadWritePaths=/var/log
EOF
    fi

    # Close the service file
    $CMD_PREFIX tee -a /etc/systemd/system/webapp-manager-saas.service > /dev/null << EOF

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    $SYSTEMCTL_CMD daemon-reload
    $SYSTEMCTL_CMD enable webapp-manager-saas.service
    
    log_success "Systemd service created and enabled"
}

# Install missing Python packages
install_missing_packages() {
    log_step "Installing missing Python packages..."
    
    cd "$ACTUAL_WORKING_DIR"
    source "$ACTUAL_VENV_DIR/bin/activate"
    
    # Update pip first
    log_info "Updating pip to latest version..."
    pip install --upgrade pip
    
    # List of essential packages that might be missing
    local missing_packages=()
    
    # Core web framework packages
    local core_packages=(
        "rich"
        "fastapi"
        "uvicorn[standard]"
        "jinja2"
        "python-multipart"
        "psutil"
        "starlette"
        "pydantic"
        "typing-extensions"
    )
    
    # Security and authentication packages
    local auth_packages=(
        "passlib[bcrypt]"
        "python-jose[cryptography]"
        "python-multipart"
        "itsdangerous"
    )
    
    # Check and install core packages
    log_info "Checking core web framework packages..."
    for pkg in "${core_packages[@]}"; do
        # Extract package name without extras for import check
        local import_name=$(echo "$pkg" | sed 's/\[.*\]//' | tr '-' '_')
        
        # Special case for uvicorn which has [standard] extra
        if [[ "$pkg" == "uvicorn[standard]" ]]; then
            import_name="uvicorn"
        fi
        
        if ! "$ACTUAL_PYTHON_EXEC" -c "import $import_name" 2>/dev/null; then
            missing_packages+=("$pkg")
        fi
    done
    
    # Check authentication packages with special import handling
    log_info "Checking authentication packages..."
    if ! "$ACTUAL_PYTHON_EXEC" -c "import passlib.hash" 2>/dev/null; then
        missing_packages+=("passlib[bcrypt]")
    fi
    
    if ! "$ACTUAL_PYTHON_EXEC" -c "import jose" 2>/dev/null; then
        missing_packages+=("python-jose[cryptography]")
    fi
    
    if ! "$ACTUAL_PYTHON_EXEC" -c "import itsdangerous" 2>/dev/null; then
        missing_packages+=("itsdangerous")
    fi
    
    # Install missing packages if any
    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        log_info "Installing missing packages: ${missing_packages[*]}"
        pip install --upgrade "${missing_packages[@]}"
        log_success "Package installation completed"
    else
        log_info "All required packages are already installed"
    fi
    
    # Force reinstall FastAPI and related packages if there are import issues
    log_info "Ensuring FastAPI and middleware are properly installed..."
    pip install --upgrade --force-reinstall "fastapi>=0.100.0" "starlette>=0.27.0" "uvicorn[standard]>=0.23.0"
    
    # Verify rich installation specifically
    log_info "Verifying rich package installation..."
    if "$ACTUAL_PYTHON_EXEC" -c "import rich; print(f'Rich version: {rich.__version__}')" 2>/dev/null; then
        log_success "Rich package verified and working"
    else
        log_warning "Rich package verification failed, but this might be due to path issues"
        log_info "Attempting alternative verification..."
        
        # Check if rich is actually installed in site-packages
        if "$ACTUAL_PYTHON_EXEC" -c "import pkg_resources; pkg_resources.get_distribution('rich')" 2>/dev/null; then
            log_success "Rich package is installed (verified via pkg_resources)"
        else
            log_error "Rich package not found in site-packages"
            # Force install rich
            log_info "Force installing rich package..."
            pip install --upgrade --force-reinstall rich
            
            # Test again with pkg_resources
            if "$ACTUAL_PYTHON_EXEC" -c "import pkg_resources; pkg_resources.get_distribution('rich')" 2>/dev/null; then
                log_success "Rich package force installation successful"
            else
                log_error "Rich package installation still failing"
                exit 1
            fi
        fi
    fi
    # Final comprehensive verification
    log_info "Final verification of all essential packages..."
    local verification_failed=false
    
    # Test core imports
    local core_imports=("rich" "fastapi" "uvicorn" "jinja2" "psutil" "starlette" "pydantic")
    for import_name in "${core_imports[@]}"; do
        if "$ACTUAL_PYTHON_EXEC" -c "import $import_name" 2>/dev/null; then
            log_info "✅ $import_name - OK"
        else
            log_warning "❌ $import_name - Failed to import"
            verification_failed=true
        fi
    done
    
    # Test FastAPI middleware specifically
    log_info "Testing FastAPI middleware components..."
    local middleware_tests=(
        "fastapi.middleware.cors:CORSMiddleware"
        "fastapi.middleware.trustedhost:TrustedHostMiddleware" 
        "fastapi.middleware.gzip:GZipMiddleware"
        "starlette.middleware.sessions:SessionMiddleware"
    )
    
    for test in "${middleware_tests[@]}"; do
        local module_path="${test%%:*}"
        local class_name="${test##*:}"
        local test_name="$module_path.$class_name"
        
        if "$ACTUAL_PYTHON_EXEC" -c "from $module_path import $class_name" 2>/dev/null; then
            log_info "✅ $test_name - OK"
        else
            log_warning "❌ $test_name - Failed to import"
            verification_failed=true
        fi
    done
    
    # Test authentication components
    local auth_tests=("passlib.hash" "jose.jwt" "itsdangerous")
    for import_name in "${auth_tests[@]}"; do
        if "$ACTUAL_PYTHON_EXEC" -c "import $import_name" 2>/dev/null; then
            log_info "✅ $import_name - OK"
        else
            log_warning "❌ $import_name - Failed to import"
            verification_failed=true
        fi
    done
    
    if [[ "$verification_failed" == "true" ]]; then
        log_warning "Some packages failed verification, but continuing with installation..."
        log_info "The startup script will handle any remaining import issues at runtime"
        log_info "Consider running: pip install --force-reinstall fastapi starlette uvicorn"
    else
        log_success "All essential packages and middleware verified successfully"
    fi
    
    # Set ownership if not root
    if [[ "$SERVICE_USER" != "root" ]]; then
        $CMD_PREFIX chown -R "$SERVICE_USER:$SERVICE_USER" "$ACTUAL_VENV_DIR"
    fi
}

# Configure nginx
configure_nginx() {
    log_step "Configuring nginx reverse proxy..."
    
    local nginx_conf_file
    if [[ "$NGINX_SITES" == "/etc/nginx/conf.d" ]]; then
        nginx_conf_file="/etc/nginx/conf.d/webapp-manager-saas.conf"
    else
        nginx_conf_file="/etc/nginx/sites-available/webapp-manager-saas"
    fi
    
    if [[ -n "$DOMAIN" ]]; then
        server_name="$DOMAIN"
    else
        server_name="_"
    fi
    
    $CMD_PREFIX tee "$nginx_conf_file" > /dev/null << EOF
# WebApp Manager SAAS Panel
upstream webapp_manager_saas {
    server 127.0.0.1:$WEB_PORT;
    keepalive 32;
}

server {
    listen 80;
    server_name $server_name;
    
    # Logs
    access_log /var/log/nginx/webapp-manager-saas.access.log;
    error_log /var/log/nginx/webapp-manager-saas.error.log;
    
    # Security headers
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options nosniff;
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # File upload limits
    client_max_body_size 100M;
    
    # Compression
    gzip on;
    gzip_vary on;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript;
    
    location / {
        proxy_pass http://webapp_manager_saas;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket support
    location /ws/ {
        proxy_pass http://webapp_manager_saas;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 86400;
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
EOF
    
    # Enable site for Debian/Ubuntu
    if [[ "$NGINX_SITES" != "/etc/nginx/conf.d" ]]; then
        $CMD_PREFIX ln -sf "/etc/nginx/sites-available/webapp-manager-saas" "/etc/nginx/sites-enabled/"
    fi
    
    # Test nginx configuration
    if $CMD_PREFIX nginx -t; then
        log_success "Nginx configuration created and tested"
    else
        log_error "Nginx configuration test failed"
        exit 1
    fi
}

# Configure SSL with Let's Encrypt
configure_ssl() {
    if [[ "$ENABLE_SSL" == "true" && -n "$DOMAIN" ]]; then
        log_step "Configuring SSL certificate..."
        
        # Install certbot
        case $PKG_MANAGER in
            apt)
                $CMD_PREFIX $PKG_INSTALL certbot python3-certbot-nginx
                ;;
            dnf)
                $CMD_PREFIX $PKG_INSTALL certbot python3-certbot-nginx
                ;;
            pacman)
                $CMD_PREFIX $PKG_INSTALL certbot certbot-nginx
                ;;
        esac
        
        # Get certificate
        if $CMD_PREFIX certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN"; then
            log_success "SSL certificate configured for $DOMAIN"
        else
            log_warning "SSL certificate configuration failed"
        fi
    fi
}

# Configure firewall
configure_firewall() {
    log_step "Configuring firewall rules..."
    
    if command -v ufw &> /dev/null; then
        # UFW (Ubuntu/Debian)
        $CMD_PREFIX ufw --force reset
        $CMD_PREFIX ufw default deny incoming
        $CMD_PREFIX ufw default allow outgoing
        $CMD_PREFIX ufw allow ssh
        $CMD_PREFIX ufw allow 'Nginx Full'
        # Only enable if specifically requested
        if [[ "$ENABLE_FIREWALL" == "true" ]]; then
            $CMD_PREFIX ufw --force enable
            log_success "UFW firewall configured and activated"
        else
            log_info "UFW rules configured but not activated"
            log_warning "To activate UFW firewall, run: ${CMD_PREFIX:+sudo }ufw --force enable"
        fi
        log_success "UFW firewall rules configured"
    elif command -v firewall-cmd &> /dev/null; then
        # Firewalld (CentOS/RHEL/Fedora)
        $CMD_PREFIX firewall-cmd --permanent --add-service=ssh
        $CMD_PREFIX firewall-cmd --permanent --add-service=http
        $CMD_PREFIX firewall-cmd --permanent --add-service=https
        $CMD_PREFIX firewall-cmd --reload
        log_success "Firewalld configured"
    else
        log_warning "No supported firewall found - please configure manually"
    fi
}

# Start services
start_services() {
    log_step "Starting services..."
    
    # Debug: Show systemd service file content
    log_info "Systemd service file content (first 20 lines):"
    $CMD_PREFIX head -20 /etc/systemd/system/webapp-manager-saas.service
    
    # Debug: Verify files exist
    log_info "Final file verification before starting service:"
    log_info "Python executable: $(ls -la $ACTUAL_PYTHON_EXEC 2>/dev/null || echo 'NOT FOUND')"
    log_info "Main script: $(ls -la $ACTUAL_MAIN_SCRIPT 2>/dev/null || echo 'NOT FOUND')"
    log_info "Working directory: $(ls -la $ACTUAL_WORKING_DIR 2>/dev/null || echo 'NOT FOUND')"
    
    # Start and enable nginx
    $SYSTEMCTL_CMD enable nginx
    $SYSTEMCTL_CMD start nginx
    
    # Reload nginx to pick up new configuration
    $SYSTEMCTL_CMD reload nginx
    
    # Start webapp-manager-saas service
    $SYSTEMCTL_CMD start webapp-manager-saas.service
    
    # Wait a moment for services to start
    sleep 5
    
    # Check service status
    if $SYSTEMCTL_CMD is-active --quiet webapp-manager-saas.service; then
        log_success "WebApp Manager SAAS service is running"
    else
        log_error "Failed to start WebApp Manager SAAS service"
        log_info "Service logs:"
        $CMD_PREFIX journalctl -u webapp-manager-saas.service -n 20 --no-pager
        exit 1
    fi
    
    if $SYSTEMCTL_CMD is-active --quiet nginx; then
        log_success "Nginx is running"
    else
        log_warning "Nginx may not be running properly"
    fi
}

# Create backup script
create_backup_script() {
    log_step "Creating backup script..."
    
    $CMD_PREFIX tee /usr/local/bin/webapp-manager-backup.sh > /dev/null << EOF
#!/bin/bash
BACKUP_DIR="$INSTALL_DIR/.webapp-manager/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="webapp-manager-backup-\$DATE"

mkdir -p "\$BACKUP_DIR/\$BACKUP_NAME"

# Backup database
cp $INSTALL_DIR/.webapp-manager/data/webapp_manager.db "\$BACKUP_DIR/\$BACKUP_NAME/" 2>/dev/null || true

# Backup configuration
cp -r $INSTALL_DIR/.webapp-manager/config "\$BACKUP_DIR/\$BACKUP_NAME/" 2>/dev/null || true

# Create archive
cd "\$BACKUP_DIR"
tar -czf "\$BACKUP_NAME.tar.gz" "\$BACKUP_NAME"
rm -rf "\$BACKUP_NAME"

# Remove old backups (keep 7 days)
find "\$BACKUP_DIR" -name "webapp-manager-backup-*.tar.gz" -mtime +7 -delete

echo "Backup completed: \$BACKUP_NAME.tar.gz"
EOF
    
    $CMD_PREFIX chmod +x /usr/local/bin/webapp-manager-backup.sh
    
    log_success "Backup script created at /usr/local/bin/webapp-manager-backup.sh"
}

# Configure automatic backups
configure_backups() {
    if [[ "$UNATTENDED" == "false" ]]; then
        echo ""
        read -p "Configure daily automatic backups? [Y/n]: " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            return
        fi
    fi
    
    log_step "Configuring automatic backups..."
    
    # Add cron job for daily backups
    ($CMD_PREFIX crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/webapp-manager-backup.sh") | $CMD_PREFIX crontab -
    
    log_success "Daily backup configured for 2:00 AM"
}

# Create maintenance script
create_maintenance_script() {
    log_step "Creating maintenance script..."
    
    $CMD_PREFIX tee /usr/local/bin/webapp-manager-maintenance.sh > /dev/null << EOF
#!/bin/bash

SYSTEMCTL_PREFIX="${CMD_PREFIX:+$CMD_PREFIX }"

case "\$1" in
    "backup")
        /usr/local/bin/webapp-manager-backup.sh
        ;;
    "logs")
        tail -f $INSTALL_DIR/logs/webapp-manager.log
        ;;
    "restart")
        \${SYSTEMCTL_PREFIX}systemctl restart webapp-manager-saas
        echo "Service restarted"
        ;;
    "stop")
        \${SYSTEMCTL_PREFIX}systemctl stop webapp-manager-saas
        echo "Service stopped"
        ;;
    "start")
        \${SYSTEMCTL_PREFIX}systemctl start webapp-manager-saas
        echo "Service started"
        ;;
    "status")
        \${SYSTEMCTL_PREFIX}systemctl status webapp-manager-saas
        ;;
    "update")
        cd $ACTUAL_WORKING_DIR
        git pull origin main
        \${SYSTEMCTL_PREFIX}systemctl restart webapp-manager-saas
        echo "Updated and restarted"
        ;;
    *)
        echo "Usage: \$0 {backup|logs|restart|stop|start|status|update}"
        exit 1
        ;;
esac
EOF
    
    $CMD_PREFIX chmod +x /usr/local/bin/webapp-manager-maintenance.sh
    
    log_success "Maintenance script created at /usr/local/bin/webapp-manager-maintenance.sh"
}

# Show completion summary
show_completion() {
    echo ""
    echo "🎉 WebApp Manager SAAS installation completed successfully!"
    echo "========================================================"
    
    echo ""
    echo -e "${CYAN}📊 Installation Summary:${NC}"
    echo "• Installation Directory: $INSTALL_DIR"
    echo "• Service User: $SERVICE_USER"
    echo "• Web Server Port: $WEB_PORT"
    echo "• Configuration: $INSTALL_DIR/.webapp-manager/config.env"
    
    echo ""
    echo -e "${CYAN}🔐 Default Credentials:${NC}"
    echo "• Username: admin"
    echo "• Password: admin123"
    echo -e "• ${RED}⚠️  IMPORTANT: Change the default password immediately!${NC}"
    
    echo ""
    echo -e "${CYAN}🌐 Access Information:${NC}"
    if [[ -n "$DOMAIN" ]]; then
        if [[ "$ENABLE_SSL" == "true" ]]; then
            echo "• HTTPS: https://$DOMAIN"
        fi
        echo "• HTTP: http://$DOMAIN"
    else
        echo "• Direct: http://localhost:$WEB_PORT"
        echo "• Network: http://$(hostname -I | awk '{print $1}'):$WEB_PORT"
    fi
    
    echo ""
    echo -e "${CYAN}🔧 Service Management:${NC}"
    echo "• Start: systemctl start webapp-manager-saas"
    echo "• Stop: systemctl stop webapp-manager-saas"
    echo "• Restart: systemctl restart webapp-manager-saas"
    echo "• Status: systemctl status webapp-manager-saas"
    echo "• Logs: journalctl -u webapp-manager-saas -f"
    echo "• Maintenance: webapp-manager-maintenance.sh {start|stop|restart|status|backup|logs|update}"
    
    echo ""
    echo -e "${CYAN}📝 Next Steps:${NC}"
    echo "1. Access the web panel using the URLs above"
    echo "2. Login with the default credentials"
    echo "3. Change the admin password in Settings → Users"
    echo "4. Configure system settings in Settings → System"
    echo "5. Create your first domain in the Domains section"
    
    echo ""
    echo -e "${CYAN}📚 Documentation:${NC}"
    echo "• Full guide: LINUX-DEPLOYMENT.md"
    echo "• Quick start: QUICKSTART.md"
    echo "• SAAS features: README-SAAS.md"
    
    echo ""
    log_success "WebApp Manager SAAS is ready to use!"
    
    # Show service status
    echo ""
    echo -e "${CYAN}📊 Current Status:${NC}"
    $SYSTEMCTL_CMD --no-pager status webapp-manager-saas.service || true
}

# Main installation process
main() {
    echo "Starting WebApp Manager SAAS installation..."
    echo ""
    
    detect_distro
    check_root
    check_requirements
    create_service_user
    install_dependencies
    verify_installation
    install_missing_packages
    create_startup_script
    create_configuration
    create_systemd_service
    configure_nginx
    configure_ssl
    configure_firewall
    start_services
    create_backup_script
    create_maintenance_script
    configure_backups
    show_completion
}

# Run installation
main "$@"