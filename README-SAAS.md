# WebApp Manager SAAS v1.0

Sistema completo de gestión de aplicaciones web con interfaz web SAAS, nginx proxy reverso y deployers modulares.

## 🌐 Nueva Funcionalidad SAAS

**WebApp Manager SAAS** ahora incluye un panel de control web completo que permite gestionar todas las aplicaciones desde una interfaz web moderna y responsive.

### ✨ Características Principales SAAS

- **🖥️ Panel de Control Web**: Interfaz web completa accessible desde cualquier navegador
- **👤 Sistema de Autenticación**: Login seguro con gestión de usuarios y roles
- **📊 Dashboard en Tiempo Real**: Monitoreo de uso de recursos, estadísticas y estado de aplicaciones
- **🔧 Gestión de Dominios**: Crear, editar, eliminar y configurar aplicaciones web desde la interfaz
- **📈 Monitoreo Avanzado**: Gráficos de uso de CPU, memoria, disco y red
- **⚙️ Configuración Centralizada**: Panel de configuración para todos los aspectos del sistema
- **🔒 Control de Acceso**: Sistema de roles con administradores y usuarios regulares
- **💾 Base de Datos SQLite**: Almacenamiento persistente de configuraciones y datos
- **🔄 API REST**: API completa para integraciones externas
- **📱 Responsive Design**: Funciona perfectamente en desktop, tablet y móvil

## 🚀 Inicio Rápido SAAS

### 1. Instalación de Dependencias Web
```bash
# Instalar dependencias adicionales para la interfaz web
pip install -r requirements-web.txt
```

### 2. Iniciar el Servidor Web
```bash
# Iniciar el panel de control web (puerto por defecto: 8080)
python3 webapp-manager-saas.py web

# Personalizar host y puerto
python3 webapp-manager-saas.py web --host 0.0.0.0 --port 9000

# Modo debug para desarrollo
python3 webapp-manager-saas.py web --debug
```

### 3. Acceder al Panel de Control
1. Abrir navegador en: `http://tu-servidor:8080`
2. **Usuario por defecto**: `admin`
3. **Contraseña por defecto**: `admin123`
4. **¡IMPORTANTE!**: Cambiar la contraseña por defecto en el primer acceso

## 🎯 Funcionalidades del Panel Web

### Dashboard Principal
- **Estadísticas en Tiempo Real**: CPU, memoria, disco, red
- **Estado de Aplicaciones**: Vista general de todas las aplicaciones
- **Actividad Reciente**: Log de eventos y cambios del sistema
- **Acciones Rápidas**: Start/stop aplicaciones directamente desde el dashboard

### Gestión de Dominios
- **Crear Aplicaciones**: Formulario completo para nuevas aplicaciones
- **Tipos Soportados**: Next.js, FastAPI, Node.js, Sitios Estáticos
- **Configuración Automática**: nginx, SSL, systemd
- **Gestión del Ciclo de Vida**: Start, stop, restart, delete aplicaciones
- **Detalles Avanzados**: Logs, uso de recursos, configuración por aplicación

### Monitoreo del Sistema
- **Gráficos en Tiempo Real**: Uso de recursos histórico
- **Métricas por Aplicación**: Rendimiento individual de cada app
- **Logs del Sistema**: Vista centralizada de todos los eventos
- **Alertas**: Notificaciones automáticas de problemas

### Configuración
- **Configuración General**: Nombre del sistema, zona horaria, etc.
- **Servidor Web**: Puerto, host, CORS, SSL
- **Rutas del Sistema**: Directorios de trabajo, logs, backups
- **Nginx**: Configuración de proxy reverso
- **Seguridad**: Políticas de contraseñas, intentos de login
- **Respaldos**: Programación y configuración de backups
- **Usuarios**: Gestión completa de usuarios y roles

## 🔧 Configuración Avanzada SAAS

### Variables de Entorno
```bash
# Puerto del servidor web
WEBAPP_MANAGER_WEB_PORT=8080

# Host del servidor web
WEBAPP_MANAGER_WEB_HOST=0.0.0.0

# Ruta de la base de datos
WEBAPP_MANAGER_DB_PATH=/path/to/database.db

# Clave secreta para sesiones
WEBAPP_MANAGER_SECRET_KEY=your-secret-key-here

# Modo debug
WEBAPP_MANAGER_DEBUG=false
```

### Configuración de Base de Datos
La base de datos SQLite se crea automáticamente en:
- Linux: `~/.webapp-manager/data/webapp_manager.db`
- Personalizable vía configuración o variable de entorno

