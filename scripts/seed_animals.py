"""
Data Seeder - Initial Animal Data
Run with: python manage.py shell < scripts/seed_animals.py
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
import uuid

# OpenRouter configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


ANIMALS_DATA = [
    {
        "name": "Pájaro",
        "scientific_name": "Aves",
        "description": "Las aves son animales vertebrados caracterizados por tener plumas, alas y la capacidad de volar. Son descendientes directos de los dinosaurios y se encuentran en todos los continentes.",
        "animal_class": "BIRD",
        "habitat": "Cielos, bosques, y agua",
        "diet": "CARNIVORE",
        "conservation_status": "LEAST_CONCERN",
        "fun_facts": [
            "Las aves tienen huesos huecos para facilitar el vuelo",
            "Algunas aves pueden volar a altitudes de más de 10,000 metros",
            "El ritmo cardíaco de un pájaro es mucho más rápido que el de los humanos"
        ],
        "average_lifespan": "5-50 años",
        "average_weight": "0.5 kg",
        "geographic_distribution": "Todo el mundo",
        "aliases": ["Bird", "Aves"]
    },
    {
        "name": "Gato",
        "scientific_name": "Felis catus",
        "description": "El gato es un mamífero felino domesticado conocido por su agilidad, independencia y habilidades de caza. Son animales inteligentes y afectuosos que han sido compañeros humanos durante miles de años.",
        "animal_class": "MAMMAL",
        "habitat": "Hogares y ambientes urbanos",
        "diet": "CARNIVORE",
        "conservation_status": "LEAST_CONCERN",
        "fun_facts": [
            "Los gatos tienen 32 músculos en cada oreja",
            "Pueden girar sus orejas 180 grados",
            "Los gatos duermen entre 12 y 16 horas al día"
        ],
        "average_lifespan": "12-18 años",
        "average_weight": "4.5 kg",
        "geographic_distribution": "Domesticado mundialmente",
        "aliases": ["Cats", "Cat"]
    },
    {
        "name": "Vaca",
        "scientific_name": "Bos taurus",
        "description": "La vaca es un mamífero ungulado domesticado criado principalmente por su leche, carne y cuero. Son animales herbívoros tranquilos y sociales que viven en rebaños.",
        "animal_class": "MAMMAL",
        "habitat": "Granjas y pastizales",
        "diet": "HERBIVORE",
        "conservation_status": "LEAST_CONCERN",
        "fun_facts": [
            "Las vacas tienen amigos y les afecta la separación",
            "Una vaca adulta puede pesar hasta 900 kg",
            "Las vacas pueden recordar y reconocer a otros individuos"
        ],
        "average_lifespan": "18-22 años",
        "average_weight": "700 kg",
        "geographic_distribution": "Domesticado mundialmente",
        "aliases": ["Cow", "Cattle"]
    },
    {
        "name": "Ciervo",
        "scientific_name": "Cervidae",
        "description": "El ciervo es un mamífero ungulado silvestre conocido por sus astas ramificadas y su elegancia. Son animales ágiles que habitan en bosques y praderas de todo el mundo.",
        "animal_class": "MAMMAL",
        "habitat": "Bosques, bosques mixtos y praderas",
        "diet": "HERBIVORE",
        "conservation_status": "LEAST_CONCERN",
        "fun_facts": [
            "Los ciervos machos mudan sus astas cada año",
            "Pueden saltar hasta 2.5 metros de altura",
            "Los ciervos tienen visión de 310 grados"
        ],
        "average_lifespan": "15-20 años",
        "average_weight": "200 kg",
        "geographic_distribution": "Hemisferio Norte",
        "aliases": ["Deer"]
    },
    {
        "name": "Perro",
        "scientific_name": "Canis familiaris",
        "description": "El perro es un mamífero carnívoro domesticado derivado del lobo gris. Son animales sociales, leales y altamente inteligentes que viven entre humanos.",
        "animal_class": "MAMMAL",
        "habitat": "Hogares, granjas y ambientes urbanos",
        "diet": "CARNIVORE",
        "conservation_status": "LEAST_CONCERN",
        "fun_facts": [
            "Los perros pueden entender hasta 250 palabras diferentes",
            "Tienen un sentido del olfato 10,000 veces mejor que el humano",
            "Los perros son discípulos del lobo gris"
        ],
        "average_lifespan": "10-13 años",
        "average_weight": "25 kg",
        "geographic_distribution": "Domesticado mundialmente",
        "aliases": ["Dog"]
    },
    {
        "name": "Elefante",
        "scientific_name": "Loxodonta africana",
        "description": "El elefante africano es el animal terrestre más grande del mundo. Se caracteriza por su trompa larga, grandes orejas y colmillos de marfil. Son animales inteligentes y sociales.",
        "animal_class": "MAMMAL",
        "habitat": "Sabanas, bosques y desiertos de África",
        "diet": "HERBIVORE",
        "conservation_status": "ENDANGERED",
        "fun_facts": [
            "Los elefantes tienen una memoria excepcional",
            "Pueden comunicarse a través de infrasonidos",
            "Un elefante adulto puede beber hasta 200 litros de agua al día"
        ],
        "average_lifespan": "60-70 años",
        "average_weight": "6000 kg",
        "geographic_distribution": "África",
        "aliases": ["Elephant"]
    },
    {
        "name": "Jirafa",
        "scientific_name": "Giraffa camelopardalis",
        "description": "La jirafa es el animal terrestre más alto del mundo. Su característica más distintiva es su largo cuello que puede medir hasta 2 metros, que usa para alimentarse de hojas en árboles altos.",
        "animal_class": "MAMMAL",
        "habitat": "Sabanas de África",
        "diet": "HERBIVORE",
        "conservation_status": "VULNERABLE",
        "fun_facts": [
            "Las jirafas duermen solo 30 minutos al día en intervalos cortos",
            "Su lengua puede medir hasta 50 centímetros",
            "Cada jirafa tiene un patrón de manchas único como las huellas dactilares"
        ],
        "average_lifespan": "25 años",
        "average_weight": "1200 kg",
        "geographic_distribution": "África subsahariana",
        "aliases": ["Giraffe"]
    },
    {
        "name": "Persona",
        "scientific_name": "Homo sapiens",
        "description": "La persona es un primate mamífero inteligente y bípedo. Los humanos se caracterizan por su lenguaje complejo, inteligencia avanzada y capacidad de crear herramientas y culturas.",
        "animal_class": "MAMMAL",
        "habitat": "Ambientes urbanos, rurales y salvajes",
        "diet": "OMNIVORE",
        "conservation_status": "LEAST_CONCERN",
        "fun_facts": [
            "Homo sapiens es la única especie humana viviente",
            "Tienen capacidades cognitivas superiores entre todos los animales",
            "Pueden comunicarse a través del lenguaje complejo"
        ],
        "average_lifespan": "72-75 años",
        "average_weight": "70 kg",
        "geographic_distribution": "Todo el mundo",
        "aliases": ["Person", "Human", "Humano"]
    },
    {
        "name": "Cerdo",
        "scientific_name": "Sus scrofa domesticus",
        "description": "El cerdo es un mamífero ungulado domesticado criado principalmente por su carne y cuero. Son animales inteligentes, sociales y versátiles que se adaptan bien a diferentes ambientes.",
        "animal_class": "MAMMAL",
        "habitat": "Granjas y alojamientos rurales",
        "diet": "OMNIVORE",
        "conservation_status": "LEAST_CONCERN",
        "fun_facts": [
            "Los cerdos son tan inteligentes como los perros",
            "Pueden reconocerse en un espejo",
            "Los cerdos tienen sudoración limitada y usan el barro para regularse"
        ],
        "average_lifespan": "15-20 años",
        "average_weight": "300 kg",
        "geographic_distribution": "Domesticado mundialmente",
        "aliases": ["Pig"]
    },
    {
        "name": "Oveja",
        "scientific_name": "Ovis aries",
        "description": "La oveja es un mamífero ungulado domesticado criado por su lana, carne y leche. Son animales gregarios que viven en rebaños y se caracterizan por su lana espesa y rizada.",
        "animal_class": "MAMMAL",
        "habitat": "Granjas y pastizales",
        "diet": "HERBIVORE",
        "conservation_status": "LEAST_CONCERN",
        "fun_facts": [
            "Las ovejas fueron uno de los primeros animales domesticados",
            "La lana de oveja es aislante y valiosa para climas fríos",
            "Las ovejas pueden reconocer y recordar a más de 50 individuos"
        ],
        "average_lifespan": "10-12 años",
        "average_weight": "70 kg",
        "geographic_distribution": "Domesticado mundialmente",
        "aliases": ["Sheep"]
    },
]


def generate_description_with_ai(animal_name: str, scientific_name: str) -> str:
    """Generate description using OpenRouter REST API directly"""
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

    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://pokedex.local",
            "X-Title": "Pokedex Animal Recognition",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "mistral-7b-instruct",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 200,
        }
        
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        description = data['choices'][0]['message']['content'].strip()
        return description
    except Exception as e:
        print(f"  [ERROR] {str(e)[:60]}")
        return f"{animal_name} ({scientific_name}) es un miembro interesante del reino animal."


def seed_animals():
    """Seed the database with initial animal data"""
    print("Seeding animals...")
    
    for animal_data in ANIMALS_DATA:
        animal_id = str(uuid.uuid4())
        
        # Prefer updating existing record (do not change primary key). If not exists, create new.
        existing = AnimalModel.objects.filter(name=animal_data['name']).first()
        if existing:
            existing.scientific_name = animal_data['scientific_name']
            existing.description = animal_data['description']
            existing.animal_class = animal_data['animal_class']
            existing.habitat = animal_data['habitat']
            existing.diet = animal_data['diet']
            existing.conservation_status = animal_data['conservation_status']
            existing.fun_facts = animal_data['fun_facts']
            existing.average_lifespan = animal_data.get('average_lifespan')
            existing.average_weight = animal_data.get('average_weight')
            existing.geographic_distribution = animal_data.get('geographic_distribution')
            existing.aliases = animal_data.get('aliases', [])
            existing.save()
            animal = existing
            created = False
            print(f"  Updated: {animal.name}")
        else:
            animal = AnimalModel.objects.create(
                id=animal_id,
                name=animal_data['name'],
                scientific_name=animal_data['scientific_name'],
                description=animal_data['description'],
                animal_class=animal_data['animal_class'],
                habitat=animal_data['habitat'],
                diet=animal_data['diet'],
                conservation_status=animal_data['conservation_status'],
                fun_facts=animal_data['fun_facts'],
                average_lifespan=animal_data.get('average_lifespan'),
                average_weight=animal_data.get('average_weight'),
                geographic_distribution=animal_data.get('geographic_distribution'),
                aliases=animal_data.get('aliases', []),
            )
            created = True
            print(f"  Created: {animal.name}")
    
    print(f"\nTotal animals: {AnimalModel.objects.count()}")
    
    # Generate descriptions for animals without them or with placeholders
    print("\n[AI] Generando descripciones faltantes con OpenRouter...")
    generate_missing_descriptions()
    
    print("\nSeeding complete!")


def generate_missing_descriptions():
    """Generate AI descriptions for animals without descriptions or with very short ones"""
    animals = AnimalModel.objects.all()
    updated_count = 0
    
    for animal in animals:
        if not animal.description or len(animal.description) < 30:
            print(f"  [*] Generando para: {animal.name}")
            new_desc = generate_description_with_ai(animal.name, animal.scientific_name)
            animal.description = new_desc
            animal.save()
            updated_count += 1
            print(f"     [OK] {new_desc[:70]}...")
    
    if updated_count > 0:
        print(f"\n  [OK] {updated_count} descripciones generadas")
    else:
        print(f"  [OK] Todos los animales tienen descripciones")



if __name__ == '__main__':
    seed_animals()
