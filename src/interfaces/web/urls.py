"""
Web URL Configuration
"""
from django.urls import path
from .views import (HomeView, GalleryView, AnimalInfoView, AboutView, LoginView, 
                   RegisterView, GestionCuentaView, LogoutView, ChangePasswordView, 
                   ChangeEmailView, EditProfileView)

urlpatterns = [
    # Root goes to login page
    path('', LoginView.as_view(), name='login'),
    # Keep a dedicated home path for authenticated users
    path('home/', HomeView.as_view(), name='home'),
    path('gallery/', GalleryView.as_view(), name='gallery'),
    path('animal/<str:animal_id>/', AnimalInfoView.as_view(), name='animal-info'),
    path('about/', AboutView.as_view(), name='about'),
    # Also expose login at /login/
    path('login/', LoginView.as_view(), name='login-page'),
    path('register/', RegisterView.as_view(), name='register'),
    path('gestion-cuenta/', GestionCuentaView.as_view(), name='gestion_cuenta'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('cambiar-contrasena/', ChangePasswordView.as_view(), name='change_password'),
    path('cambiar-email/', ChangeEmailView.as_view(), name='change_email'),
    path('editar-perfil/', EditProfileView.as_view(), name='edit_profile'),
]
