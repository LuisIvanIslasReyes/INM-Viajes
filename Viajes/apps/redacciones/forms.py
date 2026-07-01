from django import forms

from .models import Redaccion

EXT_PERMITIDAS = ('.doc', '.docx', '.pdf')
TAM_MAX = 20 * 1024 * 1024  # 20 MB

INPUT = 'input input-bordered w-full'
SELECT = 'select select-bordered w-full'


class RedaccionForm(forms.ModelForm):
    class Meta:
        model = Redaccion
        fields = ['titulo', 'resolucion', 'tema', 'pais', 'archivo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Título del documento'}),
            'resolucion': forms.Select(attrs={'class': SELECT}),
            'tema': forms.TextInput(attrs={
                'class': INPUT, 'placeholder': 'Ej. DOCUMENTACIÓN FALSA',
                'list': 'temas-existentes', 'autocomplete': 'off',
            }),
            'pais': forms.Select(attrs={'class': SELECT}),
            'archivo': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': '.doc,.docx,.pdf',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pais'].empty_label = 'Selecciona un país'

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            if not archivo.name.lower().endswith(EXT_PERMITIDAS):
                raise forms.ValidationError('Solo se permiten archivos .doc, .docx o .pdf.')
            if archivo.size > TAM_MAX:
                mb = archivo.size / (1024 * 1024)
                raise forms.ValidationError(
                    f'El archivo es muy grande ({mb:.1f} MB). El tamaño máximo es 20 MB.'
                )
        return archivo
