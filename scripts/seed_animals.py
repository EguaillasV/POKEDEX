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
        "name": "León",
        "scientific_name": "Panthera leo",
        "description": "El león es un mamífero carnívoro de la familia de los félidos. Es uno de los cuatro grandes felinos del género Panthera. Los machos son fácilmente reconocibles por su melena.",
        "animal_class": "MAMMAL",
        "habitat": "Sabanas y praderas de África subsahariana",
        "diet": "CARNIVORE",
        "conservation_status": "VULNERABLE",
        "fun_facts": [
            "Los leones son los únicos felinos que viven en grupos llamados manadas",
            "Un león puede dormir hasta 20 horas al día",
            "El rugido de un león puede escucharse a 8 kilómetros de distancia"
        ],
        "average_lifespan": "10-14 años",
        "average_weight": "190 kg",
        "geographic_distribution": "África subsahariana",
        "aliases": ["Lion", "Leone"]
    },
    {
        "name": "Elefante Africano",
        "scientific_name": "Loxodonta africana",
        "description": "El elefante africano es el animal terrestre más grande del mundo. Se caracteriza por su trompa larga, grandes orejas y colmillos de marfil.",
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
        "aliases": ["African Elephant", "Elephant"]
    },
    {
        "name": "Jirafa",
        "scientific_name": "Giraffa camelopardalis",
        "description": "La jirafa es el animal terrestre más alto del mundo. Su característica más distintiva es su largo cuello que puede medir hasta 2 metros.",
        "animal_class": "MAMMAL",
        "habitat": "Sabanas de África",
        "diet": "HERBIVORE",
        "conservation_status": "VULNERABLE",
        "fun_facts": [
            "Las jirafas duermen solo 30 minutos al día en intervalos cortos",
            "Su lengua puede medir hasta 50 centímetros",
            "Cada jirafa tiene un patrón de manchas único, como las huellas dactilares"
        ],
        "average_lifespan": "25 años",
        "average_weight": "1200 kg",
        "geographic_distribution": "África subsahariana",
        "aliases": ["Giraffe"]
    },
    {
        "name": "Tigre",
        "scientific_name": "Panthera tigris",
        "description": "El tigre es el félido más grande del mundo. Es reconocible por su pelaje naranja con rayas negras verticales.",
        "animal_class": "MAMMAL",
        "habitat": "Bosques tropicales, manglares y taigas de Asia",
        "diet": "CARNIVORE",
        "conservation_status": "ENDANGERED",
        "fun_facts": [
            "Las rayas del tigre son únicas como las huellas dactilares humanas",
            "Son excelentes nadadores y disfrutan del agua",
            "Pueden saltar hasta 5 metros de altura"
        ],
        "average_lifespan": "10-15 años",
        "average_weight": "220 kg",
        "geographic_distribution": "Asia",
        "aliases": ["Tiger"]
    },
    {
        "name": "Cebra",
        "scientific_name": "Equus quagga",
        "description": "La cebra es un équido africano caracterizado por sus distintivas rayas blancas y negras que son únicas para cada individuo.",
        "animal_class": "MAMMAL",
        "habitat": "Sabanas y praderas de África",
        "diet": "HERBIVORE",
        "conservation_status": "NEAR_THREATENED",
        "fun_facts": [
            "Las rayas de la cebra pueden confundir a los depredadores",
            "Son sociales y viven en grupos familiares",
            "Pueden correr a velocidades de hasta 65 km/h"
        ],
        "average_lifespan": "25 años",
        "average_weight": "350 kg",
        "geographic_distribution": "África oriental y meridional",
        "aliases": ["Zebra"]
    },
    {
        "name": "Oso Pardo",
        "scientific_name": "Ursus arctos",
        "description": "El oso pardo es una de las especies de osos más grandes. Es omnívoro y habita en bosques y montañas del hemisferio norte.",
        "animal_class": "MAMMAL",
        "habitat": "Bosques y montañas de Norteamérica, Europa y Asia",
        "diet": "OMNIVORE",
        "conservation_status": "LEAST_CONCERN",
        "fun_facts": [
            "Pueden correr hasta 55 km/h a pesar de su tamaño",
            "Hibernan durante 5-7 meses en invierno",
            "Tienen un olfato 100 veces mejor que el de los humanos"
        ],
        "average_lifespan": "25-30 años",
        "average_weight": "300 kg",
        "geographic_distribution": "Hemisferio Norte",
        "aliases": ["Brown Bear"]
    },
    {
        "name": "Águila Real",
        "scientific_name": "Aquila chrysaetos",
        "description": "El águila real es una de las aves de presa más conocidas y ampliamente distribuidas. Es un símbolo de poder en muchas culturas.",
        "animal_class": "BIRD",
        "habitat": "Montañas, bosques y terrenos abiertos",
        "diet": "CARNIVORE",
        "conservation_status": "LEAST_CONCERN",
        "fun_facts": [
            "Pueden ver hasta 8 veces mejor que los humanos",
            "Alcanzan velocidades de 320 km/h en picada",
            "Construyen nidos que pueden pesar hasta 450 kg"
        ],
        "average_lifespan": "30 años",
        "average_weight": "6 kg",
        "geographic_distribution": "Hemisferio Norte",
        "aliases": ["Golden Eagle"]
    },
    {
        "name": "Pingüino Emperador",
        "scientific_name": "Aptenodytes forsteri",
        "description": "El pingüino emperador es la especie de pingüino más alta y pesada. Vive exclusivamente en la Antártida.",
        "animal_class": "BIRD",
        "habitat": "Costas y océanos de la Antártida",
        "diet": "PISCIVORE",
        "conservation_status": "NEAR_THREATENED",
        "fun_facts": [
            "Son los únicos animales que pasan el invierno en la Antártida abierta",
            "Pueden bucear hasta 500 metros de profundidad",
            "Los machos incuban los huevos durante 2 meses sin comer"
        ],
        "average_lifespan": "20 años",
        "average_weight": "40 kg",
        "geographic_distribution": "Antártida",
        "aliases": ["Emperor Penguin"]
    },
    {
        "name": "Delfín Nariz de Botella",
        "scientific_name": "Tursiops truncatus",
        "description": "El delfín nariz de botella es una de las especies de delfines más conocidas. Son muy inteligentes y sociales.",
        "animal_class": "MAMMAL",
        "habitat": "Océanos templados y tropicales de todo el mundo",
        "diet": "PISCIVORE",
        "conservation_status": "LEAST_CONCERN",
        "fun_facts": [
            "Duermen con un ojo abierto, descansando medio cerebro a la vez",
            "Pueden reconocerse en un espejo",
            "Se comunican usando silbidos únicos como nombres"
        ],
        "average_lifespan": "40-50 años",
        "average_weight": "200 kg",
        "geographic_distribution": "Océanos de todo el mundo",
        "aliases": ["Bottlenose Dolphin"]
    },
    {
        "name": "Cocodrilo del Nilo",
        "scientific_name": "Crocodylus niloticus",
        "description": "El cocodrilo del Nilo es el segundo reptil más grande del mundo. Es un depredador formidable que habita en ríos africanos.",
        "animal_class": "REPTILE",
        "habitat": "Ríos, lagos y pantanos de África",
        "diet": "CARNIVORE",
        "conservation_status": "LEAST_CONCERN",
        "fun_facts": [
            "Pueden vivir hasta un año sin comer",
            "Sus ancestros existían en la época de los dinosaurios",
            "Lloran mientras comen (lágrimas de cocodrilo)"
        ],
        "average_lifespan": "70-100 años",
        "average_weight": "500 kg",
        "geographic_distribution": "África",
        "aliases": ["Nile Crocodile"]
    },
    {
        "name": "Tortuga Marina Verde",
        "scientific_name": "Chelonia mydas",
        "description": "La tortuga marina verde es una de las tortugas marinas más grandes. Se alimenta principalmente de pastos marinos y algas.",
        "animal_class": "REPTILE",
        "habitat": "Océanos tropicales y subtropicales",
        "diet": "HERBIVORE",
        "conservation_status": "ENDANGERED",
        "fun_facts": [
            "Pueden contener la respiración hasta 5 horas mientras duermen",
            "Vuelven a la misma playa donde nacieron para poner huevos",
            "La temperatura del nido determina el sexo de las crías"
        ],
        "average_lifespan": "80-100 años",
        "average_weight": "200 kg",
        "geographic_distribution": "Océanos tropicales y subtropicales",
        "aliases": ["Green Sea Turtle"]
    },
    {
        "name": "Gorila de Montaña",
        "scientific_name": "Gorilla beringei beringei",
        "description": "El gorila de montaña es una subespecie de gorila oriental. Son los primates más grandes y viven en las montañas de África Central.",
        "animal_class": "MAMMAL",
        "habitat": "Bosques montañosos de África Central",
        "diet": "HERBIVORE",
        "conservation_status": "ENDANGERED",
        "fun_facts": [
            "Comparten el 98% de su ADN con los humanos",
            "Los machos golpean su pecho para comunicarse",
            "Cada gorila tiene huellas nasales únicas"
        ],
        "average_lifespan": "35-40 años",
        "average_weight": "200 kg",
        "geographic_distribution": "Ruanda, Uganda, República Democrática del Congo",
        "aliases": ["Mountain Gorilla"]
    },
    {
        "name": "Koala",
        "scientific_name": "Phascolarctos cinereus",
        "description": "El koala es un marsupial australiano conocido por su apariencia adorable y su dieta de hojas de eucalipto.",
        "animal_class": "MAMMAL",
        "habitat": "Bosques de eucalipto de Australia",
        "diet": "HERBIVORE",
        "conservation_status": "VULNERABLE",
        "fun_facts": [
            "Duermen hasta 22 horas al día",
            "Sus huellas dactilares son casi idénticas a las humanas",
            "No necesitan beber agua, la obtienen del eucalipto"
        ],
        "average_lifespan": "13-18 años",
        "average_weight": "14 kg",
        "geographic_distribution": "Australia",
        "aliases": ["Koala"]
    },
    {
        "name": "Canguro Rojo",
        "scientific_name": "Macropus rufus",
        "description": "El canguro rojo es el marsupial más grande del mundo y un símbolo icónico de Australia.",
        "animal_class": "MAMMAL",
        "habitat": "Praderas y desiertos de Australia",
        "diet": "HERBIVORE",
        "conservation_status": "LEAST_CONCERN",
        "fun_facts": [
            "Pueden saltar hasta 9 metros de longitud",
            "No pueden caminar hacia atrás",
            "Las crías nacen del tamaño de una uva"
        ],
        "average_lifespan": "12-18 años",
        "average_weight": "85 kg",
        "geographic_distribution": "Australia",
        "aliases": ["Red Kangaroo"]
    },
    {
        "name": "Lobo Gris",
        "scientific_name": "Canis lupus",
        "description": "El lobo gris es el miembro más grande de la familia de los cánidos. Son animales sociales que viven en manadas.",
        "animal_class": "MAMMAL",
        "habitat": "Bosques, tundras y montañas del hemisferio norte",
        "diet": "CARNIVORE",
        "conservation_status": "LEAST_CONCERN",
        "fun_facts": [
            "Pueden comunicarse a través de aullidos a 16 km de distancia",
            "Son los ancestros de todos los perros domésticos",
            "Una manada puede tener un territorio de hasta 1000 km²"
        ],
        "average_lifespan": "6-8 años",
        "average_weight": "45 kg",
        "geographic_distribution": "Hemisferio Norte",
        "aliases": ["Grey Wolf", "Gray Wolf"]
    },
    {
        "name": "Oveja",
        "scientific_name": "Ovis aries",
        "description": "La oveja es un mamífero domesticado criado por su lana y carne.",
        "animal_class": "MAMMAL",
        "habitat": "Granjas y pastizales",
        "diet": "HERBIVORE",
        "conservation_status": "LEAST_CONCERN",
        "fun_facts": [
            "Las ovejas fueron uno de los primeros animales domesticados",
            "La lana de oveja es aislante y útil para climas fríos"
        ],
        "average_lifespan": "10-12 años",
        "average_weight": "70 kg",
        "geographic_distribution": "Domesticado mundialmente",
        "aliases": ["Sheep"]
    },
    {
        "name": "Gato",
        "scientific_name": "Felis catus",
        "description": "",
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
        "name": "Persona",
        "scientific_name": "Homo sapiens",
        "description": "",
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
