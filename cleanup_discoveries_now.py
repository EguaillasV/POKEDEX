#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.infrastructure.persistence.models import DiscoveryModel

# Eliminar todos los descubrimientos
deleted_count, _ = DiscoveryModel.objects.all().delete()

print(f"✓ Descubrimientos eliminados: {deleted_count}")

# Verificar resultado
remaining = DiscoveryModel.objects.count()
print(f"Descubrimientos restantes: {remaining}")
