#!/usr/bin/env python
"""
Script para limpiar todos los descubrimientos y sus imágenes asociadas
"""
import os
import sys
import django

# Agregar el directorio padre al path de Python
project_root = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(project_root)
sys.path.insert(0, parent_dir)
sys.path.insert(0, project_root)

# Cambiar al directorio del proyecto
os.chdir(parent_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'POKEDEX.config.settings')
try:
    django.setup()
except Exception as e:
    # Intentar con otra configuración
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

from src.infrastructure.persistence.models import DiscoveryModel, SessionModel
from django.conf import settings

# Obtener conteo antes
discoveries_count = DiscoveryModel.objects.count()
sessions_count = SessionModel.objects.count()

print(f"📊 Estado actual:")
print(f"   Descubrimientos: {discoveries_count}")
print(f"   Sesiones: {sessions_count}")

# Eliminar todos los descubrimientos
if discoveries_count > 0:
    DiscoveryModel.objects.all().delete()
    print(f"\n✅ Se eliminaron {discoveries_count} descubrimientos")

# Eliminar sesiones vacías (sin descubrimientos)
empty_sessions = SessionModel.objects.filter(discoveries__isnull=True).count()
SessionModel.objects.filter(discoveries__isnull=True).delete()
print(f"✅ Se eliminaron {empty_sessions} sesiones vacías")

# Limpiar carpeta de thumbnails
thumbnails_dir = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
if os.path.exists(thumbnails_dir):
    files_deleted = 0
    for filename in os.listdir(thumbnails_dir):
        filepath = os.path.join(thumbnails_dir, filename)
        try:
            if os.path.isfile(filepath):
                os.remove(filepath)
                print(f"🗑️  Eliminado: {filename}")
                files_deleted += 1
        except Exception as e:
            print(f"⚠️  Error eliminando {filename}: {e}")
    print(f"✅ Se eliminaron {files_deleted} archivos de imágenes")
else:
    print(f"ℹ️  La carpeta de thumbnails no existe")

# Verificar estado final
final_discoveries = DiscoveryModel.objects.count()
final_sessions = SessionModel.objects.count()

print(f"\n📊 Estado final:")
print(f"   Descubrimientos: {final_discoveries}")
print(f"   Sesiones: {final_sessions}")
print(f"\n✨ Base de datos limpiada correctamente")
