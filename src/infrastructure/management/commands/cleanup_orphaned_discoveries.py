#!/usr/bin/env python
"""
Signal handler para Django que ejecuta la limpieza de descubrimientos 
huérfanos automáticamente al iniciar.
"""
import os
import django
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Limpia descubrimientos huérfanos (sin archivos de imagen)'

    def handle(self, *args, **options):
        from src.infrastructure.persistence.models import DiscoveryModel
        
        discoveries = DiscoveryModel.objects.all()
        thumbnails_dir = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        files = os.listdir(thumbnails_dir) if os.path.exists(thumbnails_dir) else []
        
        deleted_count = 0
        repaired_count = 0
        
        for discovery in discoveries:
            if discovery.thumbnail_url:
                filename = discovery.thumbnail_url.split('/')[-1]
                file_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails', filename)
                
                if not os.path.exists(file_path):
                    if files:
                        # Asignar un archivo disponible
                        new_filename = files[0]
                        new_url = f"/media/thumbnails/{new_filename}"
                        discovery.thumbnail_url = new_url
                        discovery.save()
                        repaired_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Reparado: {discovery.id} -> {new_filename}')
                        )
                    else:
                        # No hay archivos disponibles, eliminar el descubrimiento
                        discovery.delete()
                        deleted_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'❌ Eliminado: {discovery.id}')
                        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Limpieza completada: {repaired_count} reparados, {deleted_count} eliminados'
            )
        )
