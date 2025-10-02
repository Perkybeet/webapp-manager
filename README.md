# WebApp Manager v4.0 - Sistema Modular para Linux

Sistema completo de gestión de aplicaciones web con nginx proxy reverso, interfaz gráfica terminal y deployers modulares.

## ⚠️ Solo para Linux

**WebApp Manager está diseñado exclusivamente para servidores Linux**. No funciona en Windows ni macOS.

## 🚀 Características Principales

- **🎨 Interfaz gráfica Dialog**: GUI nativa para terminales Linux con dialog
- **🔧 Sistema de deployers modulares**: Factory Pattern para 4 tipos de aplicaciones
- **🎯 Auto-detección**: Reconocimiento automático de tipos de aplicaciones
- **📦 Arquitectura modular**: Código organizado en módulos especializados
- **🌐 Soporte multi-tecnología**: NextJS, FastAPI, Node.js, sitios estáticos
- **⚙️ Gestión automática**: nginx, systemd, SSL con Let's Encrypt
- **📊 Monitoreo integrado**: Logs, diagnósticos, reparación automática
- **💾 Backup automático**: Respaldo antes de actualizaciones
- **🖥️ Interfaz dual**: CLI tradicional + GUI terminal con Dialog
- **🔍 Modo Verbose**: Seguimiento detallado de comandos en tiempo real
- **🔄 Clonado Inteligente**: Fallback automático SSH → HTTPS para repositorios
- **🛡️ Progreso Robusto**: Barras de progreso que se recuperan de errores

## 📋 Uso Rápido

### Interfaz Gráfica (Recomendado)
```bash
python3 webapp-manager.py gui
```

### Comandos CLI
```bash
# Ver tipos de aplicaciones
python3 webapp-manager.py types

# Auto-detectar aplicación
python3 webapp-manager.py detect --directory /path/to/app

# Comandos tradicionales
python3 webapp-manager.py add myapp --type nextjs --port 3000
python3 webapp-manager.py list
python3 webapp-manager.py status
```

## 🔧 Instalación

### Prerrequisitos del Sistema (Solo Linux)
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx nodejs npm git dialog

# CentOS/RHEL
sudo yum install python3 python3-pip nginx nodejs npm git dialog
```

### Dependencias Python
```bash
# Instalar dependencias necesarias
pip3 install pythondialog colorama

# Para desarrollo (opcional)
pip3 install pytest pytest-cov black flake8
```

### Instalación Rápida
```bash
# 1. Clonar el repositorio
git clone <repository-url>
cd webapp-manager

# 2. Instalación completa automática
make install-complete

# 3. Para entornos externally-managed (Python 3.11+)
make install-clean

# 4. Verificar instalación
webapp-manager gui
```

### Instalación Manual
```bash
# 1. Hacer ejecutable
chmod +x webapp-manager.py

# 2. Crear enlace simbólico (opcional)
sudo ln -s $(pwd)/webapp-manager.py /usr/local/bin/webapp-manager

# 3. Crear directorios necesarios
sudo mkdir -p /var/www/apps /var/log/apps /etc/webapp-manager /var/backups/webapp-manager

# 4. Configurar permisos
sudo chown -R www-data:www-data /var/www/apps /var/log/apps
```
webapp-manager add --domain app.ejemplo.com --source /ruta/app --port 3000

# API FastAPI
webapp-manager add --domain api.ejemplo.com --source /ruta/api --port 8000 --type fastapi

# Desde repositorio Git
webapp-manager add --domain mi-app.com --source https://github.com/usuario/mi-app.git --port 3001
```

### Gestión de aplicaciones

```bash
# Listar aplicaciones
webapp-manager list --detailed

# Reiniciar aplicación
webapp-manager restart --domain app.ejemplo.com

# Actualizar aplicación
webapp-manager update --domain app.ejemplo.com

# Ver logs
webapp-manager logs --domain app.ejemplo.com --follow

# Remover aplicación
webapp-manager remove --domain app.ejemplo.com
```

