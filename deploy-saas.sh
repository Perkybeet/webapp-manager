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
        return 0
    fi
    
    # Check if user has sudo privileges
    if ! sudo -n true 2>/dev/null; then
        log_error "This script requires sudo privileges or must be run as root"
        log_info "Please run with sudo or as root user"
        exit 1
    fi
    
    log_info "Running with sudo privileges"
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
                $PKG_INSTALL python3 python3-pip python3-venv git nginx sqlite3 curl wget
                ;;
            dnf)
                $PKG_INSTALL python3 python3-pip git nginx sqlite curl wget
                ;;
            pacman)
                $PKG_INSTALL python python-pip git nginx sqlite curl wget
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
        mkdir -p "$INSTALL_DIR"
        return 0
    fi
    
    if id "$SERVICE_USER" &>/dev/null; then
        log_info "User '$SERVICE_USER' already exists"
    else
        if [[ $EUID -eq 0 ]]; then
            useradd -r -s /bin/bash -d "$INSTALL_DIR" -m "$SERVICE_USER"
        else
            sudo useradd -r -s /bin/bash -d "$INSTALL_DIR" -m "$SERVICE_USER"
        fi
        log_success "Created user '$SERVICE_USER'"
    fi
    
    # Ensure install directory exists with correct permissions
    if [[ $EUID -eq 0 ]]; then
        mkdir -p "$INSTALL_DIR"
        chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    else
        sudo mkdir -p "$INSTALL_DIR"
        sudo chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    fi
}

# Install Python dependencies in virtual environment
install_dependencies() {
    log_step "Installing Python dependencies..."
    
    # Execute commands as appropriate user
    if [[ "$SERVICE_USER" == "root" || $EUID -eq 0 ]]; then
        # Running as root or installing for root
        cd "$INSTALL_DIR"
        
        # Clone or update repository
        if [[ -d "app" ]]; then
            cd app
            git pull origin main || true
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
            git clone https://github.com/Perkybeet/webapp-manager.git app
        fi
        
        cd app
        
        # Create virtual environment
        python3 -m venv venv
        source venv/bin/activate
        
        # Upgrade pip
        pip install --upgrade pip
        
        # Install dependencies
        if [[ -f "webapp_manager/web/requirements-web.txt" ]]; then
            pip install -r webapp_manager/web/requirements-web.txt
        else
            log_warning "requirements-web.txt not found, installing basic dependencies"
            pip install fastapi uvicorn jinja2 python-multipart 'passlib[bcrypt]' 'python-jose[cryptography]' psutil
        fi
        
        # Install core dependencies if available
        if [[ -f "requirements.txt" ]]; then
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
        
        # Verify virtual environment and main script
        if [[ ! -f "venv/bin/python" ]]; then
            log_error "Virtual environment not created properly"
            log_info "Contents of venv directory:"
            ls -la venv/ || echo "venv directory does not exist"
            if [[ -d venv/bin ]]; then
                ls -la venv/bin/ || echo "venv/bin directory does not exist"
            fi
            exit 1
        fi
        
        if [[ ! -f "webapp-manager-saas.py" ]]; then
            log_error "webapp-manager-saas.py not found in app directory"
            log_info "Contents of app directory:"
            ls -la ./
            exit 1
        fi
        
        # Make sure the python executable has correct permissions
        chmod +x venv/bin/python
    else
        # Switch to service user and create virtual environment
        sudo -u "$SERVICE_USER" bash << EOF
set -e
cd "$INSTALL_DIR"

# Clone or update repository
if [[ -d "app" ]]; then
    cd app
    git pull origin main || true
    cd ..
elif [[ -f "webapp-manager-saas.py" && -d "webapp_manager" ]]; then
    # Already in the repository directory, create symlink
    ln -sf . app
    log_info "Using current directory as app"
else
    git clone https://github.com/Perkybeet/webapp-manager.git app
fi

cd app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
if [[ -f "webapp_manager/web/requirements-web.txt" ]]; then
    pip install -r webapp_manager/web/requirements-web.txt
else
    log_warning "requirements-web.txt not found, installing basic dependencies"
    pip install fastapi uvicorn jinja2 python-multipart 'passlib[bcrypt]' 'python-jose[cryptography]' psutil
fi

# Install core dependencies if available
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
fi

# Additional verification and fix for virtual environment
if [[ ! -f "venv/bin/python" ]]; then
    echo "WARNING: venv/bin/python not found, creating symlink"
    if [[ -f "venv/bin/python3" ]]; then
        ln -sf python3 venv/bin/python
    fi
fi

# Ensure we have a working Python executable
test_python=""
for py_exec in python python3; do
    if [[ -x "venv/bin/\$py_exec" ]]; then
        test_python="venv/bin/\$py_exec"
        break
    fi
done

if [[ -z "\$test_python" ]]; then
    echo "ERROR: No working Python executable found in virtual environment"
    echo "Contents of venv/bin directory:"
    ls -la venv/bin/ || echo "venv/bin directory does not exist"
    exit 1
fi

# Test the Python executable
if ! "\$test_python" --version; then
    echo "ERROR: Python executable test failed: \$test_python"
    exit 1
fi

# Verify virtual environment and main script
if [[ ! -f "venv/bin/python" ]]; then
    echo "ERROR: Virtual environment not created properly"
    echo "Contents of venv directory:"
    ls -la venv/ || echo "venv directory does not exist"
    if [[ -d venv/bin ]]; then
        ls -la venv/bin/ || echo "venv/bin directory does not exist"
    fi
    exit 1
fi

if [[ ! -f "webapp-manager-saas.py" ]]; then
    echo "ERROR: webapp-manager-saas.py not found in app directory"
    echo "Contents of app directory:"
    ls -la ./
    exit 1
fi

# Make sure the python executable has correct permissions
chmod +x venv/bin/python

EOF
    fi
    
    log_success "Python dependencies installed"
}

