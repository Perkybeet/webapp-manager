# 🛠️ Mejoras Implementadas - WebApp Manager

## Resumen de Cambios

Este documento describe las mejoras implementadas para resolver los problemas reportados:

1. **Barras de progreso que se quedan pilladas**
2. **Falta de parámetro --verbose**
3. **Problemas al clonar repositorios SSH**

---

## 🎯 Problema 1: Barras de Progreso Pilladas

### Problema Original
Las barras de progreso se quedaban bloqueadas y la interfaz gráfica no respondía, requiriendo reiniciar el bash.

### Solución Implementada

#### 1.1 Mejorado el ProgressManager
- **Archivo**: `webapp_manager/utils/progress_manager.py`
- **Cambios**:
  - Manejo robusto de excepciones en `task()` context manager
  - Método `force_cleanup()` para limpiar estado en caso de error
  - Manejo específico de `KeyboardInterrupt` (Ctrl+C)
  - Limpieza automática de tareas incluso cuando hay errores

```python
@contextmanager
def task(self, description: str, total: Optional[int] = None):
    """Context manager para una tarea con progreso"""
    task_id = None
    try:
        # ... código existente ...
    except KeyboardInterrupt:
        # Manejar interrupción del usuario
        self.console.print("\n[bold red]⚠️  Operación cancelada por el usuario[/bold red]")
        raise
    except Exception as e:
        # Manejar errores
        self.console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        raise
    finally:
        # Limpiar tarea - SIEMPRE se ejecuta
        if task_id is not None and self.progress:
            try:
                self.progress.update(task_id, completed=total or 100)
                self.progress.remove_task(task_id)
            except Exception:
                # Si hay error removiendo la tarea, simplemente continuar
                pass
```

#### 1.2 Mejorado el CLI
- **Archivo**: `webapp_manager/cli/cli.py`
- **Cambios**:
  - Limpieza automática del progreso antes de salir
  - Manejo de interrupciones de usuario (Ctrl+C)
  - Limpieza forzada en caso de errores

```python
except KeyboardInterrupt:
    self._show_warning("\n⚠️  Operación cancelada por el usuario")
    
    # Limpiar progreso en caso de interrupción
    if hasattr(self, 'progress_manager') and self.progress_manager:
        self.progress_manager.force_cleanup()
    
    sys.exit(1)
```

---

## 🔍 Problema 2: Falta de Parámetro --verbose

### Problema Original
No había forma de ver en tiempo real todos los comandos que se ejecutaban, dificultando la localización de errores.

### Solución Implementada

#### 2.1 Parámetro --verbose ya existía
El parámetro `--verbose` ya estaba implementado en el CLI, pero no se usaba consistentemente en todos los servicios.

#### 2.2 Nuevo CmdService con soporte verbose
- **Archivo**: `webapp_manager/services/cmd_service.py`
- **Cambios**:
  - Constructor acepta parámetro `verbose`
  - Muestra comandos ejecutados en tiempo real
  - Muestra salida y errores detallados

```python
def run(self, command: str, check: bool = True, timeout: Optional[int] = None) -> Optional[str]:
    if self.verbose:
        print(f"🔧 Ejecutando: {command}")
    
    # ... ejecutar comando ...
    
    if self.verbose:
        if output:
            print(f"📤 Salida: {output}")
        if result.stderr:
            print(f"⚠️  Error: {result.stderr}")
```

#### 2.3 Actualización de todos los servicios
- **AppService**: Usa `CmdService` con verbose
- **NginxService**: Usa `CmdService` con verbose  
- **SystemdService**: Usa `CmdService` con verbose
- **WebAppManager**: Pasa verbose a todos los servicios

#### 2.4 Mensajes verbose mejorados
- **AppService**: Mensajes detallados durante despliegue
- Información de rutas, comandos y resultados
- Detalles de errores con stack traces
- Emojis para mejor legibilidad

---

## 🔗 Problema 3: Error al Clonar Repositorios SSH

### Problema Original
Error clonando repositorio SSH: `git@github.com:Arenna-Labs/neurolimpiadas-portal.git`

### Solución Implementada

#### 3.1 Lógica de Fallback SSH → HTTPS
- **Archivo**: `webapp_manager/services/app_service.py`
- **Método**: `_get_source_code()`

