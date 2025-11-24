from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
import os


class ExcelUploadForm(forms.Form):
    """Formulario para subir archivos Excel"""
    archivo = forms.FileField(
        label='Archivo Excel',
        help_text='Seleccione un archivo Excel (.xlsx) para cargar',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )
    
    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # Validar extensión
            if not archivo.name.endswith(('.xlsx', '.xls')):
                raise forms.ValidationError('El archivo debe ser un Excel (.xlsx o .xls)')
            
            # Validar tamaño (max 10MB)
            if archivo.size > 10 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede ser mayor a 10MB')
            
            #Validar si ya existe un archivo con el mismo nombre en el servidor
            from django.core.files.storage import default_storage
            ruta_archivo = f'uploads/{archivo.name}'

            if default_storage.exists(ruta_archivo):
                raise forms.ValidationError(
                    f'El archivo "{archivo.name}" ya existe en el servidor.'
                    f'Por favor, suba otro archivo e intente de nuevo.'
                )
        
        return archivo

class CreateUserForm(UserCreationForm):
    """Formulario para crear nuevos usuarios"""
    username = forms.CharField(
        label='Nombre de usuario',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Ingrese nombre de usuario'
        })
    )
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Ingrese contraseña'
        })
    )
    password2 = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Confirme contraseña'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')