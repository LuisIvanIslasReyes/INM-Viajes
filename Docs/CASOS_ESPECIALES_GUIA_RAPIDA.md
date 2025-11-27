# 🔔 Casos Especiales - Guía Rápida

## ¿Qué son los Casos Especiales?

Cuando subes un archivo Excel y una persona tiene el mismo número de documento que otra persona que ya está en el sistema **pero en un vuelo o fecha diferente**, el sistema:

1. ✅ **NO bloquea** el registro (permite que se suba)

## ¿Cuándo se crean?

### ✅ SÍ se crea caso especial:
- Mismo documento + mismo vuelo + misma fecha = **Duplicado Real**
- Ejemplo: Juan Pérez en vuelo CA123 del 24/11 aparece dos veces en el archivo

- Mimso nombre + Mismo documento + mismo vuelo + misma fecha = **Duplicado Real**
- Ejemplo: Juan Pérez en vuelo CA123 del 24/11 aparece dos veces en el archivo

## Cómo Acceder

**Menú Principal** → **🔔 Casos Especiales**

## Estados de un Caso

| Ícono | Estado | Significado |
|-------|--------|-------------|
| 🔔 | Pendiente | Necesita tu revisión |
| ✅ | Aceptado | Aprobaste ambos registros |
| ✏️ | Editado | Corregiste el documento |
| 🚫 | Inadmitido | Marcaste como inválido |
| 🗑️ | Eliminado | Eliminaste el registro |

## 4 Acciones Posibles

### 1. ✅ Aceptar Ambos
**Úsalo cuando**: Ambos registros son válidos (ej. hermanos con mismo documento)

**Qué hace**: Marca todos los registros como confirmados

**Ejemplo**: Luis y María son hermanos, tienen el mismo documento, viajaron el mismo día en el mismo vuelo

---

### 2. ✏️ Editar Documento
**Úsalo cuando**: Se ingresó un documento incorrecto

**Qué hace**: Cambia el número de documento del registro que elijas

**Ejemplo**: Se ingresó "12345" pero debería ser "12346"

---

### 3. 🚫 Inadmitir
**Úsalo cuando**: El registro es inválido pero quieres conservarlo

**Qué hace**: Marca el registro como inadmitido (se conserva en el sistema para auditoría)

**Ejemplo**: El pasajero no abordó el vuelo finalmente

---

### 4. 🗑️ Eliminar
**Úsalo cuando**: El registro está completamente mal y debe desaparecer

**Qué hace**: ⚠️ **ELIMINA PERMANENTEMENTE** el registro (no se puede deshacer)

**Ejemplo**: Registro ingresado por error total

## Flujo Rápido de Revisión

```
1. Ve a "Casos Especiales" → Filtro "Pendientes"
2. Lee la información de ambos registros
3. Compara:
   - ¿Son personas diferentes? → Aceptar Ambos
   - ¿Documento incorrecto? → Editar Documento
   - ¿Pasajero no viajó? → Inadmitir
   - ¿Error total? → Eliminar
4. ¡Listo! El caso queda resuelto
```

## Ejemplos Comunes

### 👨‍👩‍👧‍👦 Hermanos con Mismo Documento
```
Juan García - Doc: 111 - Vuelo: CA123 - 24/11
Ana García  - Doc: 111 - Vuelo: CA123 - 24/11
```
**Acción**: ✅ Aceptar Ambos

---

### ✏️ Error al Escribir el Documento
```
Pedro López - Doc: 222 - Vuelo: CA123 - 24/11
Pedro López - Doc: 222 - Vuelo: CA789 - 25/11
(El segundo debería ser Doc: 333)
```
**Acción**: ✏️ Editar Documento del segundo a "333"

---

### 🚫 Pasajero No Abordó
```
María Ruiz - Doc: 444 - Vuelo: CA123 - 24/11 ✅ (viajó)
María Ruiz - Doc: 444 - Vuelo: CA456 - 25/11 ❌ (canceló)
```
**Acción**: 🚫 Inadmitir el segundo registro

---

### 🗑️ Registro Completamente Erróneo
```
Carlos Díaz - Doc: 555 - Vuelo: CA123 - 24/11 ✅ (correcto)
Carlos Díaz - Doc: 555 - Vuelo: CA123 - 24/11 ❌ (duplicado error)
```
**Acción**: 🗑️ Eliminar el registro duplicado

## Consejos Importantes

✅ **HAZ**:
- Revisa casos pendientes diariamente
- Lee toda la información antes de decidir
- Usa "Inadmitir" en vez de "Eliminar" cuando sea posible (mantiene auditoría)
- Confirma antes de eliminar (es permanente)

❌ **NO HAGAS**:
- Eliminar registros sin revisar bien
- Ignorar casos pendientes por mucho tiempo
- Aceptar sin investigar si hay dudas

## ¿Necesitas Ayuda?

Si no estás seguro de qué acción tomar:

1. Contacta al usuario que subió el archivo
2. Revisa los archivos Excel originales
3. Verifica con el personal de vuelo
4. En caso de duda, usa "Inadmitir" (se puede revertir más fácilmente que "Eliminar")

---

**Recuerda**: El sistema te ayuda a mantener la base de datos limpia sin bloquear cargas válidas. ¡Usa este módulo para revisar casos especiales de manera eficiente! 