### Modo Verbose para Debugging

```bash
# Usar modo verbose para ver todos los comandos ejecutados
webapp-manager add --domain app.com --source git@github.com:user/repo.git --port 3000 --verbose

# Forma corta
webapp-manager add --domain app.com --source /path/app --port 3000 -v

# Útil para debugging cuando hay problemas
webapp-manager update --domain app.com --verbose
webapp-manager repair --domain app.com --verbose
```

### Clonado Inteligente de Repositorios

```bash
# El sistema automáticamente prueba SSH primero, luego HTTPS si falla
webapp-manager add --domain app.com --source git@github.com:user/repo.git --port 3000

# También funciona directamente con HTTPS
webapp-manager add --domain app.com --source https://github.com/user/repo.git --port 3000

# Repositorios privados (requiere configuración SSH o token)
webapp-manager add --domain app.com --source git@github.com:company/private-repo.git --port 3000 --verbose
```

### Diagnóstico y reparación

```bash
# Diagnóstico general
webapp-manager diagnose

# Diagnóstico específico
webapp-manager diagnose --domain app.ejemplo.com

# Reparar aplicación
webapp-manager repair --domain app.ejemplo.com
```

### SSL

```bash
# Configurar SSL
webapp-manager ssl --domain app.ejemplo.com --email admin@ejemplo.com
```

## 🚧 Páginas de Mantenimiento

WebApp Manager incluye un sistema automático de páginas de mantenimiento profesionales que se muestran cuando las aplicaciones están siendo actualizadas o experimentan problemas.

### Características

- **📱 Páginas Modernas**: Diseño profesional y responsivo sin emojis
- **🔄 Auto-actualización**: Las páginas se recargan automáticamente cada 30 segundos
- **🎨 Diferentes Tipos**: 
  - `updating.html` - Para actualizaciones en progreso
  - `error502.html` - Para errores de servidor (502/503/504)
  - `maintenance.html` - Para mantenimiento programado
- **⚙️ Configuración Automática**: Se aplica automáticamente en nuevas instalaciones
- **🔧 Redirección Inteligente**: nginx redirige automáticamente en caso de errores

### Uso

```bash
# Aplicar páginas de mantenimiento a aplicaciones existentes
webapp-manager apply-maintenance

# Las páginas se crean automáticamente al instalar nuevas aplicaciones
webapp-manager add --domain miapp.com --source /ruta/app --port 3000
```

### Ubicación de Archivos

```
/apps/maintenance/
├── updating.html      # Página de actualización
├── error502.html      # Página de error de servidor
└── maintenance.html   # Página de mantenimiento programado
```

### Configuración de nginx

El sistema configura automáticamente nginx para:

```nginx
# Redirección automática en errores
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

### Para Aplicaciones Existentes

Si tienes aplicaciones instaladas antes de esta actualización, puedes aplicar las páginas de mantenimiento ejecutando:

```bash
webapp-manager apply-maintenance
```

Este comando:
1. ✅ Verifica qué aplicaciones necesitan actualización
2. 🔧 Aplica la configuración de mantenimiento a las que no la tienen
3. 📁 Crea los archivos HTML necesarios
4. 🔄 Recarga la configuración de nginx
5. 📊 Muestra un resumen de la operación

## Estructura del proyecto

```
webapp-manager/
├── webapp_manager/
│   ├── __init__.py
│   ├── cli/                 # Interfaz de línea de comandos
│   │   ├── __init__.py
│   │   └── cli.py
│   ├── config/              # Gestión de configuración
│   │   ├── __init__.py
│   │   └── config_manager.py
│   ├── core/                # Lógica principal
│   │   ├── __init__.py
│   │   └── manager.py
│   ├── models/              # Modelos de datos
│   │   ├── __init__.py
│   │   └── app_config.py
│   ├── services/            # Servicios especializados
│   │   ├── __init__.py
│   │   ├── app_service.py
│   │   ├── nginx_service.py
│   │   └── systemd_service.py
│   └── utils/               # Utilidades
│       ├── __init__.py
│       ├── colors.py
│       ├── command_runner.py
│       └── validators.py
├── webapp-manager.py        # Punto de entrada principal
└── README.md
```

## Tipos de aplicación soportados

### Next.js
- Construcción automática con `npm run build`
- Configuración de nginx optimizada para SSR
- Manejo de rutas estáticas y dinámicas

### FastAPI
- Entorno virtual Python automático
- Configuración de uvicorn
- Documentación automática (Swagger/ReDoc)

### Node.js genérico
- Configuración flexible para aplicaciones Node.js
- Soporte para Express, Koa, etc.

### Sitios estáticos
- Servicio directo con nginx
- Optimización para assets estáticos

## Configuración avanzada

### Variables de entorno

```bash
webapp-manager add --domain app.com --source /ruta/app --port 3000 \
  --env NODE_ENV=production \
  --env API_KEY=abc123 \
  --env DATABASE_URL=postgresql://...
