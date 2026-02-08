from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


class RegisterForm(forms.Form):
    username = forms.CharField(label='Nombre de Usuario', max_length=150,
                               widget=forms.TextInput(attrs={'placeholder': 'nombre_usuario', 'class': 'w-full border border-gray-200 rounded px-4 py-2'}))
    full_name = forms.CharField(label='Nombre completo', required=False,
                                widget=forms.TextInput(attrs={'placeholder': 'Ingrese sus dos nombres y dos apellidos', 'class': 'w-full border border-gray-200 rounded px-4 py-2'}))
    email = forms.EmailField(label='Correo Electrónico', widget=forms.EmailInput(attrs={'placeholder': 'Ingrese el correo electrónico', 'class': 'w-full border border-gray-200 rounded px-4 py-2'}))
    phone = forms.CharField(label='Teléfono', required=False, max_length=30,
                           widget=forms.TextInput(attrs={'placeholder': 'Incluye el código del país. Ej: +593 99 999 9999', 'class': 'w-full border border-gray-200 rounded px-4 py-2'}))
    country = forms.CharField(label='País', required=False, initial='Ecuador',
                              widget=forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded px-4 py-2'}))
    province = forms.CharField(label='Provincia / Estado', required=False,
                               widget=forms.TextInput(attrs={'placeholder': 'Selecciona una provincia/estado', 'class': 'w-full border border-gray-200 rounded px-4 py-2'}))
    city = forms.CharField(label='Ciudad', required=False,
                          widget=forms.TextInput(attrs={'placeholder': 'No hay datos', 'class': 'w-full border border-gray-200 rounded px-4 py-2'}))
    address = forms.CharField(label='Dirección', required=False,
                             widget=forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded px-4 py-2'}))
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'placeholder': 'Ingrese su contraseña', 'class': 'w-full border border-gray-200 rounded px-4 py-2'}))
    password_confirm = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput(attrs={'placeholder': 'Repita su contraseña', 'class': 'w-full border border-gray-200 rounded px-4 py-2'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        User = get_user_model()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('El nombre de usuario ya está en uso')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        User = get_user_model()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('El correo ya está registrado')
        return email

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
        import re
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres')
        if not re.search(r"[A-Z]", password):
            raise ValidationError('La contraseña debe incluir al menos una letra mayúscula')
        if not re.search(r"[a-z]", password):
            raise ValidationError('La contraseña debe incluir al menos una letra minúscula')
        if not re.search(r"\\d", password):
            raise ValidationError('La contraseña debe incluir al menos un número')
        if not re.search(r"[!@#$%^&*()_+\-=[\]{};':\"\\\\|,.<>/?]", password):
            raise ValidationError('La contraseña debe incluir al menos un símbolo')

        return password

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            return phone
        # Normalize spaces
        import re
        phone_normalized = re.sub(r"\\s+", " ", phone).strip()
        # Basic validation: should contain + and digits
        if not re.match(r"^\\+?[0-9\\s()-]+$", phone_normalized):
            raise ValidationError('Número de teléfono inválido')
        return phone_normalized
