"""API Package"""
from .views import (
    AnimalListView,
    AnimalDetailView,
    AnimalSearchView,
    AnimalsByClassView,
    EndangeredAnimalsView,
    RecognizeImageView,
)

__all__ = [
    'AnimalListView',
    'AnimalDetailView',
    'AnimalSearchView',
    'AnimalsByClassView',
    'EndangeredAnimalsView',
    'RecognizeImageView',
]
