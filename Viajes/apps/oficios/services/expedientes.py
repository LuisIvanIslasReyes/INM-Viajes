"""
Reglas del flujo de expedientes y oficios (las vistas solo llaman aquí).

- Las personas se toman de `uploader.Registro` (precarga) o se capturan a mano; sus
  datos se editan siempre en `PersonaExpediente`, nunca en el Registro.
- Un borrador copia el texto de la plantilla; desde ahí se edita por su cuenta.
- Imprimir congela: valida, guarda las variables (`snap_contexto`) y el .docx, y deja
  el oficio de solo lectura. Reabrir pide motivo y queda en el historial.
"""
import re
import unicodedata

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.uploader.utils.parsers import obtener_nacionalidad

from ..catalogos import aerolinea_de_vuelo, origen_de_aeropuerto
from ..gentilicios import gentilicio
from ..models import (
    Expediente,
    Idioma,
    OficioHistorial,
    OficioInstancia,
    PersonaExpediente,
    PlantillaHistorial,
)
from .contexto import VARIABLES, contexto_para
from .docx_oficio import formato_de_instancia, pieza_de, render_docx
from .html_docx import EVIDENCIAS_RE, limpiar_html, pendientes
from .variables import sustituir, variables_usadas

Accion = OficioHistorial.Accion
ETIQUETAS = {clave: etiqueta for clave, etiqueta, _ejemplo in VARIABLES}

# Idioma sugerido por el país que emitió el documento (ISO-2 o ISO-3). Solo es una
# sugerencia: se corrige en la persona.
IDIOMA_POR_PAIS = {
    Idioma.CHINO: {'CHN', 'CN', 'HKG', 'HK', 'MAC', 'MO', 'TWN', 'TW'},
    Idioma.RUSO: {'RUS', 'RU', 'BLR', 'BY', 'KAZ', 'KZ', 'KGZ', 'KG'},
    Idioma.FRANCES: {'FRA', 'FR', 'HTI', 'HT', 'SEN', 'SN', 'CMR', 'CM', 'COD', 'CD', 'CIV', 'CI',
                     'GIN', 'GN', 'MLI', 'ML', 'BFA', 'BF', 'NER', 'NE', 'TCD', 'TD', 'BEN', 'BJ',
                     'TGO', 'TG', 'COG', 'CG', 'GAB', 'GA', 'MDG', 'MG', 'BDI', 'BI'},
    Idioma.INGLES: {'USA', 'US', 'GBR', 'GB', 'CAN', 'CA', 'IND', 'IN', 'NGA', 'NG', 'GHA', 'GH',
                    'JAM', 'JM', 'AUS', 'AU'},
    Idioma.ARABE: {'SAU', 'SA', 'EGY', 'EG', 'IRQ', 'IQ', 'SYR', 'SY', 'JOR', 'JO', 'LBN', 'LB',
                   'YEM', 'YE', 'ARE', 'AE', 'MAR', 'MA', 'DZA', 'DZ'},
}
SEXO_POR_GENERO = {'M': 'M', 'H': 'M', 'MALE': 'M', '男': 'M', 'F': 'F', 'FEMALE': 'F', '女': 'F'}


class ErrorOficio(Exception):
    """Acción no permitida (con mensaje para el usuario)."""


# ---------------------------------------------------------------- expedientes y personas

def idioma_sugerido(codigo_pais):
    codigo = (codigo_pais or '').strip().upper()
    for idioma, codigos in IDIOMA_POR_PAIS.items():
        if codigo in codigos:
            return idioma
    return Idioma.ESPANOL


def datos_desde_registro(registro):
    """Valores iniciales de una persona a partir del pasajero del vuelo."""
    codigo = (registro.codigo_pais_emision or '').strip()
    # 1) gentilicio ("china"); 2) nombre del país ("China"); 3) lo que traiga el Excel.
    nacionalidad = gentilicio(codigo) or (obtener_nacionalidad(codigo) if codigo else '')
    if not nacionalidad or nacionalidad in ('N/A', codigo.upper()):
        nacionalidad = registro.pais_emision or nacionalidad
    return {
        'registro': registro,
        'nombre': (registro.nombre_pasajero or '').strip(),
        'nacionalidad': nacionalidad,
        'fecha_nacimiento': registro.fecha_nacimiento,
        'documento': registro.numero_documento or '',
        'sexo': SEXO_POR_GENERO.get((registro.genero or '').strip().upper(), ''),
        'vuelo': registro.vuelo_numero or '',
        'fecha_arribo': timezone.localdate(registro.vuelo_fecha) if registro.vuelo_fecha else None,
        'origen': origen_de_aeropuerto(registro.aeropuerto_salida),
        'aerolinea': aerolinea_de_vuelo(registro.vuelo_numero),
        'idioma': idioma_sugerido(codigo),
    }


