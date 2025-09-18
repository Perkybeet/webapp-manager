# WebApp Manager SAAS - Guía de Instalación y Deployment para Linux

## 📋 Requisitos del Sistema

### Sistema Operativo
- Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / RHEL 8+
- Arch Linux / Fedora 35+

### Software Requerido
- **Python 3.8+** con pip
- **Nginx** (para reverse proxy)
- **Systemd** (para servicios)
- **Git** (para deployment desde repositorios)
- **Sudo** privileges para el usuario

### Hardware Recomendado
- **RAM**: 2GB mínimo, 4GB recomendado
- **CPU**: 2 cores mínimo
- **Disco**: 20GB mínimo, 50GB recomendado
- **Red**: Conexión a internet estable

## 🚀 Instalación Automatizada

### Script de Instalación Rápida
```bash
# Descargar el repositorio
git clone https://github.com/tu-usuario/webapp-manager.git
cd webapp-manager

# Hacer ejecutable el script
chmod +x deploy-saas.sh

# Ejecutar instalación (modo interactivo)
./deploy-saas.sh

# O instalación desatendida
WEBAPP_MANAGER_WEB_PORT=8080 \
WEBAPP_MANAGER_WEB_HOST=0.0.0.0 \
WEBAPP_MANAGER_DOMAIN=panel.tudominio.com \
./deploy-saas.sh --unattended
```

## 🔧 Instalación Manual

### 1. Preparar el Sistema

#### Ubuntu/Debian:
```bash
# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y python3 python3-pip python3-venv nginx git sqlite3 curl wget

# Instalar Node.js (para aplicaciones web modernas)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### CentOS/RHEL/Fedora:
```bash
# CentOS/RHEL
sudo dnf update -y
sudo dnf install -y python3 python3-pip nginx git sqlite wget curl

# Fedora
sudo dnf install -y python3 python3-pip nginx git sqlite wget curl nodejs npm
```

### 2. Crear Usuario del Sistema
```bash
# Crear usuario dedicado para webapp-manager
sudo useradd -r -s /bin/bash -d /opt/webapp-manager webapp-manager
sudo mkdir -p /opt/webapp-manager
sudo chown webapp-manager:webapp-manager /opt/webapp-manager
```

### 3. Instalar WebApp Manager SAAS
```bash
# Cambiar al usuario webapp-manager
sudo su - webapp-manager

# Clonar el repositorio
git clone https://github.com/tu-usuario/webapp-manager.git /opt/webapp-manager/app
cd /opt/webapp-manager/app

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r webapp_manager/web/requirements-web.txt

# Crear directorios necesarios
mkdir -p ~/.webapp-manager/{data,logs,backups,config}
```

### 4. Configurar la Base de Datos
```bash
# La base de datos se crea automáticamente al primer inicio
# Pero podemos pre-configurar algunos ajustes

cat > ~/.webapp-manager/config/database.conf << 'EOF'
# Database configuration
DB_PATH=~/.webapp-manager/data/webapp_manager.db
DB_BACKUP_PATH=~/.webapp-manager/backups
DB_BACKUP_INTERVAL=24  # hours
DB_MAX_BACKUPS=7
EOF
```

### 5. Configurar Variables de Entorno
```bash
# Generar clave secreta
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Crear archivo de configuración
cat > ~/.webapp-manager/config.env << EOF
# WebApp Manager SAAS Configuration
WEBAPP_MANAGER_WEB_PORT=8080
WEBAPP_MANAGER_WEB_HOST=0.0.0.0
WEBAPP_MANAGER_SECRET_KEY=$SECRET_KEY
WEBAPP_MANAGER_DEBUG=false
WEBAPP_MANAGER_DATA_DIR=/home/webapp-manager/.webapp-manager/data
WEBAPP_MANAGER_LOG_DIR=/home/webapp-manager/.webapp-manager/logs
WEBAPP_MANAGER_BACKUP_DIR=/home/webapp-manager/.webapp-manager/backups

# Paths del sistema
NGINX_SITES_PATH=/etc/nginx/sites-available
NGINX_ENABLED_PATH=/etc/nginx/sites-enabled
SYSTEMD_PATH=/etc/systemd/system
WEBAPP_BASE_DIR=/var/www

# Configuración de logs
LOG_LEVEL=INFO
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5

# Configuración de seguridad
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=300
EOF

# Asegurar permisos del archivo de configuración
chmod 600 ~/.webapp-manager/config.env
```

## ⚙️ Configurar Servicios del Sistema

### 1. Crear Servicio Systemd

```bash
# Volver a ser root para configurar systemd
exit

# Crear archivo de servicio
sudo tee /etc/systemd/system/webapp-manager-saas.service << 'EOF'
[Unit]
Description=WebApp Manager SAAS Control Panel
Documentation=https://github.com/tu-usuario/webapp-manager
After=network.target nginx.service
Wants=nginx.service

