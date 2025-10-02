# 🚀 Guía Rápida - WebApp Manager con Páginas de Mantenimiento

## 📦 Instalación Completa

```bash
# 1. Clonar e instalar
git clone <repo-url> webapp-manager
cd webapp-manager
sudo make install-complete

# 2. Configuración inicial (OBLIGATORIO)
sudo webapp-manager setup
```

## ✨ ¿Qué hace el comando setup?

El comando `webapp-manager setup` configura automáticamente:

- ✅ **Páginas de mantenimiento** en `/apps/maintenance/`
  - error502.html (servicio caído)
  - updating.html (actualización en progreso)
  - maintenance.html (mantenimiento programado)

- ✅ **Verificación de nginx** 
  - Detecta conflictos con sitio default
  - Ofrece deshabilitar el default automáticamente
  - Crea backup antes de hacer cambios

- ✅ **Requisitos del sistema**
  - Verifica nginx, python3, systemctl
  - Crea directorios necesarios
  - Configura permisos adecuados

## 🎯 Uso Básico

### Agregar una aplicación

```bash
# Next.js
webapp-manager add --domain app.ejemplo.com --source /ruta/app --port 3000

# FastAPI
webapp-manager add --domain api.ejemplo.com --source /ruta/api --port 8000 --type fastapi

# Node.js
webapp-manager add --domain node.ejemplo.com --source /ruta/node --port 4000 --type nodejs

# Sitio estático
webapp-manager add --domain sitio.ejemplo.com --source /ruta/static --type static
```

### Ver aplicaciones

```bash
# Lista simple
webapp-manager list

# Con detalles completos
webapp-manager list --detailed

# Estado de una app específica
webapp-manager status --domain app.ejemplo.com
```

### Ver logs

```bash
# Últimas 50 líneas
webapp-manager logs --domain app.ejemplo.com

# Últimas 100 líneas
webapp-manager logs --domain app.ejemplo.com --lines 100

# Seguir en tiempo real
webapp-manager logs --domain app.ejemplo.com --follow
```

### Gestión de aplicaciones

```bash
# Reiniciar
webapp-manager restart --domain app.ejemplo.com

# Actualizar
webapp-manager update --domain app.ejemplo.com

# Eliminar
webapp-manager remove --domain app.ejemplo.com

# Diagnóstico
webapp-manager diagnose --domain app.ejemplo.com

# Reparar
webapp-manager repair --domain app.ejemplo.com
```

## 🔧 Páginas de Mantenimiento

### ¿Cuándo se muestran?

Las páginas de mantenimiento se muestran automáticamente cuando:

1. **Error 502/503/504** - El servicio está caído o reiniciando
2. **Error 500** - Error interno del servidor
3. **Durante actualizaciones** - Cuando se ejecuta `webapp-manager update`

### Configuración automática en nginx

Al agregar cualquier aplicación, nginx se configura automáticamente con:

```nginx
# Páginas de error
error_page 502 503 504 /maintenance/error502.html;
error_page 500 /maintenance/error502.html;

# Ubicación de mantenimiento
location ^~ /maintenance/ {
    root /apps;
    internal;
    expires 30s;
    add_header Cache-Control "public, must-revalidate, proxy-revalidate";
}
```

### Características de las páginas

- 🎨 **Diseño moderno** con gradientes y animaciones
- 📱 **Responsive** - Se adapta a cualquier dispositivo
- ⏱️ **Auto-refresh** - Se actualizan cada 30 segundos
- 🌐 **Multiidioma** - Actualmente en español

## 🛠️ Comandos Avanzados

### Modo verbose

Ver todos los detalles de ejecución:

```bash
webapp-manager add --domain app.com --source /path --port 3000 --verbose
webapp-manager update --domain app.com --verbose
webapp-manager setup --verbose
```

### SSL con Let's Encrypt

```bash
webapp-manager ssl --domain app.ejemplo.com --email admin@ejemplo.com
```

### Exportar/Importar configuración

```bash
# Exportar
webapp-manager export --file backup-config.json

# Importar
webapp-manager import --file backup-config.json
```

### Auto-detección de tipo

```bash
webapp-manager detect --directory /ruta/a/tu/app
```

### Ver tipos soportados

```bash
webapp-manager types
```

### Aplicar mantenimiento a apps existentes

Si ya tenías aplicaciones instaladas antes de esta actualización:

```bash
webapp-manager apply-maintenance
```

## 🔍 Verificación del Sistema

### Verificar que todo está configurado

