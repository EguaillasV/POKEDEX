"""
Data Seeder - Initial Animal Data
Run with: python manage.py shell < scripts/seed_animals.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.infrastructure.persistence.models import AnimalModel
import uuid


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
        "geographic_distribution": "África subsahariana"
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
        "geographic_distribution": "África"
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
        "geographic_distribution": "África subsahariana"
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
        "geographic_distribution": "Asia"
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
        "geographic_distribution": "África oriental y meridional"
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
        "geographic_distribution": "Hemisferio Norte"
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
        "geographic_distribution": "Hemisferio Norte"
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
        "geographic_distribution": "Antártida"
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
        "geographic_distribution": "Océanos de todo el mundo"
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
        "geographic_distribution": "África"
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
        "geographic_distribution": "Océanos tropicales y subtropicales"
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
        "geographic_distribution": "Ruanda, Uganda, República Democrática del Congo"
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
        "geographic_distribution": "Australia"
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
        "geographic_distribution": "Australia"
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
        "geographic_distribution": "Hemisferio Norte"
    },
]


def seed_animals():
    """Seed the database with initial animal data"""
    print("Seeding animals...")
    
    for animal_data in ANIMALS_DATA:
        animal_id = str(uuid.uuid4())
        
        animal, created = AnimalModel.objects.update_or_create(
            name=animal_data['name'],
            defaults={
                'id': animal_id,
                'scientific_name': animal_data['scientific_name'],
                'description': animal_data['description'],
                'animal_class': animal_data['animal_class'],
                'habitat': animal_data['habitat'],
                'diet': animal_data['diet'],
                'conservation_status': animal_data['conservation_status'],
                'fun_facts': animal_data['fun_facts'],
                'average_lifespan': animal_data.get('average_lifespan'),
                'average_weight': animal_data.get('average_weight'),
                'geographic_distribution': animal_data.get('geographic_distribution'),
            }
        )
        
        status = "Created" if created else "Updated"
        print(f"  {status}: {animal.name}")
    
    print(f"\nTotal animals: {AnimalModel.objects.count()}")
    print("Seeding complete!")


if __name__ == '__main__':
    seed_animals()
