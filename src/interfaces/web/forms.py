from django import forms


class LoginForm(forms.Form):
    identifier = forms.CharField(
        label='Correo o Usuario',
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ingrese el correo electronico',
            'class': 'w-full border border-gray-200 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-200',
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Ingrese su contraseña',
            'class': 'w-full border border-gray-200 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-200',
        })
    )
