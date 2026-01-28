"""
Domain Ports (Interfaces)
These are the contracts that the domain expects from the outside world.
They define what the domain needs, not how it's implemented.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np

from .entities import Animal, Discovery, RecognitionResult, UserSession
from .value_objects import ImageFrame


class AnimalRepositoryPort(ABC):
    """
    Port: Animal Repository
    Defines the contract for animal data persistence.
    """
    
    @abstractmethod
    def get_by_id(self, animal_id: str) -> Optional[Animal]:
        """Get an animal by its ID"""
        pass
    
    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Animal]:
        """Get an animal by its name"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Animal]:
        """Get all animals"""
        pass
    
    @abstractmethod
    def search(self, query: str) -> List[Animal]:
        """Search animals by name or description"""
        pass
    
    @abstractmethod
    def save(self, animal: Animal) -> Animal:
        """Save an animal"""
        pass
    
    @abstractmethod
    def get_by_class(self, animal_class: str) -> List[Animal]:
        """Get animals by their taxonomic class"""
        pass


class DiscoveryRepositoryPort(ABC):
    """
    Port: Discovery Repository
    Defines the contract for discovery data persistence.
    """
    
    @abstractmethod
    def save(self, discovery: Discovery) -> Discovery:
        """Save a discovery"""
        pass
    
    @abstractmethod
    def get_by_session(self, session_id: str) -> List[Discovery]:
        """Get all discoveries for a session"""
        pass
    
    @abstractmethod
    def get_by_user(self, user_id: str) -> List[Discovery]:
        """Get all discoveries for a user"""
        pass
    
    @abstractmethod
    def get_unique_animals_by_session(self, session_id: str) -> List[str]:
        """Get unique animal IDs discovered in a session"""
        pass


class SessionRepositoryPort(ABC):
    """
    Port: Session Repository
    Defines the contract for session data persistence.
    """
    
    @abstractmethod
    def create(self, session: UserSession) -> UserSession:
        """Create a new session"""
        pass
    
    @abstractmethod
    def get_by_id(self, session_id: str) -> Optional[UserSession]:
        """Get a session by ID"""
        pass
    
    @abstractmethod
    def update(self, session: UserSession) -> UserSession:
        """Update a session"""
        pass
    
    @abstractmethod
    def end_session(self, session_id: str) -> None:
        """End a session"""
        pass


class AnimalRecognitionPort(ABC):
    """
    Port: Animal Recognition Service
    Defines the contract for ML-based animal recognition.
    """
    
    @abstractmethod
    def recognize(self, image: np.ndarray) -> List[RecognitionResult]:
        """
        Recognize animals in an image.
        Returns a list of recognition results sorted by confidence.
        """
        pass
    
    @abstractmethod
    def preprocess_image(self, frame: ImageFrame) -> np.ndarray:
        """Preprocess an image frame for recognition"""
        pass
    
    @abstractmethod
    def get_supported_animals(self) -> List[str]:
        """Get list of animal names the model can recognize"""
        pass
    
    @abstractmethod
    def is_ready(self) -> bool:
        """Check if the recognition service is ready"""
        pass


class ImageStoragePort(ABC):
    """
    Port: Image Storage Service
    Defines the contract for image storage (thumbnails, etc.).
    """
    
    @abstractmethod
    def save_thumbnail(self, image: ImageFrame, filename: str) -> str:
        """Save a thumbnail and return its URL"""
        pass
    
    @abstractmethod
    def get_thumbnail_url(self, filename: str) -> str:
        """Get the URL for a thumbnail"""
        pass
    
    @abstractmethod
    def delete_thumbnail(self, filename: str) -> bool:
        """Delete a thumbnail"""
        pass


class NotificationPort(ABC):
    """
    Port: Notification Service
    Defines the contract for sending notifications (WebSocket, etc.).
    """
    
    @abstractmethod
    async def send_recognition_result(
        self, 
        session_id: str, 
        result: RecognitionResult,
        animal: Animal
    ) -> None:
        """Send a recognition result to a client"""
        pass
    
    @abstractmethod
    async def send_discovery_update(
        self, 
        session_id: str, 
        discovery: Discovery
    ) -> None:
        """Send a discovery update to a client"""
        pass
    
    @abstractmethod
    async def send_error(self, session_id: str, error: str) -> None:
        """Send an error message to a client"""
        pass
