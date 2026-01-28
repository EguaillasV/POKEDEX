"""
Repository Implementations
These are the adapters that implement the domain ports.
"""
from typing import List, Optional
from django.db.models import Q
from django.utils import timezone

from src.domain.entities import (
    Animal, 
    Discovery, 
    UserSession,
    AnimalClass,
    DietType,
    ConservationStatus,
)
from src.domain.ports import (
    AnimalRepositoryPort,
    DiscoveryRepositoryPort,
    SessionRepositoryPort,
)
from .models import AnimalModel, SessionModel, DiscoveryModel


class DjangoAnimalRepository(AnimalRepositoryPort):
    """Django ORM implementation of AnimalRepositoryPort"""
    
    def _to_entity(self, model: AnimalModel) -> Animal:
        """Convert ORM model to domain entity"""
        return Animal(
            id=model.id,
            name=model.name,
            scientific_name=model.scientific_name,
            description=model.description,
            animal_class=AnimalClass[model.animal_class],
            habitat=model.habitat,
            diet=DietType[model.diet],
            conservation_status=ConservationStatus[model.conservation_status],
            fun_facts=model.fun_facts or [],
            average_lifespan=model.average_lifespan,
            average_weight=model.average_weight,
            average_height=model.average_height,
            geographic_distribution=model.geographic_distribution,
            image_url=model.image_url,
            sound_url=model.sound_url,
        )
    
    def _to_model(self, entity: Animal) -> AnimalModel:
        """Convert domain entity to ORM model"""
        return AnimalModel(
            id=entity.id,
            name=entity.name,
            scientific_name=entity.scientific_name,
            description=entity.description,
            animal_class=entity.animal_class.name,
            habitat=entity.habitat,
            diet=entity.diet.name,
            conservation_status=entity.conservation_status.name,
            fun_facts=entity.fun_facts,
            average_lifespan=entity.average_lifespan,
            average_weight=entity.average_weight,
            average_height=entity.average_height,
            geographic_distribution=entity.geographic_distribution,
            image_url=entity.image_url,
            sound_url=entity.sound_url,
        )
    
    def get_by_id(self, animal_id: str) -> Optional[Animal]:
        try:
            model = AnimalModel.objects.get(id=animal_id)
            return self._to_entity(model)
        except AnimalModel.DoesNotExist:
            return None
    
    def get_by_name(self, name: str) -> Optional[Animal]:
        try:
            model = AnimalModel.objects.get(name__iexact=name)
            return self._to_entity(model)
        except AnimalModel.DoesNotExist:
            return None
    
    def get_all(self) -> List[Animal]:
        models = AnimalModel.objects.all()
        return [self._to_entity(m) for m in models]
    
    def search(self, query: str) -> List[Animal]:
        models = AnimalModel.objects.filter(
            Q(name__icontains=query) |
            Q(scientific_name__icontains=query) |
            Q(description__icontains=query)
        )
        return [self._to_entity(m) for m in models]
    
    def save(self, animal: Animal) -> Animal:
        model = self._to_model(animal)
        model.save()
        return animal
    
    def get_by_class(self, animal_class: str) -> List[Animal]:
        models = AnimalModel.objects.filter(animal_class=animal_class.upper())
        return [self._to_entity(m) for m in models]


class DjangoSessionRepository(SessionRepositoryPort):
    """Django ORM implementation of SessionRepositoryPort"""
    
    def _to_entity(self, model: SessionModel) -> UserSession:
        """Convert ORM model to domain entity"""
        return UserSession(
            id=model.id,
            user_id=str(model.user_id) if model.user_id else None,
            started_at=model.started_at,
            is_active=model.is_active,
            discoveries=[],  # Loaded separately if needed
        )
    
    def create(self, session: UserSession) -> UserSession:
        model = SessionModel(
            id=session.id,
            user_id=session.user_id,
            is_active=True,
        )
        model.save()
        return session
    
    def get_by_id(self, session_id: str) -> Optional[UserSession]:
        try:
            model = SessionModel.objects.get(id=session_id)
            return self._to_entity(model)
        except SessionModel.DoesNotExist:
            return None
    
    def update(self, session: UserSession) -> UserSession:
        SessionModel.objects.filter(id=session.id).update(
            is_active=session.is_active,
        )
        return session
    
    def end_session(self, session_id: str) -> None:
        SessionModel.objects.filter(id=session_id).update(
            is_active=False,
            ended_at=timezone.now(),
        )


class DjangoDiscoveryRepository(DiscoveryRepositoryPort):
    """Django ORM implementation of DiscoveryRepositoryPort"""
    
    def _to_entity(self, model: DiscoveryModel) -> Discovery:
        """Convert ORM model to domain entity"""
        return Discovery(
            id=model.id,
            user_id=str(model.user_id) if model.user_id else None,
            session_id=model.session_id,
            animal_id=model.animal_id,
            thumbnail_url=model.thumbnail_url,
            discovered_at=model.discovered_at,
            location=model.location,
            confidence=model.confidence,
        )
    
    def save(self, discovery: Discovery) -> Discovery:
        model = DiscoveryModel(
            id=discovery.id,
            session_id=discovery.session_id,
            user_id=discovery.user_id,
            animal_id=discovery.animal_id,
            thumbnail_url=discovery.thumbnail_url,
            location=discovery.location,
            confidence=discovery.confidence,
        )
        model.save()
        return discovery
    
    def get_by_session(self, session_id: str) -> List[Discovery]:
        models = DiscoveryModel.objects.filter(session_id=session_id)
        return [self._to_entity(m) for m in models]
    
    def get_by_user(self, user_id: str) -> List[Discovery]:
        models = DiscoveryModel.objects.filter(user_id=user_id)
        return [self._to_entity(m) for m in models]
    
    def get_unique_animals_by_session(self, session_id: str) -> List[str]:
        return list(
            DiscoveryModel.objects
            .filter(session_id=session_id)
            .values_list('animal_id', flat=True)
            .distinct()
        )