# Verify installation integrity
verify_installation() {
    log_step "Verifying installation integrity..."
    
    local app_dir="$INSTALL_DIR/app"
    local venv_dir="$app_dir/venv"
    local python_exec="$venv_dir/bin/python"
    local main_script="$app_dir/webapp-manager-saas.py"
    
    log_info "Checking directory structure..."
    log_info "Install directory: $INSTALL_DIR"
    log_info "App directory: $app_dir"
    log_info "Virtual environment: $venv_dir"
    log_info "Python executable: $python_exec"
    log_info "Main script: $main_script"
    
    # Check if directories exist
    if [[ ! -d "$INSTALL_DIR" ]]; then
        log_error "Install directory does not exist: $INSTALL_DIR"
        exit 1
    fi
    
    if [[ ! -d "$app_dir" ]]; then
        log_error "App directory does not exist: $app_dir"
        ls -la "$INSTALL_DIR"
        exit 1
    fi
    
    if [[ ! -d "$venv_dir" ]]; then
        log_error "Virtual environment directory does not exist: $venv_dir"
        ls -la "$app_dir"
        exit 1
    fi
    
    if [[ ! -f "$python_exec" ]]; then
        log_error "Python executable does not exist: $python_exec"
        ls -la "$venv_dir/bin" || ls -la "$venv_dir"
        exit 1
    fi
    
    if [[ ! -x "$python_exec" ]]; then
        log_error "Python executable is not executable: $python_exec"
        ls -la "$python_exec"
        exit 1
    fi
    
    if [[ ! -f "$main_script" ]]; then
        log_error "Main script does not exist: $main_script"
        ls -la "$app_dir"
        exit 1
    fi
    
    # Test Python executable
    log_info "Testing Python executable..."
    if [[ "$SERVICE_USER" == "root" || $EUID -eq 0 ]]; then
        if ! "$python_exec" --version; then
            log_error "Python executable test failed"
            exit 1
        fi
    else
        if ! sudo -u "$SERVICE_USER" "$python_exec" --version; then
            log_error "Python executable test failed for user $SERVICE_USER"
            exit 1
        fi
    fi
    
    # Test main script syntax
    log_info "Testing main script syntax..."
    if [[ "$SERVICE_USER" == "root" || $EUID -eq 0 ]]; then
        if ! "$python_exec" -m py_compile "$main_script"; then
            log_error "Main script syntax check failed"
            exit 1
        fi
    else
        if ! sudo -u "$SERVICE_USER" "$python_exec" -m py_compile "$main_script"; then
            log_error "Main script syntax check failed for user $SERVICE_USER"
            exit 1
        fi
    fi
    
    log_success "Installation verification completed"
}

