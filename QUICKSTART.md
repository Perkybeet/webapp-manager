# WebApp Manager SAAS - Quick Start Guide

## 🚀 Instalación Rápida

### Opción 1: Script Automático (Recomendado)
```bash
# Hacer el script ejecutable
chmod +x deploy-saas.sh

# Ejecutar la instalación
./deploy-saas.sh
```

### Opción 2: Instalación Manual

#### 1. Instalar Dependencias
```bash
# Instalar dependencias Python
pip3 install -r webapp_manager/web/requirements-web.txt

# O instalar manualmente
pip3 install fastapi uvicorn jinja2 python-multipart passlib[bcrypt] python-jose[cryptography]
```

#### 2. Crear Base de Datos
```bash
# La base de datos se crea automáticamente al primer inicio
mkdir -p ~/.webapp-manager/data
```

#### 3. Iniciar el Servicio
```bash
# Modo desarrollo (con debug)
python3 webapp-manager-saas.py web --debug

# Modo producción
python3 webapp-manager-saas.py web --host 0.0.0.0 --port 8080
```

## 📋 Configuración Inicial

### Acceso Web
- **URL**: http://localhost:8080 (o la IP del servidor)
- **Usuario por defecto**: admin
- **Contraseña por defecto**: admin123

### Primeros Pasos

1. **Cambiar Contraseña**
   - Ir a Settings → Users
   - Cambiar la contraseña del usuario admin

2. **Configurar Sistema**
   - Ir a Settings → System
   - Configurar rutas de nginx, systemd, etc.

3. **Crear Dominios**
   - Ir a Domains
   - Usar "Add Domain" para crear nuevas aplicaciones

## 🔧 Configuración Avanzada

### Variables de Entorno
Crear archivo `~/.webapp-manager/config.env`:
```bash
WEBAPP_MANAGER_WEB_PORT=8080
WEBAPP_MANAGER_WEB_HOST=0.0.0.0
WEBAPP_MANAGER_SECRET_KEY=tu_clave_secreta_aqui
WEBAPP_MANAGER_DEBUG=false
```

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name tu-panel.ejemplo.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Servicio Systemd
```bash
# Crear servicio
sudo systemctl daemon-reload
sudo systemctl enable webapp-manager-saas
sudo systemctl start webapp-manager-saas

# Ver logs
sudo journalctl -u webapp-manager-saas -f
```

## 📊 Uso del Panel

### Dashboard
- Vista general de aplicaciones
- Estadísticas de uso
- Estado del sistema

### Domains (Dominios)
- Crear nuevas aplicaciones
- Gestionar aplicaciones existentes
- Ver estadísticas por dominio

### Monitoring
- Recursos del sistema
- Logs en tiempo real
- Alertas y notificaciones

### Settings
- Configuración del sistema
- Gestión de usuarios
- Configuración de servicios

## 🐛 Solución de Problemas

### Error: Puerto en uso
```bash
# Ver qué proceso usa el puerto
sudo lsof -i :8080

# Cambiar puerto
python3 webapp-manager-saas.py web --port 8081
```

### Error: Permisos de base de datos
```bash
# Verificar permisos
ls -la ~/.webapp-manager/data/

# Crear directorio si no existe
mkdir -p ~/.webapp-manager/data
chmod 755 ~/.webapp-manager/data
```

### Error: Módulos no encontrados
```bash
# Reinstalar dependencias
pip3 install -r webapp_manager/web/requirements-web.txt --force-reinstall
```

## 📝 Logs

### Ubicación de Logs
- Sistema: `~/.webapp-manager/logs/webapp-manager.log`
- Web: `~/.webapp-manager/logs/web.log`
- Nginx: `/var/log/nginx/access.log` y `/var/log/nginx/error.log`

### Ver Logs en Tiempo Real
```bash
# Logs del sistema
tail -f ~/.webapp-manager/logs/webapp-manager.log

# Logs del servicio
sudo journalctl -u webapp-manager-saas -f

# Logs de nginx
sudo tail -f /var/log/nginx/access.log
```

## 🔐 Seguridad

### Recomendaciones
1. Cambiar contraseña por defecto
2. Usar HTTPS con certificado SSL
3. Configurar firewall apropiado
4. Mantener sistema actualizado
5. Hacer backups regulares

### Configurar HTTPS
```bash
# Con Let's Encrypt
sudo certbot --nginx -d tu-panel.ejemplo.com
```

## 📚 API REST

### Endpoints Principales
- `GET /api/applications` - Listar aplicaciones
- `POST /api/applications` - Crear aplicación
- `PUT /api/applications/{id}` - Actualizar aplicación
- `DELETE /api/applications/{id}` - Eliminar aplicación
- `GET /api/system/stats` - Estadísticas del sistema

### Ejemplo de Uso
```bash
# Obtener aplicaciones
curl -X GET http://localhost:8080/api/applications \
  -H "Authorization: Bearer tu_token"
```

## 🆘 Soporte

Si encuentras problemas:
1. Revisa los logs del sistema
2. Verifica la configuración
3. Consulta la documentación completa en `README-SAAS.md`
4. Verifica que todos los servicios estén corriendo

## 📋 Lista de Verificación

- [ ] Dependencias instaladas
- [ ] Base de datos creada
- [ ] Servicio web iniciado
- [ ] Acceso al panel web
- [ ] Contraseña cambiada
- [ ] Primer dominio creado
- [ ] Nginx configurado (opcional)
- [ ] Firewall configurado
- [ ] Backup configurado