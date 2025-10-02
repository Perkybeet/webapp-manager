# ✅ Checklist de Verificación - WebApp Manager

## 🔧 Pre-requisitos

- [ ] Sistema Linux (Ubuntu/Debian recomendado)
- [ ] Acceso root/sudo
- [ ] nginx instalado
- [ ] python3 instalado
- [ ] Node.js instalado (para apps Node/Next.js)

## 📦 Instalación

```bash
cd webapp-manager

# 1. Instalar globalmente
sudo make install-complete

# 2. Verificar instalación
webapp-manager --help

# 3. Ejecutar setup inicial
sudo webapp-manager setup
```

### Verificar Setup
- [ ] Mensaje de confirmación exitosa
- [ ] Directorio `/apps/maintenance/` creado
- [ ] Archivos HTML presentes:
  - [ ] error502.html
  - [ ] updating.html
  - [ ] maintenance.html
- [ ] Permisos correctos (www-data:www-data)
- [ ] No hay conflictos con nginx default

## 🧪 Tests Funcionales

### 1. Comando Logs (Bug Fix)
```bash
# Agregar una app primero
webapp-manager add --domain test.local --source /var/www/html --type static --port 8080

# Probar logs (esto estaba fallando)
webapp-manager logs --domain test.local
webapp-manager logs --domain test.local --lines 100
webapp-manager logs --domain test.local --follow
```
**Verificar:**
- [ ] ❌ NO debe mostrar error de 'capture_output'
- [ ] ✅ Debe mostrar logs correctamente
- [ ] ✅ Follow funciona (Ctrl+C para salir)

### 2. Agregar Aplicación - Modo Normal

```bash
webapp-manager add \
  --domain app-test.local \
  --source /path/to/your/app \
  --port 3000 \
  --type nextjs
```

**Verificar:**
- [ ] Barra de progreso visible y funcionando
- [ ] Sin mensajes duplicados
- [ ] Solo información esencial visible
- [ ] Mensaje de éxito al final
- [ ] No hay outputs de comandos git/npm

**Resultado esperado:**
```
[===>     ] Desplegando app-test.local
✓ Aplicación app-test.local agregada exitosamente
```

### 3. Agregar Aplicación - Modo Verbose

```bash
webapp-manager add \
  --domain app-verbose.local \
  --source /path/to/your/app \
  --port 3001 \
  --type nextjs \
  --verbose
```

**Verificar:**
- [ ] Mensajes detallados paso a paso
- [ ] Comandos ejecutados son visibles
- [ ] Sin duplicación de información
- [ ] Formato consistente con "→" para pasos
- [ ] Información de Git/npm visible

**Resultado esperado:**
```
→ Validando parámetros
  Dominio: app-verbose.local
  Puerto: 3001
→ Desplegando aplicación
  Creando backup
→ Obteniendo código fuente
  🔧 Ejecutando: git clone...
→ Instalando dependencias
  🔧 Ejecutando: npm install...
✓ Aplicación app-verbose.local agregada exitosamente
  HTTP: http://app-verbose.local
  Puerto interno: 3001
```

### 4. Actualizar Aplicación - Modo Normal

```bash
webapp-manager update --domain app-test.local
```

**Verificar:**
- [ ] Barra de progreso muestra "Actualizando"
- [ ] Sin mensajes duplicados
- [ ] Mensaje de mantenimiento activado
- [ ] Mensaje de éxito al final

### 5. Actualizar Aplicación - Modo Verbose

```bash
webapp-manager update --domain app-verbose.local --verbose
```

**Verificar:**
- [ ] Pasos claros y sin duplicados
- [ ] Git pull visible
- [ ] npm install/build visible
- [ ] Activación y desactivación de mantenimiento visible

### 6. Reiniciar Aplicación

```bash
webapp-manager restart --domain app-test.local
webapp-manager restart --domain app-test.local --verbose
```

**Verificar:**
- [ ] Modo normal: barra de progreso
- [ ] Modo verbose: pasos detallados
- [ ] Sin mensajes duplicados

### 7. Ver Lista de Aplicaciones

```bash
webapp-manager list
webapp-manager list --detailed
```

**Verificar:**
- [ ] Muestra todas las apps agregadas
- [ ] Información clara y organizada
- [ ] Estado de cada app visible

### 8. Ver Estado de Aplicación

```bash
webapp-manager status --domain app-test.local
```

**Verificar:**
- [ ] Información completa de la app
- [ ] Estado del servicio
- [ ] Sin errores

## 🎨 Verificación de Páginas de Mantenimiento

### 1. Verificar Archivos

```bash
ls -la /apps/maintenance/
```

**Debe mostrar:**
```
drwxr-xr-x  www-data www-data maintenance/
-rw-r--r--  www-data www-data error502.html
-rw-r--r--  www-data www-data maintenance.html
-rw-r--r--  www-data www-data updating.html
```

### 2. Verificar Configuración nginx

```bash
cat /etc/nginx/sites-available/app-test.local | grep -A 10 "error_page"
```

**Debe contener:**
```nginx
error_page 502 503 504 /maintenance/error502.html;
error_page 500 /maintenance/error502.html;

location ^~ /maintenance/ {
    root /apps;
    internal;
    expires 30s;
    add_header Cache-Control "public, must-revalidate, proxy-revalidate";
}
```