# Create configuration
create_configuration() {
    log_step "Creating configuration files..."
    
    # Generate secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Create configuration directory - handle root vs non-root
    if [[ "$SERVICE_USER" == "root" || $EUID -eq 0 ]]; then
        mkdir -p "$INSTALL_DIR/.webapp-manager/"{data,logs,backups,config}
        
        # Create main configuration file
        cat > "$INSTALL_DIR/.webapp-manager/config.env" << EOF
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
        chmod 600 "$INSTALL_DIR/.webapp-manager/config.env"
    else
        # Create configuration directory
        sudo -u "$SERVICE_USER" mkdir -p "$INSTALL_DIR/.webapp-manager/"{data,logs,backups,config}
        
        # Create main configuration file
        sudo -u "$SERVICE_USER" cat > "$INSTALL_DIR/.webapp-manager/config.env" << EOF
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
        sudo chmod 600 "$INSTALL_DIR/.webapp-manager/config.env"
    fi
    
    log_success "Configuration created"
}

# Create systemd service
create_systemd_service() {
    log_step "Creating systemd service..."
    
    # Always resolve the Python executable to the real path (not symlink)
    # This ensures systemd can properly execute it
    local venv_python="$INSTALL_DIR/app/venv/bin/python"
    if [[ -L "$venv_python" ]]; then
        # If it's a symlink, resolve it to the real path
        PYTHON_EXEC=$(readlink -f "$venv_python")
    elif [[ -f "$venv_python" ]]; then
        # If it's a real file, use it directly
        PYTHON_EXEC="$venv_python"
    else
        # Try alternative paths
        for py_exec in python3 python3.12 python3.11 python3.10 python3.9 python3.8; do
            if [[ -f "$INSTALL_DIR/app/venv/bin/$py_exec" ]]; then
                if [[ -L "$INSTALL_DIR/app/venv/bin/$py_exec" ]]; then
                    PYTHON_EXEC=$(readlink -f "$INSTALL_DIR/app/venv/bin/$py_exec")
                else
                    PYTHON_EXEC="$INSTALL_DIR/app/venv/bin/$py_exec"
                fi
                break
            fi
        done
    fi
    
    # Final validation
    if [[ ! -f "$PYTHON_EXEC" ]]; then
        log_error "Cannot find a valid Python executable in virtual environment"
        log_info "Searched paths:"
        ls -la "$INSTALL_DIR/app/venv/bin/" 2>/dev/null || echo "venv/bin directory not found"
        exit 1
    fi
    
    # Debug information
    log_info "Service configuration:"
    log_info "  Service User: $SERVICE_USER"
    log_info "  Install Directory: $INSTALL_DIR"
    log_info "  Python Executable (resolved): $PYTHON_EXEC"
    log_info "  Main Script: $INSTALL_DIR/app/webapp-manager-saas.py"
    log_info "  Working Directory: $INSTALL_DIR/app"
    
    # Verify files exist before creating service
    if [[ ! -f "$PYTHON_EXEC" ]]; then
        log_error "Python executable not found: $PYTHON_EXEC"
        exit 1
    fi
    
    if [[ ! -f "$INSTALL_DIR/app/webapp-manager-saas.py" ]]; then
        log_error "Main script not found: $INSTALL_DIR/app/webapp-manager-saas.py"
        exit 1
    fi
    
    if [[ $EUID -eq 0 ]]; then
        tee /etc/systemd/system/webapp-manager-saas.service > /dev/null << EOF
[Unit]
Description=WebApp Manager SAAS Control Panel
Documentation=https://github.com/Perkybeet/webapp-manager
After=network.target nginx.service
Wants=nginx.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/app
Environment=PATH=$INSTALL_DIR/app/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
EnvironmentFile=$INSTALL_DIR/.webapp-manager/config.env
ExecStart=$PYTHON_EXEC $INSTALL_DIR/app/webapp-manager-saas.py web --host $WEB_HOST --port $WEB_PORT
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

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR/.webapp-manager
ReadWritePaths=/var/www
ReadWritePaths=/tmp
ReadWritePaths=/var/log

[Install]
WantedBy=multi-user.target
EOF
        
        # Reload systemd and enable service
        systemctl daemon-reload
        systemctl enable webapp-manager-saas.service
    else
        sudo tee /etc/systemd/system/webapp-manager-saas.service > /dev/null << EOF
[Unit]
Description=WebApp Manager SAAS Control Panel
Documentation=https://github.com/Perkybeet/webapp-manager
After=network.target nginx.service
Wants=nginx.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/app
Environment=PATH=$INSTALL_DIR/app/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
EnvironmentFile=$INSTALL_DIR/.webapp-manager/config.env
ExecStart=$PYTHON_EXEC $INSTALL_DIR/app/webapp-manager-saas.py web --host $WEB_HOST --port $WEB_PORT
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

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR/.webapp-manager
ReadWritePaths=/var/www
ReadWritePaths=/tmp
ReadWritePaths=/var/log

[Install]
WantedBy=multi-user.target
EOF
        
        # Reload systemd and enable service
        sudo systemctl daemon-reload
        sudo systemctl enable webapp-manager-saas.service
    fi
    
    log_success "Systemd service created and enabled"
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
    
    # Determine server_name
    local server_name
    if [[ -n "$DOMAIN" ]]; then
        server_name="$DOMAIN"
    else
        server_name="_"
    fi
    
    if [[ $EUID -eq 0 ]]; then
        tee "$nginx_conf_file" > /dev/null << EOF
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
    else
        sudo tee "$nginx_conf_file" > /dev/null << EOF
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
    fi
    
    # Enable site for Debian/Ubuntu
    if [[ "$NGINX_SITES" != "/etc/nginx/conf.d" ]]; then
        if [[ $EUID -eq 0 ]]; then
            ln -sf "/etc/nginx/sites-available/webapp-manager-saas" "/etc/nginx/sites-enabled/"
        else
            sudo ln -sf "/etc/nginx/sites-available/webapp-manager-saas" "/etc/nginx/sites-enabled/"
        fi
    fi
    
    # Test nginx configuration
    if [[ $EUID -eq 0 ]]; then
        if nginx -t; then
            log_success "Nginx configuration created and tested"
        else
            log_error "Nginx configuration test failed"
            exit 1
        fi
    else
        if sudo nginx -t; then
            log_success "Nginx configuration created and tested"
        else
            log_error "Nginx configuration test failed"
            exit 1
        fi
    fi
}