def resultado_sugerido(registros):
    if any(r.rechazado for r in registros):
        return Expediente.Resultado.RECHAZO
    if any(r.internacion for r in registros):
        return Expediente.Resultado.INTERNACION
    return Expediente.Resultado.PENDIENTE


@transaction.atomic
def crear_expediente(usuario, registros=()):
    registros = list(registros)
    expediente = Expediente.objects.create(creado_por=usuario, resultado=resultado_sugerido(registros))
    for orden, registro in enumerate(registros, start=1):
        PersonaExpediente.objects.create(expediente=expediente, orden=orden, **datos_desde_registro(registro))
    return expediente


def siguiente_orden(expediente):
    ultimo = expediente.personas.order_by('-orden').values_list('orden', flat=True).first()
    return (ultimo or 0) + 1


def agregar_registros(expediente, registros):
    ya = set(expediente.personas.exclude(registro=None).values_list('registro_id', flat=True))
    creadas = []
    for registro in registros:
        if registro.pk in ya:
            continue
        creadas.append(PersonaExpediente.objects.create(
            expediente=expediente, orden=siguiente_orden(expediente), **datos_desde_registro(registro),
        ))
    return creadas


# ---------------------------------------------------------------- oficios

def _historial(instancia, accion, usuario, detalle=''):
    OficioHistorial.objects.create(instancia=instancia, accion=accion, usuario=usuario, detalle=detalle)


def texto_base(plantilla, idioma):
    """(idioma, html) con que arranca un borrador: la traducción si existe, si no el español."""
    variante = plantilla.variante(idioma)
    if variante:
        # Texto vacío = igual al español (solo cambian el título y la leyenda de firma; ej. el 07).
        return variante.idioma, variante.contenido_html or plantilla.contenido_html
    return Idioma.ESPANOL, plantilla.contenido_html


@transaction.atomic
def crear_borradores(persona, plantillas, usuario):
    """Un borrador por plantilla que la persona todavía no tenga, en su idioma si hay traducción.

    Devuelve los creados; los que quedaron en español aunque la persona hable otro idioma
    se reconocen por `instancia.idioma != persona.idioma`.
    """
    existentes = set(persona.oficios.values_list('plantilla_id', flat=True))
    creados = []
    for plantilla in plantillas:
        if plantilla.pk in existentes:
            continue
        idioma, contenido = texto_base(plantilla, persona.idioma)
        instancia = OficioInstancia.objects.create(
            persona=persona, plantilla=plantilla, idioma=idioma, contenido_html=contenido,
        )
        en = '' if idioma == Idioma.ESPANOL else f' ({instancia.get_idioma_display().lower()})'
        _historial(instancia, Accion.CREADO, usuario, f'Desde la plantilla {plantilla.clave}{en}.')
        creados.append(instancia)
    return creados


@transaction.atomic
def recargar_texto(instancia, idioma, usuario):
    """Reemplaza el texto del borrador por el de la plantilla en `idioma` (o en español si no hay)."""
    _exigir_borrador(instancia)
    idioma_final, contenido = texto_base(instancia.plantilla, idioma)
    instancia.idioma = idioma_final
    instancia.contenido_html = contenido
    instancia.save(update_fields=['idioma', 'contenido_html', 'actualizado_en'])
    _historial(instancia, Accion.EDITADO, usuario,
               f'Texto recargado de la plantilla ({instancia.get_idioma_display().lower()}).')
    return idioma_final


def comparar_variables(base_html, traduccion_html):
    """(las del español que faltan en la traducción, las de la traducción que no existen)."""
    base = variables_usadas(base_html)
    traduccion = variables_usadas(traduccion_html)
    faltan = [v for v in base if v not in traduccion]
    desconocidas = [v for v in traduccion if v not in ETIQUETAS]
    return faltan, desconocidas


def guardar_version(plantilla, usuario, variante=None):
    """Deja en el historial la versión recién guardada de la plantilla o de su traducción."""
    origen = variante or plantilla
    PlantillaHistorial.objects.create(
        plantilla=plantilla, idioma=variante.idioma if variante else Idioma.ESPANOL,
        titulo=origen.titulo, contenido_html=origen.contenido_html,
        leyenda_firma_persona=variante.leyenda_firma_persona if variante else '', usuario=usuario,
    )


def _exigir_borrador(instancia):
    if not instancia.editable:
        raise ErrorOficio('El oficio ya se marcó como impreso. Para cambiarlo, primero hay que reabrirlo.')


