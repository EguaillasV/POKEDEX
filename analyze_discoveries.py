#!/usr/bin/env python
"""
Script para revisar los descubrimientos y sus archivos correspondientes.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.infrastructure.persistence.models import DiscoveryModel
from django.conf import settings

print("=" * 70)
print("ANÁLISIS DE DESCUBRIMIENTOS Y ARCHIVOS")
print("=" * 70)

discoveries = DiscoveryModel.objects.all()
print(f"\nTotal de descubrimientos en BD: {discoveries.count()}\n")

for discovery in discoveries:
    print(f"ID Descubrimiento: {discovery.id}")
    print(f"  Animal: {discovery.animal.name}")
    print(f"  Usuario: {discovery.user.username if discovery.user else 'N/A'}")
    print(f"  Thumbnail URL guardada: {discovery.thumbnail_url}")
    
    if discovery.thumbnail_url:
        # Extraer el nombre del archivo
        filename = discovery.thumbnail_url.split('/')[-1]
        file_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails', filename)
        
        exists = os.path.exists(file_path)
        print(f"  Nombre de archivo: {filename}")
        print(f"  Ruta completa: {file_path}")
        print(f"  ¿Existe el archivo?: {'✓ SÍ' if exists else '✗ NO'}")
    
    print()

print("=" * 70)
print("ARCHIVOS EXISTENTES EN media/thumbnails/")
print("=" * 70)
thumbnails_dir = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
if os.path.exists(thumbnails_dir):
    files = os.listdir(thumbnails_dir)
    print(f"\nTotal de archivos en disco: {len(files)}\n")
    for f in sorted(files):
        file_path = os.path.join(thumbnails_dir, f)
        size = os.path.getsize(file_path)
        print(f"  {f} ({size} bytes)")
else:
    print(f"\n❌ Carpeta no existe: {thumbnails_dir}")
