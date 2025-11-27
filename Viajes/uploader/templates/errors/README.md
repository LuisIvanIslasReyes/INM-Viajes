# 📁 Páginas de Error del Sistema

Esta carpeta contiene las páginas de error personalizadas que Django muestra cuando ocurren diferentes tipos de errores en **producción** (cuando `DEBUG=False`).

## 📄 Archivos

- **`404.html`** → Página no encontrada
- **`500.html`** → Error interno del servidor
- **`403.html`** → Acceso denegado / Sin permisos
- **`400.html`** → Solicitud incorrecta / Bad request

## 🔧 Configuración

Django busca automáticamente estos archivos cuando `DEBUG=False`. 

**Ubicaciones que Django verifica (en orden):**
1. `templates/errors/404.html` ✅ (Aquí están)
2. `templates/404.html`

## 🎨 Características

Todas las páginas incluyen:
- ✅ Diseño responsive (Tailwind CSS + DaisyUI)
- ✅ Iconos animados
- ✅ Explicaciones claras del error
- ✅ Botones de navegación
- ✅ Colores temáticos por tipo de error

## 📝 Notas

- Estas páginas solo se muestran en **producción** (`DEBUG=False`)
- En desarrollo (`DEBUG=True`), Django muestra sus propias páginas de error con información de debugging
- Para probarlas en desarrollo, temporalmente pon `DEBUG=False` en settings

---
**Última actualización:** Noviembre 2025
