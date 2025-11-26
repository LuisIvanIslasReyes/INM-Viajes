# 🔔 Módulo de Casos Especiales - Documentación

## 📋 Descripción General

El módulo de **Casos Especiales** permite manejar situaciones donde un número de documento aparece duplicado en diferentes vuelos o fechas, requiriendo validación manual por parte del administrador.

## 🎯 Casos de Uso

Este módulo es útil cuando:

1. **Hermanos con el mismo documento**: Dos personas diferentes registradas con el mismo número
2. **Error de captura**: Se ingresó el documento incorrecto por error
3. **Viajes múltiples**: La misma persona viajó en fechas/vuelos diferentes (esto es válido y el sistema lo permite automáticamente)

## 🔧 Funcionamiento

### Detección Automática

Cuando se sube un archivo Excel, el sistema:

1. **Valida duplicados exactos** (mismo documento + mismo vuelo + misma fecha):
   - ❌ **BLOQUEA** el registro (es un duplicado real)
   - ⚠️ Muestra mensaje de error

2. **Detecta documentos en diferentes vuelos/fechas**:
   - ✅ **PERMITE** el registro (puede ser válido)
   - 🔔 **CREA** un Caso Especial para revisión
   - 📧 Notifica al administrador

### Estados de un Caso Especial

| Estado | Descripción | Acción |
|--------|-------------|--------|
| 🔔 **Pendiente** | Requiere revisión del administrador | Sin acción aún |
| ✅ **Aceptado** | Ambos registros son válidos (ej. hermanos) | Confirmados todos |
| ✏️ **Editado** | Se corrigió el número de documento | Documento actualizado |
| 🚫 **Inadmitido** | Registro marcado como inadmitido | Marcado como inválido |
| 🗑️ **Eliminado** | Registro eliminado del sistema | Eliminado permanentemente |

## 🎨 Interfaz de Usuario

### Acceso al Módulo

Desde el menú principal: **🔔 Casos Especiales**

### Filtros Disponibles

- 🔔 **Pendientes**: Casos que requieren atención (con contador)
- ✅ **Aceptados**: Casos resueltos positivamente
- ✏️ **Editados**: Casos con documentos corregidos
- 🚫 **Inadmitidos**: Casos marcados como inválidos
- 🗑️ **Eliminados**: Casos con registros eliminados
- 📋 **Todos**: Vista completa de todos los casos

### Vista de Cada Caso

Cada caso muestra:

- **Registro Nuevo** (destacado con borde amarillo):
  - 👤 Nombre del pasajero
  - 🔢 Número de documento
  - ✈️ Número de vuelo
  - 📅 Fecha del vuelo
  - 🏠 Aeropuerto de salida
  - 🌍 Aeropuerto de llegada
  - 💺 Número de asiento
  - 📦 Archivo de origen

- **Registros Previos Conflictivos**:
  - Misma información detallada
  - Para comparar y validar

## 🛠️ Acciones Disponibles

### 1. ✅ Aceptar Ambos Registros

**Cuándo usar**: Cuando ambos registros son válidos (ej. hermanos con mismo documento)

**Efecto**:
- Marca todos los registros como `confirmado = True`
- Cambia el estado del caso a `aceptado`
- Registra el administrador que lo resolvió

**Ejemplo**: Luis y María (hermanos) tienen el mismo documento, ambos viajaron el mismo día pero en vuelos diferentes.

### 2. ✏️ Editar Documento

**Cuándo usar**: Cuando se ingresó un documento incorrecto por error

**Efecto**:
- Actualiza el número de documento del registro seleccionado
- Valida que el nuevo documento no exista para ese vuelo/fecha
- Cambia el estado del caso a `editado`
- Guarda el documento original y el nuevo

**Ejemplo**: Se ingresó documento "12345" pero debería ser "12346"

### 3. 🚫 Inadmitir Registro

**Cuándo usar**: Cuando el registro es inválido pero quieres conservarlo para auditoría

**Efecto**:
- Marca el registro seleccionado como `inadmitido = True`
- Agrega comentario automático
- Cambia el estado del caso a `inadmitido`
- El registro permanece en el sistema pero marcado como inválido

**Ejemplo**: Pasajero no abordó finalmente el vuelo

### 4. 🗑️ Eliminar Registro

**Cuándo usar**: Cuando el registro es completamente erróneo y debe eliminarse

**Efecto**:
- **ELIMINA PERMANENTEMENTE** el registro de la base de datos
- ⚠️ **ACCIÓN IRREVERSIBLE** - No se puede deshacer
- Cambia el estado del caso a `eliminado`

**Ejemplo**: Registro ingresado por error en el archivo equivocado

## 📊 Modelo de Datos

### CasoEspecial

```python
class CasoEspecial(models.Model):
    registro                    # Registro afectado (OneToOne)
    razon                       # documento_duplicado, mismo_vuelo_fecha, datos_sospechosos
    estado                      # pendiente, aceptado, editado, inadmitido, eliminado
    registros_conflictivos_ids  # Lista JSON de IDs de registros con mismo documento
    documento_original          # Número de documento que causó el conflicto
    documento_nuevo             # Nuevo documento si fue editado
    notas_admin                 # Notas del administrador
    resuelto_por                # Usuario que resolvió el caso
    fecha_creacion              # Cuándo se detectó
    fecha_resolucion            # Cuándo se resolvió
```

## 🔄 Flujo de Trabajo Completo

