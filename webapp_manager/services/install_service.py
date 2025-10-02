"""
Servicio para la instalación y configuración inicial del sistema
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from ..utils import Colors
from .cmd_service import CmdService


class InstallService:
    """Servicio para instalación y configuración inicial"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.cmd = CmdService(verbose=verbose)
        
        # Directorios importantes
        self.apps_dir = Path("/apps")
        self.maintenance_dir = self.apps_dir / "maintenance"
        self.nginx_sites_available = Path("/etc/nginx/sites-available")
        self.nginx_sites_enabled = Path("/etc/nginx/sites-enabled")
        self.nginx_default_site = self.nginx_sites_enabled / "default"
    
    def setup_maintenance_pages(self) -> bool:
        """
        Configurar páginas de mantenimiento del sistema
        Copia los HTML de mantenimiento a /apps/maintenance/
        """
        try:
            if self.verbose:
                print(Colors.info("🔧 Configurando páginas de mantenimiento..."))
            
            # Crear directorio /apps si no existe
            if not self.apps_dir.exists():
                if self.verbose:
                    print(Colors.info(f"Creando directorio: {self.apps_dir}"))
                self.cmd.run_sudo(f"mkdir -p {self.apps_dir}")
            
            # Crear directorio de mantenimiento
            if not self.maintenance_dir.exists():
                if self.verbose:
                    print(Colors.info(f"Creando directorio: {self.maintenance_dir}"))
                self.cmd.run_sudo(f"mkdir -p {self.maintenance_dir}")
            
            # Obtener el directorio de instalación (donde están los templates)
            install_dir = Path(__file__).parent.parent.parent
            templates_source = install_dir / "apps" / "maintenance"
            
            if not templates_source.exists():
                print(Colors.warning(f"⚠️  No se encontraron templates en: {templates_source}"))
                print(Colors.info("Los templates deben estar en el directorio apps/maintenance/"))
                return False
            
            # Copiar archivos HTML
            html_files = ["maintenance.html", "error502.html", "updating.html"]
            copied_files = 0
            
            for html_file in html_files:
                source_file = templates_source / html_file
                dest_file = self.maintenance_dir / html_file
                
                if source_file.exists():
                    try:
                        if self.verbose:
                            print(Colors.info(f"📄 Copiando {html_file}..."))
                        
                        # Copiar archivo con sudo
                        result = self.cmd.run_sudo(f"cp {source_file} {dest_file}")
                        
                        if result is not None:
                            # Establecer permisos apropiados
                            self.cmd.run_sudo(f"chmod 644 {dest_file}")
                            copied_files += 1
                            
                            if self.verbose:
                                print(Colors.success(f"✅ {html_file} copiado correctamente"))
                        else:
                            print(Colors.warning(f"⚠️  Error copiando {html_file}"))
                    
                    except Exception as e:
                        print(Colors.warning(f"⚠️  Error copiando {html_file}: {e}"))
                else:
                    print(Colors.warning(f"⚠️  No se encontró: {html_file}"))
            
            if copied_files > 0:
                # Establecer permisos del directorio
                self.cmd.run_sudo(f"chmod 755 {self.maintenance_dir}")
                self.cmd.run_sudo(f"chown -R www-data:www-data {self.maintenance_dir}")
                
                print(Colors.success(f"✅ {copied_files} páginas de mantenimiento configuradas en {self.maintenance_dir}"))
                return True
            else:
                print(Colors.error("❌ No se pudo copiar ninguna página de mantenimiento"))
                return False
                
        except Exception as e:
            print(Colors.error(f"❌ Error configurando páginas de mantenimiento: {e}"))
            return False
    
    def check_nginx_default_site(self) -> bool:
        """
        Verificar si existe el sitio default de nginx y manejarlo
        Retorna True si todo está OK, False si hay problemas
        """
        try:
            if self.verbose:
                print(Colors.info("🔍 Verificando sitio default de nginx..."))
            
            # Verificar si existe el sitio default habilitado
            if self.nginx_default_site.exists():
                if self.verbose:
                    print(Colors.warning("⚠️  Encontrado sitio default de nginx habilitado"))
                
                # Leer el contenido para verificar si es el default original
                try:
                    with open(self.nginx_default_site, 'r') as f:
                        content = f.read()
                    
                    # Verificar si es la configuración default estándar
                    is_default_config = (
                        "Welcome to nginx" in content or 
                        "default_server" in content or
                        "/var/www/html" in content
                    )
                    
                    if is_default_config:
                        print(Colors.warning("⚠️  El sitio default de nginx puede interferir con webapp-manager"))
                        print(Colors.info("💡 Se recomienda deshabilitarlo con:"))
                        print(Colors.info("   sudo rm /etc/nginx/sites-enabled/default"))
                        print(Colors.info("   sudo nginx -s reload"))
                        return False
                    else:
                        if self.verbose:
                            print(Colors.info("✅ El sitio default parece ser una configuración personalizada"))
                        return True
                        
                except Exception as e:
                    print(Colors.warning(f"⚠️  No se pudo leer el sitio default: {e}"))
                    return True
            else:
                if self.verbose:
                    print(Colors.success("✅ No hay sitio default habilitado"))
                return True
                
        except Exception as e:
            print(Colors.error(f"❌ Error verificando sitio default: {e}"))
            return False
    
    def disable_nginx_default_site(self) -> bool:
        """
        Deshabilitar el sitio default de nginx
        """
        try:
            if not self.nginx_default_site.exists():
                if self.verbose:
                    print(Colors.info("ℹ️  El sitio default ya está deshabilitado"))
                return True
            
            print(Colors.info("🔧 Deshabilitando sitio default de nginx..."))
            
            # Hacer backup del sitio default
            backup_path = self.nginx_sites_available / "default.backup"
            if not backup_path.exists():
                self.cmd.run_sudo(f"cp {self.nginx_default_site} {backup_path}")
                if self.verbose:
                    print(Colors.info(f"📦 Backup creado en: {backup_path}"))
            
            # Deshabilitar el sitio
            result = self.cmd.run_sudo(f"rm {self.nginx_default_site}")
            
            if result is not None:
                # Recargar nginx
                reload_result = self.cmd.run_sudo("nginx -s reload")
                
                if reload_result is not None:
                    print(Colors.success("✅ Sitio default deshabilitado correctamente"))
                    return True
                else:
                    print(Colors.error("❌ Error recargando nginx"))
                    return False
            else:
                print(Colors.error("❌ Error deshabilitando sitio default"))
                return False
                
        except Exception as e:
            print(Colors.error(f"❌ Error deshabilitando sitio default: {e}"))
            return False
    
    def verify_system_requirements(self) -> bool:
        """
        Verificar que el sistema cumple con los requisitos
        """
        try:
            if self.verbose:
                print(Colors.info("🔍 Verificando requisitos del sistema..."))
            
            requirements_met = True
            
            # Verificar nginx
            if not self.cmd.test_command_exists("nginx"):
                print(Colors.error("❌ nginx no está instalado"))
                print(Colors.info("💡 Instalar con: sudo apt-get install nginx"))
                requirements_met = False
            else:
                if self.verbose:
                    print(Colors.success("✅ nginx instalado"))
            
            # Verificar systemctl
            if not self.cmd.test_command_exists("systemctl"):
                print(Colors.error("❌ systemctl no está disponible"))
                requirements_met = False
            else:
                if self.verbose:
                    print(Colors.success("✅ systemctl disponible"))
            
            # Verificar Python 3
            if not self.cmd.test_command_exists("python3"):
                print(Colors.error("❌ python3 no está instalado"))
                requirements_met = False
            else:
                if self.verbose:
                    print(Colors.success("✅ python3 instalado"))
            
            # Verificar permisos de root
            user_id = self.cmd.run("id -u", check=False)
            if user_id and user_id.strip() != "0":
                if self.verbose:
                    print(Colors.warning("⚠️  No se está ejecutando como root"))
                    print(Colors.info("💡 Algunas operaciones requerirán sudo"))
            else:
                if self.verbose:
                    print(Colors.success("✅ Ejecutando con permisos de root"))
            
            return requirements_met
            
        except Exception as e:
            print(Colors.error(f"❌ Error verificando requisitos: {e}"))
            return False
    
    def run_initial_setup(self) -> bool:
        """
        Ejecutar configuración inicial completa
        """
        try:
            print(Colors.bold("\n🚀 Iniciando configuración inicial de webapp-manager\n"))
            
            # Verificar requisitos
            if not self.verify_system_requirements():
                print(Colors.error("\n❌ Los requisitos del sistema no se cumplen"))
                return False
            
            # Configurar páginas de mantenimiento
            if not self.setup_maintenance_pages():
                print(Colors.warning("\n⚠️  No se pudieron configurar las páginas de mantenimiento"))
                print(Colors.info("💡 Esto puede afectar el funcionamiento durante actualizaciones"))
            
            # Verificar sitio default de nginx
            if not self.check_nginx_default_site():
                print(Colors.warning("\n⚠️  Se detectaron posibles conflictos con el sitio default de nginx"))
                
                # Preguntar si se debe deshabilitar (solo si hay TTY)
                if os.isatty(0):
                    response = input("¿Desea deshabilitar el sitio default? (s/n): ")
                    if response.lower() in ['s', 'si', 'y', 'yes']:
                        self.disable_nginx_default_site()
            
            print(Colors.success("\n✅ Configuración inicial completada\n"))
            return True
            
        except Exception as e:
            print(Colors.error(f"\n❌ Error en configuración inicial: {e}\n"))
            return False
