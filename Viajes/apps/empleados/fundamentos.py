"""
Fundamento legal del firmante según su plaza.

En los oficios, el párrafo del fundamento cambia según quién firma, por ejemplo:

    …Gobernación vigente (D.O.F 21/03/2025) y Artículo 14, apartado B,
    fracciones I, II y III del ACUERDO por el que se delegan atribuciones…

El catálogo (`FundamentoPlaza`) es propio de Viajes: la Estancia no lo conoce.
Cada fundamento se asigna solo por la plaza que replica la Estancia (D-144):

  - `plaza_empieza_con`: la plaza debe empezar con ese texto, en palabras
    completas. Vacío = ese fundamento nunca se asigna solo (ej. Sub
    Representante Federal, que hoy no existe como plaza): solo a mano.
  - `descripcion_contiene`: además, la descripción de la plaza debe contenerlo.
    Hace falta para el Subdirector de Control y Verificación, porque D-144 deja
    todas las subdirecciones como "SUBDIRECTOR DE ÁREA".

Si varias filas aplican, gana la más específica: prefijo más largo y, a igualdad,
la que también pide descripción. Se compara sin acentos, en mayúsculas y con
espacios simples.

Este módulo no importa modelos: recibe el catálogo ya cargado, para que el
listado y el buscador resuelvan muchos empleados con una sola consulta.
"""
import unicodedata


def normalizar(texto):
    """MAYÚSCULAS sin acentos y con espacios simples (solo para comparar).

    Copia de `normalizar` en `apps/Personal/plazas.py` de la Estancia: si allá
    cambia, copiar aquí.
    """
    sin_acentos = ''.join(
        c for c in unicodedata.normalize('NFD', texto or '')
        if unicodedata.category(c) != 'Mn'
    )
    return ' '.join(sin_acentos.upper().split())


def _empieza_con(texto, prefijo):
    """True si `texto` empieza con `prefijo` en palabras completas (TITULAR ≠ TITULARIDAD)."""
    return texto == prefijo or texto.startswith(prefijo + ' ')


def elegir_fundamento(plaza, descripcion, catalogo):
    """El fundamento de `catalogo` que le toca a la plaza, o None.

    `catalogo`: filas de `FundamentoPlaza` (o cualquier objeto con `activo`,
    `plaza_empieza_con` y `descripcion_contiene`).
    """
    plaza_n = normalizar(plaza)
    if not plaza_n:
        return None
    descripcion_n = normalizar(descripcion)

    mejor, mejor_rango = None, None
    for fundamento in catalogo:
        prefijo = normalizar(fundamento.plaza_empieza_con)
        if not fundamento.activo or not prefijo or not _empieza_con(plaza_n, prefijo):
            continue
        contiene = normalizar(fundamento.descripcion_contiene)
        if contiene and contiene not in descripcion_n:
            continue
        rango = (len(prefijo), bool(contiene))
        if mejor_rango is None or rango > mejor_rango:
            mejor, mejor_rango = fundamento, rango
    return mejor
