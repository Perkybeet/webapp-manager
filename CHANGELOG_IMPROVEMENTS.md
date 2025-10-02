# 🎉 WebApp Manager - Changelog de Mejoras

## ✅ Problemas Resueltos

### 1. Error en el comando `logs`
**Problema:** `CmdService.run_sudo() got an unexpected keyword argument 'capture_output'`

**Solución:** Se corrigió el método `run_sudo()` en `webapp_manager/services/cmd_service.py` para pasar correctamente los argumentos como keywords en lugar de posicionales.

```python
# Antes (incorrecto):
return self.run(command, check, timeout, capture_output)

# Ahora (correcto):
return self.run(command, check=check, timeout=timeout, capture_output=capture_output)
```

## 🆕 Nuevas Funcionalidades

### 2. Sistema de Páginas de Mantenimiento

Se implementó un sistema completo de páginas de mantenimiento que se muestran automáticamente cuando hay errores.

#### Archivos HTML Disponibles:
- **error502.html** - Se muestra cuando el servicio está caído (errores 502, 503, 504)
- **updating.html** - Para mostrar durante actualizaciones
- **maintenance.html** - Para modo de mantenimiento programado

#### Ubicación:
- **Desarrollo:** `apps/maintenance/*.html`
- **Producción:** `/apps/maintenance/*.html` (después de ejecutar setup)

### 3. Configuración Automática de nginx

Todas las configuraciones de nginx ahora incluyen automáticamente:

```nginx
# Redirección automática a páginas de error
error_page 502 503 504 /maintenance/error502.html;
error_page 500 /maintenance/error502.html;

# Ubicación de páginas de mantenimiento
location ^~ /maintenance/ {
    root /apps;
    internal;
    expires 30s;
    add_header Cache-Control "public, must-revalidate, proxy-revalidate";
}
```

Esto aplica para todos los tipos de aplicación:
- ✅ Next.js
- ✅ FastAPI
- ✅ Node.js
- ✅ Sitios estáticos

### 4. Nuevo Servicio: `InstallService`

Se creó un nuevo servicio `webapp_manager/services/install_service.py` con las siguientes funcionalidades:

#### Métodos principales:
- `setup_maintenance_pages()` - Instala las páginas HTML en `/apps/maintenance/`
- `check_nginx_default_site()` - Verifica conflictos con el sitio default de nginx
- `disable_nginx_default_site()` - Deshabilita el sitio default (con backup)
- `verify_system_requirements()` - Verifica requisitos del sistema
- `run_initial_setup()` - Ejecuta configuración inicial completa

### 5. Nuevo Comando CLI: `setup`

```bash
# Ejecutar después de instalar webapp-manager
sudo webapp-manager setup
```

Este comando realiza:
- ✅ Verificación de requisitos del sistema (nginx, python3, systemctl)
- ✅ Instalación de páginas de mantenimiento en `/apps/maintenance/`
- ✅ Verificación de conflictos con el sitio default de nginx
- ✅ Configuración de directorios y permisos necesarios

**Ejemplo de uso:**
```bash
# Después de la instalación
sudo webapp-manager setup

# El comando muestra información detallada y solicita confirmación antes de proceder
```

### 6. Actualización del Makefile

Se actualizó el target `install-complete` para recordar al usuario ejecutar el setup:

```bash
make install-complete
# Ahora muestra:
# ⚠️  IMPORTANTE: Ejecuta el comando de configuración inicial:
#    sudo webapp-manager setup
```

### 7. Verificación del Sitio Default de nginx

El sistema ahora verifica automáticamente si existe el sitio default de nginx que podría interferir con webapp-manager.

**Detección automática:**
- Busca `/etc/nginx/sites-enabled/default`
- Analiza el contenido para determinar si es la configuración estándar
- Ofrece deshabilitarlo automáticamente (con backup)

**Deshabilitación manual:**
```bash
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -s reload
```

### 8. Archivos de Configuración Actualizados

#### `setup.py`
- Agregado `package_data` para incluir archivos HTML
- Los templates de mantenimiento ahora se empaquetan correctamente

