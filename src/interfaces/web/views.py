"""
Web Views - Django Template Views
Main web interface for the application.
"""
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import LoginForm
from .forms_register import RegisterForm
from django.contrib.auth.models import User
from src.infrastructure.persistence.models import ProfileModel
from django.db import transaction


class HomeView(View):
    """Home page with camera recognition interface"""
    
    def get(self, request):
        return render(request, 'web/home.html')


class GalleryView(View):
    """Gallery of discovered animals"""
    
    def get(self, request):
        return render(request, 'web/gallery.html')


class AnimalInfoView(View):
    """Detailed animal information page"""
    
    def get(self, request, animal_id):
        return render(request, 'web/animal_info.html', {
            'animal_id': animal_id,
        })


class AboutView(View):
    """About page"""
    
    def get(self, request):
        return render(request, 'web/about.html')


class LoginView(View):
    """Login page and authentication"""

    def get(self, request):
        form = LoginForm()
        return render(request, 'web/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['identifier']
            password = form.cleaned_data['password']

            User = get_user_model()
            # Try to authenticate by username first
            user = authenticate(request, username=identifier, password=password)
            if user is None:
                # If not, try to find by email
                try:
                    possible = User.objects.filter(email__iexact=identifier).first()
                    if possible:
                        user = authenticate(request, username=possible.username, password=password)
                except Exception:
                    user = None

            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                # Show form with error
                form.add_error(None, 'Nombre de usuario/correo o contraseña incorrectos')

        return render(request, 'web/login.html', {'form': form})


class RegisterView(View):
    """User registration view"""

    def get(self, request):
        form = RegisterForm()
        return render(request, 'web/register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            username = data['username']
            email = data['email']
            password = data['password']
            full_name = data.get('full_name') or ''
            first_name = ''
            last_name = ''
            parts = full_name.split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = ' '.join(parts[1:])
            elif len(parts) == 1:
                first_name = parts[0]

            with transaction.atomic():
                user = get_user_model().objects.create_user(username=username, email=email, password=password,
                                                           first_name=first_name, last_name=last_name)
                ProfileModel.objects.create(
                    user=user,
                    phone=data.get('phone'),
                    country=data.get('country'),
                    province=data.get('province'),
                    city=data.get('city'),
                    address=data.get('address')
                )

            # Auto-login after registration
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('home')

        return render(request, 'web/register.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['identifier']
            password = form.cleaned_data['password']

            User = get_user_model()
            # Try to authenticate by username first
            user = authenticate(request, username=identifier, password=password)
            if user is None:
                # If not, try to find by email
                try:
                    possible = User.objects.filter(email__iexact=identifier).first()
                    if possible:
                        user = authenticate(request, username=possible.username, password=password)
                except Exception:
                    user = None

            if user is not None:
                login(request, user)
                return redirect('home')

        return render(request, 'web/login.html', {'form': form})


@method_decorator(login_required(login_url='login'), name='dispatch')
class GestionCuentaView(View):
    """Account management page"""
    
    def get(self, request):
        try:
            profile = ProfileModel.objects.get(user=request.user)
        except ProfileModel.DoesNotExist:
            profile = None
        
        return render(request, 'web/gestion_cuenta.html', {
            'profile': profile
        })


class ChangePasswordView(View):
    """Change password page"""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        return render(request, 'web/change_password.html')


class ChangeEmailView(View):
    """Change email page"""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        return render(request, 'web/change_email.html')


class EditProfileView(View):
    """Edit profile page"""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        return render(request, 'web/edit_profile.html')
    
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        
        try:
            # Update user fields
            full_name = request.POST.get('full_name', '')
            parts = full_name.split()
            
            if len(parts) >= 2:
                request.user.first_name = parts[0]
                request.user.last_name = ' '.join(parts[1:])
            elif len(parts) == 1:
                request.user.first_name = parts[0]
                request.user.last_name = ''
            
            request.user.save()
            
            # Update or create profile
            profile, created = ProfileModel.objects.get_or_create(user=request.user)
            profile.phone = request.POST.get('phone', '')
            profile.country = request.POST.get('country', '')
            profile.province = request.POST.get('province', '')
            profile.city = request.POST.get('city', '')
            profile.address = request.POST.get('address', '')
            profile.save()
            
            return redirect('gestion_cuenta')
        except Exception as e:
            return render(request, 'web/edit_profile.html', {
                'error': 'Error al guardar los cambios: ' + str(e)
            })


class LogoutView(View):
    """Logout view"""
    
    def post(self, request):
        logout(request)
        return redirect('login')
