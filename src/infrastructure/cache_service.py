#!/usr/bin/env python
"""
Sistema de caché para descripciones de animales
Guarda descripciones nuevas generadas por OpenRouter para futuras consultas
"""

import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

CACHE_FILE = Path(__file__).parent / 'descriptions_cache.json'

def load_cache():
    """Cargar caché de descripciones"""
    if not CACHE_FILE.exists():
        return {}
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Error cargando caché: {e}")
        return {}

def save_to_cache(animal_name: str, data: dict):
    """Guardar descripción al caché"""
    try:
        cache = load_cache()
        cache[animal_name.lower()] = data
        
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Descripción guardada en caché: {animal_name}")
    except Exception as e:
        logger.error(f"Error guardando caché: {e}")

def get_from_cache(animal_name: str):
    """Obtener descripción del caché"""
    cache = load_cache()
    return cache.get(animal_name.lower())

def has_in_cache(animal_name: str) -> bool:
    """Verificar si está en caché"""
    cache = load_cache()
    return animal_name.lower() in cache
