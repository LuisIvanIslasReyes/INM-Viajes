# Nuevos Requerimientos

## Desarrollo de los módulos "Directorio" y "Redacciones"

Quiero que actúes como:

- Arquitecto de Software.
- Senior Full Stack Developer.
- Arquitecto de Base de Datos.
- Especialista en Django.
- Especialista en UI/UX.
- Analista Funcional.

Necesito que analices el siguiente requerimiento y propongas la mejor arquitectura posible.

No quiero únicamente código.

Quiero que primero analices la lógica de negocio, propongas mejoras, detectes posibles problemas futuros y únicamente después propongas la implementación.

---

# Contexto

Se desarrollarán **dos módulos completamente nuevos**:

1. Directorio
2. Redacciones

Estos módulos **NO forman parte del flujo principal del sistema**.

No tienen relación con:

- Viajes
- Excel de carga
- Segundas revisiones
- Rechazos existentes
- Pines
- Procesos de validación actuales
- Flujo principal del aeropuerto

Son módulos independientes que únicamente compartirán el sistema de autenticación.

---

# Gestión de Usuarios

Actualmente existen dos tipos de usuario:

- SuperUser
- Usuario Aeropuerto

El usuario Aeropuerto tiene acceso al listado principal y a todo el flujo operativo.

Ahora se requiere un tercer tipo de usuario.

## Nuevo Rol

**Usuario General**

Este usuario únicamente podrá acceder a:

- Directorio
- Redacciones

No podrá visualizar:

- Lista principal de Viajes
- Botones principales
- Panel operativo
- Funciones administrativas del flujo principal

## Permisos

### SuperUser

Puede acceder a:

- Flujo principal
- Directorio
- Redacciones
- Administración completa

### Usuario Aeropuerto

Puede acceder a:

- Flujo principal
- Directorio
- Redacciones

### Usuario General

Puede acceder únicamente a:

- Directorio
- Biblioteca de Redacciones

No tendrá acceso a ningún componente del flujo principal.

Quiero que me propongas la mejor forma de implementar estos permisos dentro de Django.

---

# Módulo Directorio

Este módulo funcionará como un catálogo histórico de empresas.

Su finalidad es permitir que los agentes consulten información previamente registrada sobre empresas que ya han participado en procesos migratorios.

No genera PIN.

No participa en ningún flujo.

Únicamente permite:

- Alta
- Consulta
- Búsqueda

---

## Campos

### Empresa

Texto libre.

```text
CharField
```

---

### Domicilio

Texto libre.

```text
CharField o TextField
```

---

### Estado

Aquí quiero una recomendación arquitectónica.

Actualmente existen únicamente los 32 estados de México.

Tengo dos opciones:

### Opción 1

Guardar únicamente los 32 estados en una tabla catálogo.

Después seleccionar uno.

---

### Opción 2

Utilizar una base de datos completa como:

https://github.com/khristoff/mexico-ciudades

La cual contiene:

- Países
- Estados
- Municipios
- Colonias

Quiero que analices:

- si realmente aporta valor
- si sería sobreingeniería
- el impacto en mantenimiento
- rendimiento
- escalabilidad

y me recomiendes la mejor alternativa.

---

### Ciudad

También necesito recomendación.

Actualmente pienso dos opciones.

Opción A

Ciudad como texto libre.

Opción B

Ciudad dependiente del Estado.

Analiza cuál tendría más sentido para este caso de uso.

---

### Firma del Encargado

Corresponde al nombre de la persona responsable.

```text
CharField
```

---

### Teléfono

Quiero que me recomiendes el tipo de dato correcto.

No quiero perder ceros.

Debe soportar:

- teléfonos fijos
- celulares
- posibles extensiones futuras

Analiza si debe ser:

- Integer
- BigInteger
- CharField

y justifica la decisión.

---

### Tentativa de Resolución

Será un catálogo cerrado.

Opciones:

- INTERNACIÓN
- RECHAZO

No existirán más valores.

---

# Lógica del Directorio

Este catálogo servirá como referencia histórica.

Muchos extranjeros llegan indicando que asistirán a entrevistas laborales.

Antes de registrar una nueva empresa, el usuario debe poder realizar una búsqueda previa.

Ejemplo:

Busca:

```
Alphacom
```

Si ya existe.

Debe mostrar coincidencias.

Ejemplo:

Empresa

Alphacom

Encargado

Javier

Resolución

Internación

---

Empresa

Alphacom

Encargado

Victoria

Resolución

Rechazo

---

Si la información coincide exactamente con la proporcionada por el extranjero, simplemente utilizarán la existente como referencia.

Si el encargado o teléfono son distintos, entonces sí podrá registrarse una nueva entrada.

Es decir:

La empresa NO debe ser única.

Puede repetirse siempre que exista una diferencia relevante en la información.

Quiero que propongas la mejor lógica para evitar duplicados innecesarios sin impedir nuevos registros válidos.

---

# Módulo Redacciones

Este módulo será una biblioteca documental.

Su finalidad es reutilizar documentos previamente aceptados o rechazados.

Contexto:

Dependiendo de:

- nacionalidad
- resolución
- motivo

Los agentes redactan documentos (actas, oficios, etc.) que posteriormente son enviados a oficinas centrales para su revisión y aprobación.

Actualmente muchos documentos vuelven a redactarse desde cero.

Se desea construir una biblioteca compartida.

---

# Usuarios que podrán subir archivos

Únicamente:

- SuperUser
- Usuario Aeropuerto

---

# Usuarios que únicamente consultan

Usuario General.

Este usuario NO podrá subir documentos.

Únicamente podrá:

- buscar
- visualizar
- descargar

---

# Información de cada documento

## Resolución

Catálogo:

- INTERNACIÓN
- RECHAZO

---

## Tema

Inicialmente será texto libre.

En un futuro probablemente exista un catálogo.

Diseña el sistema considerando esa futura migración.

---

## País

Debe existir un catálogo de países.

No quiero texto libre.

Analiza la mejor fuente de datos.

---

## Archivo

Se deberá permitir subir archivos como:

- .doc
- .docx

Analiza si conviene permitir además:

- PDF
- ODT

Justifica la decisión.

---

# Funcionalidades

Los usuarios deberán poder buscar utilizando filtros.

Filtros:

- Resolución
- Tema
- País

Se podrán combinar.

Ejemplo:

```
Resolución:
RECHAZO

Tema:
DOCUMENTACIÓN FALSA

País:
COLOMBIA
```

Resultado:

Todos los documentos que cumplan esos criterios.

---

# Vista previa

Analiza si técnicamente es viable mostrar una vista previa del documento Word dentro del sistema.

En caso de no ser recomendable:

Propón alternativas.

Por ejemplo:

- conversión automática a PDF
- visor integrado
- miniaturas
- visualización parcial

Quiero conocer ventajas y desventajas.

---

# Descarga

Cada documento deberá tener un botón para descargar el archivo original.

---

# Lo que espero de tu respuesta

Quiero que antes de escribir código realices un análisis completo.

Necesito que desarrolles:

1. Análisis funcional.
2. Casos de uso.
3. Diseño de permisos.
4. Modelo de Base de Datos.
5. Relaciones entre tablas.
6. Recomendaciones de normalización.
7. Índices recomendados.
8. Posibles problemas futuros.
9. Mejoras de UX.
10. Flujo de pantallas.
11. Wireframe conceptual.
12. Validaciones de negocio.
13. Riesgos técnicos.
14. Recomendaciones para mantener el sistema escalable.

Finalmente, cuando toda la arquitectura esté aprobada, procederemos con la implementación en Django.