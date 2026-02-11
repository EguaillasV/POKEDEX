#!/usr/bin/env python
"""
Script to delete all user discoveries from the database.
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.infrastructure.persistence.models import DiscoveryModel

def cleanup_all_discoveries():
    """Delete all discoveries from the database."""
    initial_count = DiscoveryModel.objects.count()
    print(f"Descubrimientos antes: {initial_count}")
    
    # Delete all discoveries
    DiscoveryModel.objects.all().delete()
    
    final_count = DiscoveryModel.objects.count()
    print(f"Descubrimientos después: {final_count}")
    print(f"Eliminados: {initial_count - final_count}")
    print("✓ Todas las galerías de usuarios están ahora en cero")

if __name__ == '__main__':
    cleanup_all_discoveries()
