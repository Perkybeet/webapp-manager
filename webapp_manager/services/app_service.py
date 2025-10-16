"""
Servicio para gestión de aplicaciones
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..utils import CommandRunner, Colors, Validators
from ..models import AppConfig
from .cmd_service import CmdService


class AppService:
    """Servicio para gestión de aplicaciones"""
    
    def __init__(self, apps_dir: Path, verbose: bool = False, progress_manager=None):
        self.apps_dir = apps_dir
        self.cmd = CmdService(verbose=verbose)
        self.verbose = verbose
        self.progress = progress_manager
    
    def deploy_app(self, app_config: AppConfig) -> bool:
        """Desplegar aplicación usando el sistema modular de deployers"""
        try:
            from ..deployers import DeployerFactory
            
            app_dir = self.apps_dir / app_config.domain
            temp_dir = self.apps_dir / f"{app_config.domain}_temp"

            if temp_dir.exists():
                shutil.rmtree(temp_dir)

            # Paso 1: Preparación
            if self.progress:
                self.progress.console.print(f"[cyan]→[/cyan] Preparando despliegue")
            elif self.verbose:
                print(Colors.info("→ Preparando despliegue"))

            # Backup si existe
            if app_dir.exists():
                if self.verbose:
                    print(Colors.info("  Creando backup de aplicación existente..."))
                    
                backup_dir = self.apps_dir / f"{app_config.domain}_backup"
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                shutil.copytree(app_dir, backup_dir)
                
                if self.verbose:
                    print(Colors.success(f"  Backup creado en: {backup_dir}"))

            # Paso 2: Obtener código
            if self.progress:
                self.progress.console.print(f"[cyan]→[/cyan] Obteniendo código fuente")
            elif self.verbose:
                print(Colors.info("→ Obteniendo código fuente"))

            if not self._get_source_code(app_config.source, app_config.branch, temp_dir):
                return False

            # Paso 3: Validar estructura
            if self.progress:
                self.progress.console.print(f"[cyan]→[/cyan] Validando estructura")
            elif self.verbose:
                print(Colors.info("→ Validando estructura"))
            
            # Crear deployer específico
            deployer = DeployerFactory.create_deployer(app_config.app_type, str(self.apps_dir), self.cmd)
            
            if not deployer.validate_structure(temp_dir):
                print(Colors.error("Estructura de aplicación inválida"))
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                return False

            # Paso 4: Verificar requerimientos
            if self.progress:
                self.progress.console.print(f"[cyan]→[/cyan] Verificando requerimientos")
            elif self.verbose:
                print(Colors.info("→ Verificando requerimientos"))
                
            if not deployer.check_requirements():
                print(Colors.error("Requerimientos del sistema no cumplidos"))
                return False

            # Paso 5: Instalar y construir
            if self.progress:
                self.progress.console.print(f"[cyan]→[/cyan] Instalando dependencias y construyendo")
            elif self.verbose:
                print(Colors.info("→ Instalando dependencias y construyendo"))
            
            # Instalar dependencias
            if not deployer.install_dependencies(temp_dir, app_config):
                print(Colors.error("Error instalando dependencias"))
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                return False
            
            # Construir aplicación
            if not deployer.build_application(temp_dir, app_config):
                print(Colors.error("Error construyendo aplicación"))
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                return False
            
            # Manejar archivo .env
            if hasattr(deployer, 'handle_environment_file'):
                if not deployer.handle_environment_file(temp_dir, app_config):
                    if self.verbose:
                        print(Colors.warning("Error configurando archivo .env"))

            # Paso 6: Finalizar
            if self.progress:
                self.progress.console.print(f"[cyan]→[/cyan] Finalizando despliegue")
            elif self.verbose:
                print(Colors.info("→ Finalizando despliegue"))
                
            if not self._finalize_deployment(app_dir, temp_dir):
                return False

            # Si el despliegue fue exitoso, eliminar backup
            backup_dir = self.apps_dir / f"{app_config.domain}_backup"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
                if self.verbose:
                    print(Colors.info("  Backup temporal eliminado"))

            if self.verbose:
                print(Colors.success(f"✓ Aplicación desplegada exitosamente en {app_dir}"))
            
            return True

        except Exception as e:
            print(Colors.error(f"Error en despliegue: {e}"))
            if self.verbose:
                import traceback
                print(Colors.error(f"Detalles del error:\n{traceback.format_exc()}"))
            self._cleanup_failed_deployment(app_config.domain, temp_dir)
            return False

    def update_app(self, domain: str, app_config: AppConfig) -> bool:
        """
        Actualizar aplicación existente con zero-downtime deployment
        La aplicación se actualiza en una copia temporal y solo se cambia cuando está lista
        """
        try:
            app_dir = self.apps_dir / domain
            update_dir = self.apps_dir / f"{domain}_update"
            backup_dir = self.apps_dir / f"{domain}_backup"

            if not app_config.source.startswith(("http", "git@")):
                error_msg = "Solo se pueden actualizar aplicaciones desde repositorios git"
                if self.progress:
                    self.progress.error(error_msg)
                else:
                    print(Colors.error(error_msg))
                return False

            if not app_dir.exists():
                error_msg = f"Directorio de aplicación no existe: {app_dir}"
                if self.progress:
                    self.progress.error(error_msg)
                else:
                    print(Colors.error(error_msg))
                return False

            # Paso 1: Crear copia de trabajo para actualización (excluyendo node_modules y otros)
            if self.verbose:
                print(Colors.info("  Creando copia de trabajo para actualización (sin node_modules)"))
            if update_dir.exists():
                shutil.rmtree(update_dir)
            
            # Copiar excluyendo directorios problemáticos con enlaces simbólicos
            def ignore_patterns(directory, contents):
                """Ignorar node_modules y otros directorios con enlaces simbólicos"""
                ignore = set()
                if 'node_modules' in contents:
                    ignore.add('node_modules')
                if '.next' in contents:
                    ignore.add('.next')
                if '.venv' in contents:
                    ignore.add('.venv')
                if '__pycache__' in contents:
                    ignore.add('__pycache__')
                return ignore
            
            shutil.copytree(app_dir, update_dir, ignore=ignore_patterns)
            if self.verbose:
                print(Colors.success(f"  Copia de trabajo creada (sin enlaces simbólicos): {update_dir}"))

            # Paso 2: Configurar permisos para Git en la copia
            if self.verbose:
                print(Colors.info("  Configurando permisos para Git"))
            self.cmd.run_sudo(f"chown root:root {update_dir}", check=False)
            self._configure_git_safe_directory(update_dir)
            
            try:
                git_status = self.cmd.run(f"cd {update_dir} && git status --porcelain", check=False)
            except Exception as e:
                if self.verbose:
                    print(Colors.warning(f"  Advertencia Git: {e}"))

            # Paso 3: Actualizar código en la copia
            if self.verbose:
                print(Colors.info("  Actualizando código desde repositorio"))
            update_success, used_branch = self._update_git_with_branch_fallback(update_dir, app_config.branch)
            
            if not update_success:
                print(Colors.error("Error actualizando código - ninguna rama válida encontrada"))
                if update_dir.exists():
                    shutil.rmtree(update_dir)
                return False
            
            if used_branch != app_config.branch:
                print(Colors.warning(f"Nota: Se usó la rama '{used_branch}' en lugar de '{app_config.branch}'"))

            # Paso 4: Reconstruir aplicación
            # Para Next.js: hacer build en la carpeta original para evitar problemas con rutas
            # Para otros: reconstruir en la copia
            if self.verbose:
                if app_config.app_type == "nextjs":
                    print(Colors.info("  Construyendo Next.js en carpeta original (evitando problemas de rutas)"))
                else:
                    print(Colors.info("  Reconstruyendo aplicación en copia temporal"))
            
            self.cmd.run_sudo(f"chown www-data:www-data {update_dir}", check=False)
            
            if app_config.app_type == "nextjs":
                # Para Next.js: actualizar dependencias y hacer build en carpeta ORIGINAL
                if not self._rebuild_nextjs_in_place(app_dir, app_config):
                    print(Colors.error("Error construyendo aplicación Next.js"))
                    if update_dir.exists():
                        shutil.rmtree(update_dir)
                    return False
            else:
                # Para otros tipos: reconstruir en la copia temporal
                if not self._rebuild_application(update_dir, app_config):
                    print(Colors.error("Error reconstruyendo aplicación"))
                    if update_dir.exists():
                        shutil.rmtree(update_dir)
                    return False

            # Paso 5: Configurar permisos
            if self.verbose:
                print(Colors.info("  Configurando permisos"))
            
            # Configurar permisos en update_dir (código actualizado)
            self._set_permissions(update_dir)
            
            # Si es Next.js, también configurar permisos en app_dir (donde está el build)
            if app_config.app_type == "nextjs":
                self._set_permissions(app_dir)

            # Paso 6: Crear backup de la versión actual antes del intercambio
            if self.verbose:
                print(Colors.info("  Creando backup de versión actual"))
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            
            # Aquí la aplicación actual sigue corriendo
            if self.verbose:
                print(Colors.info("  La aplicación actual sigue funcionando..."))
            
            # Paso 7: Intercambio selectivo - actualizar solo código y build, preservar node_modules
            # Este es el único momento donde podría haber un breve downtime
            if self.verbose:
                print(Colors.info("  Realizando actualización selectiva de archivos"))
            
            try:
                # Crear backup antes del intercambio
                shutil.move(str(app_dir), str(backup_dir))
                
                # Crear nuevo directorio de app
                app_dir.mkdir(parents=True, exist_ok=True)
                
                # Copiar todo desde update_dir excepto los directorios que vamos a preservar
                if self.verbose:
                    print(Colors.info("  Copiando código actualizado..."))
                
                for item in update_dir.iterdir():
                    dest = app_dir / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)
                
                # Si es Next.js, copiar .next desde el backup (ya fue construido en el paso anterior)
                if app_config.app_type == "nextjs":
                    backup_next = backup_dir / ".next"
                    app_next = app_dir / ".next"
                    if backup_next.exists():
                        if self.verbose:
                            print(Colors.info("  Copiando build .next actualizado..."))
                        shutil.copytree(backup_next, app_next)
                
                # Preservar node_modules del backup (mantener enlaces simbólicos intactos)
                if app_config.app_type in ["nextjs", "node"]:
                    backup_node_modules = backup_dir / "node_modules"
                    app_node_modules = app_dir / "node_modules"
                    if backup_node_modules.exists():
                        if self.verbose:
                            print(Colors.info("  Preservando node_modules con enlaces simbólicos..."))
                        # Mover (no copiar) para mantener enlaces simbólicos intactos
                        shutil.move(str(backup_node_modules), str(app_node_modules))
                
                # Preservar .venv para FastAPI
                if app_config.app_type == "fastapi":
                    backup_venv = backup_dir / ".venv"
                    app_venv = app_dir / ".venv"
                    if backup_venv.exists():
                        if self.verbose:
                            print(Colors.info("  Preservando entorno virtual Python..."))
                        shutil.move(str(backup_venv), str(app_venv))
                
                if self.verbose:
                    print(Colors.success("  ✓ Actualización selectiva completada exitosamente"))
            except Exception as e:
                print(Colors.error(f"Error en actualización de directorios: {e}"))
                # Intentar revertir si falla
                if backup_dir.exists() and app_dir.exists():
                    shutil.rmtree(app_dir)
                    shutil.move(str(backup_dir), str(app_dir))
                if update_dir.exists():
                    shutil.rmtree(update_dir)
                return False

            # Paso 8: Limpiar directorios temporales después del intercambio exitoso
            if update_dir.exists():
                if self.verbose:
                    print(Colors.info("  Limpiando directorio temporal de actualización..."))
                shutil.rmtree(update_dir)
            
            # El backup se mantiene por si necesitamos rollback manual
            if self.verbose:
                print(Colors.info(f"  Backup mantenido en: {backup_dir}"))
                print(Colors.success("  Actualización completada con zero-downtime"))
            
            return True

        except Exception as e:
            print(Colors.error(f"Error durante actualización: {e}"))
            if self.verbose:
                import traceback
                print(Colors.error(f"Detalles:\n{traceback.format_exc()}"))
            
            # Limpiar directorios temporales
            if update_dir.exists():
                try:
                    shutil.rmtree(update_dir)
                except:
                    pass
            
            return False

    def remove_app(self, domain: str) -> bool:
        """Remover aplicación"""
        try:
            app_dir = self.apps_dir / domain
            if app_dir.exists():
                shutil.rmtree(app_dir)
                print(Colors.success(f"Directorio de aplicación {domain} removido"))
            return True
        except Exception as e:
            print(Colors.error(f"Error removiendo aplicación: {e}"))
            return False

    def test_connectivity(self, domain: str, port: int) -> bool:
        """Probar conectividad de la aplicación"""
        try:
            import time
            time.sleep(3)

            test_result = self.cmd.run(
                f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:{port}',
                check=False,
            )

            if test_result and test_result.startswith(("2", "3")):
                print(Colors.success("Aplicación responde correctamente"))
                return True
            else:
                print(Colors.warning(f"Aplicación no responde (código: {test_result})"))
                return False

        except Exception as e:
            print(Colors.warning(f"Error probando conectividad: {e}"))
            return False

    def _try_clone_with_branch_fallback(self, url: str, target_dir: Path, preferred_branch: str) -> tuple[bool, str]:
        """
        Intentar clonar con fallback de ramas
        
        Args:
            url: URL del repositorio (SSH o HTTPS)
            target_dir: Directorio destino
            preferred_branch: Rama preferida a intentar primero
            
        Returns:
            tuple[bool, str]: (éxito, rama_usada)
        """
        # Lista de ramas a intentar en orden de preferencia
        branches_to_try = [preferred_branch]
        
        # Añadir ramas comunes si no están ya en la lista
        common_branches = ["main", "master", "develop", "dev"]
        for branch in common_branches:
            if branch not in branches_to_try:
                branches_to_try.append(branch)
        
        if self.verbose:
            print(Colors.info(f"🌿 Ramas a intentar: {', '.join(branches_to_try)}"))
        
        for branch in branches_to_try:
            if self.verbose:
                print(Colors.info(f"🔄 Intentando con rama: {branch}"))
            
            # Limpiar directorio si existe de intentos anteriores
            if target_dir.exists():
                shutil.rmtree(target_dir)
            
            clone_result = self.cmd.run(
                f"git clone --depth 1 --branch {branch} {url} {target_dir}",
                check=False,
            )
            
            if clone_result is not None and target_dir.exists():
                if self.verbose:
                    print(Colors.success(f"✅ Clonado exitoso con rama: {branch}"))
                return True, branch
            elif self.verbose:
                print(Colors.warning(f"⚠️  Rama '{branch}' no encontrada, probando siguiente..."))
        
        return False, ""

    def _update_git_with_branch_fallback(self, app_dir: Path, preferred_branch: str) -> tuple[bool, str]:
        """
        Actualizar repositorio Git con fallback de ramas
        
        Args:
            app_dir: Directorio de la aplicación
            preferred_branch: Rama preferida a intentar primero
            
        Returns:
            tuple[bool, str]: (éxito, rama_usada)
        """
        # Lista de ramas a intentar en orden de preferencia
        branches_to_try = [preferred_branch]
        
        # Añadir ramas comunes si no están ya en la lista
        common_branches = ["main", "master", "develop", "dev"]
        for branch in common_branches:
            if branch not in branches_to_try:
                branches_to_try.append(branch)
        
        if self.verbose:
            print(Colors.info(f"🌿 Ramas a intentar para actualización: {', '.join(branches_to_try)}"))
        
        # Primero hacer fetch general
        try:
            fetch_result = self.cmd.run(f"cd {app_dir} && git fetch origin")
            if self.verbose:
                print(Colors.success("✅ Git fetch completado"))
        except Exception as e:
            if self.verbose:
                print(Colors.error(f"❌ Error haciendo git fetch: {e}"))
            return False, ""
        
        # Intentar con cada rama
        for branch in branches_to_try:
            if self.verbose:
                print(Colors.info(f"🔄 Intentando actualizar con rama: {branch}"))
            
            try:
                # Verificar si la rama existe en el remoto
                check_result = self.cmd.run(
                    f"cd {app_dir} && git ls-remote --heads origin {branch}",
                    check=False
                )
                
                if not check_result:
                    if self.verbose:
                        print(Colors.warning(f"⚠️  Rama '{branch}' no existe en el remoto"))
                    continue
                
                # Intentar hacer reset hard a esa rama
                reset_result = self.cmd.run(f"cd {app_dir} && git reset --hard origin/{branch}")
                
                if reset_result is not None:
                    if self.verbose:
                        print(Colors.success(f"✅ Actualización exitosa con rama: {branch}"))
                    return True, branch
                    
            except Exception as e:
                if self.verbose:
                    print(Colors.warning(f"⚠️  Error con rama '{branch}': {e}"))
                continue
        
        return False, ""

    def _get_source_code(self, source: str, branch: str, target_dir: Path) -> bool:
        """Obtener código fuente"""
        try:
            if source.startswith(("http", "git@")):
                if self.verbose:
                    print(Colors.info(f"🔄 Clonando repositorio: {source}"))
                    print(Colors.info(f"🌿 Rama preferida: {branch}"))
                    print(Colors.info(f"📁 Destino: {target_dir}"))
                else:
                    print(Colors.info(f"Clonando repositorio: {source}"))
                
                # Intentar clonar primero con SSH si es una URL SSH
                clone_success = False
                used_branch = branch
                
                if source.startswith("git@"):
                    # Para URLs SSH, intentar primero con SSH
                    if self.verbose:
                        print(Colors.info("🔑 Intentando clonado SSH..."))
                    
                    clone_success, used_branch = self._try_clone_with_branch_fallback(source, target_dir, branch)
                    
                    if not clone_success:
                        # Convertir SSH a HTTPS y reintentar
                        if "github.com" in source:
                            https_url = source.replace("git@github.com:", "https://github.com/")
                            if self.verbose:
                                print(Colors.warning("🔄 SSH falló, intentando con HTTPS..."))
                                print(Colors.info(f"🌐 URL HTTPS: {https_url}"))
                            
                            clone_success, used_branch = self._try_clone_with_branch_fallback(https_url, target_dir, branch)
                
                else:
                    # Para URLs HTTPS
                    if self.verbose:
                        print(Colors.info("🌐 Clonando via HTTPS..."))
                    
                    clone_success, used_branch = self._try_clone_with_branch_fallback(source, target_dir, branch)
                
                if not clone_success:
                    print(Colors.error(f"❌ Error clonando repositorio: {source}"))
                    if self.verbose:
                        print(Colors.error("💡 Posibles causas:"))
                        print(Colors.error("   • Repositorio privado sin acceso"))
                        print(Colors.error("   • Ninguna de las ramas comunes existe (main, master, develop, dev)"))
                        print(Colors.error("   • Problemas de red"))
                        print(Colors.error("   • Credenciales SSH no configuradas"))
                    return False

                if target_dir.exists():
                    self._configure_git_safe_directory(target_dir)
                    if self.verbose:
                        if used_branch != branch:
                            print(Colors.warning(f"⚠️  Nota: Se usó la rama '{used_branch}' en lugar de '{branch}'"))
                        print(Colors.success("✅ Repositorio clonado exitosamente"))
            else:
                if not Path(source).exists():
                    print(Colors.error(f"Directorio fuente no existe: {source}"))
                    return False

                if self.verbose:
                    print(Colors.info(f"📂 Copiando desde directorio local: {source}"))
                    print(Colors.info(f"📁 Destino: {target_dir}"))
                else:
                    print(Colors.info(f"Copiando desde: {source}"))
                
                shutil.copytree(source, target_dir)
                
                if self.verbose:
                    print(Colors.success("✅ Código copiado exitosamente"))

            return True

        except Exception as e:
            print(Colors.error(f"Error obteniendo código fuente: {e}"))
            if self.verbose:
                import traceback
                print(Colors.error(f"🔍 Detalles del error:\n{traceback.format_exc()}"))
            return False

    def _validate_app_structure(self, app_dir: Path, app_type: str) -> bool:
        """Validar estructura de aplicación según tipo"""
        try:
            if app_type == "nextjs":
                return self._validate_nextjs_structure(app_dir)
            elif app_type == "fastapi":
                return self._validate_fastapi_structure(app_dir)
            elif app_type == "node":
                return self._validate_node_structure(app_dir)
            elif app_type == "static":
                return self._validate_static_structure(app_dir)
            else:
                print(Colors.warning(f"Tipo de aplicación desconocido: {app_type}"))
                return True

        except Exception as e:
            print(Colors.error(f"Error validando estructura: {e}"))
            return False

    def _validate_nextjs_structure(self, app_dir: Path) -> bool:
        """Validar estructura Next.js"""
        required_files = ["package.json"]
        required_deps = ["next", "react"]

        # Verificar archivos requeridos
        for file in required_files:
            if not (app_dir / file).exists():
                print(Colors.error(f"Archivo requerido no encontrado: {file}"))
                return False

        # Validar package.json
        try:
            with open(app_dir / "package.json", "r") as f:
                package_data = json.load(f)

            dependencies = {
                **package_data.get("dependencies", {}),
                **package_data.get("devDependencies", {}),
            }

            for dep in required_deps:
                if not any(dep in key for key in dependencies.keys()):
                    print(Colors.error(f"Dependencia requerida no encontrada: {dep}"))
                    return False

            scripts = package_data.get("scripts", {})
            if "build" not in scripts:
                print(Colors.warning("Script 'build' no encontrado en package.json"))
            if "start" not in scripts:
                print(Colors.warning("Script 'start' no encontrado en package.json"))

            print(Colors.success("Estructura Next.js válida"))
            return True

        except Exception as e:
            print(Colors.error(f"Error validando package.json: {e}"))
            return False

    def _validate_fastapi_structure(self, app_dir: Path) -> bool:
        """Validar estructura FastAPI"""
        # Solo main.py es requerido, requirements.txt es opcional
        required_files = ["main.py"]
        
        for file in required_files:
            if not (app_dir / file).exists():
                print(Colors.error(f"Archivo requerido no encontrado: {file}"))
                return False

        # Verificar requirements.txt si existe
        requirements_file = app_dir / "requirements.txt"
        if requirements_file.exists():
            try:
                with open(requirements_file, "r") as f:
                    requirements_content = f.read().lower()

                if "fastapi" not in requirements_content:
                    print(Colors.warning("FastAPI no encontrado en requirements.txt - se instalará automáticamente"))

                if "uvicorn" not in requirements_content:
                    print(Colors.warning("Uvicorn no encontrado en requirements.txt - se instalará automáticamente"))

                print(Colors.success("requirements.txt encontrado y será procesado"))
            except Exception as e:
                print(Colors.warning(f"Error leyendo requirements.txt: {e}"))
        else:
            print(Colors.info("requirements.txt no encontrado - se instalarán dependencias básicas"))

        # Verificar estructura de main.py
        main_file = app_dir / "main.py"
        try:
            with open(main_file, "r") as f:
                main_content = f.read()
                
            if "from fastapi import" not in main_content and "import fastapi" not in main_content:
                print(Colors.warning("main.py no parece ser una aplicación FastAPI"))
            
            if "app = " not in main_content and "application = " not in main_content:
                print(Colors.warning("Variable de aplicación no encontrada en main.py"))
            
            print(Colors.success("Estructura FastAPI válida"))
            return True
            
        except Exception as e:
            print(Colors.error(f"Error validando main.py: {e}"))
            return False

    def _validate_node_structure(self, app_dir: Path) -> bool:
        """Validar estructura Node.js"""
        if not (app_dir / "package.json").exists():
            print(Colors.error("package.json no encontrado"))
            return False
        print(Colors.success("Estructura Node.js válida"))
        return True

    def _validate_static_structure(self, app_dir: Path) -> bool:
        """Validar estructura de sitio estático"""
        index_files = ["index.html", "index.htm"]
        if not any((app_dir / f).exists() for f in index_files):
            print(Colors.warning("No se encontró archivo index.html"))
        print(Colors.success("Estructura estática válida"))
        return True

    def _build_application(self, app_dir: Path, app_config: AppConfig) -> bool:
        """Construir aplicación según su tipo"""
        try:
            if app_config.app_type in ["nextjs", "node"]:
                return self._build_nodejs_app(app_dir, app_config)
            elif app_config.app_type == "fastapi":
                return self._build_fastapi_app(app_dir, app_config)
            else:
                return True  # Sitios estáticos no requieren construcción

        except Exception as e:
            print(Colors.error(f"Error construyendo aplicación: {e}"))
            return False

    def _build_nodejs_app(self, app_dir: Path, app_config: AppConfig) -> bool:
        """Construir aplicación Node.js/Next.js"""
        package_json = app_dir / "package.json"
        if not package_json.exists():
            print(Colors.error("package.json no encontrado"))
            return False

        print(Colors.info("Instalando dependencias..."))
        install_result = self.cmd.run(f"cd {app_dir} && npm ci --production=false", check=False)
        if not install_result:
            print(Colors.warning("npm ci falló, intentando con npm install..."))
            install_result = self.cmd.run(f"cd {app_dir} && npm install", check=False)
            if not install_result:
                print(Colors.error("Error instalando dependencias"))
                return False

        # Configurar permisos de ejecución para node_modules/.bin/
        node_modules_bin = app_dir / "node_modules" / ".bin"
        if node_modules_bin.exists():
            self.cmd.run(f"chmod +x {node_modules_bin}/*", check=False)
            print(Colors.info("Permisos de ejecución configurados para node_modules/.bin/"))

        if app_config.app_type == "nextjs":
            build_cmd = app_config.build_command or "npm run build"
            print(Colors.info(f"Construyendo aplicación: {build_cmd}"))
            build_result = self.cmd.run(f"cd {app_dir} && {build_cmd}", check=False)
            if not build_result:
                print(Colors.error("Error construyendo aplicación Next.js"))
                return False

            if not (app_dir / ".next").exists():
                print(Colors.error("Construcción Next.js no generó directorio .next"))
                return False

        return True

    def _build_fastapi_app(self, app_dir: Path, app_config: AppConfig) -> bool:
        """Construir aplicación FastAPI"""
        requirements_file = app_dir / "requirements.txt"
        venv_dir = app_dir / ".venv"
        
        # Verificar si ya existe un .env y respetarlo
        env_file = app_dir / ".env"
        if env_file.exists():
            print(Colors.info("Archivo .env encontrado en el repositorio - será respetado"))
        else:
            print(Colors.info("No se encontró archivo .env en el repositorio"))
        
        # Crear entorno virtual con .venv
        print(Colors.info("Creando entorno virtual Python (.venv)..."))
        if venv_dir.exists():
            print(Colors.info("Entorno virtual existente encontrado, eliminando..."))
            shutil.rmtree(venv_dir)
        
        venv_result = self.cmd.run(f"cd {app_dir} && python3 -m venv .venv", check=False)
        if venv_result is None:
            print(Colors.error("Error creando entorno virtual"))
            return False

        # Instalar dependencias si requirements.txt existe
        if requirements_file.exists():
            print(Colors.info("Instalando dependencias desde requirements.txt..."))
            install_deps = self.cmd.run(
                f"cd {app_dir} && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt",
                check=False,
            )
            if install_deps is None:
                print(Colors.error("Error instalando dependencias de Python"))
                return False
        else:
            print(Colors.warning("requirements.txt no encontrado, instalando FastAPI y Uvicorn básicos..."))
            install_basic = self.cmd.run(
                f"cd {app_dir} && .venv/bin/pip install --upgrade pip && .venv/bin/pip install fastapi uvicorn[standard]",
                check=False,
            )
            if install_basic is None:
                print(Colors.error("Error instalando dependencias básicas"))
                return False

        # Asegurar que uvicorn está instalado
        self._ensure_uvicorn_installed(app_dir)

        # Configurar permisos
        self.cmd.run(f"chmod +x {app_dir}/.venv/bin/*", check=False)

        print(Colors.success("Aplicación FastAPI construida exitosamente"))
        return True

    def _ensure_uvicorn_installed(self, app_dir: Path):
        """Asegurar que uvicorn está instalado"""
        pip_list = self.cmd.run(f'cd {app_dir} && .venv/bin/pip list', check=False)
        if pip_list and "uvicorn" not in pip_list.lower():
            print(Colors.info("Uvicorn no encontrado, instalando..."))
            self.cmd.run(f"cd {app_dir} && .venv/bin/pip install uvicorn[standard]", check=False)
        else:
            print(Colors.success("Uvicorn ya está instalado"))

    def _rebuild_application(self, app_dir: Path, app_config: AppConfig) -> bool:
        """
        Reconstruir aplicación en directorio temporal (instalación limpia completa)
        
        Este método se usa durante actualizaciones para construir la nueva versión
        en un directorio temporal antes de hacer el swap atómico.
        """
        try:
            if app_config.app_type in ["nextjs", "node"]:
                print(Colors.info("🧹 Limpiando instalación anterior..."))
                
                # CRÍTICO: Limpiar node_modules y package-lock.json para evitar problemas de rutas
                node_modules = app_dir / "node_modules"
                package_lock = app_dir / "package-lock.json"
                next_cache = app_dir / ".next"
                
                # Eliminar node_modules si existe
                if node_modules.exists():
                    if self.verbose:
                        print(Colors.info("  Eliminando node_modules..."))
                    shutil.rmtree(node_modules)
                
                # Eliminar package-lock.json si existe
                if package_lock.exists():
                    if self.verbose:
                        print(Colors.info("  Eliminando package-lock.json..."))
                    package_lock.unlink()
                
                # Eliminar .next si existe (cache de Next.js)
                if next_cache.exists():
                    if self.verbose:
                        print(Colors.info("  Eliminando caché .next..."))
                    shutil.rmtree(next_cache)
                
                if self.verbose:
                    print(Colors.success("  ✓ Limpieza completada"))
                
                # Instalación limpia de dependencias
                print(Colors.info("📦 Instalando dependencias npm (instalación limpia)..."))
                install_result = self.cmd.run(
                    f"cd {app_dir} && npm install --production=false",
                    check=False
                )
                
                if not install_result:
                    print(Colors.error("❌ Error instalando dependencias npm"))
                    return False
                
                # Verificar que node_modules se creó correctamente
                if not node_modules.exists():
                    print(Colors.error("❌ node_modules no se creó correctamente"))
                    return False
                
                if self.verbose:
                    print(Colors.success("  ✓ Dependencias instaladas correctamente"))

                # Solo hacer build si es Next.js
                if app_config.app_type == "nextjs":
                    print(Colors.info("🔨 Construyendo aplicación Next.js..."))
                    
                    # Configurar permisos antes del build
                    node_modules_bin = app_dir / "node_modules" / ".bin"
                    if node_modules_bin.exists():
                        self.cmd.run(f"chmod -R +x {node_modules_bin}", check=False)
                        if self.verbose:
                            print(Colors.info("  Permisos configurados para node_modules/.bin/"))
                    
                    # Construir con variables de entorno necesarias
                    build_cmd = app_config.build_command or "npm run build"
                    env_vars = "NODE_ENV=production NEXT_TELEMETRY_DISABLED=1"
                    
                    build_result = self.cmd.run(
                        f"cd {app_dir} && {env_vars} {build_cmd}",
                        check=False
                    )
                    
                    if not build_result:
                        print(Colors.error("❌ Error construyendo aplicación Next.js"))
                        return False
                    
                    # Verificar que .next se creó
                    if not next_cache.exists():
                        print(Colors.error("❌ Build no generó directorio .next"))
                        return False
                    
                    # Verificar archivos críticos del build
                    build_id = next_cache / "BUILD_ID"
                    build_manifest = next_cache / "build-manifest.json"
                    
                    if not build_id.exists():
                        print(Colors.warning("⚠️  BUILD_ID no encontrado, generando..."))
                        import uuid
                        build_id.write_text(str(uuid.uuid4())[:8])
                    
                    if self.verbose:
                        print(Colors.success("  ✓ Build completado exitosamente"))
                
                # Configurar permisos finales de ejecución
                node_modules_bin = app_dir / "node_modules" / ".bin"
                if node_modules_bin.exists():
                    self.cmd.run(f"chmod -R +x {node_modules_bin}", check=False)
                    if self.verbose:
                        print(Colors.info("  Permisos finales configurados"))

            elif app_config.app_type == "fastapi":
                print(Colors.info("🐍 Configurando aplicación FastAPI..."))
                
                # Limpiar entorno virtual anterior si existe
                venv_dir = app_dir / ".venv"
                if venv_dir.exists():
                    if self.verbose:
                        print(Colors.info("  Eliminando entorno virtual anterior..."))
                    shutil.rmtree(venv_dir)
                
                # Crear nuevo entorno virtual
                print(Colors.info("  Creando entorno virtual Python..."))
                venv_result = self.cmd.run(f"cd {app_dir} && python3 -m venv .venv", check=False)
                if not venv_result:
                    print(Colors.error("❌ Error creando entorno virtual"))
                    return False

                # Instalar dependencias
                requirements_file = app_dir / "requirements.txt"
                if requirements_file.exists():
                    print(Colors.info("  Instalando dependencias desde requirements.txt..."))
                    install_deps = self.cmd.run(
                        f"cd {app_dir} && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt",
                        check=False,
                    )
                    if not install_deps:
                        print(Colors.error("❌ Error instalando dependencias de Python"))
                        return False
                else:
                    print(Colors.info("  Instalando dependencias básicas..."))
                    install_basic = self.cmd.run(
                        f"cd {app_dir} && .venv/bin/pip install --upgrade pip && .venv/bin/pip install fastapi uvicorn[standard]",
                        check=False,
                    )
                    if not install_basic:
                        print(Colors.error("❌ Error instalando dependencias básicas"))
                        return False

                # Configurar permisos del entorno virtual
                self.cmd.run(f"chmod +x {app_dir}/.venv/bin/*", check=False)
                
                if self.verbose:
                    print(Colors.success("  ✓ Aplicación FastAPI configurada"))

            print(Colors.success("✅ Aplicación reconstruida exitosamente en directorio temporal"))
            return True

        except Exception as e:
            print(Colors.error(f"❌ Error reconstruyendo aplicación: {e}"))
            if self.verbose:
                import traceback
                print(Colors.error(f"Detalles:\n{traceback.format_exc()}"))
            return False

    def _rebuild_nextjs_in_place(self, app_dir: Path, app_config: AppConfig) -> bool:
        """
        Reconstruir aplicación Next.js directamente en su carpeta (sin mover node_modules)
        
        Este método se usa durante actualizaciones para construir la nueva versión
        sin tener problemas con enlaces simbólicos en node_modules.
        """
        try:
            print(Colors.info("🧹 Preparando actualización de Next.js..."))
            
            next_cache = app_dir / ".next"
            package_lock = app_dir / "package-lock.json"
            
            # Eliminar .next si existe (cache de Next.js antiguo)
            if next_cache.exists():
                if self.verbose:
                    print(Colors.info("  Eliminando caché .next anterior..."))
                shutil.rmtree(next_cache)
            
            # NO eliminamos node_modules ni package-lock.json para preservar enlaces simbólicos
            # Solo actualizamos las dependencias si hay cambios en package.json
            
            print(Colors.info("📦 Actualizando dependencias npm (preservando enlaces)..."))
            # Usar npm install que actualizará solo lo necesario
            install_result = self.cmd.run(
                f"cd {app_dir} && npm install --production=false",
                check=False
            )
            
            if not install_result:
                print(Colors.error("❌ Error actualizando dependencias npm"))
                return False
            
            node_modules = app_dir / "node_modules"
            if not node_modules.exists():
                print(Colors.error("❌ node_modules no existe después de npm install"))
                return False
            
            if self.verbose:
                print(Colors.success("  ✓ Dependencias actualizadas correctamente"))

            # Hacer build de Next.js
            print(Colors.info("🔨 Construyendo aplicación Next.js..."))
            
            # Configurar permisos antes del build
            node_modules_bin = app_dir / "node_modules" / ".bin"
            if node_modules_bin.exists():
                self.cmd.run(f"chmod -R +x {node_modules_bin}", check=False)
                if self.verbose:
                    print(Colors.info("  Permisos configurados para node_modules/.bin/"))
            
            # Construir con variables de entorno necesarias
            build_cmd = app_config.build_command or "npm run build"
            env_vars = "NODE_ENV=production NEXT_TELEMETRY_DISABLED=1"
            
            build_result = self.cmd.run(
                f"cd {app_dir} && {env_vars} {build_cmd}",
                check=False
            )
            
            if not build_result:
                print(Colors.error("❌ Error construyendo aplicación Next.js"))
                return False
            
            # Verificar que .next se creó
            if not next_cache.exists():
                print(Colors.error("❌ Build no generó directorio .next"))
                return False
            
            # Verificar archivos críticos del build
            build_id = next_cache / "BUILD_ID"
            
            if not build_id.exists():
                print(Colors.warning("⚠️  BUILD_ID no encontrado, generando..."))
                import uuid
                build_id.write_text(str(uuid.uuid4())[:8])
            
            if self.verbose:
                print(Colors.success("  ✓ Build completado exitosamente"))
            
            # Configurar permisos finales de ejecución
            if node_modules_bin.exists():
                self.cmd.run(f"chmod -R +x {node_modules_bin}", check=False)
                if self.verbose:
                    print(Colors.info("  Permisos finales configurados"))

            print(Colors.success("✅ Aplicación Next.js reconstruida exitosamente"))
            return True

        except Exception as e:
            print(Colors.error(f"❌ Error reconstruyendo Next.js: {e}"))
            if self.verbose:
                import traceback
                print(Colors.error(f"Detalles:\n{traceback.format_exc()}"))
            return False

    def _finalize_deployment(self, app_dir: Path, temp_dir: Path) -> bool:
        """Finalizar despliegue moviendo archivos y configurando permisos"""
        try:
            # Mover directorio temporal a final
            shutil.move(temp_dir, app_dir)

            # Configurar git safe directory si es necesario
            if (app_dir / ".git").exists():
                self._configure_git_safe_directory(app_dir)

            # Configurar permisos
            self._set_permissions(app_dir)

            return True

        except Exception as e:
            print(Colors.error(f"Error finalizando despliegue: {e}"))
            return False

    def _set_permissions(self, app_dir: Path):
        """Configurar permisos de directorio de forma optimizada"""
        # Solo cambiar el propietario del directorio raíz y directorios críticos
        # Los archivos en node_modules, .next, dist, etc. no necesitan cambios
        
        if self.verbose:
            print(Colors.info("  Configurando permisos (optimizado)..."))
        
        # Cambiar propietario del directorio raíz solamente
        self.cmd.run_sudo(f"chown www-data:www-data {app_dir}", check=False)
        
        # Cambiar propietario solo de directorios críticos, no recursivamente en todo
        critical_dirs = [
            "public",
            "static",
            ".next",
            "dist",
            "build",
            "out",
            ".output"  # Para Nuxt/Nitro
        ]
        
        for dir_name in critical_dirs:
            dir_path = app_dir / dir_name
            if dir_path.exists():
                # Solo chown en el directorio, los archivos internos ya tienen permisos correctos
                self.cmd.run_sudo(f"chown -R www-data:www-data {dir_path}", check=False)
        
        # Configurar permisos de ejecución solo donde es necesario
        node_modules_bin = app_dir / "node_modules" / ".bin"
        if node_modules_bin.exists():
            self.cmd.run_sudo(f"chmod -R +x {node_modules_bin}", check=False)
            if self.verbose:
                print(Colors.info("  Permisos de ejecución para node_modules/.bin/"))
        
        # Para aplicaciones Python (FastAPI)
        venv_bin = app_dir / ".venv" / "bin"
        if venv_bin.exists():
            self.cmd.run_sudo(f"chmod -R +x {venv_bin}", check=False)
            if self.verbose:
                print(Colors.info("  Permisos de ejecución para .venv/bin/"))
        
        if self.verbose:
            print(Colors.success("  Permisos configurados (rápido)"))

    def _configure_git_safe_directory(self, directory: Path):
        """Configurar directorio como seguro para Git"""
        try:
            if self.verbose:
                print(Colors.info(f"🔧 Configurando directorio Git seguro: {directory}"))
            
            # Configurar directorio como seguro para Git (sin sudo porque ya somos root)
            result = self.cmd.run(
                f"git config --global --get-all safe.directory | grep -x {directory}",
                check=False,
            )

            if not result or str(directory) not in result:
                self.cmd.run(f"git config --global --add safe.directory {directory}")
                if self.verbose:
                    print(Colors.success(f"✅ Directorio {directory} configurado como seguro para Git"))
                else:
                    print(Colors.info(f"Directorio {directory} configurado como seguro para Git"))
            else:
                if self.verbose:
                    print(Colors.info(f"ℹ️  Directorio {directory} ya está configurado como seguro para Git"))
                else:
                    print(Colors.info(f"Directorio {directory} ya está configurado como seguro para Git"))

        except Exception as e:
            if self.verbose:
                print(Colors.warning(f"❌ Error configurando directorio Git seguro: {e}"))
                import traceback
                print(Colors.warning(f"🔍 Detalles: {traceback.format_exc()}"))
            else:
                print(Colors.warning(f"Error configurando directorio Git seguro: {e}"))

    def _restore_from_backup(self, domain: str, app_dir: Path, backup_dir: Path):
        """Restaurar aplicación desde backup en caso de error"""
        try:
            print(Colors.warning("Restaurando desde backup..."))
            
            # Eliminar directorio corrupto
            if app_dir.exists():
                shutil.rmtree(app_dir)
            
            # Restaurar desde backup
            if backup_dir.exists():
                shutil.copytree(backup_dir, app_dir)
                self._set_permissions(app_dir)
                print(Colors.success("Aplicación restaurada desde backup"))
                
                # Eliminar backup después de restaurar exitosamente
                print(Colors.info("Eliminando backup después de restauración..."))
                shutil.rmtree(backup_dir)
            else:
                print(Colors.error("No se encontró backup para restaurar"))
                
        except Exception as e:
            print(Colors.error(f"Error restaurando desde backup: {e}"))

    def _cleanup_failed_deployment(self, domain: str, temp_dir: Path):
        """Limpiar recursos de despliegue fallido"""
        try:
            print(Colors.info("Limpiando recursos de despliegue fallido..."))

            # Restaurar backup si existe
            backup_dir = self.apps_dir / f"{domain}_backup"
            app_dir = self.apps_dir / domain

            if backup_dir.exists():
                print(Colors.info("Realizando rollback..."))
                if app_dir.exists():
                    shutil.rmtree(app_dir)
                shutil.copytree(backup_dir, app_dir)
                self._set_permissions(app_dir)
                print(Colors.warning("Rollback completado"))

            # Limpiar directorio temporal
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

            print(Colors.info("Limpieza completada"))

        except Exception as e:
            print(Colors.warning(f"Error en limpieza: {e}"))
