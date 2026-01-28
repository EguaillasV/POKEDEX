"""Use Cases Package"""
from .recognition import (
    ProcessFrameUseCase,
    StartSessionUseCase,
    EndSessionUseCase,
    GetSessionDiscoveriesUseCase,
)
from .animals import (
    GetAnimalDetailsUseCase,
    SearchAnimalsUseCase,
    ListAnimalsByClassUseCase,
    ListEndangeredAnimalsUseCase,
    ListAllAnimalsUseCase,
)

__all__ = [
    'ProcessFrameUseCase',
    'StartSessionUseCase',
    'EndSessionUseCase',
    'GetSessionDiscoveriesUseCase',
    'GetAnimalDetailsUseCase',
    'SearchAnimalsUseCase',
    'ListAnimalsByClassUseCase',
    'ListEndangeredAnimalsUseCase',
    'ListAllAnimalsUseCase',
]
