"""
API URL Configuration
"""
from django.urls import path
from .views import (
    AnimalListView,
    AnimalDetailView,
    AnimalSearchView,
    AnimalsByClassView,
    EndangeredAnimalsView,
    SessionStartView,
    SessionEndView,
    SessionDiscoveriesView,
    RecognizeImageView,
)

urlpatterns = [
    # Recognition
    path('recognize/', RecognizeImageView.as_view(), name='recognize-image'),
    
    # Animals
    path('animals/', AnimalListView.as_view(), name='animal-list'),
    path('animals/search/', AnimalSearchView.as_view(), name='animal-search'),
    path('animals/endangered/', EndangeredAnimalsView.as_view(), name='animals-endangered'),
    path('animals/class/<str:animal_class>/', AnimalsByClassView.as_view(), name='animals-by-class'),
    path('animals/<str:animal_id>/', AnimalDetailView.as_view(), name='animal-detail'),
    
    # Sessions
    path('sessions/start/', SessionStartView.as_view(), name='session-start'),
    path('sessions/<str:session_id>/end/', SessionEndView.as_view(), name='session-end'),
    path('sessions/<str:session_id>/discoveries/', SessionDiscoveriesView.as_view(), name='session-discoveries'),
]
