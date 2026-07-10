/* ====================================================================
   INM-VIAJES · tailwind.config.js — ACTIVADO EN FASE 26 (PR 28)
   --------------------------------------------------------------------
   Este archivo se preparó en Fase 0 y se ACTIVA aquí, al pasar de
   Tailwind CDN a build local con purge. Es idéntico al de Fase 0 salvo
   esta nota de activación: no se cambia la configuración, solo se
   empieza a usar para compilar tailwind.min.css.

   COMANDO DE BUILD (binario standalone, sin Node en producción):
     ./herramientas/tailwindcss -c tailwind.config.js \
       -i apps/uploader/static/css/tailwind.src.css \
       -o apps/uploader/static/css/tailwind.min.css --minify
   Luego: python manage.py collectstatic --noinput
   ==================================================================== */

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './apps/**/templates/**/*.html',
    './apps/**/static/js/**/*.js',
  ],

  theme: {
    extend: {
      /* Colores → tokens CSS (una sola fuente de verdad con design-system.css) */
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
      borderRadius: { 'ds-sm': '6px', 'ds-md': '8px', 'ds-lg': '12px' },
      boxShadow: {
        'ds-xs': '0 1px 2px rgba(26,28,30,0.06)',
        'ds-sm': '0 1px 3px rgba(26,28,30,0.09), 0 1px 2px rgba(26,28,30,0.04)',
        'ds-md': '0 4px 12px rgba(26,28,30,0.10), 0 2px 4px rgba(26,28,30,0.05)',
        'ds-lg': '0 12px 32px rgba(26,28,30,0.14), 0 4px 8px rgba(26,28,30,0.06)',
      },
      maxWidth: { 'ds-container': '1400px', 'ds-form': '720px', 'ds-read': '860px' },
    },
  },

  /* Clases generadas por JS (no aparecen en templates): el purge las
     borraría sin este safelist. MANTENER SINCRONIZADO con los .js. */
  safelist: [
    'ds-toast', 'ds-toast-success', 'ds-toast-danger', 'ds-toast-warning', 'ds-toast-info',
    'ds-dropzone-over', 'ds-row-selected', 'ds-side-closed',
    'ds-step-done', 'ds-step-current', 'ds-invalid',
    'paso-ok', 'paso-actual',  /* fase 14 · validación inline del modal de menor */
  ],

  corePlugins: { preflight: true },
  plugins: [],
};