### Paso 1: Subida de Archivo
```
Usuario sube archivo Excel
    ↓
Sistema procesa cada registro
    ↓
¿Duplicado exacto (mismo vuelo+fecha)?
    → SÍ: ❌ Bloquear + mostrar error
    → NO: ¿Existe documento en otro vuelo/fecha?
        → SÍ: ✅ Crear registro + 🔔 Crear Caso Especial
        → NO: ✅ Crear registro normalmente
```

### Paso 2: Revisión del Administrador
```
Admin accede a "Casos Especiales"
    ↓
Filtra por "Pendientes"
    ↓
Revisa cada caso:
    - Compara información de ambos registros
    - Decide acción apropiada
    ↓
Ejecuta acción (Aceptar/Editar/Inadmitir/Eliminar)
    ↓
Caso marcado como resuelto
```

## 🎯 Ejemplos Prácticos

### Ejemplo 1: Hermanos con Mismo Documento ✅

**Situación**:
- Luis García - Doc: 12345 - Vuelo: CA123 - Fecha: 24/11/2025
- María García - Doc: 12345 - Vuelo: CA456 - Fecha: 24/11/2025

**Acción**: ✅ Aceptar Ambos Registros

**Resultado**: Ambos confirmados como válidos

---

### Ejemplo 2: Error de Captura ✏️

**Situación**:
- Juan Pérez - Doc: 11111 - Vuelo: CA123 - Fecha: 24/11/2025
- Juan Pérez - Doc: 11111 - Vuelo: CA789 - Fecha: 25/11/2025

**Investigación**: Se descubre que el segundo registro debería tener Doc: 22222

**Acción**: ✏️ Editar Documento del segundo registro a "22222"

**Resultado**: Caso resuelto, documento corregido

---

### Ejemplo 3: Registro Inválido 🚫

**Situación**:
- Pedro López - Doc: 33333 - Vuelo: CA123 - Fecha: 24/11/2025
- Pedro López - Doc: 33333 - Vuelo: CA456 - Fecha: 25/11/2025

**Investigación**: El segundo vuelo fue cancelado y el pasajero no viajó

**Acción**: 🚫 Inadmitir segundo registro

**Resultado**: Registro marcado como inadmitido, conservado para auditoría

---

### Ejemplo 4: Registro Erróneo 🗑️

**Situación**:
- Carlos Ruiz - Doc: 44444 - Vuelo: CA123 - Fecha: 24/11/2025
- Carlos Ruiz - Doc: 44444 - Vuelo: CA123 - Fecha: 24/11/2025 (duplicado exacto que pasó la validación por error)

**Acción**: 🗑️ Eliminar registro duplicado

**Resultado**: Registro eliminado permanentemente

## 🔐 Permisos y Seguridad

- ✅ Todos los usuarios autenticados pueden ver casos especiales
- ✅ Todos los usuarios pueden resolver casos (no requiere superusuario)
- ✅ Se registra quién resolvió cada caso y cuándo
- ✅ Las acciones quedan auditadas en `fecha_resolucion` y `resuelto_por`

## 📈 Métricas y Reportes

El módulo permite:

- 📊 Ver total de casos pendientes en el header
- 📊 Filtrar por estado para análisis
- 📊 Revisar histórico de casos resueltos
- 📊 Identificar patrones (ej. hermanos, errores frecuentes)

## 🚀 Integración con el Sistema

### URLs Configuradas

```python
/casos-especiales/                                    # Lista de casos
/casos-especiales/aceptar/<caso_id>/                  # Aceptar ambos
/casos-especiales/editar/<caso_id>/<registro_id>/     # Editar documento
/casos-especiales/inadmitir/<caso_id>/<registro_id>/  # Inadmitir registro
/casos-especiales/eliminar/<caso_id>/<registro_id>/   # Eliminar registro
```

### Vistas Principales

1. `casos_especiales_list()`: Lista filtrada de casos
2. `resolver_caso_aceptar()`: Acepta todos los registros
3. `resolver_caso_editar()`: Edita documento de un registro
4. `resolver_caso_inadmitir()`: Marca registro como inadmitido
5. `resolver_caso_eliminar()`: Elimina registro permanentemente

## 📝 Notas Importantes

### ⚠️ Advertencias

1. **Eliminación es permanente**: No hay papelera de reciclaje, el registro se borra de la BD
2. **Validación de documento nuevo**: Al editar, el sistema verifica que el nuevo documento no exista para ese vuelo/fecha
3. **Casos automáticos**: No se bloquea la carga, el registro se crea y se marca para revisión
4. **Auditoría completa**: Todas las acciones quedan registradas con usuario y fecha

### ✅ Buenas Prácticas

1. Revisar casos pendientes diariamente
2. Investigar antes de tomar acción
3. Usar "Inadmitir" en lugar de "Eliminar" cuando sea posible (para auditoría)
4. Agregar notas descriptivas al editar documentos
5. Confirmar con el usuario antes de eliminar permanentemente

## 🔮 Futuras Mejoras

- [ ] Notificaciones por email cuando se crea un caso especial
- [ ] Reportes de casos resueltos por usuario
- [ ] Exportar casos especiales a Excel
- [ ] Búsqueda por número de documento
- [ ] Filtros por fecha de creación
- [ ] Vista de timeline de acciones del caso

---

**Última actualización**: 26 de noviembre de 2025
**Versión del módulo**: 1.0