# Configure SSL with Let's Encrypt
configure_ssl() {
    if [[ "$ENABLE_SSL" == "true" && -n "$DOMAIN" ]]; then
        log_step "Configuring SSL certificate..."
        
        # Install certbot
        case $PKG_MANAGER in
            apt)
                $PKG_INSTALL certbot python3-certbot-nginx
                ;;
            dnf)
                $PKG_INSTALL certbot python3-certbot-nginx
                ;;
            pacman)
                $PKG_INSTALL certbot certbot-nginx
                ;;
        esac
        
        # Get certificate
        if [[ $EUID -eq 0 ]]; then
            if certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN"; then
                log_success "SSL certificate configured for $DOMAIN"
            else
                log_warning "SSL certificate configuration failed"
            fi
        else
            if sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN"; then
                log_success "SSL certificate configured for $DOMAIN"
            else
                log_warning "SSL certificate configuration failed"
            fi
        fi
    fi
}

# Configure firewall
configure_firewall() {
    log_step "Configuring firewall rules..."
    
    if command -v ufw &> /dev/null; then
        # UFW (Ubuntu/Debian)
        if [[ $EUID -eq 0 ]]; then
            ufw --force reset
            ufw default deny incoming
            ufw default allow outgoing
            ufw allow ssh
            ufw allow 'Nginx Full'
            # Only enable if specifically requested
            if [[ "$ENABLE_FIREWALL" == "true" ]]; then
                ufw --force enable
                log_success "UFW firewall configured and activated"
            else
                log_info "UFW rules configured but not activated"
                log_warning "To activate UFW firewall, run: ufw --force enable"
            fi
        else
            sudo ufw --force reset
            sudo ufw default deny incoming
            sudo ufw default allow outgoing
            sudo ufw allow ssh
            sudo ufw allow 'Nginx Full'
            # Only enable if specifically requested
            if [[ "$ENABLE_FIREWALL" == "true" ]]; then
                sudo ufw --force enable
                log_success "UFW firewall configured and activated"
            else
                log_info "UFW rules configured but not activated"
                log_warning "To activate UFW firewall, run: sudo ufw --force enable"
            fi
        fi
        log_success "UFW firewall rules configured"
    elif command -v firewall-cmd &> /dev/null; then
        # Firewalld (CentOS/RHEL/Fedora)
        if [[ $EUID -eq 0 ]]; then
            firewall-cmd --permanent --add-service=ssh
            firewall-cmd --permanent --add-service=http
            firewall-cmd --permanent --add-service=https
            firewall-cmd --reload
        else
            sudo firewall-cmd --permanent --add-service=ssh
            sudo firewall-cmd --permanent --add-service=http
            sudo firewall-cmd --permanent --add-service=https
            sudo firewall-cmd --reload
        fi
        log_success "Firewalld configured"
    else
        log_warning "No supported firewall found - please configure manually"
    fi
}

