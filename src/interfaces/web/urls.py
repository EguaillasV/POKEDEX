"""
Web URL Configuration
"""
from django.urls import path
from .views import HomeView, GalleryView, AnimalInfoView, AboutView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('gallery/', GalleryView.as_view(), name='gallery'),
    path('animal/<str:animal_id>/', AnimalInfoView.as_view(), name='animal-info'),
    path('about/', AboutView.as_view(), name='about'),
]
