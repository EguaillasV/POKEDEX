"""
Domain Exceptions
Custom exceptions for the domain layer.
"""


class DomainException(Exception):
    """Base exception for domain errors"""
    pass


class AnimalNotFoundException(DomainException):
    """Raised when an animal is not found"""
    def __init__(self, animal_id: str):
        self.animal_id = animal_id
        super().__init__(f"Animal not found: {animal_id}")


class SessionNotFoundException(DomainException):
    """Raised when a session is not found"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


class RecognitionException(DomainException):
    """Raised when recognition fails"""
    pass


class InvalidImageException(DomainException):
    """Raised when an image is invalid"""
    pass


class StorageException(DomainException):
    """Raised when storage operations fail"""
    pass


class ModelNotReadyException(DomainException):
    """Raised when the ML model is not ready"""
    pass