```bash
# 1. Verificar páginas de mantenimiento
ls -la /apps/maintenance/
# Deberías ver: error502.html, maintenance.html, updating.html

# 2. Verificar configuración de nginx para una app
cat /etc/nginx/sites-available/tu-dominio.com | grep -A 5 "error_page"

# 3. Probar nginx
sudo nginx -t

# 4. Ver estado de servicios
webapp-manager list --detailed
```

### Simular error 502

Para probar que las páginas funcionan:

```bash
# 1. Detener el servicio de una app
sudo systemctl stop tu-dominio.com.service

# 2. Visitar tu-dominio.com en el navegador
# Deberías ver la página error502.html

# 3. Reiniciar el servicio
sudo systemctl start tu-dominio.com.service
```

## 🐛 Solución de Problemas Comunes

### Error: "capture_output"
**Síntoma:** Error al ejecutar `webapp-manager logs`

**Solución:** Ya está corregido en esta versión. Si persiste:
```bash
cd /opt/webapp-manager
sudo git pull
sudo webapp-manager setup
```

### Páginas de mantenimiento no se muestran
**Solución:**
```bash
# 1. Verificar que existen
ls -la /apps/maintenance/

# 2. Si no existen, ejecutar setup
sudo webapp-manager setup

# 3. Aplicar a apps existentes
webapp-manager apply-maintenance

# 4. Recargar nginx
sudo nginx -s reload
```

### Conflicto con nginx default
**Solución:**
```bash
# Automático
sudo webapp-manager setup
# Responder "s" cuando pregunte

# Manual
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -s reload
```

### Permisos incorrectos
**Solución:**
```bash
sudo chown -R www-data:www-data /apps/maintenance/
sudo chmod 755 /apps/maintenance/
sudo chmod 644 /apps/maintenance/*.html
```

## 📋 Checklist Post-Instalación

- [ ] Ejecutar `sudo webapp-manager setup`
- [ ] Verificar páginas en `/apps/maintenance/`
- [ ] Verificar que nginx default está deshabilitado
- [ ] Agregar primera aplicación de prueba
- [ ] Probar páginas de mantenimiento (detener servicio)
- [ ] Configurar DNS para tus dominios
- [ ] Configurar SSL si es necesario

## 🎓 Ejemplos Prácticos

### Ejemplo 1: Desplegar Next.js desde GitHub

```bash
# 1. Configuración inicial (solo primera vez)
sudo webapp-manager setup

# 2. Agregar app
webapp-manager add \
  --domain miapp.com \
  --source https://github.com/usuario/mi-app.git \
  --port 3000 \
  --type nextjs \
  --branch main \
  --verbose

# 3. Configurar SSL
webapp-manager ssl --domain miapp.com --email admin@miapp.com

# 4. Monitorear
webapp-manager logs --domain miapp.com --follow
```

### Ejemplo 2: Desplegar FastAPI desde directorio local

```bash
# 1. Agregar API
webapp-manager add \
  --domain api.miapp.com \
  --source /home/usuario/mi-api \
  --port 8000 \
  --type fastapi \
  --env DATABASE_URL=postgresql://... \
  --env SECRET_KEY=mi-secreto

# 2. Ver estado
webapp-manager status --domain api.miapp.com

# 3. Ver documentación OpenAPI
# Visitar: http://api.miapp.com/docs
```

### Ejemplo 3: Actualizar aplicación existente

```bash
# 1. Ver estado actual
webapp-manager status --domain miapp.com

# 2. Actualizar (mostrará página updating.html automáticamente)
webapp-manager update --domain miapp.com --verbose

# 3. Verificar logs
webapp-manager logs --domain miapp.com --lines 50
```

## 📚 Recursos Adicionales

- **Logs de nginx:** `/var/log/apps/[dominio]-access.log` y `[dominio]-error.log`
- **Logs de systemd:** `journalctl -u [dominio].service`
- **Configuraciones nginx:** `/etc/nginx/sites-available/[dominio]`
- **Backups:** `/var/backups/webapp-manager/`

## 💡 Tips y Mejores Prácticas

1. **Siempre usa --verbose** para debugging
2. **Ejecuta diagnose** si algo no funciona: `webapp-manager diagnose --domain app.com`
3. **Revisa logs regularmente**: `webapp-manager logs --domain app.com`
4. **Haz backups** antes de updates importantes: `webapp-manager export --file backup.json`
5. **Usa SSL** en producción: `webapp-manager ssl --domain app.com --email tu@email.com`
6. **Monitorea recursos** del servidor con `htop` o `top`

## 🎉 ¡Listo!

Tu webapp-manager está configurado y listo para usar con páginas de mantenimiento profesionales que se mostrarán automáticamente cuando sea necesario.

**Próximo paso:** Agregar tu primera aplicación 🚀

```bash
webapp-manager add --domain tu-app.com --source /ruta/app --port 3000
```
