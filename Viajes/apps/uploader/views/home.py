"""
Vistas de inicio por rol (Fase 25 · PR 04).

Introduce el enrutamiento post-login que la Fase 24 dejó pendiente: en vez de
mandar a todos a '/', un dispatcher lee el rol y aterriza a cada usuario en su
home correspondiente. NO crea modelos ni migraciones; los "resúmenes" son
count/filter sobre agregados existentes, igual que el dashboard de la F24.

  - SuperUser  -> home_admin      (dashboard de KPIs, F24)
  - Aeropuerto -> home_aeropuerto (3 acciones grandes + resumen del turno)
  - General    -> home_general    (solo Directorio y Redacciones)
"""
from datetime import datetime, time, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.cuentas.roles import es_aeropuerto, es_general, flujo_principal_required
from ..models import Registro, CasoEspecial, Notificacion


@login_required
def home(request):
    """Dispatcher post-login: redirige a la home propia de cada rol.

    Es la vista apuntada por LOGIN_REDIRECT_URL. No renderiza nada: solo
    resuelve el rol y delega. El fallback (usuario sin grupo) va al flujo
    principal, que a su vez lo reencaminará si no tuviera permiso.
    """
    user = request.user
    if user.is_superuser:
        return redirect('home_admin')
    if es_aeropuerto(user):
        return redirect('home_aeropuerto')
    if es_general(user):
        return redirect('home_general')
    return redirect('admin_list')


@flujo_principal_required
def home_aeropuerto(request):
    """Home operativo del rol Aeropuerto: 3 acciones grandes + resumen del turno.

    flujo_principal_required deja pasar a SuperUser y Aeropuerto, y reencamina a
    un eventual General a su propio módulo. El resumen usa los mismos agregados
    que el dashboard admin para no duplicar definiciones.
    """
    hoy = timezone.localdate()
    tz = timezone.get_current_timezone()
    inicio_hoy = datetime.combine(hoy, time.min, tzinfo=tz)
    fin_hoy = inicio_hoy + timedelta(days=1)

    # Turno legible según la hora local (matutino / vespertino / nocturno).
    hora = timezone.localtime().hour
    if 6 <= hora < 14:
        turno_nombre = 'Turno matutino'
    elif 14 <= hora < 22:
        turno_nombre = 'Turno vespertino'
    else:
        turno_nombre = 'Turno nocturno'

    context = {
        'turno_nombre': turno_nombre,
        # Registros cargados hoy.
        'resumen_registros': Registro.objects.filter(
            fecha_creacion__gte=inicio_hoy, fecha_creacion__lt=fin_hoy
        ).count(),
        # Marcados para Segunda Revisión aún sin resolver.
        'resumen_sr': Registro.objects.filter(
            segunda_revision=True, rechazado=False, internacion=False
        ).count(),
        # Casos especiales pendientes.
        'resumen_casos': CasoEspecial.objects.filter(estado='pendiente').count(),
        # Notificaciones sin leer del propio usuario (badge de la acción).
        'criticas_count': Notificacion.objects.filter(
            usuario=request.user, leida=False
        ).count(),
    }
    return render(request, 'uploader/home_aeropuerto.html', context)


@login_required
def home_general(request):
    """Home de consulta del rol General: accesos a Directorio y Redacciones.

    Sin context obligatorio; los formularios apuntan a las búsquedas existentes
    por querystring. Cualquier usuario autenticado puede verla (es solo lectura).
    """
    return render(request, 'uploader/home_general.html')
