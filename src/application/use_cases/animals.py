"""
Application Use Cases - Animals
Handles animal information queries.
"""
from typing import List, Optional
import logging

from src.domain.entities import Animal
from src.domain.ports import AnimalRepositoryPort
from src.domain.services import AnimalInfoService
from src.domain.exceptions import AnimalNotFoundException

logger = logging.getLogger(__name__)


class GetAnimalDetailsUseCase:
    """
    Use Case: Get Animal Details
    Retrieves detailed information about an animal.
    """
    
    def __init__(self, animal_repository: AnimalRepositoryPort):
        self._animal_service = AnimalInfoService(animal_repository)
        self._animal_repo = animal_repository
    
    def execute(self, animal_id: str) -> dict:
        """
        Get animal details by ID.
        
        Args:
            animal_id: The animal ID
        
        Returns:
            Animal details
        """
        details = self._animal_service.get_animal_details(animal_id)
        if not details:
            raise AnimalNotFoundException(animal_id)
        
        return details


class SearchAnimalsUseCase:
    """
    Use Case: Search Animals
    Searches for animals by query string.
    """
    
    def __init__(self, animal_repository: AnimalRepositoryPort):
        self._animal_service = AnimalInfoService(animal_repository)
    
    def execute(self, query: str) -> List[dict]:
        """
        Search animals by name or description.
        
        Args:
            query: Search query
        
        Returns:
            List of matching animals
        """
        return self._animal_service.search_animals(query)


class ListAnimalsByClassUseCase:
    """
    Use Case: List Animals by Class
    Lists all animals of a specific taxonomic class.
    """
    
    def __init__(self, animal_repository: AnimalRepositoryPort):
        self._animal_service = AnimalInfoService(animal_repository)
    
    def execute(self, animal_class: str) -> List[dict]:
        """
        Get animals by class.
        
        Args:
            animal_class: The taxonomic class
        
        Returns:
            List of animals in that class
        """
        return self._animal_service.get_animals_by_class(animal_class)


class ListEndangeredAnimalsUseCase:
    """
    Use Case: List Endangered Animals
    Lists all endangered animals.
    """
    
    def __init__(self, animal_repository: AnimalRepositoryPort):
        self._animal_service = AnimalInfoService(animal_repository)
    
    def execute(self) -> List[dict]:
        """
        Get all endangered animals.
        
        Returns:
            List of endangered animals
        """
        return self._animal_service.get_endangered_animals()


class ListAllAnimalsUseCase:
    """
    Use Case: List All Animals
    Lists all available animals.
    """
    
    def __init__(self, animal_repository: AnimalRepositoryPort):
        self._animal_repo = animal_repository
    
    def execute(self) -> List[dict]:
        """
        Get all animals.
        
        Returns:
            List of all animals
        """
        animals = self._animal_repo.get_all()
        return [animal.to_dict() for animal in animals]