#### `MANIFEST.in` (Nuevo)
- Archivo creado para asegurar que los HTML se incluyan en distribuciones

#### `Makefile`
- Actualizado `install-global` para copiar el directorio `apps/`
- Mejorado `install-complete` con instrucciones de setup

## 📚 Documentación de Uso

### Flujo de Instalación Recomendado

```bash
# 1. Instalar webapp-manager
cd webapp-manager
sudo make install-complete

# 2. Ejecutar configuración inicial
sudo webapp-manager setup

# 3. Agregar primera aplicación
webapp-manager add --domain app.com --source /path --port 3000
```

### Características de las Páginas de Mantenimiento

#### 1. **Actualización Automática**
```nginx
expires 30s;
add_header Cache-Control "public, must-revalidate, proxy-revalidate";
```
Las páginas se refrescan cada 30 segundos automáticamente.

#### 2. **Diseño Moderno**
- Gradientes de color según el tipo de error
- Animaciones CSS profesionales
- Responsive design
- Iconos y mensajes claros

#### 3. **Estados Cubiertos**
- **502/503/504** → Servicio temporalmente no disponible
- **500** → Error interno del servidor
- **Actualizaciones** → Página de actualización en progreso

### Verificar que Todo Funciona

```bash
# 1. Verificar que las páginas existen
ls -la /apps/maintenance/

# 2. Verificar configuración de nginx
cat /etc/nginx/sites-available/tu-dominio.com | grep maintenance

# 3. Ver logs de nginx
webapp-manager logs --domain tu-dominio.com
```

## 🔍 Modo Verbose

Todos los comandos soportan el flag `--verbose` para ver detalles:

```bash
# Ver detalles durante el setup
sudo webapp-manager setup --verbose

# Ver detalles al agregar app
webapp-manager add --domain app.com --source /path --port 3000 --verbose
```

## 🛡️ Seguridad

### Permisos de Archivos
```bash
# Directorio de mantenimiento
drwxr-xr-x  /apps/maintenance/
-rw-r--r--  /apps/maintenance/*.html

# Propietario
www-data:www-data
```

### Nginx Security Headers
Todas las configuraciones incluyen headers de seguridad:
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
```

## 🐛 Solución de Problemas

### Error: "No se encontraron templates"
```bash
# Verificar que existen los archivos
ls -la /opt/webapp-manager/apps/maintenance/

# Re-instalar si es necesario
cd /path/to/webapp-manager
sudo make install-global
sudo webapp-manager setup
```

### Error: "nginx no está instalado"
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install nginx

# Verificar
nginx -v
```

### Conflicto con sitio default de nginx
```bash
# Opción 1: Dejar que setup lo maneje
sudo webapp-manager setup
# Cuando pregunte, responder "s" para deshabilitar

# Opción 2: Manual
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -s reload
```

## 📝 Notas Importantes

1. **Solo Linux:** Esta aplicación solo funciona en sistemas Linux
2. **Requiere root:** El comando `setup` requiere permisos de sudo
3. **Primera ejecución:** Ejecutar `webapp-manager setup` es obligatorio después de la instalación
4. **Backup automático:** El sitio default se respalda antes de deshabilitar

## 🎯 Próximos Pasos Sugeridos

Después de instalar y configurar:

1. Ver tipos de aplicaciones soportados:
   ```bash
   webapp-manager types
   ```

2. Agregar tu primera aplicación:
   ```bash
   webapp-manager add --domain app.com --source /path --port 3000
   ```

3. Monitorear logs:
   ```bash
   webapp-manager logs --domain app.com --follow
   ```

4. Ver estado del sistema:
   ```bash
   webapp-manager list --detailed
   ```

## 📞 Soporte

Si encuentras problemas:
1. Ejecuta con `--verbose` para ver detalles
2. Revisa los logs de nginx: `/var/log/apps/`
3. Verifica el estado de servicios: `systemctl status`
4. Comprueba la configuración de nginx: `nginx -t`
