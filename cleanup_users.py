#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from src.infrastructure.persistence.models import DiscoveryModel

# Encontrar todos los usuarios que tienen descubrimientos
users_with_discoveries = set(
    DiscoveryModel.objects.values_list('user_id', flat=True).distinct()
)

print(f"Encontrados {len(users_with_discoveries)} usuarios con descubrimientos")

# Eliminar estos usuarios
if users_with_discoveries:
    deleted_count = 0
    for user_id in users_with_discoveries:
        try:
            user = User.objects.get(id=user_id)
            username = user.username
            User.objects.filter(id=user_id).delete()
            print(f"✓ Eliminado usuario: {username}")
            deleted_count += 1
        except User.DoesNotExist:
            print(f"⚠ Usuario con ID {user_id} no encontrado")
    
    print(f"\n✓ Total de usuarios eliminados: {deleted_count}")
else:
    print("No hay usuarios con descubrimientos para eliminar")

# Verificar resultado
remaining_discoveries = DiscoveryModel.objects.count()
remaining_users = User.objects.exclude(is_superuser=True).count()

print(f"\nVerificación:")
print(f"Descubrimientos restantes: {remaining_discoveries}")
print(f"Usuarios normales restantes: {remaining_users}")
