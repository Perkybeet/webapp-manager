# WebApp Manager SAAS - Windows Deployment Script
# PowerShell script for Windows installation

param(
    [string]$Port = "8080",
    [string]$Host = "0.0.0.0",
    [switch]$Debug,
    [switch]$Help
)

# Configuration
$ErrorActionPreference = "Stop"
$WebPort = $Port
$WebHost = $Host
$InstallDir = $PWD

# Colors for output
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Show-Help {
    Write-Host "WebApp Manager SAAS - Windows Deployment Script"
    Write-Host "================================================"
    Write-Host ""
    Write-Host "Usage: .\deploy-saas.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Port <number>    Web server port (default: 8080)"
    Write-Host "  -Host <address>   Web server host (default: 0.0.0.0)"
    Write-Host "  -Debug           Enable debug mode"
    Write-Host "  -Help            Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\deploy-saas.ps1"
    Write-Host "  .\deploy-saas.ps1 -Port 9000 -Debug"
    Write-Host "  .\deploy-saas.ps1 -Host 127.0.0.1 -Port 8080"
}

# Check if help was requested
if ($Help) {
    Show-Help
    exit 0
}

function Test-Requirements {
    Write-Info "Checking system requirements..."
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python 3") {
            Write-Success "Python found: $pythonVersion"
        } else {
            Write-Error-Custom "Python 3 is required but not found"
            Write-Info "Please install Python 3 from https://python.org"
            exit 1
        }
    } catch {
        Write-Error-Custom "Python 3 is required but not found"
        Write-Info "Please install Python 3 from https://python.org"
        exit 1
    }
    
    # Check pip
    try {
        $pipVersion = pip --version 2>&1
        Write-Success "pip found: $pipVersion"
    } catch {
        Write-Error-Custom "pip is required but not found"
        Write-Info "Please install pip or reinstall Python with pip"
        exit 1
    }
    
    Write-Success "System requirements check completed"
}

function Install-Dependencies {
    Write-Info "Installing Python dependencies..."
    
    try {
        if (Test-Path "webapp_manager\web\requirements-web.txt") {
            pip install -r webapp_manager\web\requirements-web.txt
            Write-Success "Web dependencies installed"
        } else {
            Write-Warning "requirements-web.txt not found, installing basic dependencies"
            pip install fastapi uvicorn jinja2 python-multipart "passlib[bcrypt]" "python-jose[cryptography]"
        }
        
        # Install original requirements if exists
        if (Test-Path "requirements.txt") {
            pip install -r requirements.txt
            Write-Success "Core dependencies installed"
        }
    } catch {
        Write-Error-Custom "Failed to install dependencies: $_"
        exit 1
    }
}

function New-Directories {
    Write-Info "Creating necessary directories..."
    
    try {
        # Create data directory in user's home
        $dataDir = "$env:USERPROFILE\.webapp-manager\data"
        $logsDir = "$env:USERPROFILE\.webapp-manager\logs"
        $backupsDir = "$env:USERPROFILE\.webapp-manager\backups"
        
        New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
        New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
        New-Item -ItemType Directory -Force -Path $backupsDir | Out-Null
        
        Write-Success "Directories created at $env:USERPROFILE\.webapp-manager\"
    } catch {
        Write-Error-Custom "Failed to create directories: $_"
        exit 1
    }
}

function New-Configuration {
    Write-Info "Generating secure configuration..."
    
    try {
        # Generate secret key
        $secretKey = [System.Web.Security.Membership]::GeneratePassword(32, 8)
        
        # Create config file
        $configPath = "$env:USERPROFILE\.webapp-manager\config.env"
        $configContent = @"
# WebApp Manager SAAS Configuration - Windows
WEBAPP_MANAGER_WEB_PORT=$WebPort
WEBAPP_MANAGER_WEB_HOST=$WebHost
WEBAPP_MANAGER_SECRET_KEY=$secretKey
WEBAPP_MANAGER_DEBUG=$($Debug.IsPresent.ToString().ToLower())
"@
        
        Set-Content -Path $configPath -Value $configContent
        Write-Success "Configuration file created at $configPath"
    } catch {
        Write-Error-Custom "Failed to create configuration: $_"
        exit 1
    }
}

