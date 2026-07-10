/* ====================================================================
   INM-VIAJES · tailwind.config.js (preparado en Fase 0, se ACTIVA en Fase 26)
   --------------------------------------------------------------------
   HOY el sistema usa Tailwind por CDN; este archivo deja lista la
   migración a build local sin Node en producción:

   PLAN DE MIGRACIÓN CDN → BUILD LOCAL (Fase 26):
   1. Descargar el binario standalone de Tailwind (no requiere Node):
        tailwindcss-linux-x64 v3.4.x → herramientas/tailwindcss
   2. Crear static/css/tailwind.src.css con:
        @tailwind base; @tailwind components; @tailwind utilities;
   3. Compilar:
        ./tailwindcss -c tailwind.config.js \
          -i apps/uploader/static/css/tailwind.src.css \
          -o apps/uploader/static/css/tailwind.min.css --minify
   4. En base_ds.html sustituir el <script src="cdn.tailwindcss.com">
      por <link rel="stylesheet" href="{% static 'css/tailwind.min.css' %}">
   5. `collectstatic` + smoke test QA por rol (checklist Fase 26).
   Rollback: revertir el <link> al <script> CDN (1 línea).
   ==================================================================== */

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './apps/**/templates/**/*.html',
    './apps/**/static/js/**/*.js',
  ],

  theme: {
    extend: {
      /* Los colores apuntan a los tokens CSS → una sola fuente de verdad.
         En templates: bg-guinda-700, text-warm-ink, border-neutral-200… */
      colors: {
        guinda: {
          50:  'var(--ds-guinda-50)',  100: 'var(--ds-guinda-100)',
          200: 'var(--ds-guinda-200)', 300: 'var(--ds-guinda-300)',
          400: 'var(--ds-guinda-400)', 500: 'var(--ds-guinda-500)',
          600: 'var(--ds-guinda-600)', 700: 'var(--ds-guinda-700)',
          800: 'var(--ds-guinda-800)', 900: 'var(--ds-guinda-900)',
          950: 'var(--ds-guinda-950)',
        },
        gold: {
          DEFAULT: 'var(--ds-gold)',
          soft: 'var(--ds-gold-soft)',
          tint: 'var(--ds-gold-tint)',
          ink:  'var(--ds-gold-ink)',
        },
        warm: {
          50:  'var(--ds-warm-50)',  100: 'var(--ds-warm-100)',
          200: 'var(--ds-warm-200)', 300: 'var(--ds-warm-300)',
          ink: 'var(--ds-warm-ink)',
        },
        success: { DEFAULT: 'var(--ds-success)', container: 'var(--ds-success-container)', on: 'var(--ds-on-success)' },
        warning: { DEFAULT: 'var(--ds-warning)', container: 'var(--ds-warning-container)', on: 'var(--ds-on-warning)' },
        danger:  { DEFAULT: 'var(--ds-danger)',  container: 'var(--ds-danger-container)',  on: 'var(--ds-on-danger)' },
        info:    { DEFAULT: 'var(--ds-info)',    container: 'var(--ds-info-container)',    on: 'var(--ds-on-info)' },
      },
      fontFamily: {
        sans: ['Public Sans', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['ui-monospace', 'SF Mono', 'Cascadia Mono', 'Segoe UI Mono', 'Menlo', 'Consolas', 'monospace'],
      },
      borderRadius: {
        'ds-sm': '6px', 'ds-md': '8px', 'ds-lg': '12px',
      },
      boxShadow: {
        'ds-xs': '0 1px 2px rgba(26,28,30,0.06)',
        'ds-sm': '0 1px 3px rgba(26,28,30,0.09), 0 1px 2px rgba(26,28,30,0.04)',
        'ds-md': '0 4px 12px rgba(26,28,30,0.10), 0 2px 4px rgba(26,28,30,0.05)',
        'ds-lg': '0 12px 32px rgba(26,28,30,0.14), 0 4px 8px rgba(26,28,30,0.06)',
      },
      maxWidth: {
        'ds-container': '1400px',
        'ds-form': '720px',
        'ds-read': '860px',
      },
    },
  },

  /* Clases generadas dinámicamente por JS (no aparecen en templates):
     el purge las conservará. Mantener sincronizado con los .js. */
  safelist: [
    'ds-toast', 'ds-toast-success', 'ds-toast-danger', 'ds-toast-warning', 'ds-toast-info',
    'ds-dropzone-over', 'ds-row-selected', 'ds-side-closed',
    'ds-step-done', 'ds-step-current', 'ds-invalid',
  ],

  corePlugins: {
    preflight: true,
  },
  plugins: [],
};