# Start services
start_services() {
    log_step "Starting services..."
    
    # Debug: Show systemd service file content
    log_info "Systemd service file content:"
    if [[ $EUID -eq 0 ]]; then
        cat /etc/systemd/system/webapp-manager-saas.service | head -20
    else
        sudo cat /etc/systemd/system/webapp-manager-saas.service | head -20
    fi
    
    # Debug: Verify files exist
    log_info "Final file verification before starting service:"
    log_info "Python executable: $(ls -la $PYTHON_EXEC 2>/dev/null || echo 'NOT FOUND')"
    log_info "Main script: $(ls -la $INSTALL_DIR/app/webapp-manager-saas.py 2>/dev/null || echo 'NOT FOUND')"
    log_info "Working directory: $(ls -la $INSTALL_DIR/app 2>/dev/null || echo 'NOT FOUND')"
    
    if [[ $EUID -eq 0 ]]; then
        # Start and enable nginx
        systemctl enable nginx
        systemctl start nginx
        
        # Reload nginx to pick up new configuration
        systemctl reload nginx
        
        # Start webapp-manager-saas service
        systemctl start webapp-manager-saas.service
        
        # Wait a moment for services to start
        sleep 3
        
        # Check service status
        if systemctl is-active --quiet webapp-manager-saas.service; then
            log_success "WebApp Manager SAAS service is running"
        else
            log_error "Failed to start WebApp Manager SAAS service"
            journalctl -u webapp-manager-saas.service -n 20
            exit 1
        fi
        
        if systemctl is-active --quiet nginx; then
            log_success "Nginx is running"
        else
            log_warning "Nginx may not be running properly"
        fi
    else
        # Start and enable nginx
        sudo systemctl enable nginx
        sudo systemctl start nginx
        
        # Reload nginx to pick up new configuration
        sudo systemctl reload nginx
        
        # Start webapp-manager-saas service
        sudo systemctl start webapp-manager-saas.service
        
        # Wait a moment for services to start
        sleep 3
        
        # Check service status
        if sudo systemctl is-active --quiet webapp-manager-saas.service; then
            log_success "WebApp Manager SAAS service is running"
        else
            log_error "Failed to start WebApp Manager SAAS service"
            sudo journalctl -u webapp-manager-saas.service -n 20
            exit 1
        fi
        
        if sudo systemctl is-active --quiet nginx; then
            log_success "Nginx is running"
        else
            log_warning "Nginx may not be running properly"
        fi
    fi
}

