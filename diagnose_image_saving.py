#!/usr/bin/env python
"""
Script de diagnóstico para verificar el proceso de guardado de imágenes.
"""
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.domain.value_objects import ImageFrame
from src.infrastructure.storage import get_image_storage
import base64

print("=" * 70)
print("DIAGNÓSTICO DE GUARDADO DE IMÁGENES")
print("=" * 70)

# Verificar configuración de rutas
print(f"\n✓ MEDIA_ROOT: {settings.MEDIA_ROOT}")
print(f"✓ MEDIA_URL: {settings.MEDIA_URL}")

thumbnails_dir = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
print(f"✓ Directorio de thumbnails: {thumbnails_dir}")
print(f"✓ ¿Existe el directorio?: {os.path.exists(thumbnails_dir)}")

# Crear una imagen de prueba
print("\n" + "-" * 70)
print("PRUEBA 1: Crear imagen de prueba simple")
print("-" * 70)

try:
    # Crear una pequeña imagen PNG de prueba (1x1 píxel rojo)
    png_data = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=='
    )
    print(f"✓ Imagen de prueba creada: {len(png_data)} bytes")
    
    # Intentar guardar
    image_storage = get_image_storage()
    
    # Convertir a ImageFrame
    frame = ImageFrame(data=png_data, format='JPEG')
    print(f"✓ ImageFrame creado: {frame}")
    print(f"✓ Image data length: {len(frame.data)} bytes")
    
    # Intentar guardar
    filename = "test_diagnosis.jpg"
    print(f"\n📝 Intentando guardar como: {filename}")
    
    url = image_storage.save_thumbnail(frame, filename)
    print(f"✓ URL retornada: {url}")
    
    # Verificar que el archivo existe
    file_path = os.path.join(thumbnails_dir, filename)
    exists = os.path.exists(file_path)
    print(f"✓ ¿Existe el archivo en disco?: {exists}")
    
    if exists:
        size = os.path.getsize(file_path)
        print(f"✓ Tamaño del archivo: {size} bytes")
    else:
        print(f"❌ ERROR: El archivo NO existe en: {file_path}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Listar archivos existentes
print("\n" + "-" * 70)
print("ARCHIVOS ACTUALES EN THUMBNAILS")
print("-" * 70)

if os.path.exists(thumbnails_dir):
    files = os.listdir(thumbnails_dir)
    print(f"\nTotal de archivos: {len(files)}\n")
    for f in sorted(files)[:5]:  # Mostrar solo los primeros 5
        file_path = os.path.join(thumbnails_dir, f)
        size = os.path.getsize(file_path)
        print(f"  ✓ {f} ({size} bytes)")
else:
    print(f"❌ La carpeta no existe: {thumbnails_dir}")