### Configuración de Nginx para el Panel Web
```nginx
server {
    listen 80;
    server_name tu-dominio-panel.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 API REST

El panel web expone una API REST completa para integraciones:

### Endpoints Principales
- `GET /api/v1/applications` - Listar aplicaciones
- `POST /api/v1/applications` - Crear aplicación
- `PUT /api/v1/applications/{id}` - Actualizar aplicación
- `DELETE /api/v1/applications/{id}` - Eliminar aplicación
- `GET /api/v1/system/stats` - Estadísticas del sistema
- `GET /api/v1/system/usage/{app_id}` - Uso por aplicación
- `GET /api/v1/system/logs` - Logs del sistema
- `GET /api/v1/config` - Configuración del sistema
- `POST /api/v1/config` - Actualizar configuración

### Autenticación API
```bash
# Login para obtener sesión
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Usar la sesión en requests posteriores
curl -X GET http://localhost:8080/api/v1/applications \
  -H "Cookie: session=your-session-cookie"
```

## 🔒 Seguridad

### Medidas de Seguridad Implementadas
- **Autenticación Basada en Sesiones**: Cookies HTTP-only seguras
- **Hashing de Contraseñas**: Bcrypt con salt aleatorio
- **Protección CSRF**: Tokens CSRF en formularios
- **Rate Limiting**: Limitación de intentos de login
- **Headers de Seguridad**: XSS Protection, Content Type, etc.
- **Logs de Auditoría**: Registro de todas las acciones administrativas

### Recomendaciones de Seguridad
1. **Cambiar contraseña por defecto** inmediatamente
2. **Usar HTTPS** en producción con certificados SSL
3. **Firewall**: Restringir acceso al puerto del panel web
4. **Backups regulares** de la base de datos
5. **Monitorear logs** de acceso y errores

## 🐳 Despliegue en Producción

### Con Systemd
```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/webapp-manager-saas.service
```

```ini
[Unit]
Description=WebApp Manager SAAS
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/webapp-manager
ExecStart=/usr/bin/python3 webapp-manager-saas.py web --host 127.0.0.1 --port 8080
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar y iniciar el servicio
sudo systemctl enable webapp-manager-saas
sudo systemctl start webapp-manager-saas
sudo systemctl status webapp-manager-saas
```

### Con Docker (Próximamente)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements-web.txt

EXPOSE 8080

CMD ["python3", "webapp-manager-saas.py", "web", "--host", "0.0.0.0", "--port", "8080"]
```

## 🔄 Migración desde CLI a SAAS

### Importar Aplicaciones Existentes
El panel web detectará automáticamente aplicaciones existentes gestionadas por la versión CLI y las importará a la base de datos.

### Compatibilidad
- ✅ **CLI Completa**: La interfaz CLI sigue funcionando igual
- ✅ **Configuraciones Existentes**: Se migran automáticamente
- ✅ **Aplicaciones Actuales**: Se importan sin interrupción
- ✅ **Nginx Configs**: Se mantienen compatibles

## 📱 Interfaz Mobile

El panel web está completamente optimizado para dispositivos móviles:
- **Responsive Design**: Se adapta a cualquier tamaño de pantalla
- **Touch Friendly**: Botones y controles optimizados para touch
- **Navegación Mobile**: Menú colapsible y navegación intuitiva
- **Performance**: Carga rápida en conexiones móviles

## 🔍 Troubleshooting

### Problemas Comunes

#### El panel web no inicia
```bash
# Verificar que las dependencias estén instaladas
pip install -r requirements-web.txt

# Verificar puertos disponibles
netstat -tulpn | grep 8080

# Iniciar en modo debug
python3 webapp-manager-saas.py web --debug
```

#### Error de base de datos
```bash
# Verificar permisos del directorio de datos
ls -la ~/.webapp-manager/data/

# Recrear base de datos si es necesario
rm ~/.webapp-manager/data/webapp_manager.db
python3 webapp-manager-saas.py web
```

#### Problemas de autenticación
```bash
# Resetear usuario admin (eliminar base de datos)
rm ~/.webapp-manager/data/webapp_manager.db

# El próximo inicio recreará el usuario admin por defecto
```

## 📈 Próximas Funcionalidades

- **🔗 WebSockets**: Updates en tiempo real sin refresh
- **📊 Métricas Avanzadas**: Integración con Prometheus/Grafana
- **🔔 Notificaciones**: Email, Slack, Discord
- **👥 Multi-tenancy**: Soporte para múltiples organizaciones
- **🔧 Plugins**: Sistema de extensiones
- **📦 Marketplace**: Plantillas de aplicaciones predefinidas
- **🌐 Multi-servidor**: Gestión de múltiples servidores
- **📱 Mobile App**: Aplicación nativa para iOS/Android

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Ver el archivo `CONTRIBUTING.md` para más detalles.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

---

**WebApp Manager SAAS v1.0** - Sistema de Gestión de Aplicaciones Web con Panel de Control Completo