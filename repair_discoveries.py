#!/usr/bin/env python
"""
Script para reparar descubrimientos asignando archivos existentes.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.infrastructure.persistence.models import DiscoveryModel
from django.conf import settings

print("=" * 70)
print("REPARANDO DESCUBRIMIENTOS HUÉRFANOS")
print("=" * 70)

# Obtener descubrimientos
discoveries = DiscoveryModel.objects.all()

# Obtener archivos disponibles
thumbnails_dir = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
files = os.listdir(thumbnails_dir) if os.path.exists(thumbnails_dir) else []

print(f"\nTotal de descubrimientos: {discoveries.count()}")
print(f"Total de archivos disponibles: {len(files)}\n")

repaired = 0

for i, discovery in enumerate(discoveries):
    if discovery.thumbnail_url:
        filename = discovery.thumbnail_url.split('/')[-1]
        file_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails', filename)
        
        if not os.path.exists(file_path):
            print(f"❌ Descubrimiento {i+1} es huérfano: {filename}")
            
            # Si hay archivos disponibles, asignar el primero
            if files:
                new_filename = files[0]
                new_url = f"/media/thumbnails/{new_filename}"
                discovery.thumbnail_url = new_url
                discovery.save()
                print(f"   ✓ Reparado con: {new_filename}")
                repaired += 1
            else:
                print(f"   ✗ No hay archivos disponibles para asignar")
                discovery.delete()
                print(f"   ✓ Descubrimiento eliminado")
        else:
            print(f"✓ Descubrimiento {i+1} está OK: {filename}")

print("\n" + "=" * 70)
print(f"Total de descubrimientos reparados: {repaired}")
print("=" * 70)
