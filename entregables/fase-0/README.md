# Fase 0 — Fundaciones del Design System · Guía de implementación

**PR 01 · rama sugerida:** `feature/f0-design-system`

## Archivos de este paquete → destino en el repo

| Archivo | Destino |
|---|---|
| `design-system.css` | `Viajes/apps/uploader/static/css/design-system.css` |
| `components.css` | `Viajes/apps/uploader/static/css/components.css` |
| `base_ds.html` | `Viajes/apps/uploader/templates/uploader/base_ds.html` |
| `tailwind.config.js` | `Viajes/tailwind.config.js` (inactivo hasta Fase 26) |

Icono: instalar `lucide-static` (o descargar release) y copiar `sprite.svg` a
`Viajes/apps/uploader/static/img/lucide-sprite.svg`. Uso:
`<svg class="ds-icon" aria-hidden="true"><use href="{% static 'img/lucide-sprite.svg' %}#search"/></svg>`.
Mientras tanto, los SVG inline estilo Lucide de `base_ds.html` funcionan sin dependencia.

## Qué NO toca esta fase

- `base.html` actual: intacto. Las vistas legadas siguen extendiéndolo.
- `views.py`, `models.py`, `urls.py`, endpoints, context: cero cambios.
- DaisyUI: sigue cargado en `base.html` para las vistas legadas.

## Cómo migra una vista (a partir de Fase 1)

1. Cambiar `{% extends 'uploader/base.html' %}` → `{% extends 'uploader/base_ds.html' %}`.
2. Reemplazar clases DaisyUI por `ds-*` según el mapa de su fase.
3. Si su JS genera clases (toasts, badges), usar `window.dsToast(...)` y clases `ds-*`.

**Rollback por vista:** revertir el extends (1 línea). **Rollback de la fase:** revert del PR
(los archivos nuevos no son referenciados por ninguna vista legada).

## Verificación manual de Fase 0

1. `collectstatic` y abrir cualquier vista legada con los 3 roles → **cero cambios visuales** (nada legado referencia los archivos nuevos).
2. Crear una vista de prueba `{% extends 'uploader/base_ds.html' %}` con un `ds-btn ds-btn-primary` → navbar guinda con pleca dorada, sidebar operativa, botón correcto.
3. Teclado: `Tab` recorre navbar → sidebar → contenido con anillo de foco visible en todo momento; `Esc` cierra menús kebab.
4. `dsToast('Prueba', 'success')` en consola → toast inferior derecho, se anuncia por lector de pantalla (región `aria-live`).
5. Django messages → aparecen como toasts al recargar.

## Notas de arquitectura

- **Dos shells en paralelo** (`base.html` legado / `base_ds.html` nuevo) en lugar de
  coexistencia por prefijos dentro de un mismo shell: elimina el riesgo de colisión
  DaisyUI↔custom por completo y hace el rollback por vista trivial.
- `components.css` es **autocontenido**: los componentes no dependen de utilidades
  Tailwind, así el purge de Fase 26 no puede romperlos y las páginas de error (Fase 23)
  pueden cargarlo sin Tailwind.
- El anillo de foco es doble (blanco + guinda) → visible sobre claro y oscuro,
  cumple WCAG 2.2 (2.4.13 apariencia del foco).
- `admin_list.css` usa `oklch(var(--b2))` (variables DaisyUI) en columnas sticky:
  la Fase 5·bis las sustituye por `.ds-col-sticky`.