```python
if source.startswith("git@"):
    # Para URLs SSH, intentar primero con SSH
    if self.verbose:
        print(Colors.info("🔑 Intentando clonado SSH..."))
    
    clone_result = self.cmd.run(
        f"git clone --depth 1 --branch {branch} {source} {target_dir}",
        check=False,
    )
    clone_success = clone_result is not None and target_dir.exists()
    
    if not clone_success:
        # Convertir SSH a HTTPS y reintentar
        if "github.com" in source:
            https_url = source.replace("git@github.com:", "https://github.com/")
            if self.verbose:
                print(Colors.warning("🔄 SSH falló, intentando con HTTPS..."))
                print(Colors.info(f"🌐 URL HTTPS: {https_url}"))
            
            # Limpiar directorio parcial si existe
            if target_dir.exists():
                shutil.rmtree(target_dir)
            
            clone_result = self.cmd.run(
                f"git clone --depth 1 --branch {branch} {https_url} {target_dir}",
                check=False,
            )
            clone_success = clone_result is not None and target_dir.exists()
```

#### 3.2 Mejor manejo de errores
- Detección automática del tipo de URL
- Conversión automática SSH → HTTPS para GitHub
- Limpieza de directorios parciales en caso de fallo
- Mensajes informativos sobre el proceso
- Sugerencias de posibles causas del error

#### 3.3 Información detallada en modo verbose
```python
if self.verbose:
    print(Colors.info(f"🔄 Clonando repositorio: {source}"))
    print(Colors.info(f"🌿 Rama: {branch}"))
    print(Colors.info(f"📁 Destino: {target_dir}"))

# ... si falla ...

if self.verbose:
    print(Colors.error("💡 Posibles causas:"))
    print(Colors.error("   • Repositorio privado sin acceso"))
    print(Colors.error("   • Rama especificada no existe"))
    print(Colors.error("   • Problemas de red"))
    print(Colors.error("   • Credenciales SSH no configuradas"))
```

---

## 🧪 Cómo Probar las Mejoras

### Para Verbose Mode
```bash
# Ejecutar con verbose activado
python3 webapp-manager.py add --domain test.com --source /path/app --port 3000 --verbose

# O usando la forma corta
python3 webapp-manager.py add --domain test.com --source /path/app --port 3000 -v
```

### Para Clonado SSH → HTTPS
```bash
# Probar con URL SSH (fallback automático a HTTPS)
python3 webapp-manager.py add --domain test.com --source git@github.com:user/repo.git --port 3000 --verbose

# Probar con URL HTTPS directamente
python3 webapp-manager.py add --domain test.com --source https://github.com/user/repo.git --port 3000 --verbose
```

### Para Manejo de Interrupciones
```bash
# Iniciar deployment y presionar Ctrl+C
python3 webapp-manager.py add --domain test.com --source /path/app --port 3000
# Presionar Ctrl+C durante el proceso
```

---

## 📊 Beneficios de las Mejoras

1. **🔧 Mejor Debugging**: El modo verbose permite ver exactamente qué está pasando
2. **🛡️ Mayor Robustez**: Las barras de progreso no se quedan pilladas
3. **🔄 Fallback Automático**: Clonado SSH falla → automáticamente prueba HTTPS
4. **👥 Mejor UX**: Mensajes más claros y informativos
5. **⚠️ Manejo de Errores**: Limpieza adecuada cuando el usuario cancela operaciones

---

## 📝 Archivos Modificados

- `webapp_manager/services/cmd_service.py` - Nuevo servicio con verbose
- `webapp_manager/services/app_service.py` - Mejor clonado y verbose
- `webapp_manager/services/nginx_service.py` - Usa CmdService
- `webapp_manager/services/systemd_service.py` - Usa CmdService
- `webapp_manager/core/manager.py` - Usa CmdService
- `webapp_manager/utils/progress_manager.py` - Mejor manejo de errores
- `webapp_manager/cli/cli.py` - Limpieza de progreso mejorada

---

## ⚡ Próximos Pasos Recomendados

1. **Probar las mejoras** en un entorno de desarrollo
2. **Validar** el fallback SSH → HTTPS con repositorios reales
3. **Verificar** que las interrupciones se manejan correctamente
4. **Considerar** añadir más protocolos de fallback (ej: para GitLab, Bitbucket)
5. **Documentar** casos de uso específicos para el equipo de desarrollo
