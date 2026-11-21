"""
Vistas del catálogo de empleados (réplica de la Estancia).

- listado:   consulta con búsqueda y filtro por municipio (todos los roles).
- buscar:    JSON para autocompletar (lo usarán los oficios para firmante/testigos).
- sincronizar / firmante: acciones POST, solo SuperUser y Aeropuerto.

Todo lee la réplica local, así que funciona aunque la Estancia esté apagada.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.cuentas.roles import puede_flujo_principal

from .models import Empleado, SincronizacionEmpleados
from .services import ErrorSincronizacion, sincronizar, ultima_sincronizacion_exitosa

LIMITE_BUSQUEDA = 20


def _filtrar(request, qs):
    """Aplica `q` (palabras en nombre/apellidos/número) y `municipio` (id de la Estancia)."""
    q = (request.GET.get('q') or '').strip()
    for palabra in q.split():
        qs = qs.filter(
            Q(nombres__icontains=palabra)
            | Q(apellidos__icontains=palabra)
            | Q(numero_empleado__icontains=palabra)
        )
    municipio = (request.GET.get('municipio') or '').strip()
    if municipio.isdigit():
        qs = qs.filter(municipio_id_estancia=int(municipio))
    return qs, q, municipio


def _gestion_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not puede_flujo_principal(request.user):
            messages.error(request, 'No tienes permiso para esta acción.')
            return redirect('empleados:listado')
        return view_func(request, *args, **kwargs)
    return login_required(_wrapped)


@login_required
def listado(request):
    inactivos = request.GET.get('inactivos') == '1'
    qs = Empleado.objects.all() if inactivos else Empleado.objects.filter(activo=True)
    qs, q, municipio = _filtrar(request, qs)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)

    municipios = (
        Empleado.objects.filter(activo=True)
        .exclude(municipio_id_estancia__isnull=True)
        .values_list('municipio_id_estancia', 'municipio')
        .distinct()
        .order_by('municipio')
    )
    context = {
        'page_obj': page_obj,
        'total': paginator.count,
        'busqueda': q,
        'municipio': municipio,
        'municipios': list(municipios),
        'inactivos': inactivos,
        'querystring': params.urlencode(),
        'ultima_ok': ultima_sincronizacion_exitosa(),
        'ultimo_intento': SincronizacionEmpleados.objects.first(),
        'puede_gestionar': puede_flujo_principal(request.user),
    }
    return render(request, 'empleados/listado.html', context)


@login_required
def buscar(request):
    """Autocompletar: hasta 20 empleados activos, firmantes habituales primero."""
    qs, _q, _m = _filtrar(request, Empleado.objects.filter(activo=True))
    datos = [
        {
            'id': e.pk,
            'numero_empleado': e.numero_empleado,
            'nombre_completo': e.nombre_completo,
            'nombre_para_oficio': e.nombre_para_oficio,
            'titulo': e.titulo_abreviado,
            'cargo': e.cargo,
            'plaza': e.plaza,
            'sexo': e.sexo,
            'municipio': e.municipio,
            'firmante_habitual': e.firmante_habitual,
        }
        for e in qs[:LIMITE_BUSQUEDA]
    ]
    return JsonResponse({'resultados': datos})


@require_POST
@_gestion_required
def sincronizar_ahora(request):
    try:
        r = sincronizar(origen=SincronizacionEmpleados.Origen.MANUAL, usuario=request.user)
    except ErrorSincronizacion as e:
        messages.error(request, f'No se pudo sincronizar: {e} Se sigue usando la última copia.')
    else:
        messages.success(
            request,
            f'Catálogo actualizado: {r.recibidos} recibidos, {r.creados} nuevos, '
            f'{r.actualizados} con cambios, {r.desactivados} desactivados.',
        )
    return redirect('empleados:listado')


@require_POST
@_gestion_required
def alternar_firmante(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    empleado.firmante_habitual = not empleado.firmante_habitual
    empleado.save(update_fields=['firmante_habitual'])
    estado = 'marcado como' if empleado.firmante_habitual else 'quitado de'
    messages.success(request, f'{empleado.nombre_completo} {estado} firmante habitual.')
    # Volver al mismo filtro/página del listado (solo querystring, nunca otra URL).
    querystring = (request.POST.get('querystring') or '').lstrip('?')
    destino = reverse('empleados:listado')
    return redirect(f'{destino}?{querystring}' if querystring else destino)