### 3. Probar Página de Error

```bash
# Detener la aplicación para forzar error 502
sudo systemctl stop app-test.local.service

# Visitar en navegador: http://app-test.local
# O usar curl:
curl -I http://app-test.local
```

**Verificar:**
- [ ] Página error502.html se muestra
- [ ] Diseño profesional y responsivo
- [ ] Sin error de nginx (404)

```bash
# Reiniciar la aplicación
sudo systemctl start app-test.local.service
```

### 4. Probar Página de Actualización

```bash
# Durante una actualización, visitar la URL
# La página updating.html debería mostrarse automáticamente
webapp-manager update --domain app-test.local &
# Rápidamente en otro terminal o navegador:
curl http://app-test.local
```

## 📊 Verificación de Salida Limpia

### Comparación de Outputs

#### ❌ Antes (con problemas):
```
[1/8] Validando parámetros
[1/8] Validando parámetros
Dominio: app.com
[2/8] 📥 Obteniendo código fuente
[2/8] Obteniendo código fuente
🔧 Ejecutando: git clone...
```

#### ✅ Ahora (modo normal):
```
[===>     ] Desplegando app.com
✓ Aplicación app.com agregada exitosamente
```

#### ✅ Ahora (modo verbose):
```
→ Validando parámetros
→ Desplegando aplicación
→ Obteniendo código fuente
✓ Aplicación app.com agregada exitosamente
```

## 🔍 Verificación de Sitio Default nginx

### Si Existe Sitio Default

```bash
# Verificar si existe
ls -la /etc/nginx/sites-enabled/default

# Si existe, el setup debería haberlo detectado
# Verificar backup
ls -la /etc/nginx/sites-available/default.backup
```

**Setup debe:**
- [ ] Detectar el sitio default
- [ ] Preguntar si deshabilitar
- [ ] Crear backup antes de deshabilitar
- [ ] Recargar nginx correctamente

## 🧹 Limpieza de Tests

```bash
# Remover apps de prueba
webapp-manager remove --domain test.local
webapp-manager remove --domain app-test.local
webapp-manager remove --domain app-verbose.local

# Verificar que se removieron
webapp-manager list
```

## 📋 Checklist Final

### Funcionalidad Core
- [ ] ✅ Comando `logs` funciona sin errores
- [ ] ✅ Comando `add` sin duplicados (normal)
- [ ] ✅ Comando `add` con detalles (verbose)
- [ ] ✅ Comando `update` funciona correctamente
- [ ] ✅ Comando `restart` funciona correctamente
- [ ] ✅ Comando `setup` configura todo correctamente

### Sistema de Mantenimiento
- [ ] ✅ Páginas HTML instaladas
- [ ] ✅ Permisos correctos
- [ ] ✅ nginx configurado para servir páginas
- [ ] ✅ Páginas se muestran en errores
- [ ] ✅ Páginas tienen diseño profesional

### Experiencia de Usuario
- [ ] ✅ Sin mensajes duplicados
- [ ] ✅ Barras de progreso funcionan
- [ ] ✅ Modo verbose apropiado
- [ ] ✅ Mensajes claros y concisos
- [ ] ✅ Errores se muestran correctamente

### Documentación
- [ ] ✅ CHANGELOG_IMPROVEMENTS.md
- [ ] ✅ GUIA_RAPIDA.md
- [ ] ✅ MEJORAS_LOGS_Y_PROGRESO.md
- [ ] ✅ RESUMEN_CAMBIOS.md
- [ ] ✅ Este checklist

## ⚠️ Problemas Conocidos y Soluciones

### Problema: Permisos
```bash
# Si hay problemas de permisos:
sudo chown -R www-data:www-data /apps/maintenance/
sudo chmod 755 /apps/maintenance/
sudo chmod 644 /apps/maintenance/*.html
```

### Problema: nginx no recarga
```bash
# Verificar configuración
sudo nginx -t

# Recargar manualmente
sudo nginx -s reload

# O reiniciar
sudo systemctl restart nginx
```

### Problema: Servicios no inician
```bash
# Ver logs del servicio
sudo journalctl -u dominio.service -n 50

# Ver estado
sudo systemctl status dominio.service

# Diagnóstico
webapp-manager diagnose --domain dominio
```

## 📊 Métricas de Éxito

Al finalizar todos los tests, debes tener:

- ✅ **0** errores de capture_output
- ✅ **0** mensajes duplicados
- ✅ **0** barras de progreso rotas
- ✅ **3** páginas de mantenimiento instaladas
- ✅ **100%** comandos funcionando correctamente

## 🎉 Confirmación Final

Si todos los checks están ✅:

**¡El webapp-manager está completamente funcional y optimizado!**

Ahora puedes:
1. Usarlo en producción con confianza
2. Documentar en tu README los nuevos comandos
3. Desplegar apps sin preocuparte por logs duplicados
4. Disfrutar de páginas de mantenimiento profesionales

---

**Notas:**
- Este checklist es para sistemas Linux únicamente
- Ejecutar siempre los comandos con los permisos apropiados
- En caso de dudas, consultar GUIA_RAPIDA.md
- Para debugging, usar siempre el flag `--verbose`
