#!/bin/bash

# WebApp Manager SAAS - Systemd Service Fix Script
# This script fixes the Python executable path issue in the systemd service

set -e

echo "🔧 Fixing WebApp Manager SAAS systemd service..."
echo "================================================"

# Configuration
INSTALL_DIR=${INSTALL_DIR:-/root/webapp-manager}
SERVICE_USER=${SERVICE_USER:-root}
WEB_PORT=${WEBAPP_MANAGER_WEB_PORT:-8080}
WEB_HOST=${WEBAPP_MANAGER_WEB_HOST:-0.0.0.0}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Stop the current service
log_info "Stopping current service..."
if [[ $EUID -eq 0 ]]; then
    systemctl stop webapp-manager-saas || true
else
    sudo systemctl stop webapp-manager-saas || true
fi

# Find the correct Python executable path
log_info "Finding correct Python executable..."

# Always resolve the Python executable to the real path (not symlink)
local venv_python="$INSTALL_DIR/app/venv/bin/python"
PYTHON_EXEC=""

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

log_info "Using Python executable: $PYTHON_EXEC"

# Verify files exist
if [[ ! -f "$PYTHON_EXEC" ]]; then
    log_error "Python executable not found: $PYTHON_EXEC"
    exit 1
fi

if [[ ! -f "$INSTALL_DIR/app/webapp-manager-saas.py" ]]; then
    log_error "Main script not found: $INSTALL_DIR/app/webapp-manager-saas.py"
    exit 1
fi

# Test the Python executable
log_info "Testing Python executable..."
if [[ "$SERVICE_USER" == "root" || $EUID -eq 0 ]]; then
    if ! "$PYTHON_EXEC" --version; then
        log_error "Python executable test failed"
        exit 1
    fi
else
    if ! sudo -u "$SERVICE_USER" "$PYTHON_EXEC" --version; then
        log_error "Python executable test failed for user $SERVICE_USER"
        exit 1
    fi
fi

# Create the fixed systemd service
log_info "Creating fixed systemd service..."

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

    # Reload systemd
    systemctl daemon-reload
    
    # Start the service
    log_info "Starting service..."
    systemctl start webapp-manager-saas.service
    
    # Wait a moment for the service to start
    sleep 5
    
    # Check service status
    if systemctl is-active --quiet webapp-manager-saas.service; then
        log_success "WebApp Manager SAAS service is now running!"
    else
        log_error "Failed to start WebApp Manager SAAS service"
        echo "Service logs:"
        journalctl -u webapp-manager-saas.service -n 20
        exit 1
    fi
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

    # Reload systemd
    sudo systemctl daemon-reload
    
    # Start the service
    log_info "Starting service..."
    sudo systemctl start webapp-manager-saas.service
    
    # Wait a moment for the service to start
    sleep 5
    
    # Check service status
    if sudo systemctl is-active --quiet webapp-manager-saas.service; then
        log_success "WebApp Manager SAAS service is now running!"
    else
        log_error "Failed to start WebApp Manager SAAS service"
        echo "Service logs:"
        sudo journalctl -u webapp-manager-saas.service -n 20
        exit 1
    fi
fi

# Show service status
log_info "Service status:"
if [[ $EUID -eq 0 ]]; then
    systemctl --no-pager status webapp-manager-saas.service
else
    sudo systemctl --no-pager status webapp-manager-saas.service
fi

echo ""
log_success "Fix completed! The WebApp Manager SAAS should now be accessible at:"
echo "• http://localhost:$WEB_PORT"
echo "• http://$(hostname -I | awk '{print $1}'):$WEB_PORT"
echo ""
echo "Default credentials:"
echo "• Username: admin"
echo "• Password: admin123"