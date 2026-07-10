# Anexo B · Guía WCAG 2.2 AA aplicada

**Fase 26 · PR 28 · Rediseño INM-Viajes**

Criterios de la WCAG 2.2 nivel AA que el design system garantiza por construcción, dónde se aplican en el sistema y cómo verificarlos. La accesibilidad no es una fase aparte: cada componente `ds-*` la trae de fábrica.

---

## Perceptible

### 1.1.1 Contenido no textual (A)
- **Regla:** todo icono decorativo lleva `aria-hidden="true"`; los informativos, `role="img"` + `<title>`.
- **Dónde:** todos los SVG `ds-icon`; el visor PDF (F22) lleva `title` + link de descarga como fallback.
- **Verificar:** ningún icono queda anunciado dos veces por el lector.

### 1.3.1 Información y relaciones (A)
- **Regla:** `<th scope="col">`, `<fieldset>/<legend>`, `<label for>` reales.
- **Dónde:** todas las tablas (`ds-table`), el grupo de rol en F12, cada `ds-field`.

### 1.4.1 Uso del color (A) — **criterio insignia del rediseño**
- **Regla:** el color nunca es el único indicador; siempre icono o texto.
- **Dónde:** badges de estado, toggles SR/R/I (F5·bis), prioridad de notificaciones (F5), diff de duplicados (F11), estados de lote (F10), badges de tipo de documento (F19).
- **Verificar:** en escala de grises, cada estado sigue siendo distinguible.

### 1.4.3 Contraste mínimo (AA)
- **Regla:** ≥4.5:1 texto normal, ≥3:1 texto grande y componentes de UI.
- **Dónde:** escalas de token validadas en `design-system.css` (guinda-700 = 11.5:1; neutrales con ratio anotado). **El dorado (#A57F2C = 3.7:1) está prohibido como texto de cuerpo** — solo plecas, líneas y sellos.

### 1.4.11 Contraste de no-texto (AA)
- **Regla:** bordes de input, foco y límites de control ≥3:1.
- **Dónde:** `--ds-border-strong` (#C9C9CE = 3:1 sobre blanco); anillo de foco guinda.

## Operable

### 2.1.1 Teclado (A)
- **Regla:** toda función accesible por teclado.
- **Dónde:** `<dialog>` y `<details>` nativos (modales, kebab, acordeón); dropzone con `<input>` real (F4/F20); radio-cards con `<input type=radio>` (F12).

### 2.4.7 Foco visible (AA) · 2.4.13 Apariencia del foco (AA 2.2)
- **Regla:** foco siempre visible, ≥2px, contraste ≥3:1.
- **Dónde:** anillo doble `--ds-focus-ring` (halo blanco + guinda) en cada control; variante inversa `--ds-focus-ring-inverse` sobre la navbar guinda.

### 2.4.8 Ubicación (AA)
- **Dónde:** breadcrumbs (`ds-crumbs` + `aria-current="page"`) en detalle de Directorio (F18) y Redacciones (F22).

### 2.5.8 Tamaño del objetivo (AA 2.2) — **mínimo 24×24; meta 44×44**
- **Regla:** targets ≥44×44px; en filas densas ≥24px con ≥8px de separación.
- **Dónde:** `ds-btn` (44px), `ds-btn-sm` (36px, solo filas densas), toggles, links de fila, acciones grandes del home Aeropuerto (F25).

## Comprensible

### 3.2.4 Identificación consistente (AA)
- **Dónde:** un patrón de reporte (F7→F8→F9), uno de formulario (F12→F16→F17→F20→F21), una dropzone (F4→F20). El mismo componente hace siempre lo mismo.

### 3.3.1 Identificación de errores (A) · 3.3.3 Sugerencia ante error (AA)
- **Regla:** errores en texto, asociados al campo, con sugerencia de corrección.
- **Dónde:** `ds-invalid` + `aria-invalid` + `ds-error-text` con `aria-describedby`; validación inline en F14 (menor) y F12/F16/F17 (formularios); confirmación tipada en borrado de lote (F10).

### 3.3.4 Prevención de errores (AA)
- **Dónde:** confirmación tipada en destructivos (F10), estado "cambios sin guardar" + `beforeunload` (F17), resumen antes de enviar (F12/F14), regla SR→R/I explicada en la UI (F5·bis).

## Robusto

### 4.1.2 Nombre, función, valor (A)
- **Dónde:** `aria-label` en todo control icon-only; `aria-pressed`/`aria-selected` en pills y tabs; `role="switch"` en toggles.

### 4.1.3 Mensajes de estado (AA)
- **Regla:** cambios de estado anunciados sin mover el foco.
- **Dónde:** `aria-live="polite"` en la región de toasts, autosave "Guardado ✓" (F13), progreso de subida (F4) y de revisión de duplicados (F11).

---

## Transversal (no es un criterio, es política)

- **`prefers-reduced-motion`** respetado globalmente (`design-system.css`) → animaciones a 0.01ms.
- **Sin internet:** Public Sans cae al system font stack; el sistema no depende de la fuente remota.
- **Skip link** `ds-sr-only` "Saltar al contenido" al inicio de `base.html`.

## Cómo se audita cada PR

1. Navegación completa por teclado (Tab / Shift+Tab / Enter / Esc).
2. Lector de pantalla (NVDA/VoiceOver) en el flujo principal del rol.
3. Zoom 200% sin pérdida de contenido ni scroll horizontal.
4. Verificación de contraste con los ratios anotados en `design-system.css`.
5. Escala de grises: ningún estado depende solo del color.