@transaction.atomic
def guardar_borrador(instancia, usuario, contenido_html, fecha_oficio=None, testigo_1=None, testigo_2=None):
    _exigir_borrador(instancia)
    limpio = limpiar_html(contenido_html)
    cambios = []
    if limpio != instancia.contenido_html:
        instancia.contenido_html = limpio
        cambios.append('texto')
    if fecha_oficio and fecha_oficio != instancia.fecha_oficio:
        instancia.fecha_oficio = fecha_oficio
        cambios.append('fecha')
    if (testigo_1, testigo_2) != (instancia.testigo_1, instancia.testigo_2):
        instancia.testigo_1, instancia.testigo_2 = testigo_1, testigo_2
        cambios.append('testigos')
    if cambios:
        instancia.save()
        _historial(instancia, Accion.EDITADO, usuario, 'Cambió: ' + ', '.join(cambios) + '.')
    return cambios


def revisar(instancia, contexto=None):
    """(errores que impiden imprimir, avisos). Los avisos son datos vacíos que sí se usan."""
    contexto = contexto if contexto is not None else contexto_para(instancia)
    expediente = instancia.persona.expediente
    errores, avisos = [], []

    if not expediente.firmante:
        errores.append('Falta el firmante del expediente.')
    elif not expediente.firmante.fundamento:
        errores.append(
            f'{expediente.firmante.nombre_para_oficio} no tiene fundamento. '
            'Asígnale uno en Empleados ("Cambiar").'
        )
    if instancia.plantilla.requiere_testigos and not all(instancia.testigos):
        errores.append('Faltan los 2 testigos de asistencia.')

    por_llenar = pendientes(instancia.contenido_html)
    if por_llenar:
        errores.append('Falta llenar en el texto: ' + ', '.join(f'«{p}»' for p in por_llenar) + '.')

    _html, desconocidas = sustituir(instancia.contenido_html, contexto)
    if desconocidas:
        errores.append('El texto usa variables que no existen: '
                       + ', '.join('{{' + v + '}}' for v in desconocidas) + '.')
    if instancia.plantilla.evidencias and EVIDENCIAS_RE.search(instancia.contenido_html):
        lista = list(instancia.persona.evidencias.filter(plantilla=instancia.plantilla))
        if not lista:
            avisos.append('No hay evidencias capturadas: sale un espacio en blanco para llenarlo a mano.')
        elif any(not e.foto for e in lista):
            avisos.append('Hay evidencias sin foto: sale su recuadro vacío.')
    vacias = [v for v in variables_usadas(instancia.contenido_html) if v in contexto and not contexto[v]]
    if vacias:
        avisos.append('Sin dato (saldrá en blanco): ' + ', '.join(ETIQUETAS.get(v, v) for v in vacias) + '.')
    return errores, avisos


def _slug(texto):
    plano = unicodedata.normalize('NFKD', texto or '').encode('ascii', 'ignore').decode()
    return re.sub(r'[^A-Za-z0-9]+', '_', plano).strip('_')[:40] or 'persona'


def nombre_archivo(instancia, extension):
    exp = instancia.persona.expediente
    return f'{exp.folio}_{instancia.plantilla.clave}_{_slug(instancia.persona.nombre)}.{extension}'


@transaction.atomic
def imprimir(instancia, usuario):
    """Congela el oficio: guarda variables y .docx y lo deja de solo lectura."""
    _exigir_borrador(instancia)
    contexto = contexto_para(instancia)
    errores, _avisos = revisar(instancia, contexto)
    if errores:
        raise ErrorOficio(' '.join(errores))
    docx = render_docx([pieza_de(instancia, contexto)])
    instancia.snap_contexto = contexto
    instancia.snap_formato = formato_de_instancia(instancia)
    instancia.estado = OficioInstancia.Estado.IMPRESO
    instancia.impreso_en = timezone.now()
    instancia.impreso_por = usuario
    instancia.docx_impreso.save(nombre_archivo(instancia, 'docx'), ContentFile(docx), save=False)
    instancia.save()
    _historial(instancia, Accion.IMPRESO, usuario)
    return docx


@transaction.atomic
def reabrir(instancia, usuario, motivo):
    motivo = (motivo or '').strip()
    if instancia.editable:
        raise ErrorOficio('El oficio ya está en borrador.')
    if not motivo:
        raise ErrorOficio('Escribe el motivo para reabrir el oficio.')
    archivo = instancia.docx_impreso.name if instancia.docx_impreso else ''
    instancia.estado = OficioInstancia.Estado.BORRADOR
    instancia.snap_contexto = None
    instancia.snap_formato = None
    instancia.docx_impreso = None
    instancia.impreso_en = None
    instancia.impreso_por = None
    instancia.save()
    detalle = f'Motivo: {motivo}' + (f' (impresión anterior: {archivo})' if archivo else '')
    _historial(instancia, Accion.REABIERTO, usuario, detalle)


# ---------------------------------------------------------------- familia y paquete

