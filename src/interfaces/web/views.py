"""
Web Views - Django Template Views
Main web interface for the application.
"""
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from .forms import LoginForm
from .forms_register import RegisterForm
from django.contrib.auth.models import User
from src.infrastructure.persistence.models import ProfileModel
from django.db import transaction


@method_decorator(login_required(login_url='login'), name='dispatch')
class HomeView(View):
    """Home page with camera recognition interface"""
    
    def get(self, request):
        return render(request, 'web/home.html')


@method_decorator(login_required(login_url='login'), name='dispatch')
class GalleryView(View):
    """Gallery of discovered animals"""
    
    def get(self, request):
        user_discoveries = None
        if request.user.is_authenticated:
            from src.infrastructure.persistence.models import DiscoveryModel
            try:
                discoveries = DiscoveryModel.objects.filter(
                    user=request.user
                ).select_related('animal').order_by('-discovered_at').values_list('animal_id', flat=True).distinct()
                user_discoveries = list(discoveries)
            except Exception as e:
                user_discoveries = []
        
        return render(request, 'web/gallery.html', {
            'user_discoveries': user_discoveries or []
        })


@method_decorator(login_required(login_url='login'), name='dispatch')
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


@method_decorator(never_cache, name='dispatch')
class LoginView(View):
    """Login page and authentication"""

    def get(self, request):
        # Redirect if already authenticated
        if request.user.is_authenticated:
            return redirect('home')
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
                form.add_error(None, 'Usuario o contraseña incorrecto')

        return render(request, 'web/login.html', {'form': form})


@method_decorator(never_cache, name='dispatch')
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


@method_decorator(login_required(login_url='login'), name='dispatch')
class ChangePasswordView(View):
    """Change password page"""
    
    def get(self, request):
        return render(request, 'web/change_password.html')
    
    def post(self, request):
        import re
        from django.contrib.auth import update_session_auth_hash
        from django.contrib import messages
        
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        error_message = None
        success_message = None
        
        # Validar que no estén vacíos
        if not current_password or not new_password or not confirm_password:
            error_message = 'Todos los campos son requeridos'
        # Validar contraseña actual
        elif not request.user.check_password(current_password):
            error_message = 'La contraseña actual es incorrecta'
        # Validar que las nuevas contraseñas coincidan
        elif new_password != confirm_password:
            error_message = 'Las nuevas contraseñas no coinciden'
        # Validar que la nueva contraseña sea diferente de la actual
        elif request.user.check_password(new_password):
            error_message = 'La nueva contraseña debe ser diferente a la actual'
        else:
            # Validar fortaleza de contraseña
            validation_errors = []
            if len(new_password) < 8:
                validation_errors.append('La contraseña debe tener al menos 8 caracteres')
            if not re.search(r"[A-Z]", new_password):
                validation_errors.append('Debe incluir al menos una letra mayúscula')
            if not re.search(r"[a-z]", new_password):
                validation_errors.append('Debe incluir al menos una letra minúscula')
            if not re.search(r"\d", new_password):
                validation_errors.append('Debe incluir al menos un número')
            if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", new_password):
                validation_errors.append('Debe incluir al menos un símbolo')
            
            if validation_errors:
                error_message = ' | '.join(validation_errors)
            else:
                # Cambiar contraseña
                try:
                    request.user.set_password(new_password)
                    request.user.save()
                    
                    # Mantener sesión actual activa
                    update_session_auth_hash(request, request.user)
                    
                    success_message = 'Contraseña cambiada exitosamente'
                except Exception as e:
                    error_message = f'Error al cambiar la contraseña: {str(e)}'
        
        # Si hay error, mostrar el formulario con el error
        if error_message:
            return render(request, 'web/change_password.html', {
                'error_message': error_message
            })
        
        # Si hay éxito, mostrar mensaje y redirigir
        if success_message:
            messages.success(request, success_message, extra_tags='success')
            return redirect('gestion_cuenta')


@method_decorator(login_required(login_url='login'), name='dispatch')
@method_decorator(login_required(login_url='login'), name='dispatch')
@method_decorator(never_cache, name='dispatch')
class ChangeEmailView(View):
    """Change email page"""
    
    def get(self, request):
        return render(request, 'web/change_email.html')
    
    def post(self, request):
        from django.core.mail import send_mail as django_send_mail
        import re
        
        new_email = request.POST.get('new_email', '').strip()
        confirm_email = request.POST.get('confirm_email', '').strip()
        
        error_message = None
        success_message = None
        
        # Validar que no estén vacíos
        if not new_email or not confirm_email:
            error_message = 'Todos los campos son requeridos'
        # Validar formato del email
        elif not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', new_email):
            error_message = 'El formato del correo no es válido'
        # Validar longitud
        elif len(new_email) > 30:
            error_message = 'El correo no puede exceder 30 caracteres'
        # Validar que sean iguales
        elif new_email != confirm_email:
            error_message = 'Los correos no coinciden'
        # Validar que sea diferente al actual
        elif new_email == request.user.email:
            error_message = 'El nuevo correo debe ser diferente al actual'
        else:
            # Validar que el email no esté en uso
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.filter(email=new_email).exists():
                error_message = 'Este correo ya está registrado en el sistema'
            else:
                # Cambiar email
                try:
                    request.user.email = new_email
                    request.user.save()
                    
                    success_message = 'Correo actualizado exitosamente'
                except Exception as e:
                    error_message = f'Error al cambiar el correo: {str(e)}'
        
        # Si hay error, mostrar el formulario con el error
        if error_message:
            return render(request, 'web/change_email.html', {
                'error_message': error_message
            })
        
        # Si hay éxito, mostrar mensaje y redirigir
        if success_message:
            messages.success(request, success_message, extra_tags='success')
            return redirect('gestion_cuenta')


@method_decorator(login_required(login_url='login'), name='dispatch')
class EditProfileView(View):
    """Edit profile page"""
    
    def get(self, request):
        return render(request, 'web/edit_profile.html')
    
    def post(self, request):
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


@method_decorator(login_required(login_url='login'), name='dispatch')
@method_decorator(never_cache, name='dispatch')
class LogoutView(View):
    """Logout view"""
    
    def get(self, request):
        logout(request)
        response = redirect('login')
        # Clear session cookies explicitly
        response.delete_cookie('sessionid')
        return response
    
    def post(self, request):
        logout(request)
        response = redirect('login')
        # Clear session cookies explicitly
        response.delete_cookie('sessionid')
        return response
