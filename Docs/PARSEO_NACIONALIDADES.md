# Sistema de Parseo de Nacionalidades

## Resumen
Se implementó un sistema automático para convertir códigos ISO de países (como "CHN", "MEX", "USA") a nombres completos de países en español (como "China", "México", "Estados Unidos").

## Cambios Realizados

### 1. Diccionario de Códigos ISO (`views.py`)
Se agregó un diccionario completo con todos los códigos ISO de países según el estándar ISO 3166-1:
- **Códigos Alpha-3** (3 letras): CHN, MEX, USA, etc.
- **Códigos Alpha-2** (2 letras): CN, MX, US, etc.

El diccionario incluye más de 200 países con sus nombres en español.

### 2. Función de Parseo
```python
def obtener_nacionalidad(codigo_pais):
    """
    Convierte un código ISO de país a su nombre completo en español.
    
    Args:
        codigo_pais: Código ISO del país (ej: 'CHN', 'CN', 'MEX', 'MX')
        
    Returns:
        Nombre del país en español o el código original si no se encuentra
    """
```

### 3. Integración Automática en Upload
El sistema ahora automáticamente parsea las nacionalidades cuando se sube un archivo Excel:
- Lee el campo `codigo_pais_emision` del Excel
- Lo convierte al nombre completo del país
- Guarda el resultado en el campo `pais_emision`

### 4. Comando de Actualización
Se creó un comando de Django para actualizar registros existentes:
```bash
python manage.py actualizar_nacionalidades
```

Este comando:
- Procesa todos los registros en la base de datos
- Convierte los códigos ISO a nombres de países
- Actualiza el campo `pais_emision` automáticamente
- Muestra un reporte de progreso

## Resultados
✅ **691 registros actualizados exitosamente**

### Ejemplos de Conversión
- `CHN` → `China`
- `MEX` → `México`
- `USA` → `Estados Unidos`
- `CN` → `China` (código de 2 letras)
- `MX` → `México` (código de 2 letras)

## Uso Futuro
A partir de ahora, **todos los nuevos Excels** que se suban automáticamente tendrán:
1. El código ISO original en `codigo_pais_emision`
2. El nombre del país en español en `pais_emision`

Esto mejora:
- La legibilidad en los reportes (especialmente el PIN)
- Las búsquedas por nacionalidad
- La presentación de datos al usuario

## Archivos Modificados
- `uploader/views.py` - Agregado diccionario PAISES_ISO y función obtener_nacionalidad()
- `uploader/views.py` - Integrado parseo automático en upload_excel()
- `uploader/management/commands/actualizar_nacionalidades.py` - Nuevo comando de actualización

## Notas Técnicas
- El sistema es tolerante a mayúsculas/minúsculas
- Si un código no se encuentra en el diccionario, devuelve el código original
- Funciona tanto con códigos de 2 letras (ISO 3166-1 alpha-2) como de 3 letras (ISO 3166-1 alpha-3)
- Los registros existentes ya fueron actualizados y no requieren acción adicional
