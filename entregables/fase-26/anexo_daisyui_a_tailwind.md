# Anexo A · Mapa exhaustivo DaisyUI → `ds-*`

**Fase 26 · PR 28 · Rediseño INM-Viajes**

Tabla de equivalencias que consumió cada fase del plan. Regla general: donde DaisyUI dependía de JS de framework o de variables de tema (`oklch(var(--b2))`, `hsl(var(--p))`), el reemplazo usa **HTML nativo** (`<dialog>`, `<details>`) + una clase `ds-` autocontenida y **tokens `--ds-*`**. Ningún `ds-*` depende de DaisyUI.

---

## 1 · Botones

| DaisyUI | `ds-*` | Nota |
|---|---|---|
| `btn` | `ds-btn` | min-height 44px (target AA) |
| `btn-primary` | `ds-btn-primary` | **uno solo por vista** (regla de catálogo) |
| `btn-secondary` | `ds-btn-secondary` | borde + superficie |
| `btn-ghost` | `ds-btn-ghost` | — |
| `btn-error` | `ds-btn-danger` | `--ds-danger` ≠ guinda |
| — | `ds-btn-danger-ghost` | destructivo de baja prominencia (menús/tablas) |
| `btn-circle` / `btn-square` | `ds-btn-icon` | icon-only **siempre** con `aria-label` |
| `btn-sm` / `btn-lg` | `ds-btn-sm` / `ds-btn-lg` | — |
| `btn-block` | `ds-btn-block` | — |
| `loading` (spinner) | `ds-btn-spinner` | `<span>` con `@keyframes ds-spin` |
| botón en navbar | `ds-btn-on-dark` | foco inverso sobre guinda |

## 2 · Formularios

| DaisyUI | `ds-*` | Nota |
|---|---|---|
| `form-control` | `ds-field` | flex column + gap |
| `label` | `ds-label` | + `ds-req` para asterisco |
| `input input-bordered` | `ds-input` | — |
| `select` | `ds-select` | flecha SVG inline (sin dep. daisy) |
| `textarea` | `ds-textarea` | resize vertical |
| `checkbox` | `ds-check` | check SVG inline |
| `radio` | `ds-radio` | — |
| `toggle` | `ds-switch` | `role="switch"`; verde al activar |
| estado error | `ds-invalid` + `aria-invalid` | + `ds-error-text` con `aria-describedby` |
| ayuda de campo | `ds-help` | — |

## 3 · Datos y contenedores

| DaisyUI | `ds-*` | Nota |
|---|---|---|
| `badge` | `ds-badge` | nunca solo color: icono o texto |
| `badge-success/warning/error/info` | `ds-badge-success/warning/danger/info` | — |
| contador | `ds-badge-count` | número, no solo color |
| `card` / `card-body` / `card-title` | `ds-card` / `ds-card-body` / `ds-h3` | card en reposo: borde, no sombra |
| `table` / `table-zebra` | `ds-table` / `ds-table-compact` | thead sticky neutro |
| columna fija oklch | `ds-col-sticky` | **sustituye** el hack `oklch(var(--b2))` de admin_list.css |
| `progress` | `ds-progress` / `ds-progress-bar` | + `role="progressbar"` |
| etapas | `ds-steps` | Subiendo → Validando → Procesando |
| `skeleton` | `ds-skeleton*` | shimmer con `@keyframes` |

## 4 · Overlays e interacción (HTML nativo)

| DaisyUI | `ds-*` | Nota |
|---|---|---|
| `modal` / `modal-box` / `modal-action` | `<dialog class="ds-modal">` + `ds-modal-box` / `ds-modal-footer` | `showModal()`/`close()` → foco y Esc nativos |
| `dropdown` / `dropdown-content` / `menu` | `<details class="ds-menu">` + `ds-menu-list` | cierre por clic-fuera/Esc en base_ds.js |
| `collapse` / `collapse-title` / `collapse-content` | `<details class="ds-acc">` + `ds-acc-summary` / `ds-acc-body` | — |
| `alert alert-*` | `ds-alert ds-alert-*` | inline persistente, `role="alert"` |
| `tooltip` | `[data-ds-tip]` | CSS puro; info esencial también en `aria-label` |
| `tabs` / `tab-active` | `ds-tabs` / `ds-tab` + `[aria-selected]` | `role="tablist"` |
| pills de filtro | `ds-pill` + `[aria-pressed]` | — |
| chip de filtro activo | `ds-chip` / `ds-chip-x` | — |

## 5 · Layout / shell

| DaisyUI | `ds-*` | Nota |
|---|---|---|
| `navbar` | `ds-nav` | guinda profundo + pleca dorada |
| `drawer` / `menu` | `ds-side` / `ds-side-link` | estado activo `aria-current="page"` |
| breadcrumbs | `ds-crumbs` | separador CSS `::before` |
| empty state | `ds-empty` | siempre con CTA |

## 6 · JS que genera clases (migra con su vista)

| Origen | Antes (DaisyUI) | Ahora |
|---|---|---|
| Toasts | clases `alert alert-*` inyectadas | `window.dsToast(text, kind)` → `.ds-toast` |
| Toggle de fila | clases daisy en fetch | `.ds-switch` + actualización optimista (misma URL) |
| Dropzone dragover | — | `.ds-dropzone-over` (safelist) |
| Fila seleccionada | — | `.ds-row-selected` (safelist) |

## 7 · Variables de tema DaisyUI → tokens

| Antes | Ahora |
|---|---|
| `oklch(var(--b2))` | `var(--ds-bg-sunken)` |
| `hsl(var(--p))` | `var(--ds-primary)` |
| `var(--b1)` | `var(--ds-bg-surface)` |
| `var(--bc)` | `var(--ds-text)` |

> **Código muerto detectado:** `@apply badge badge-warning` en `casos_especiales.css` (CSS estático servido sin build) — el navegador lo ignora. Los badges se estilizaban por el CDN, no por ese archivo. Confirmado en el inventario de la Fase 2.

---

**Verificación de retiro (precondición del kill switch):**

```bash
grep -r "cdn.tailwindcss.com\|daisyui" apps/          # → 0 en templates
grep -rE "\b(btn|card|modal|badge|alert|input-bordered|table-zebra|tab-active|drawer|navbar|collapse|dropdown|toggle)\b" \
     apps/**/templates                                 # → 0 clases daisy sin ds-
```
