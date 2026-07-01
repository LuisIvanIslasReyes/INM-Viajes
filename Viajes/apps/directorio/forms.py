from django import forms

from .models import EmpresaDirectorio, ResolucionChoices

INPUT = 'input input-bordered w-full'
SELECT = 'select select-bordered w-full'


class EmpresaDirectorioForm(forms.ModelForm):
    class Meta:
        model = EmpresaDirectorio
        fields = [
            'empresa', 'domicilio', 'estado', 'ciudad',
            'firma_encargado', 'telefono', 'tentativa_resolucion',
        ]
        widgets = {
            'empresa': forms.TextInput(attrs={
                'class': INPUT, 'placeholder': 'Nombre de la empresa',
                'autocomplete': 'off', 'id': 'id_empresa',
            }),
            'domicilio': forms.TextInput(attrs={
                'class': INPUT, 'placeholder': 'Calle, número, colonia',
            }),
            'estado': forms.Select(attrs={'class': SELECT}),
            'ciudad': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Ciudad'}),
            'firma_encargado': forms.TextInput(attrs={
                'class': INPUT, 'placeholder': 'Nombre del encargado',
            }),
            'telefono': forms.TextInput(attrs={
                'class': INPUT, 'placeholder': 'Ej. 664 123 4567 ext. 10',
            }),
            'tentativa_resolucion': forms.Select(attrs={'class': SELECT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estado'].empty_label = 'Selecciona un estado'
        # La tentativa de resolución es opcional: puede definirse más adelante.
        self.fields['tentativa_resolucion'].required = False
        self.fields['tentativa_resolucion'].choices = [
            ('', 'Sin especificar (opcional)'),
            *ResolucionChoices.choices,
        ]