function Test-FirewallRule {
    Write-Info "Checking Windows Firewall..."
    
    try {
        # Check if running as administrator
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        
        if (-not $isAdmin) {
            Write-Warning "Not running as administrator. Firewall configuration will be skipped."
            Write-Info "To configure firewall manually, run as administrator:"
            Write-Info "netsh advfirewall firewall add rule name='WebApp Manager SAAS' dir=in action=allow protocol=TCP localport=$WebPort"
            return
        }
        
        # Add firewall rule
        $ruleName = "WebApp Manager SAAS - Port $WebPort"
        
        # Check if rule already exists
        $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        
        if ($existingRule) {
            Write-Info "Firewall rule already exists: $ruleName"
        } else {
            New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $WebPort -Action Allow
            Write-Success "Firewall rule added: $ruleName"
        }
    } catch {
        Write-Warning "Could not configure firewall: $_"
        Write-Info "You may need to manually configure Windows Firewall to allow port $WebPort"
    }
}

function Start-WebService {
    Write-Info "Starting WebApp Manager SAAS..."
    
    $debugFlag = if ($Debug) { "--debug" } else { "" }
    
    Write-Info "Starting web service on http://$WebHost`:$WebPort"
    Write-Info "Press Ctrl+C to stop the service"
    Write-Info ""
    
    try {
        # Start the web service
        if ($Debug) {
            python webapp-manager-saas.py web --host $WebHost --port $WebPort --debug
        } else {
            python webapp-manager-saas.py web --host $WebHost --port $WebPort
        }
    } catch {
        Write-Error-Custom "Failed to start web service: $_"
        exit 1
    }
}

function Show-CompletionInfo {
    Write-Success "WebApp Manager SAAS setup completed!"
    
    Write-Host ""
    Write-Host "🎉 Setup Summary:" -ForegroundColor Cyan
    Write-Host "=================" -ForegroundColor Cyan
    Write-Host "• Web Panel Port: $WebPort"
    Write-Host "• Web Panel Host: $WebHost"
    Write-Host "• Data Directory: $env:USERPROFILE\.webapp-manager\"
    Write-Host "• Configuration: $env:USERPROFILE\.webapp-manager\config.env"
    
    Write-Host ""
    Write-Host "🔐 Default Credentials:" -ForegroundColor Cyan
    Write-Host "======================" -ForegroundColor Cyan
    Write-Host "• Username: admin"
    Write-Host "• Password: admin123"
    Write-Host "• ⚠️  IMPORTANT: Change the default password after first login!" -ForegroundColor Red
    
    Write-Host ""
    Write-Host "🌐 Access URLs:" -ForegroundColor Cyan
    Write-Host "===============" -ForegroundColor Cyan
    if ($WebHost -eq "0.0.0.0") {
        Write-Host "• Local: http://localhost:$WebPort"
        Write-Host "• Network: http://$(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -ne '127.0.0.1'} | Select-Object -First 1 -ExpandProperty IPAddress):$WebPort"
    } else {
        Write-Host "• Access: http://$WebHost`:$WebPort"
    }
    
    Write-Host ""
    Write-Host "📚 Next Steps:" -ForegroundColor Cyan
    Write-Host "==============" -ForegroundColor Cyan
    Write-Host "• 🔧 Configure system in Settings panel"
    Write-Host "• 📊 Monitor applications in Dashboard"
    Write-Host "• 📖 Read QUICKSTART.md for detailed guide"
    Write-Host "• 📚 Read README-SAAS.md for full documentation"
    
    Write-Host ""
    Write-Success "Service will start automatically..."
}

function Install-WindowsService {
    Write-Host ""
    $response = Read-Host "Do you want to install as Windows Service? (y/N)"
    
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Warning "Windows Service installation requires additional tools (NSSM or similar)"
        Write-Info "For now, you can use Task Scheduler or run manually"
        Write-Info "Manual start command:"
        Write-Info "python $PWD\webapp-manager-saas.py web --host $WebHost --port $WebPort"
        
        # Create batch file for easy starting
        $batContent = @"
@echo off
cd /d "$PWD"
python webapp-manager-saas.py web --host $WebHost --port $WebPort
pause
"@
        Set-Content -Path "start-webapp-manager-saas.bat" -Value $batContent
        Write-Success "Created start-webapp-manager-saas.bat for easy launching"
    }
}

# Main installation process
function Main {
    Write-Host "🚀 WebApp Manager SAAS - Windows Deployment" -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Green
    Write-Host ""
    
    Test-Requirements
    Install-Dependencies
    New-Directories
    New-Configuration
    Test-FirewallRule
    Install-WindowsService
    Show-CompletionInfo
    
    # Start the service
    Start-WebService
}

# Run the deployment
try {
    Main
} catch {
    Write-Error-Custom "Deployment failed: $_"
    Write-Info "Please check the error messages above and try again"
    exit 1
}