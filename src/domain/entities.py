"""
Domain Entities - Core Business Objects
These are the fundamental objects in our domain.
They are independent of any framework or infrastructure.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid


class ConservationStatus(Enum):
    """Estado de conservación según IUCN"""
    EXTINCT = "Extinto"
    EXTINCT_IN_WILD = "Extinto en Estado Silvestre"
    CRITICALLY_ENDANGERED = "En Peligro Crítico"
    ENDANGERED = "En Peligro"
    VULNERABLE = "Vulnerable"
    NEAR_THREATENED = "Casi Amenazado"
    LEAST_CONCERN = "Preocupación Menor"
    DATA_DEFICIENT = "Datos Insuficientes"
    NOT_EVALUATED = "No Evaluado"


class DietType(Enum):
    """Tipos de dieta animal"""
    CARNIVORE = "Carnívoro"
    HERBIVORE = "Herbívoro"
    OMNIVORE = "Omnívoro"
    INSECTIVORE = "Insectívoro"
    PISCIVORE = "Piscívoro"


class AnimalClass(Enum):
    """Clases taxonómicas"""
    MAMMAL = "Mamífero"
    BIRD = "Ave"
    REPTILE = "Reptil"
    AMPHIBIAN = "Anfibio"
    FISH = "Pez"
    INVERTEBRATE = "Invertebrado"


@dataclass
class Animal:
    """
    Entity: Animal
    Represents an animal species in our domain.
    This is a rich domain model with behavior.
    """
    id: str
    name: str
    scientific_name: str
    description: str
    animal_class: AnimalClass
    habitat: str
    diet: DietType
    conservation_status: ConservationStatus
    fun_facts: List[str] = field(default_factory=list)
    average_lifespan: Optional[str] = None
    average_weight: Optional[str] = None
    average_height: Optional[str] = None
    geographic_distribution: Optional[str] = None
    image_url: Optional[str] = None
    sound_url: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        name: str,
        scientific_name: str,
        description: str,
        animal_class: AnimalClass,
        habitat: str,
        diet: DietType,
        conservation_status: ConservationStatus,
        **kwargs
    ) -> 'Animal':
        """Factory method to create a new Animal entity"""
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            scientific_name=scientific_name,
            description=description,
            animal_class=animal_class,
            habitat=habitat,
            diet=diet,
            conservation_status=conservation_status,
            **kwargs
        )
    
    def is_endangered(self) -> bool:
        """Check if the animal is in any endangered category"""
        endangered_statuses = [
            ConservationStatus.CRITICALLY_ENDANGERED,
            ConservationStatus.ENDANGERED,
            ConservationStatus.VULNERABLE,
        ]
        return self.conservation_status in endangered_statuses
    
    def get_random_fun_fact(self) -> Optional[str]:
        """Return a random fun fact about the animal"""
        import random
        if self.fun_facts:
            return random.choice(self.fun_facts)
        return None
    
    def to_dict(self) -> dict:
        """Convert entity to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'scientific_name': self.scientific_name,
            'description': self.description,
            'animal_class': self.animal_class.value,
            'habitat': self.habitat,
            'diet': self.diet.value,
            'conservation_status': self.conservation_status.value,
            'fun_facts': self.fun_facts,
            'average_lifespan': self.average_lifespan,
            'average_weight': self.average_weight,
            'average_height': self.average_height,
            'geographic_distribution': self.geographic_distribution,
            'image_url': self.image_url,
            'sound_url': self.sound_url,
            'is_endangered': self.is_endangered(),
        }


@dataclass
class RecognitionResult:
    """
    Value Object: Recognition Result
    Represents the result of an animal recognition.
    """
    animal_id: str
    animal_name: str
    confidence: float
    bounding_box: Optional[dict] = None  # {x, y, width, height}
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def is_confident(self, threshold: float = 0.7) -> bool:
        """Check if the recognition meets the confidence threshold"""
        return self.confidence >= threshold
    
    def to_dict(self) -> dict:
        return {
            'animal_id': self.animal_id,
            'animal_name': self.animal_name,
            'confidence': self.confidence,
            'confidence_percentage': f"{self.confidence * 100:.1f}%",
            'bounding_box': self.bounding_box,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class Discovery:
    """
    Entity: Discovery
    Represents a user's discovery of an animal.
    """
    id: str
    user_id: Optional[str]
    session_id: str
    animal_id: str
    thumbnail_url: str
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    location: Optional[str] = None
    confidence: float = 0.0
    
    @classmethod
    def create(
        cls,
        session_id: str,
        animal_id: str,
        thumbnail_url: str,
        confidence: float,
        user_id: Optional[str] = None,
        location: Optional[str] = None
    ) -> 'Discovery':
        """Factory method to create a new Discovery"""
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            animal_id=animal_id,
            thumbnail_url=thumbnail_url,
            confidence=confidence,
            location=location,
        )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'animal_id': self.animal_id,
            'thumbnail_url': self.thumbnail_url,
            'discovered_at': self.discovered_at.isoformat(),
            'location': self.location,
            'confidence': self.confidence,
        }


@dataclass
class UserSession:
    """
    Entity: User Session
    Represents an active recognition session.
    """
    id: str
    user_id: Optional[str]
    started_at: datetime = field(default_factory=datetime.utcnow)
    discoveries: List[Discovery] = field(default_factory=list)
    is_active: bool = True
    
    @classmethod
    def create(cls, user_id: Optional[str] = None) -> 'UserSession':
        """Factory method to create a new session"""
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
        )
    
    def add_discovery(self, discovery: Discovery) -> None:
        """Add a discovery to the session"""
        self.discoveries.append(discovery)
    
    def get_unique_animals_count(self) -> int:
        """Get count of unique animals discovered"""
        unique_animals = set(d.animal_id for d in self.discoveries)
        return len(unique_animals)
    
    def has_discovered(self, animal_id: str) -> bool:
        """Check if an animal has already been discovered in this session"""
        return any(d.animal_id == animal_id for d in self.discoveries)
    
    def end_session(self) -> None:
        """End the session"""
        self.is_active = False
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'started_at': self.started_at.isoformat(),
            'discoveries_count': len(self.discoveries),
            'unique_animals_count': self.get_unique_animals_count(),
            'is_active': self.is_active,
        }
