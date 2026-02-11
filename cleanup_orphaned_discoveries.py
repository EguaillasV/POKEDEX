#!/usr/bin/env python
"""
Script para encontrar y eliminar descubrimientos huérfanos
(aquellos cuyo archivo de thumbnail no existe en el disco).
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.infrastructure.persistence.models import DiscoveryModel
from django.conf import settings

def cleanup_orphaned_discoveries():
    """Eliminar descubrimientos cuyo archivo de thumbnail no existe."""
    
    discoveries = DiscoveryModel.objects.all()
    orphaned_count = 0
    
    print(f"Total de descubrimientos: {discoveries.count()}")
    print("-" * 50)
    
    for discovery in discoveries:
        # Extraer el nombre del archivo del thumbnail_url
        if discovery.thumbnail_url:
            # El thumbnail_url es algo como: media/thumbnails/upload_xxx.jpg
            # Necesitamos obtener solo el nombre del archivo
            filename = discovery.thumbnail_url.split('/')[-1]
            
            # Construir la ruta completa
            file_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails', filename)
            
            # Verificar si el archivo existe
            if not os.path.exists(file_path):
                print(f"❌ Descubrimiento huérfano encontrado:")
                print(f"   ID: {discovery.id}")
                print(f"   Animal: {discovery.animal.name}")
                print(f"   Thumbnail URL: {discovery.thumbnail_url}")
                print(f"   Usuario: {discovery.user.username if discovery.user else 'N/A'}")
                
                # Eliminar el descubrimiento
                discovery.delete()
                orphaned_count += 1
                print(f"   ✓ Eliminado\n")
    
    print("-" * 50)
    print(f"Total de descubrimientos huérfanos eliminados: {orphaned_count}")
    print("✓ Limpieza completada")

if __name__ == '__main__':
    cleanup_orphaned_discoveries()
