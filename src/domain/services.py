"""
Domain Services
Business logic that doesn't naturally fit within an entity.
"""
from typing import List, Optional
from .entities import Animal, Discovery, RecognitionResult, UserSession
from .value_objects import ImageFrame, Confidence
# Import OpenCV preprocessor for drawing boxes on thumbnails
from src.infrastructure.ml.recognition import OpenCVPreprocessor
from .ports import (
    AnimalRepositoryPort,
    DiscoveryRepositoryPort,
    AnimalRecognitionPort,
    ImageStoragePort,
)


class AnimalRecognitionService:
    """
    Domain Service: Animal Recognition
    Orchestrates the animal recognition process.
    """
    
    def __init__(
        self,
        recognition_port: AnimalRecognitionPort,
        animal_repository: AnimalRepositoryPort,
        discovery_repository: DiscoveryRepositoryPort,
        image_storage: ImageStoragePort,
        confidence_threshold: float = 0.7
    ):
        self._recognition = recognition_port
        self._animal_repo = animal_repository
        self._discovery_repo = discovery_repository
        self._image_storage = image_storage
        self._confidence_threshold = confidence_threshold
    
    def process_frame(
        self, 
        frame: ImageFrame, 
        session: UserSession
    ) -> Optional[tuple]:
        """
        Process a camera frame and return recognition results.
        Returns tuple of (RecognitionResult, Animal, Discovery) if successful.
        """
        # Preprocess the image
        processed_image = self._recognition.preprocess_image(frame)
        
        # Run recognition
        results = self._recognition.recognize(processed_image)
        
        if not results:
            return None
        
        # Get the best result
        best_result = results[0]
        
        # Check confidence threshold
        confidence = Confidence(best_result.confidence)
        if not confidence.meets_threshold(self._confidence_threshold):
            return None
        
        # Get animal information
        animal = self._animal_repo.get_by_name(best_result.animal_name)
        if not animal:
            return None
        
        # Check if already discovered in this session
        if session.has_discovered(animal.id):
            # Return result but no new discovery
            return (best_result, animal, None)
        
        # Create thumbnail and save discovery
        thumbnail_filename = f"{session.id}_{animal.id}_{best_result.timestamp.timestamp()}.jpg"
        thumbnail_url = self._image_storage.save_thumbnail(frame, thumbnail_filename)
        
        discovery = Discovery.create(
            session_id=session.id,
            animal_id=animal.id,
            thumbnail_url=thumbnail_url,
            confidence=best_result.confidence,
            user_id=session.user_id,
        )
        
        # Save discovery
        saved_discovery = self._discovery_repo.save(discovery)
        session.add_discovery(saved_discovery)
        
        return (best_result, animal, saved_discovery)
    
    def get_session_discoveries(self, session_id: str) -> List[dict]:
        """Get all discoveries for a session with animal info"""
        discoveries = self._discovery_repo.get_by_session(session_id)
        
        result = []
        for discovery in discoveries:
            animal = self._animal_repo.get_by_id(discovery.animal_id)
            if animal:
                result.append({
                    'discovery': discovery.to_dict(),
                    'animal': animal.to_dict(),
                })
        
        return result


class AnimalInfoService:
    """
    Domain Service: Animal Information
    Provides animal information and search capabilities.
    """
    
    def __init__(self, animal_repository: AnimalRepositoryPort):
        self._animal_repo = animal_repository
    
    def get_animal_details(self, animal_id: str) -> Optional[dict]:
        """Get detailed information about an animal"""
        animal = self._animal_repo.get_by_id(animal_id)
        if not animal:
            return None
        
        return {
            **animal.to_dict(),
            'random_fun_fact': animal.get_random_fun_fact(),
        }
    
    def search_animals(self, query: str) -> List[dict]:
        """Search for animals by name or description"""
        animals = self._animal_repo.search(query)
        return [animal.to_dict() for animal in animals]
    
    def get_animals_by_class(self, animal_class: str) -> List[dict]:
        """Get all animals of a specific class"""
        animals = self._animal_repo.get_by_class(animal_class)
        return [animal.to_dict() for animal in animals]
    
    def get_endangered_animals(self) -> List[dict]:
        """Get all endangered animals"""
        all_animals = self._animal_repo.get_all()
        endangered = [a for a in all_animals if a.is_endangered()]
        return [animal.to_dict() for animal in endangered]