# Formatos que normalmente lleva cada resultado (los 2 PDF firmados de la USB: internación
# AI000278 y rechazo AR000316). Solo preselecciona casillas: el usuario elige.
FORMATOS_SUGERIDOS = {
    Expediente.Resultado.INTERNACION: {2, 3, 4, 7, 8, 9},
    Expediente.Resultado.RECHAZO: {2, 3, 4, 5, 7, 8, 9, 11, 13, 14},
    Expediente.Resultado.PENDIENTE: {2, 3, 4, 7, 8, 9},
}


def crear_borradores_familia(expediente, plantillas, usuario):
    """Los mismos formatos para todas las personas. Devuelve cuántos borradores se crearon."""
    plantillas = list(plantillas)
    return sum(len(crear_borradores(p, plantillas, usuario)) for p in expediente.personas.all())


def ordenar_paquete(instancias):
    """Orden del paquete: por persona y, dentro de cada una, del 02 al 14 (como los PDF firmados)."""
    return sorted(instancias, key=lambda i: (i.persona.orden, i.persona_id, i.plantilla.numero))


def render_paquete(instancias):
    """Un solo .docx con una sección por oficio. Los impresos salen con lo congelado."""
    return render_docx([pieza_de(i) for i in ordenar_paquete(instancias)])


def nombre_paquete(expediente, instancias, extension):
    personas = {i.persona_id: i.persona for i in instancias}
    if len(personas) == 1:
        return f'{expediente.folio}_{_slug(next(iter(personas.values())).nombre)}_paquete.{extension}'
    return f'{expediente.folio}_paquete.{extension}'


def imprimir_varios(instancias, usuario):
    """Marca como impresos los borradores. Devuelve (impresos, [(instancia, error)]). Los que ya lo están se saltan."""
    impresos, errores = [], []
    for instancia in ordenar_paquete(instancias):
        if not instancia.editable:
            continue
        try:
            imprimir(instancia, usuario)
        except ErrorOficio as e:
            errores.append((instancia, str(e)))
        else:
            impresos.append(instancia)
    return impresos, errores


def docx_de(instancia):
    """El .docx del oficio: el congelado si ya se imprimió; si no, generado con los datos actuales."""
    if not instancia.editable and instancia.docx_impreso:
        try:
            with instancia.docx_impreso.open('rb') as fh:
                return fh.read()
        except FileNotFoundError:
            pass  # el archivo se perdió: se regenera con lo congelado (snap_contexto)
    return render_docx([pieza_de(instancia)])


# ---------------------------------------------------------------- evidencias (09 y 05)

def evidencias_bloqueadas(persona, plantilla):
    """Si el oficio de ese formato ya está impreso, sus evidencias no cambian hasta reabrirlo."""
    return persona.oficios.filter(plantilla=plantilla, estado=OficioInstancia.Estado.IMPRESO).exists()


def _exigir_evidencias_editables(persona, plantilla):
    if not plantilla.evidencias:
        raise ErrorOficio(f'El formato {plantilla.clave} no lleva evidencias.')
    if evidencias_bloqueadas(persona, plantilla):
        raise ErrorOficio(f'El {plantilla.clave} de {persona.nombre} ya está impreso: reábrelo para cambiar sus evidencias.')


def siguiente_orden_evidencia(persona, plantilla):
    ultimo = persona.evidencias.filter(plantilla=plantilla).order_by('-orden').values_list('orden', flat=True).first()
    return (ultimo or 0) + 1


def guardar_evidencia(evidencia, usuario):
    """Alta o edición (la evidencia ya trae persona y plantilla)."""
    _exigir_evidencias_editables(evidencia.persona, evidencia.plantilla)
    if not evidencia.pk:
        evidencia.creada_por = usuario
        if not evidencia.orden:
            evidencia.orden = siguiente_orden_evidencia(evidencia.persona, evidencia.plantilla)
    evidencia.save()
    return evidencia


def quitar_evidencia(evidencia):
    _exigir_evidencias_editables(evidencia.persona, evidencia.plantilla)
    if evidencia.foto:
        evidencia.foto.delete(save=False)
    evidencia.delete()


def importar_de_camara(persona, plantilla, foto_rechazo, usuario):
    """Copia una foto de la app Cámara (de este pasajero) como evidencia nueva."""
    from ..models import Evidencia
    _exigir_evidencias_editables(persona, plantilla)
    if not persona.registro_id or foto_rechazo.registro_id != persona.registro_id:
        raise ErrorOficio('Esa foto no es de este pasajero.')
    evidencia = Evidencia(persona=persona, plantilla=plantilla, foto_rechazo=foto_rechazo,
                          nota=foto_rechazo.notas or '', creada_por=usuario,
                          orden=siguiente_orden_evidencia(persona, plantilla))
    with foto_rechazo.foto.open('rb') as fh:
        evidencia.foto.save(foto_rechazo.nombre_archivo, ContentFile(fh.read()), save=False)
    evidencia.save()
    return evidencia