# Create backup script
create_backup_script() {
    log_step "Creating backup script..."
    
    if [[ $EUID -eq 0 ]]; then
        tee /usr/local/bin/webapp-manager-backup.sh > /dev/null << EOF
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
        
        chmod +x /usr/local/bin/webapp-manager-backup.sh
    else
        sudo tee /usr/local/bin/webapp-manager-backup.sh > /dev/null << EOF
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
        
        sudo chmod +x /usr/local/bin/webapp-manager-backup.sh
    fi
    
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
    if [[ $EUID -eq 0 ]]; then
        (crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/webapp-manager-backup.sh") | crontab -
    else
        (sudo crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/webapp-manager-backup.sh") | sudo crontab -
    fi
    
    log_success "Daily backup configured for 2:00 AM"
}

# Create maintenance script
create_maintenance_script() {
    log_step "Creating maintenance script..."
    
    if [[ $EUID -eq 0 ]]; then
        tee /usr/local/bin/webapp-manager-maintenance.sh > /dev/null << EOF
#!/bin/bash

case "\$1" in
    "backup")
        /usr/local/bin/webapp-manager-backup.sh
        ;;
    "logs")
        tail -f $INSTALL_DIR/logs/webapp-manager.log
        ;;
    "restart")
        systemctl restart webapp-manager-saas
        echo "Service restarted"
        ;;
    "stop")
        systemctl stop webapp-manager-saas
        echo "Service stopped"
        ;;
    "start")
        systemctl start webapp-manager-saas
        echo "Service started"
        ;;
    "status")
        systemctl status webapp-manager-saas
        ;;
    "update")
        cd $INSTALL_DIR/app
        git pull origin main
        systemctl restart webapp-manager-saas
        echo "Updated and restarted"
        ;;
    *)
        echo "Usage: \$0 {backup|logs|restart|stop|start|status|update}"
        exit 1
        ;;
esac
EOF
        
        chmod +x /usr/local/bin/webapp-manager-maintenance.sh
    else
        sudo tee /usr/local/bin/webapp-manager-maintenance.sh > /dev/null << EOF
#!/bin/bash

case "\$1" in
    "backup")
        /usr/local/bin/webapp-manager-backup.sh
        ;;
    "logs")
        tail -f $INSTALL_DIR/logs/webapp-manager.log
        ;;
    "restart")
        sudo systemctl restart webapp-manager-saas
        echo "Service restarted"
        ;;
    "stop")
        sudo systemctl stop webapp-manager-saas
        echo "Service stopped"
        ;;
    "start")
        sudo systemctl start webapp-manager-saas
        echo "Service started"
        ;;
    "status")
        sudo systemctl status webapp-manager-saas
        ;;
    "update")
        cd $INSTALL_DIR/app
        git pull origin main
        sudo systemctl restart webapp-manager-saas
        echo "Updated and restarted"
        ;;
    *)
        echo "Usage: \$0 {backup|logs|restart|stop|start|status|update}"
        exit 1
        ;;
esac
EOF
        
        sudo chmod +x /usr/local/bin/webapp-manager-maintenance.sh
    fi
    
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
    if [[ $EUID -eq 0 ]]; then
        systemctl --no-pager status webapp-manager-saas.service || true
    else
        sudo systemctl --no-pager status webapp-manager-saas.service || true
    fi
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