```

### Comandos personalizados

```bash
webapp-manager add --domain app.com --source /ruta/app --port 3000 \
  --build-command "npm run build:production" \
  --start-command "npm run start:custom"
```

## Arquitectura

### Separación de responsabilidades

- **CLI**: Interfaz de usuario y parsing de argumentos
- **Core**: Lógica principal y orquestación
- **Services**: Servicios especializados (nginx, systemd, apps)
- **Models**: Estructuras de datos y validaciones
- **Utils**: Utilidades reutilizables
- **Config**: Gestión de configuración persistente

### Beneficios de la arquitectura modular

1. **Mantenibilidad**: Cada módulo tiene responsabilidades claras
2. **Testabilidad**: Fácil crear tests unitarios para cada componente
3. **Escalabilidad**: Fácil agregar nuevos tipos de aplicaciones
4. **Reutilización**: Servicios pueden ser utilizados independientemente
5. **Debugging**: Fácil localizar y corregir problemas

## Logs y diagnóstico

Los logs se almacenan en:
- Sistema: `/var/log/webapp-manager.log`
- Aplicaciones: `/var/log/apps/<domain>-{access,error}.log`
- Systemd: `journalctl -u <domain>.service`

## Requisitos del sistema

- Ubuntu/Debian Linux
- Python 3.8+
- nginx
- systemd
- Node.js y npm (para apps Node.js/Next.js)
- Python 3 y pip (para apps FastAPI)
- Git (para repositorios remotos)

## Contribuir

1. Fork el repositorio
2. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Agregar nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## 🔧 Resolución de Problemas

### Error de Sintaxis en Instalación Global

Si ves errores como:
```
SyntaxError: invalid syntax
  python3 webapp-manager.py "$@"
          ^^^^^^
```

**Solución:**
```bash
# 1. Desinstalar completamente
make uninstall

# 2. Usar instalación limpia (sin pip)
make install-clean

# 3. Verificar instalación
make debug-install
```

### Entorno Externally-Managed (Python 3.11+)

Si ves errores como:
```
error: externally-managed-environment
```

**Opciones de solución:**
```bash
# Opción 1: Instalación limpia (recomendada)
make install-clean

# Opción 2: Usar virtual environment
python3 -m venv venv
source venv/bin/activate
make install

# Opción 3: Forzar con --break-system-packages
make install-with-pip
```

### Debug de Instalación

```bash
# Verificar estado de instalación
make debug-install

# Ejecutar directamente sin instalación
make run ARGS="--help"

# Crear alias local
make create-alias
source ~/.bashrc
```

### Problemas de Permisos

```bash
# Asegurar permisos correctos
sudo chown -R www-data:www-data /var/www/apps
sudo chmod 755 /usr/local/bin/webapp-manager
sudo chmod -R 755 /opt/webapp-manager
```

### Verificación Post-Instalación

```bash
# Verificar comando disponible
which webapp-manager

# Verificar versión
webapp-manager --version

# Test básico
webapp-manager list
```

## Licencia

MIT License - ver archivo LICENSE para detalles.
