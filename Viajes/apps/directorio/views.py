"""
Vistas del módulo Directorio (catálogo histórico de empresas).

Accesible a los tres roles (SuperUser, Aeropuerto y General): solo requieren estar
autenticados. No participa en el flujo principal ni genera PIN.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, models, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import EmpresaDirectorioForm
from .models import EmpresaDirectorio, ResolucionChoices


@login_required
def listado(request):
    """Consulta y búsqueda del directorio de empresas."""
    empresas = EmpresaDirectorio.objects.select_related('estado', 'creado_por')

    busqueda = (request.GET.get('q') or '').strip()
    if busqueda:
        empresas = empresas.filter(
            models.Q(empresa__icontains=busqueda) |
            models.Q(firma_encargado__icontains=busqueda) |
            models.Q(ciudad__icontains=busqueda)
        )

    resolucion = (request.GET.get('resolucion') or '').strip()
    if resolucion in ResolucionChoices.values:
        empresas = empresas.filter(tentativa_resolucion=resolucion)

    paginator = Paginator(empresas, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    params = request.GET.copy()
    params.pop('page', None)

    context = {
        'page_obj': page_obj,
        'busqueda': busqueda,
        'resolucion': resolucion,
        'resoluciones': ResolucionChoices.choices,
        'querystring': params.urlencode(),
        'total': paginator.count,
    }
    return render(request, 'directorio/listado.html', context)


@login_required
def crear(request):
    """
    Alta de empresa con lógica anti-duplicados:
    - Duplicado exacto (empresa + encargado + teléfono): se bloquea.
    - Misma empresa con datos distintos: se permite, previa confirmación del usuario.
    """
    coincidencias = None
    requiere_confirmacion = False

    if request.method == 'POST':
        form = EmpresaDirectorioForm(request.POST)
        if form.is_valid():
            empresa = EmpresaDirectorio._normaliza(form.cleaned_data['empresa'])
            encargado = EmpresaDirectorio._normaliza(form.cleaned_data['firma_encargado'])
            telefono = EmpresaDirectorio._normaliza(form.cleaned_data['telefono'])

            # 1) Duplicado exacto -> bloquear.
            existe_exacto = EmpresaDirectorio.objects.filter(
                empresa__iexact=empresa,
                firma_encargado__iexact=encargado,
                telefono=telefono,
            ).exists()
            if existe_exacto:
                messages.error(
                    request,
                    f'Ya existe un registro idéntico de "{empresa}" (mismo encargado y '
                    f'teléfono). Usa el registro existente como referencia.'
                )
                coincidencias = EmpresaDirectorio.objects.filter(empresa__iexact=empresa)
                return render(request, 'directorio/crear.html', {
                    'form': form, 'coincidencias': coincidencias,
                })

            # 2) Misma empresa con datos distintos -> permitir con confirmación.
            mismas_empresa = EmpresaDirectorio.objects.filter(empresa__iexact=empresa)
            confirmado = request.POST.get('confirmar') == '1'
            if mismas_empresa.exists() and not confirmado:
                messages.warning(
                    request,
                    f'Ya existen {mismas_empresa.count()} registro(s) de "{empresa}" con '
                    f'distinto encargado o teléfono. Revisa las coincidencias y confirma '
                    f'para registrar de todos modos.'
                )
                return render(request, 'directorio/crear.html', {
                    'form': form,
                    'coincidencias': mismas_empresa,
                    'requiere_confirmacion': True,
                })

            # 3) Guardar.
            empresa_obj = form.save(commit=False)
            empresa_obj.creado_por = request.user
            try:
                with transaction.atomic():
                    empresa_obj.save()
            except IntegrityError:
                messages.error(request, 'Ya existe un registro idéntico. No se creó un duplicado.')
                return render(request, 'directorio/crear.html', {'form': form})

            messages.success(request, f'Empresa "{empresa_obj.empresa}" registrada en el directorio.')
            return redirect('directorio:detalle', pk=empresa_obj.pk)
    else:
        form = EmpresaDirectorioForm()

    return render(request, 'directorio/crear.html', {
        'form': form,
        'coincidencias': coincidencias,
        'requiere_confirmacion': requiere_confirmacion,
    })


@login_required
def editar(request, pk):
    """
    Edición de una empresa del directorio.

    Disponible para todos los roles autenticados (SuperUser, Aeropuerto y General):
    todos pueden mantener actualizado el directorio.
    """
    empresa = get_object_or_404(EmpresaDirectorio, pk=pk)

    if request.method == 'POST':
        form = EmpresaDirectorioForm(request.POST, instance=empresa)
        if form.is_valid():
            try:
                with transaction.atomic():
                    empresa = form.save()
            except IntegrityError:
                messages.error(
                    request,
                    'Ya existe otro registro idéntico (misma empresa, encargado y '
                    'teléfono). Ajusta algún dato para diferenciarlo.'
                )
                return render(request, 'directorio/editar.html', {
                    'form': form, 'empresa': empresa,
                })
            messages.success(request, f'Empresa "{empresa.empresa}" actualizada.')
            return redirect('directorio:detalle', pk=empresa.pk)
    else:
        form = EmpresaDirectorioForm(instance=empresa)

    return render(request, 'directorio/editar.html', {
        'form': form, 'empresa': empresa,
    })


@login_required
def detalle(request, pk):
    """Ficha de una empresa del directorio."""
    empresa = get_object_or_404(
        EmpresaDirectorio.objects.select_related('estado', 'creado_por'), pk=pk
    )
    return render(request, 'directorio/detalle.html', {'empresa': empresa})


@login_required
def buscar_coincidencias(request):
    """Endpoint AJAX: coincidencias por nombre de empresa (búsqueda previa al alta)."""
    q = (request.GET.get('empresa') or '').strip()
    resultados = []
    if len(q) >= 2:
        qs = EmpresaDirectorio.objects.filter(
            empresa__icontains=q
        ).select_related('estado')[:10]
        resultados = [{
            'id': e.id,
            'empresa': e.empresa,
            'encargado': e.firma_encargado,
            'telefono': e.telefono,
            'ciudad': e.ciudad,
            'estado': e.estado.nombre if e.estado else '',
            'resolucion': e.get_tentativa_resolucion_display(),
            'url': reverse('directorio:detalle', args=[e.id]),
        } for e in qs]
    return JsonResponse({'resultados': resultados})
