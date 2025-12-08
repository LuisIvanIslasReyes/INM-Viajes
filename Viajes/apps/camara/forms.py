from django import forms
from .models import FotoRechazo


class FotoRechazoForm(forms.ModelForm):
    """Formulario para subir foto de rechazo"""
    
    class Meta:
        model = FotoRechazo
        fields = ['foto', 'notas']
        widgets = {
            'foto': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered file-input-primary w-full',
                'accept': 'image/jpeg,image/jpg,image/png,image/webp',
                'required': True
            }),
            'notas': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered',
                'rows': 3,
                'placeholder': 'Notas adicionales (opcional)...'
            })
        }
        labels = {
            'foto': 'Foto del rechazo',
            'notas': 'Notas adicionales'
        }