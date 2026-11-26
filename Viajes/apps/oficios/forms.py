from django import forms

from apps.empleados.models import Empleado

from .models import (
    Evidencia,
    Expediente,
    MotivoRechazo,
    OficioInstancia,
    PersonaExpediente,
    PlantillaOficio,
    PlantillaOficioIdioma,
)


def _con_clases(form):
    """Clases del sistema de diseño en todos los widgets visibles."""
    for campo in form.fields.values():
        widget = campo.widget
        if isinstance(widget, (forms.HiddenInput, forms.CheckboxInput)):
            continue
        clase = 'ds-select' if isinstance(widget, forms.Select) else 'ds-input'
        widget.attrs.setdefault('class', clase)


class FechaInput(forms.DateInput):
    input_type = 'date'

    def __init__(self, **kwargs):
        super().__init__(format='%Y-%m-%d', **kwargs)


def _empleado_field(etiqueta):
    return forms.ModelChoiceField(
        queryset=Empleado.objects.filter(activo=True), required=False,
        widget=forms.HiddenInput, label=etiqueta,
    )


class BusquedaRegistrosForm(forms.Form):
    q = forms.CharField(label='Nombre o documento', required=False)
    vuelo = forms.CharField(label='Vuelo', required=False)
    fecha = forms.DateField(label='Fecha del vuelo', required=False, widget=FechaInput())
    solo_marcados = forms.BooleanField(label='Solo marcados SR o R', required=False, initial=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _con_clases(self)


class FirmasForm(forms.ModelForm):
    firmante = _empleado_field('Firmante')
    testigo_1 = _empleado_field('Testigo 1')
    testigo_2 = _empleado_field('Testigo 2')

    class Meta:
        model = Expediente
        fields = ['resultado', 'firmante', 'testigo_1', 'testigo_2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _con_clases(self)

    def clean(self):
        datos = super().clean()
        personas = [datos.get('firmante'), datos.get('testigo_1'), datos.get('testigo_2')]
        elegidos = [p.pk for p in personas if p]
        if len(elegidos) != len(set(elegidos)):
            raise forms.ValidationError('El firmante y los testigos deben ser personas distintas.')
        return datos


class PersonaForm(forms.ModelForm):
    class Meta:
        model = PersonaExpediente
        fields = ['nombre', 'nacionalidad', 'fecha_nacimiento', 'documento', 'sexo', 'idioma',
                  'vuelo', 'fecha_arribo', 'origen', 'aerolinea', 'sala_entrevista', 'numero_acta',
                  'motivo_rechazo']
        widgets = {'fecha_nacimiento': FechaInput(), 'fecha_arribo': FechaInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motivo_rechazo'].queryset = MotivoRechazo.objects.filter(activo=True)
        self.fields['motivo_rechazo'].empty_label = '— Sin motivo —'
        _con_clases(self)


class OficioForm(forms.ModelForm):
    testigo_1 = _empleado_field('Testigo 1 de este oficio')
    testigo_2 = _empleado_field('Testigo 2 de este oficio')

    class Meta:
        model = OficioInstancia
        fields = ['contenido_html', 'fecha_oficio', 'testigo_1', 'testigo_2']
        widgets = {'contenido_html': forms.HiddenInput, 'fecha_oficio': FechaInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contenido_html'].required = False
        _con_clases(self)


class PlantillaForm(forms.ModelForm):
    class Meta:
        model = PlantillaOficio
        fields = ['nombre', 'titulo', 'bloque_firmas', 'tamano_letra_pt', 'lleva_fecha', 'activo', 'contenido_html']
        widgets = {'contenido_html': forms.HiddenInput}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contenido_html'].required = False
        _con_clases(self)


class VarianteForm(forms.ModelForm):
    class Meta:
        model = PlantillaOficioIdioma
        fields = ['titulo', 'leyenda_firma_persona', 'activo', 'contenido_html']
        widgets = {'contenido_html': forms.HiddenInput}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contenido_html'].required = False
        _con_clases(self)


FOTO_MAXIMA_MB = 15


class EvidenciaForm(forms.ModelForm):
    class Meta:
        model = Evidencia
        fields = ['verificacion_a', 'hora', 'respuesta', 'intentos', 'nota', 'foto', 'orden']
        widgets = {
            'hora': forms.TimeInput(attrs={'type': 'time'}),
            'nota': forms.Textarea(attrs={'rows': 2}),
            'foto': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
        }

    def __init__(self, *args, tipo='', **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['orden'].required = False
        if tipo != 'VERIFICACION':  # el 05 solo lleva foto y observaciones
            for campo in ('verificacion_a', 'hora', 'respuesta', 'intentos'):
                del self.fields[campo]
        _con_clases(self)

    def clean_foto(self):
        foto = self.cleaned_data.get('foto')
        if foto and getattr(foto, 'size', 0) > FOTO_MAXIMA_MB * 1024 * 1024:
            raise forms.ValidationError(f'La foto pesa más de {FOTO_MAXIMA_MB} MB.')
        return foto

    def clean_orden(self):
        return self.cleaned_data.get('orden') or 0
