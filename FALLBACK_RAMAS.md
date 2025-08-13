# 🌿 Nueva Funcionalidad: Fallback Automático de Ramas

## 🎯 Problema Resuelto

**Situación Original:**
- Muchos repositorios usan `master` como rama principal en lugar de `main`
- Si se especifica una rama que no existe, el clonado/actualización falla
- El usuario tenía que saber exactamente qué rama usar

**Ejemplo de Error:**
```bash
webapp-manager add --domain app.com --source git@github.com:user/repo.git --branch main -p 3000
❌ Error clonando repositorio: rama 'main' no existe
```

## ✅ Solución Implementada

### **Sistema Inteligente de Fallback de Ramas**

El sistema ahora intenta automáticamente múltiples ramas en orden de preferencia:

1. **Rama especificada** (ej: `main`) 
2. **main** (si no era la especificada)
3. **master** 
4. **develop**
5. **dev**

## 🔧 Implementación Técnica

### Nuevos Métodos Añadidos

#### 1. `_try_clone_with_branch_fallback()`
```python
def _try_clone_with_branch_fallback(self, url: str, target_dir: Path, preferred_branch: str) -> tuple[bool, str]:
    """Intentar clonar con fallback de ramas"""
    branches_to_try = [preferred_branch, "main", "master", "develop", "dev"]
    
    for branch in branches_to_try:
        clone_result = self.cmd.run(
            f"git clone --depth 1 --branch {branch} {url} {target_dir}",
            check=False,
        )
        
        if clone_result is not None and target_dir.exists():
            return True, branch  # Éxito, devolver rama usada
    
    return False, ""  # Ninguna rama funcionó
```

#### 2. `_update_git_with_branch_fallback()`
```python
def _update_git_with_branch_fallback(self, app_dir: Path, preferred_branch: str) -> tuple[bool, str]:
    """Actualizar repositorio Git con fallback de ramas"""
    branches_to_try = [preferred_branch, "main", "master", "develop", "dev"]
    
    # Hacer fetch general primero
    self.cmd.run(f"cd {app_dir} && git fetch origin")
    
    for branch in branches_to_try:
        # Verificar si la rama existe en el remoto
        check_result = self.cmd.run(
            f"cd {app_dir} && git ls-remote --heads origin {branch}",
            check=False
        )
        
        if check_result:  # Rama existe
            reset_result = self.cmd.run(f"cd {app_dir} && git reset --hard origin/{branch}")
            if reset_result is not None:
                return True, branch
    
    return False, ""
```

## 🚀 Beneficios para el Usuario

### ✅ **Clonado Inteligente**
```bash
# El usuario especifica 'main' pero el repo usa 'master'
webapp-manager add --domain app.com --source git@github.com:user/repo.git --branch main -p 3000

# Salida con verbose:
🌿 Ramas a intentar: main, master, develop, dev
🔄 Intentando con rama: main
⚠️  Rama 'main' no encontrada, probando siguiente...
🔄 Intentando con rama: master  
✅ Clonado exitoso con rama: master
⚠️  Nota: Se usó la rama 'master' en lugar de 'main'
```

### ✅ **Actualización Robusta**
```bash
# Actualizar aplicación que cambió de 'master' a 'main'
webapp-manager update --domain app.com --verbose

# El sistema automáticamente encuentra la nueva rama principal
🌿 Ramas a intentar para actualización: master, main, develop, dev
🔄 Intentando actualizar con rama: master
⚠️  Rama 'master' no existe en el remoto
🔄 Intentando actualizar con rama: main
✅ Actualización exitosa con rama: main
⚠️  Nota: Se usó la rama 'main' en lugar de 'master'
```

## 📋 Casos de Uso Cubiertos

### 1. **Repositorios que Migran de Master a Main**
- Clonado inicial funciona automáticamente
- Actualizaciones se adaptan al cambio de rama

### 2. **Repositorios con Ramas No Estándar**
- Si usan `develop` como principal, lo encuentra automáticamente
- Si usan `dev`, también funciona

### 3. **Especificación Incorrecta de Rama**
- Usuario escribe `main` pero repo usa `master` → funciona
- Usuario escribe `master` pero repo usa `main` → funciona

### 4. **Repositorios Fork/Branch**
- Intenta la rama especificada primero (comportamiento esperado)
- Si no existe, fallback a ramas principales

## 🧪 Ejemplos de Uso

### Clonado Básico
```bash
# Funciona independientemente de si el repo usa main o master
webapp-manager add --domain app.com --source https://github.com/user/repo.git -p 3000

# Especificar rama explícita (con fallback automático)
webapp-manager add --domain app.com --source https://github.com/user/repo.git --branch main -p 3000
```

### Con Verbose para Ver el Proceso
```bash
webapp-manager add --domain app.com --source https://github.com/user/repo.git --branch main -p 3000 --verbose

# Salida esperada:
🌿 Ramas a intentar: main, master, develop, dev
🔄 Intentando con rama: main
⚠️  Rama 'main' no encontrada, probando siguiente...
🔄 Intentando con rama: master
✅ Clonado exitoso con rama: master
⚠️  Nota: Se usó la rama 'master' en lugar de 'main'
🎉 Aplicación desplegada exitosamente
```

### Actualización de Aplicación
```bash
webapp-manager update --domain app.com --verbose

# El sistema automáticamente encuentra la rama correcta
🌿 Ramas a intentar para actualización: main, master, develop, dev
🔄 Intentando actualizar con rama: main
✅ Actualización exitosa con rama: main
```

## 📊 Compatibilidad

- ✅ **GitHub**: main, master
- ✅ **GitLab**: main, master, develop  
- ✅ **Bitbucket**: main, master, develop
- ✅ **Repositorios privados**: Funciona con cualquier rama
- ✅ **URLs SSH y HTTPS**: Ambos soportados

## 🔍 Transparencia para el Usuario

El sistema **siempre informa** qué rama se usó:

- ✅ Si usó la rama especificada: Silencioso (comportamiento normal)
- ⚠️ Si usó rama diferente: Muestra advertencia informativa
- 📝 En modo verbose: Muestra todo el proceso de búsqueda

## 💡 Próximas Mejoras Posibles

1. **Configuración de ramas preferidas** por usuario
2. **Cache de ramas por repositorio** para evitar verificaciones repetidas
3. **Soporte para más proveedores Git** (GitLab, Bitbucket)
4. **Detección inteligente** de rama principal via API del proveedor

---

## 📝 Archivos Modificados

- ✅ `webapp_manager/services/app_service.py`
  - Nuevo método `_try_clone_with_branch_fallback()`
  - Nuevo método `_update_git_with_branch_fallback()`
  - Actualizado `_get_source_code()` para usar fallback
  - Actualizado `update_app()` para usar fallback

---

## 🎉 Resultado Final

**Ahora el usuario puede:**
- Especificar cualquier rama sin preocuparse si existe
- Clonar repositorios sin saber si usan `main` o `master`
- Actualizar aplicaciones aunque el repo haya cambiado de rama principal
- Ver exactamente qué rama se usó con modo verbose

**El sistema es inteligente y tolerante a fallos** 🚀
