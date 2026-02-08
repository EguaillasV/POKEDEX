"""
Generate animal descriptions using OpenRouter (Claude/Mistral)
This script generates natural descriptions for animals that don't have them.

Usage: python scripts/generate_animal_descriptions.py
"""
import os
import sys
import django
import requests
import json

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.infrastructure.persistence.models import AnimalModel

# OpenRouter configuration
# Prefer environment variable, fallback to the user-provided key (one-time test)
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY') or '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'
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def generate_description(animal_name: str, scientific_name: str) -> str:
    """
    Generate a description for an animal using OpenRouter/Mistral.
    """
    prompt = f"""Genera una descripción científica pero accesible en español para el siguiente animal:
- Nombre común: {animal_name}
- Nombre científico: {scientific_name}

La descripción debe:
1. Ser de 2-3 oraciones
2. Describir características físicas y comportamentales principales
3. Ser educativa pero comprensible para el público general
4. Estar completamente en español
5. Ser única y diferente a otras descripciones

Responde SOLO con la descripción, sin explicaciones adicionales."""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    # Use the OpenRouter message format similar to the sample in iamuestra.py
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ],
        "temperature": 0.7,
        "max_tokens": 200,
    }

    try:
        r = requests.post(OPENROUTER_URL, headers=headers, data=json.dumps(payload), timeout=20)
        r.raise_for_status()
        body = r.json()

        # Try common response shapes
        if isinstance(body, dict):
            # OpenRouter can return choices -> message -> content
            choices = body.get('choices') or body.get('outputs')
            if choices and isinstance(choices, list):
                first = choices[0]
                # message.content
                msg = first.get('message') or first.get('output') or first
                if isinstance(msg, dict):
                    # Try nested message.content
                    content = msg.get('content') or msg.get('text') or msg.get('output_text')
                    if isinstance(content, dict):
                        # content may be {'type':'text','text':'...'}
                        text = content.get('text')
                    else:
                        text = content
                    if not text:
                        # fallbacks
                        text = first.get('text') or first.get('output_text')
                else:
                    text = str(msg)

                if text:
                    return text.strip()

        # Last resort: try simple keys
        if isinstance(body, dict) and 'output_text' in body:
            return body['output_text'].strip()

        return f"{animal_name} ({scientific_name}) es un miembro fascinante del reino animal."
    except Exception as e:
        print(f"[ERROR] Error generando descripción para {animal_name}: {e}")
        # Do not raise — keep pipeline working with fallback
        return f"{animal_name} ({scientific_name}) es un miembro fascinante del reino animal."


def generate_descriptions_for_missing():
    """
    Generate descriptions for all animals that don't have one or have very short descriptions.
    """
    print("[*] Generando descripciones con OpenRouter...\n")
    
    animals = AnimalModel.objects.all()
    updated_count = 0
    
    for animal in animals:
        # Check if description is empty or too short (placeholder)
        if not animal.description or len(animal.description) < 30:
            print(f"[*] Generando para: {animal.name}")
            
            # Generate using OpenRouter
            new_description = generate_description(
                animal.name,
                animal.scientific_name
            )
            
            # Update in database
            animal.description = new_description
            animal.save()
            updated_count += 1
            
            print(f"    [OK] {new_description[:70]}...\n")
        else:
            print(f"[*] {animal.name} ya tiene descripcion")
    
    print(f"\n[OK] Completado: {updated_count} descripciones generadas/actualizadas")
    print(f"[OK] Total de animales en BD: {animals.count()}")


if __name__ == '__main__':
    generate_descriptions_for_missing()
