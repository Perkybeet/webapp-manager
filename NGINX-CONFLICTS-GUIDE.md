# Guía de Resolución de Conflictos Nginx - WebApp Manager SAAS

## Problema Común: Conflicto entre Virtual Hosts de Nginx

Cuando WebApp Manager SAAS se despliega en un servidor que ya tiene nginx configurado con otros sitios web, puede ocurrir un conflicto donde las peticiones por IP se redirigen al dominio incorrecto en lugar de llegar al panel SAAS.

### ¿Por qué Ocurre?

1. **Orden de evaluación**: Nginx evalúa los virtual hosts en orden alfabético
2. **Server_name conflicts**: Múltiples sitios compiten por las mismas peticiones
3. **Catch-all configurations**: El uso de `server_name _;` puede capturar peticiones no intencionadas

### Síntomas

- Acceder a `http://YOUR_SERVER_IP` redirige a otro dominio
- El panel SAAS no es accesible por IP
- Error 301/302 cuando se espera el panel de login

### Solución Automática

El script `deploy-saas.sh` actualizado incluye:

1. **Detección automática de IP**: Usa la IP del servidor como `server_name`
2. **Detección de conflictos**: Identifica configuraciones problemáticas
3. **Configuración específica**: Evita usar catch-all (`_`) cuando hay otros sitios

### Solución Manual

Si el problema persiste después del despliegue:

#### 1. Identificar la IP del servidor
```bash
curl ifconfig.me
```

#### 2. Editar la configuración de webapp-manager-saas
```bash
sudo nano /etc/nginx/sites-available/webapp-manager-saas
```

Cambiar:
```nginx
server_name _;
```

Por:
```nginx
server_name YOUR_SERVER_IP;
```

#### 3. Verificar y recargar nginx
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Configuración Recomendada

Para evitar conflictos futuros, la configuración óptima es:

```nginx
# WebApp Manager SAAS Panel
upstream webapp_manager_saas {
    server 127.0.0.1:8080;
    keepalive 32;
}

server {
    listen 80;
    server_name YOUR_SERVER_IP;  # IP específica, no catch-all
    
    # ... resto de configuración
}
```

### Casos de Uso

#### Servidor Solo para SAAS
- Usar `server_name _;` (catch-all) está bien
- No hay conflictos con otros sitios

#### Servidor Compartido
- Usar `server_name YOUR_SERVER_IP;` (IP específica)
- Permite coexistencia con otros dominios

#### Con Dominio Dedicado
- Usar `server_name your-saas-domain.com;`
- Configurar DNS apropiadamente

### Verificación

Para verificar que todo funciona correctamente:

```bash
# Probar acceso directo por IP
curl -I http://YOUR_SERVER_IP

# Debería retornar headers del panel SAAS, no redirecciones
```

### Script de Diagnóstico

Usar este comando para diagnosticar problemas:

```bash
# Mostrar todas las configuraciones nginx activas
nginx -T | grep -A5 -B5 "server_name\|listen.*80"

# Verificar qué sitio responde por IP
curl -I -H "Host: YOUR_SERVER_IP" http://localhost
```

### Prevención

1. **Usar el script actualizado**: El `deploy-saas.sh` actualizado maneja automáticamente estos conflictos
2. **Configuración específica**: Siempre usar `server_name` específicos en lugar de catch-all
3. **Orden de configuración**: Asegurar que webapp-manager-saas tenga precedencia
4. **Documentación**: Mantener registro de todos los virtual hosts configurados

## Troubleshooting

### Problem: Still getting redirected to wrong domain
**Solution**: Check for other nginx configs with catch-all `server_name _;`

### Problem: 404 errors on the SAAS panel
**Solution**: Verify nginx logs and check proxy_pass configuration

### Problem: SSL certificate conflicts
**Solution**: Use different certificates for different domains

---

**Nota**: Esta documentación debe consultarse cada vez que se haga un redespliegue en un servidor compartido con otros servicios web.