[Service]
Type=simple
User=webapp-manager
Group=webapp-manager
WorkingDirectory=/opt/webapp-manager/app
Environment=PATH=/opt/webapp-manager/app/venv/bin
EnvironmentFile=/home/webapp-manager/.webapp-manager/config.env
ExecStart=/opt/webapp-manager/app/venv/bin/python webapp-manager-saas.py web --host ${WEBAPP_MANAGER_WEB_HOST} --port ${WEBAPP_MANAGER_WEB_PORT}
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Límites de recursos
LimitNOFILE=65536
LimitNPROC=4096

# Seguridad
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/webapp-manager/.webapp-manager
ReadWritePaths=/var/www
ReadWritePaths=/tmp

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd y habilitar el servicio
sudo systemctl daemon-reload
sudo systemctl enable webapp-manager-saas.service
```

### 2. Configurar Nginx como Reverse Proxy

```bash
# Crear configuración de nginx para el panel SAAS
sudo tee /etc/nginx/sites-available/webapp-manager-saas << 'EOF'
# WebApp Manager SAAS Panel
upstream webapp_manager_saas {
    server 127.0.0.1:8080;
    keepalive 32;
}

server {
    listen 80;
    server_name panel.tudominio.com;  # Cambiar por tu dominio
    
    # Logs
    access_log /var/log/nginx/webapp-manager-saas.access.log;
    error_log /var/log/nginx/webapp-manager-saas.error.log;
    
    # Seguridad
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options nosniff;
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:";
    
    # Límites de carga
    client_max_body_size 100M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    # Compresión
    gzip on;
    gzip_vary on;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml;
    
    location / {
        proxy_pass http://webapp_manager_saas;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket support para monitoreo en tiempo real
    location /ws/ {
        proxy_pass http://webapp_manager_saas;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
    
    # Static files (opcional, FastAPI los sirve)
    location /static/ {
        alias /opt/webapp-manager/app/webapp_manager/web/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
EOF

# Habilitar el sitio
sudo ln -sf /etc/nginx/sites-available/webapp-manager-saas /etc/nginx/sites-enabled/

# Verificar configuración de nginx
sudo nginx -t

# Si la configuración es correcta, recargar nginx
sudo systemctl reload nginx
```

### 3. Configurar SSL con Let's Encrypt (Opcional pero Recomendado)

```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx  # Ubuntu/Debian
# o
sudo dnf install certbot python3-certbot-nginx  # CentOS/Fedora

# Obtener certificado SSL
sudo certbot --nginx -d panel.tudominio.com

# Verificar renovación automática
sudo certbot renew --dry-run
```

### 4. Configurar Firewall

#### UFW (Ubuntu/Debian):
```bash
# Configurar firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable

# Verificar estado
sudo ufw status
```

#### Firewalld (CentOS/RHEL/Fedora):
```bash
# Configurar firewall
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Verificar configuración
sudo firewall-cmd --list-all
```

## 🚀 Iniciar el Sistema

```bash
# Iniciar el servicio
sudo systemctl start webapp-manager-saas.service

# Verificar estado
sudo systemctl status webapp-manager-saas.service

# Ver logs en tiempo real
sudo journalctl -u webapp-manager-saas.service -f

# Verificar que el servicio responde
curl -I http://localhost:8080
curl -I http://panel.tudominio.com
```

## 🔐 Configuración Inicial del Panel

### Primer Acceso
1. Abrir navegador en `http://panel.tudominio.com` (o la IP del servidor con puerto 8080)
2. **Usuario por defecto**: `admin`
3. **Contraseña por defecto**: `admin123`
4. **¡IMPORTANTE!**: Cambiar la contraseña inmediatamente

### Configuración del Sistema
1. Ir a **Settings → System**
2. Configurar rutas del sistema:
   - Nginx sites path: `/etc/nginx/sites-available`
   - Systemd path: `/etc/systemd/system`
   - Web applications base directory: `/var/www`
3. Configurar opciones de seguridad
4. Configurar notificaciones por email (opcional)

### Crear Primer Dominio
1. Ir a **Domains**
2. Clic en **Add Domain**
3. Completar información de la aplicación
4. El sistema creará automáticamente:
   - Configuración de Nginx
   - Servicio de Systemd
   - Directorio de la aplicación

## 🔧 Mantenimiento

### Logs del Sistema
```bash
# Ver logs del SAAS
sudo journalctl -u webapp-manager-saas.service -f

# Ver logs de nginx
sudo tail -f /var/log/nginx/webapp-manager-saas.access.log
sudo tail -f /var/log/nginx/webapp-manager-saas.error.log

# Ver logs específicos del WebApp Manager
tail -f /home/webapp-manager/.webapp-manager/logs/webapp-manager.log
```

### Actualizar el Sistema
```bash
# Cambiar al usuario webapp-manager
sudo su - webapp-manager
cd /opt/webapp-manager/app

# Hacer backup de la configuración
cp -r ~/.webapp-manager/data ~/.webapp-manager/backups/backup-$(date +%Y%m%d)

# Actualizar código
git pull origin main

# Actualizar dependencias
source venv/bin/activate
pip install -r webapp_manager/web/requirements-web.txt --upgrade

# Volver a root y reiniciar servicio
exit
sudo systemctl restart webapp-manager-saas.service
```

### Backup Automático
```bash
# Crear script de backup
sudo tee /usr/local/bin/webapp-manager-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/webapp-manager/.webapp-manager/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="webapp-manager-backup-$DATE"

# Crear backup
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# Backup de la base de datos
cp /home/webapp-manager/.webapp-manager/data/webapp_manager.db "$BACKUP_DIR/$BACKUP_NAME/"

# Backup de configuración
cp -r /home/webapp-manager/.webapp-manager/config "$BACKUP_DIR/$BACKUP_NAME/"

# Comprimir backup
cd "$BACKUP_DIR"
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

# Eliminar backups antiguos (mantener 7 días)
find "$BACKUP_DIR" -name "webapp-manager-backup-*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_NAME.tar.gz"
EOF

# Hacer ejecutable
sudo chmod +x /usr/local/bin/webapp-manager-backup.sh

# Configurar cron para backup diario
sudo crontab -e
# Agregar línea:
# 0 2 * * * /usr/local/bin/webapp-manager-backup.sh
```

## 🐛 Solución de Problemas

### Servicio no inicia
```bash
# Verificar logs
sudo journalctl -u webapp-manager-saas.service -n 50

# Verificar permisos
sudo ls -la /opt/webapp-manager/
sudo ls -la /home/webapp-manager/.webapp-manager/

# Verificar dependencias Python
sudo su - webapp-manager
source /opt/webapp-manager/app/venv/bin/activate
python3 -c "import fastapi, uvicorn, jinja2, passlib, psutil; print('OK')"
```

### Problema de permisos con aplicaciones
```bash
# Configurar permisos para el directorio web
sudo chown -R webapp-manager:www-data /var/www
sudo chmod -R 755 /var/www

# Agregar usuario webapp-manager al grupo www-data
sudo usermod -a -G www-data webapp-manager
```

### Nginx no puede conectar al backend
```bash
# Verificar que el servicio escucha en el puerto correcto
sudo netstat -tlnp | grep 8080

# Verificar configuración de nginx
sudo nginx -t

# Verificar logs de nginx
sudo tail -f /var/log/nginx/error.log
```

### Base de datos corrupta
```bash
# Restaurar desde backup
sudo su - webapp-manager
cd ~/.webapp-manager/backups
tar -xzf webapp-manager-backup-YYYYMMDD_HHMMSS.tar.gz
cp webapp-manager-backup-YYYYMMDD_HHMMSS/webapp_manager.db ~/.webapp-manager/data/
exit
sudo systemctl restart webapp-manager-saas.service
```

## 📊 Monitoreo del Sistema

### Métricas importantes
- CPU y memoria del servidor
- Estado de los servicios systemd
- Logs de error de nginx
- Conexiones activas al panel SAAS
- Estado de las aplicaciones web gestionadas

### Alertas recomendadas
- Servicio webapp-manager-saas caído
- Uso de CPU > 80%
- Uso de memoria > 90%
- Espacio en disco < 10%
- Errores 5xx en nginx > 5%

## 🔐 Consideraciones de Seguridad

### Configuración básica de seguridad
1. **Firewall**: Solo puertos necesarios abiertos
2. **SSL**: Certificado válido configurado
3. **Usuarios**: Contraseñas fuertes, usuario admin renombrado
4. **Actualizaciones**: Sistema y dependencias actualizadas
5. **Backups**: Backup automático configurado
6. **Logs**: Monitoreo activo de logs de seguridad

### Configuración avanzada (opcional)
1. **Fail2ban**: Protección contra ataques de fuerza bruta
2. **ModSecurity**: WAF para nginx
3. **Intrusion Detection**: OSSEC o similar
4. **Network Monitoring**: Nagios o Zabbix

## 📚 Referencias Útiles

- [Documentación FastAPI](https://fastapi.tiangolo.com/)
- [Guía de Nginx](https://nginx.org/en/docs/)
- [Systemd Service Management](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Let's Encrypt](https://letsencrypt.org/)
- [UFW Firewall](https://help.ubuntu.com/community/UFW)

## 🆘 Soporte

Si encuentras problemas durante la instalación:
1. Revisa los logs del sistema
2. Verifica la configuración paso a paso  
3. Consulta la sección de solución de problemas
4. Busca en los issues del repositorio GitHub
5. Crea un nuevo issue con detalles completos del error