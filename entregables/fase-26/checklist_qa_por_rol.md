# Checklist QA por rol · Kill switch

**Fase 26 · PR 28 · Rediseño INM-Viajes**

Smoke test que se ejecuta **antes de mergear el kill switch** (retiro de DaisyUI) y tras cada `collectstatic`. Marcar todo en verde por rol antes de retirar el CDN.

---

## Precondición del kill switch (bloqueante)

- [ ] `grep -r "cdn.tailwindcss.com\|daisyui" apps/` → **0** resultados en templates
- [ ] `grep -rE "\b(btn|card|modal|badge|input-bordered|table-zebra|tab-active|drawer|navbar|collapse|dropdown|toggle)\b" apps/**/templates` → **0** clases daisy sin prefijo `ds-`
- [ ] Build local compila sin error: `tailwindcss -c tailwind.config.js -i tailwind.src.css -o tailwind.min.css --minify`
- [ ] `collectstatic` sin warnings; `tailwind.min.css` presente en `staticfiles/`
- [ ] Tamaño de `tailwind.min.css` razonable (decenas de KB, no MB) → confirma que el purge corrió

---

## SuperUser

- [ ] Login → redirige al **Home dashboard** (F24), no a una lista
- [ ] KPIs del día muestran cifras (no `0` por error de context)
- [ ] Alerta de casos críticos enlaza a Casos Especiales
- [ ] Reporte por fechas (F7): filtros aplican, KPIs y tabla coherentes
- [ ] Export PDF / Excel / Imagen funciona en F7, F8, F9
- [ ] Inadmitidos (F8): export html2canvas mantiene fidelidad (CSS plano)
- [ ] Gestión de lotes (F10): badges de estado correctos
- [ ] Borrar lote: botón deshabilitado hasta tipear el nombre exacto
- [ ] Crear usuario (F12): radio-cards de rol + resumen de acceso vivo
- [ ] Duplicados (F11): conservar A / B / ambos; progreso avanza

## Aeropuerto

- [ ] Login → **Home operativo** (F25) con 3 acciones grandes
- [ ] Contador de notificaciones críticas visible (número, no solo color)
- [ ] Resumen del turno con cifras reales
- [ ] Subir Excel (F4): dropzone por clic Y por teclado; etapas + progreso
- [ ] Registros (F5·bis): toggle SR activa R/I **sin recargar**
- [ ] R/I deshabilitados muestran tooltip "Requiere SR activo"
- [ ] Foto de rechazo: pegar con Ctrl+V sigue funcionando
- [ ] Modal Tiempos (F13): autosave con "Guardado ✓"; duración autocalculada
- [ ] Modal Menor (F14): validación inline; CTA habilitado solo al validar las 3 secciones
- [ ] Casos Especiales (F6): split view, un caso a la vez

## General

- [ ] Login → **Home mínimo** (F25): solo 2 buscadores
- [ ] Forzar una URL admin por barra → **403** con página institucional
- [ ] Directorio (F15): buscar con debounce; ver ficha (F18)
- [ ] No aparece CTA "Agregar"/"Editar" (sin permiso)
- [ ] Redacciones (F19): grid de tarjetas; abrir preview PDF (F22)
- [ ] Descargar / imprimir / abrir en pestaña desde el visor

---

## Transversal (los 3 roles)

- [ ] Navegación completa por teclado (Tab/Shift+Tab/Enter/Esc)
- [ ] Foco visible en cada control (anillo doble)
- [ ] Zoom 200%: sin scroll horizontal ni recorte
- [ ] Escala de grises: todo estado sigue distinguible
- [ ] `prefers-reduced-motion`: sin animaciones
- [ ] Sin internet: la fuente cae al system stack; layout intacto
- [ ] Toasts de Django messages aparecen y se autocierran
- [ ] Páginas de error (F23): 400/403/404 institucionales; **500 se ve sin estáticos** (CSS inline)
- [ ] Sidebar recuerda su estado (localStorage) entre navegaciones

---

## Post-merge

- [ ] Monitorear logs 24h por 404 de estáticos o errores de plantilla
- [ ] Confirmar métricas base para el seguimiento (tiempo por tarea, clics, SUS)
- [ ] Rollback listo: revertir el `<link>` a los `<script>/<link>` del CDN (1 línea) si algo falla
