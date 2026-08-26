from django import forms

from .models import Redaccion, TEXTO_CRUDO_MAX_CARACTERES, TipoContenidoChoices

EXT_PERMITIDAS = ('.doc', '.docx', '.pdf')
TAM_MAX = 20 * 1024 * 1024  # 20 MB

INPUT = 'input input-bordered w-full'
SELECT = 'select select-bordered w-full'


class RedaccionForm(forms.ModelForm):
    class Meta:
        model = Redaccion
        fields = ['titulo', 'resolucion', 'tema', 'pais', 'tipo_contenido', 'archivo', 'texto_crudo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Título del documento'}),
            'resolucion': forms.Select(attrs={'class': SELECT}),
            'tema': forms.TextInput(attrs={
                'class': INPUT, 'placeholder': 'Ej. DOCUMENTACIÓN FALSA',
                'list': 'temas-existentes', 'autocomplete': 'off',
            }),
            'pais': forms.Select(attrs={'class': SELECT}),
            'tipo_contenido': forms.HiddenInput(),
            'archivo': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': '.doc,.docx,.pdf',
            }),
            'texto_crudo': forms.Textarea(attrs={
                'class': 'ds-textarea',
                'rows': 14,
                'placeholder': 'Pega aquí el texto completo de la redacción…',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pais'].empty_label = 'Selecciona un país'
        self.fields['tipo_contenido'].required = False
        self.fields['archivo'].required = False
        self.fields['texto_crudo'].required = False

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

    def clean_texto_crudo(self):
        texto = self.cleaned_data.get('texto_crudo') or ''
        if len(texto) > TEXTO_CRUDO_MAX_CARACTERES:
            raise forms.ValidationError(
                f'El texto es muy largo ({len(texto)} caracteres). '
                f'El máximo es {TEXTO_CRUDO_MAX_CARACTERES} caracteres.'
            )
        return texto

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_contenido') or TipoContenidoChoices.ARCHIVO
        cleaned_data['tipo_contenido'] = tipo

        # Un archivo "presente" en cleaned_data puede ser uno recién subido o,
        # al editar, el que ya tenía la instancia (FileField.clean() cae a él
        # si no se sube uno nuevo). Para la regla de "no ambos" solo cuenta un
        # archivo realmente adjuntado en ESTE envío, no el heredado.
        archivo_subido = self.files.get('archivo')
        texto_crudo = cleaned_data.get('texto_crudo')

        if archivo_subido and texto_crudo:
            raise forms.ValidationError('Elige un solo método: sube un archivo o pega el texto, no ambos.')

        if tipo == TipoContenidoChoices.TEXTO:
            # Cambiar a texto descarta el archivo anterior (si lo había), incluso
            # aunque el form lo hubiera heredado por defecto.
            cleaned_data['archivo'] = False
            if not texto_crudo:
                self.add_error('texto_crudo', 'Debes pegar el texto de la redacción.')
        else:
            cleaned_data['texto_crudo'] = ''
            if not cleaned_data.get('archivo'):
                self.add_error('archivo', 'Debes subir un documento.')

        return cleaned_data
