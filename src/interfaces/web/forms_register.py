from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re


class RegisterForm(forms.Form):
    username = forms.CharField(
        label='Nombre de Usuario',
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'máximo 20 caracteres',
            'class': 'w-full border border-gray-200 rounded px-4 py-2'
        })
    )
    
    full_name = forms.CharField(
        label='Nombre Completo',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: Juan Pérez García',
            'class': 'w-full border border-gray-200 rounded px-4 py-2'
        })
    )
    
    email = forms.EmailField(
        label='Correo Electrónico',
        max_length=30,
        widget=forms.EmailInput(attrs={
            'placeholder': 'tu@email.com',
            'class': 'w-full border border-gray-200 rounded px-4 py-2'
        })
    )
    
    phone = forms.CharField(
        label='Teléfono',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+593 991234567 (máximo 20 caracteres)',
            'class': 'w-full border border-gray-200 rounded px-4 py-2'
        })
    )
    
    country = forms.CharField(
        label='País',
        max_length=50,
        required=False,
        initial='Ecuador',
        widget=forms.TextInput(attrs={
            'class': 'w-full border border-gray-200 rounded px-4 py-2'
        })
    )
    
    province = forms.CharField(
        label='Provincia / Estado',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Selecciona una provincia/estado',
            'class': 'w-full border border-gray-200 rounded px-4 py-2'
        })
    )
    
    city = forms.CharField(
        label='Ciudad',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nombre de la ciudad',
            'class': 'w-full border border-gray-200 rounded px-4 py-2'
        })
    )
    
    address = forms.CharField(
        label='Dirección',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Calle #123, Apt 4B',
            'class': 'w-full border border-gray-200 rounded px-4 py-2'
        })
    )
    
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mínimo 8 caracteres con mayúsculas, números y símbolos',
            'class': 'w-full border border-gray-200 rounded px-4 py-2'
        })
    )
    
    password_confirm = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Repita su contraseña',
            'class': 'w-full border border-gray-200 rounded px-4 py-2'
        })
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        User = get_user_model()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('El nombre de usuario ya está en uso')
        # Solo letras, números y guiones bajos
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError('Solo se permiten letras, números y guiones bajos')
        return username

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name', '').strip()
        if full_name:
            # Solo letras, espacios y acentos
            if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', full_name):
                raise ValidationError('El nombre solo puede contener letras y espacios')
        return full_name

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        User = get_user_model()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('El correo ya está registrado')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            return phone
        
        # Solo permitir: + números y espacios
        if not re.match(r'^[\+0-9\s\(\)\-]+$', phone):
            raise ValidationError('Teléfono inválido. Use solo números, +, espacios, paréntesis y guiones')
        
        # Contar dígitos (sin símbolos)
        digits_only = re.sub(r'[^\d]', '', phone)
        if len(digits_only) < 7 or len(digits_only) > 15:
            raise ValidationError('El teléfono debe tener entre 7 y 15 dígitos')
        
        return phone

    def clean_address(self):
        address = self.cleaned_data.get('address', '').strip()
        if address:
            # Permitir: letras, números, espacios, comas, puntos, #, guiones y paréntesis
            if not re.match(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s,.\#\-\(\)]+$', address):
                raise ValidationError('La dirección contiene caracteres no permitidos. Use solo letras, números, espacios, comas, puntos, # y guiones')
        return address

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('password_confirm')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Las contraseñas no coinciden')
        return cleaned

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            return password

        # Password strength: at least 8 chars, uppercase, lowercase, digit, symbol
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres')
        if not re.search(r"[A-Z]", password):
            raise ValidationError('La contraseña debe incluir al menos una letra mayúscula')
        if not re.search(r"[a-z]", password):
            raise ValidationError('La contraseña debe incluir al menos una letra minúscula')
        if not re.search(r"\d", password):
            raise ValidationError('La contraseña debe incluir al menos un número')
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
            raise ValidationError('La contraseña debe incluir al menos un símbolo')

        return password

