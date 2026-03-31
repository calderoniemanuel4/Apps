# AGENTS.md - Estándar Zen de Ingeniería para IA

## Propósito

Este archivo define el estándar operativo de ingeniería para agentes de IA, Codex y asistentes de programación que trabajen en los proyectos de Emanuel.

Su objetivo no es solo mejorar la calidad del código, sino preservar la consistencia entre sesiones en:

- arquitectura
- estilo de implementación
- confiabilidad
- observabilidad
- calidad de entrega
- mantenibilidad
- seguridad operativa

Este documento debe ser accionable.
Cuando exista cualquier ambigüedad, los agentes deben seguir la prioridad de decisión definida abajo en lugar de adivinar.

---

## Prioridad de Reglas

Si dos reglas parecen entrar en conflicto, aplícalas en este orden:

1. Seguridad, corrección y protección de datos
2. Solicitud explícita del usuario
3. Nivel de madurez del proyecto
4. Regla de proporcionalidad
5. Claridad y mantenibilidad
6. Rendimiento y optimización
7. Conveniencia

Interpretación:

- Nunca sacrificar corrección por velocidad
- Nunca sobrearquitectar un prototipo
- Nunca subarquitectar un camino de producción
- Preferir la solución más pequeña que siga siendo segura, testeable y mantenible

---

## Principios Base de Ingeniería

- Confiabilidad por encima de lo ingenioso
- Estructura por encima de la improvisación
- Documentación por encima de la adivinación
- Determinismo por encima de la magia
- Observabilidad por encima de la opacidad
- Claridad por encima de la complejidad
- Simplicidad antes que abstracción
- Explicitud antes que comportamiento oculto
- Validación antes que confianza
- Mantenibilidad por encima de la conveniencia a corto plazo

Todos los agentes deben producir sistemas que sean:

- predecibles
- observables
- testeables
- refactorizables
- reemplazables
- suficientemente documentados para poder continuarse después

---

## Contexto del Workspace

Lenguaje principal: Python

Lenguajes secundarios:
- HTML
- pequeñas cantidades de JavaScript solo cuando sea estrictamente necesario

Enfoque principal:
- APIs
- automatización
- agentes de IA
- integraciones
- dashboards
- herramientas operativas

Plataformas y servicios preferidos:
- Google Cloud Run
- Google Cloud Functions
- Firestore
- Google Sheets
- APIs REST
- OpenAI

Flujo de trabajo preferido:
- terminal primero
- incrementos pequeños
- validar temprano
- documentar decisiones que afecten trabajo futuro

---

## Reglas de Oro

- Resolver el problema real, no un problema futuro hipotético
- Hacer que el siguiente cambio sea más fácil, no más difícil
- Preferir patrones sobrios y bien entendidos
- Todo límite externo debe validarse
- Todo camino de falla importante debe ser visible
- Toda integración orientada a producción debe poder configurarse
- Si un comportamiento importa, debe quedar codificado en tests o documentación
- Si una solución es difícil de explicar, simplifícala

---

## Regla de Proporcionalidad

Las soluciones deben ser proporcionales al problema.

Usa esta regla de forma agresiva.

- Tarea pequeña -> implementación simple
- Prototipo -> estructura mínima y feedback rápido
- Proyecto en crecimiento -> modularizar temprano donde el dolor ya sea visible
- Sistema de producción -> optimizar para confiabilidad, observabilidad y mantenibilidad

Esto significa en la práctica:

- No introducir capas "por si acaso"
- No dividir un script pequeño en abstracciones excesivas
- Sí introducir separación cuando las responsabilidades ya estén divergiendo
- Sí introducir validación, logging, reintentos y tests antes de considerar un sistema listo para producción

---

## Niveles de Madurez del Proyecto

### Prototipo

Objetivo: validar una idea rápidamente.

Permitido:
- estructura mínima
- validación manual solo en entorno local
- implementaciones directas con abstracción limitada

Requerido:
- código legible
- configuración aislada
- punto de entrada claro
- visibilidad básica de errores

Evitar:
- arquitectura compleja
- generalización prematura
- interfaces innecesarias

### MVP

Objetivo: estabilizar una versión útil.

Requerido:
- estructura modular
- configuración separada
- tests básicos
- logging
- `.env.example`
- setup documentado

Recomendado:
- límites de servicio
- esquemas tipados
- wrappers de integración
- validación en límites de entrada y salida

### Producción

Objetivo: confiabilidad y mantenibilidad.

Requerido:
- arquitectura limpia cuando esté justificada
- logging estructurado
- reintentos y fallbacks
- tests para flujos críticos
- observabilidad
- manejo de secretos
- documentación de despliegue
- health checks cuando apliquen
- estrategia explícita de manejo de errores

---

## Expectativas de Ejecución por Defecto para Agentes

Cuando trabajen en este workspace, los agentes deben:

1. Entender la tarea antes de cambiar código
2. Preferir cambios pequeños y reversibles
3. Inspeccionar el contexto local del proyecto antes de inventar estructura
4. Reutilizar patrones existentes salvo que sean claramente dañinos
5. Validar supuestos con documentación cuando haya librerías o APIs involucradas
6. Dejar el codebase en un estado más claro que como fue encontrado

Los agentes no deben:

- inventar comportamiento de librerías
- inventar nombres de configuración sin comprobar su uso
- ignorar errores en silencio
- ocultar tradeoffs cuando importen
- introducir dependencias sin justificación

---

## Expectativas a Nivel de Repositorio

Todo proyecto Python debería hacer fácil encontrar lo siguiente:

- qué hace la aplicación
- cómo correrla localmente
- cómo configurarla
- cómo testearla
- cómo desplegarla
- cómo está documentada en español latino

Como mínimo, el repositorio normalmente debería contener:

- `README.md`
- `.env.example`
- `AGENTS.md`
- directorio de código fuente
- directorio de tests cuando el proyecto supere la etapa de prototipo descartable

Si el proyecto crece más allá de una utilidad muy pequeña, también debería incluir:

- configuración centralizada
- un archivo claro de dependencias como `pyproject.toml` o `requirements.txt`
- notas de despliegue

La documentación del proyecto debe escribirse en español latino salvo que el usuario indique otra cosa.

---

## Estructura Recomendada de Proyecto Python

Usa una estructura apropiada al nivel de madurez.

### Proyecto Pequeño

```text
project_name/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── services/
│   └── integrations/
├── tests/
├── .env.example
├── README.md
└── AGENTS.md
```

### Proyecto de Servicio o API

```text
project_name/
├── app/
│   ├── api/
│   ├── core/
│   ├── services/
│   ├── repositories/
│   ├── integrations/
│   ├── schemas/
│   ├── domain/
│   └── main.py
├── tests/
├── scripts/
├── docs/
├── .env.example
├── pyproject.toml
├── README.md
└── AGENTS.md
```

### Sistema Agéntico o de Múltiples Flujos

```text
project_name/
├── app/
│   ├── api/
│   ├── core/
│   ├── agents/
│   │   ├── core/
│   │   ├── memory/
│   │   ├── tools/
│   │   ├── prompts/
│   │   ├── schemas/
│   │   ├── workflows/
│   │   └── orchestration/
│   ├── services/
│   ├── repositories/
│   ├── integrations/
│   ├── schemas/
│   ├── domain/
│   └── main.py
├── tests/
├── scripts/
├── docs/
├── .env.example
├── pyproject.toml
├── README.md
└── AGENTS.md
```

Regla:

- No usar por defecto la estructura más grande
- Empezar por la estructura más pequeña que encaje limpiamente con el proyecto actual
- Promover la arquitectura solo cuando la complejidad sea real

---

## Reglas de Arquitectura Limpia

Usa separación por capas cuando el alcance lo justifique.

Capas preferidas:

```text
interface
application
domain
infrastructure
```

Mapeo:

- API / Streamlit / CLI -> interface
- casos de uso / servicios / orquestación -> application
- entidades de negocio / reglas / políticas -> domain
- base de datos / cloud / APIs externas / sheets -> infrastructure

Reglas:

- la lógica de negocio no debe vivir en la capa de transporte
- las llamadas a servicios externos no deben estar dispersas en archivos aleatorios
- el texto de prompts no debe mezclarse con el cableado de infraestructura
- la persistencia debe aislarse detrás de funciones de acceso claras o repositorios
- los handlers deben orquestar, no contener reglas de negocio pesadas

No fuerces una separación empresarial estricta en un script pequeño.
Sí aplica separación cuando ya existan múltiples responsabilidades claras.

---

## Componentes Canónicos de un Agente

Para sistemas de agentes serios, separa claramente las responsabilidades.

### AgentCore

Responsable de:
- recibir input
- invocar lógica de planificación o ejecución
- coordinar herramientas y memoria
- devolver resultados estructurados

### Planner

Responsable de:
- decidir la siguiente acción
- descomponer tareas
- determinar si hace falta más contexto
- seleccionar herramientas o flujos

### ToolExecutor

Responsable de:
- ejecutar herramientas de forma segura
- validar argumentos
- manejar errores
- devolver resultados estructurados

### MemoryManager

Responsable de:
- contexto de conversación
- estado de ejecución
- conocimiento persistido
- estrategia de recuperación

### PromptManager

Responsable de:
- instrucciones del sistema
- plantillas de prompts
- restricciones de salida
- guías específicas por rol

Regla:

- Introducir estos módulos por separado solo cuando el agente realmente tenga la complejidad suficiente para justificarlo

---

## Patrón de Flujo de Trabajo

Flujo de orquestación preferido:

```text
Input
-> Validation
-> Planner or Handler
-> Tool Selection
-> Tool Execution
-> State Update
-> Final Validation
-> Output
```

Para tareas complejas:

```text
Input
-> Plan
-> Multi-step execution
-> Intermediate state save
-> Verification or reflection
-> Final output
```

Todo flujo de trabajo debería dejar claro:

- qué entró al sistema
- qué decisiones se tomaron
- qué llamadas externas ocurrieron
- qué resultado se produjo
- cómo se expone una falla

---

## Reglas de Ingeniería en Python

Estándares por defecto para código Python:

- usar tipado explícito en código de aplicación
- usar nombres claros
- mantener funciones enfocadas
- preferir composición sobre herencia
- evitar módulos gigantes
- documentar clases públicas y funciones públicas
- validar entradas en los límites
- mantener los efectos secundarios fáciles de ubicar

Preferir:

- dataclasses o modelos Pydantic para datos estructurados
- funciones puras cuando sea posible
- capas de integración aisladas para servicios externos
- inyección de dependencias por constructor o parámetros de función cuando mejore la testabilidad

Evitar:

- globales ocultos
- constantes mágicas dispersas entre archivos
- módulos fuertemente acoplados
- `except Exception` demasiado amplio sin logging ni intención clara
- lógica de integración copiada y pegada

---

## Regla de Salidas Estructuradas

Al interactuar con LLMs:

- preferir salidas estructuradas
- preferir tool calling antes que parsear texto crudo
- validar salidas con Pydantic cuando aplique
- rechazar o reparar explícitamente una salida inválida del modelo
- evitar confiar en texto libre del modelo en flujos de producción

Si una salida no puede validarse, debe tratarse como una ejecución fallida.

Ejemplo:

```python
from pydantic import BaseModel


class WeatherResult(BaseModel):
    temperature: float
    condition: str
```

Preferir objetos validados sobre strings crudos como:

```python
return "It is hot today"
```

---

## Reglas de Diseño de Herramientas

Las herramientas deben:

- ser determinísticas siempre que sea posible
- validar entradas
- devolver datos estructurados cuando sea posible
- fallar de forma clara
- definir timeouts cuando existan llamadas externas
- evitar efectos secundarios ocultos
- registrar su ejecución en un nivel apropiado
- ser idempotentes cuando corresponda

Preferir categorías de herramientas como:

- herramientas de recuperación
- herramientas de API
- herramientas de cómputo
- herramientas de almacenamiento
- herramientas de reporting
- herramientas de notificación

Cuando el proyecto crezca, preferir un registry o catálogo explícito de herramientas para descubribilidad y testing.

Ejemplo:

```python
TOOLS = {
    "get_weather": get_weather,
    "save_report": save_report,
    "load_sheet_data": load_sheet_data,
}
```

---

## Política de Context7 MCP

Context7 debe tratarse como la fuente de documentación por defecto respaldada por MCP cuando el comportamiento de una librería importe.

### Cuándo Debe Usarse Context7

- al integrar una nueva librería externa de Python
- al usar APIs o SDKs poco familiares
- al corregir problemas específicos de versión
- al generar código de setup o despliegue
- al trabajar con librerías que evolucionan rápido
- al implementar uso del SDK de OpenAI
- al implementar integraciones con Google Cloud, Firestore, Sheets, FastAPI, Streamlit o frameworks similares cuando la precisión importe

### Proceso de Context7

1. Identificar la librería exacta
2. Resolver el library id de Context7
3. Consultar Context7 a través de MCP
4. Preferir ejemplos oficiales y sintaxis actual
5. Evitar uso deprecado
6. Aplicar solo lo que encaje con el alcance del proyecto
7. Mantener la implementación alineada con la versión instalada o prevista

### Regla

- Documentación por encima de supuestos
- Context7 por encima de alucinaciones
- Docs respaldadas por MCP por encima de la memoria cuando las versiones o APIs puedan haber cambiado

### Guía Práctica

- No inventar nombres de métodos del SDK
- No asumir que ejemplos viejos siguen siendo válidos
- No mezclar patrones de distintas versiones mayores
- Si Context7 no está disponible, indicarlo explícitamente y usar la siguiente mejor fuente oficial

---

## Política de Uso de OpenAI

Antes de generar o integrar código de OpenAI:

1. Preferir patrones oficiales del SDK
2. Preferir salidas estructuradas
3. Preferir esquemas validados
4. Implementar reintentos cuando hagan falta
5. Evitar métodos deprecados
6. Mantener prompts concisos y explícitos
7. Controlar uso de tokens y costo cuando importe

Reglas de seguridad:

- nunca ejecutar texto crudo del modelo como comandos de shell
- nunca confiar en código arbitrario generado por el modelo sin inspección
- nunca exponer secretos en prompts o logs
- validar argumentos de herramientas producidos por el modelo antes de ejecutarlos

Librerías preferidas:

- `openai`
- `pydantic`
- `httpx`

---

## Reglas de Diseño de APIs

Para APIs en Python:

- preferir FastAPI salvo que exista una razón fuerte para no hacerlo
- definir explícitamente esquemas de request y response
- validar todas las entradas en el límite
- separar routing de lógica de negocio
- devolver formas de respuesta estables y documentadas
- usar códigos de estado HTTP correctos
- implementar health endpoints para servicios desplegables

Separación recomendada:

- las rutas manejan detalles HTTP
- los servicios manejan casos de uso
- los repositorios o integraciones manejan persistencia y sistemas externos

Toda API debería hacer fácil responder:

- cuáles son las entradas
- cuáles son las salidas
- qué puede fallar
- qué se registra en logs

---

## Reglas para Firestore

Usa Firestore de forma intencional, no casual.

Reglas:

- mantener nombres de colecciones explícitos y documentados
- definir la forma del documento en código con esquemas o contratos tipados
- centralizar el acceso a Firestore en lugar de dispersar llamadas
- preferir módulos de repositorio o integración para acceso a datos
- validar datos antes de escribir y después de leer cuando la corrección importe
- diseñar consultas teniendo en cuenta las limitaciones conocidas de Firestore
- evitar round trips innecesarios por documento en caminos calientes

Guía operativa:

- manejar documentos faltantes de forma explícita
- distinguir "no encontrado" de datos vacíos
- mantener timestamps consistentes
- documentar índices necesarios para consultas no triviales
- evitar embebidos inestables o sin límite de crecimiento sin una razón clara

Para caminos de producción:

- registrar adecuadamente lecturas y escrituras fallidas
- hacer reintentos de forma deliberada, especialmente ante fallas transitorias
- evitar escrituras duplicadas accidentales

---

## Reglas para Google Sheets

Sheets debe tratarse como una interfaz de datos operativa, no como almacenamiento mágico sin estructura.

Reglas:

- centralizar el código de acceso a Sheets
- documentar spreadsheet id, propósito de cada worksheet y expectativas de columnas
- definir explícitamente el esquema de encabezados
- validar filas antes de procesarlas
- evitar supuestos posicionales cuando puedan usarse columnas nombradas
- normalizar los datos provenientes de Sheets antes de que la lógica de negocio los consuma

Enfoque recomendado:

- un módulo para operaciones de lectura
- un módulo o límite de servicio para operaciones de escritura o actualización
- mapeo de esquema entre filas y modelos Python

Evitar:

- hardcodear índices de columna frágiles sin explicación
- mezclar lecturas crudas de sheets directamente dentro de lógica de negocio
- aceptar filas malformadas en silencio

---

## Guía para Google Cloud Run

Cloud Run es el objetivo de despliegue preferido para APIs y procesos de servicio de larga duración.

Construir para Cloud Run con estos supuestos:

- instancias de servicio sin estado
- configuración impulsada por entorno
- el arranque debe ser predecible
- la visibilidad de health importa
- el manejo de requests debe ser consciente de timeouts

Reglas:

- la app debe arrancar desde un entrypoint claro
- la configuración debe venir de variables de entorno
- los secretos no deben estar hardcodeados
- los logs deben salir por stdout mediante logging estructurado o estándar
- debe existir un health endpoint cuando el servicio esté orientado a producción
- los handlers de requests no deben depender de estado local escribible

Recomendado:

- separar el cableado de arranque de la lógica de negocio
- mantener ligero el startup del contenedor
- fallar rápido ante configuración inválida

---

## Logging y Observabilidad

Los agentes y servicios deben registrar:

- decisiones de alto nivel
- selección de herramientas
- entradas sanitizadas de herramientas
- resúmenes de salida
- reintentos
- fallbacks
- errores
- llamadas importantes a APIs externas
- transiciones de estado importantes

Reglas de logging:

- usar `logging`, no `print`, en código de producción
- preferir logs estructurados a medida que los sistemas crezcan
- nunca loguear secretos
- los logs deben ayudar a depurar incidentes reales

Campos mínimos útiles cuando sea posible:

- timestamp
- module
- action
- status
- duration
- correlation_id o request_id

Los servicios orientados a producción deberían exponer:

- health checks
- métricas básicas o al menos visibilidad de latencia
- visibilidad de conteo de errores
- hooks opcionales de telemetría cuando estén justificados

---

## Estrategia de Manejo de Errores

Los sistemas deben manejar explícitamente:

- salida malformada del modelo
- argumentos inválidos de herramientas
- fallas de APIs externas
- timeouts
- errores de red
- configuración faltante
- estado corrupto
- datos faltantes

Estrategias de recuperación preferidas:

- reintentar cuando la falla sea plausiblemente transitoria
- usar fallback hacia un camino más seguro cuando sea válido
- simplificar el prompt o request cuando la complejidad haya causado la falla
- devolver resultado parcial solo cuando quede claramente identificado
- pedir aclaración cuando el input del usuario sea genuinamente ambiguo

Reglas:

- nunca fallar en silencio
- nunca ocultar un error que afecte la corrección
- nunca usar reintentos a ciegas en acciones no idempotentes

---

## Reglas de Configuración

- nunca hardcodear secretos
- usar `.env` solo para desarrollo local
- siempre proporcionar `.env.example` cuando exista configuración
- centralizar settings en un módulo de configuración
- preferir settings de Pydantic o una capa dedicada de configuración
- validar variables de entorno requeridas al arrancar
- separar configuración operativa de constantes de negocio

La configuración debería responder:

- qué es requerido
- qué es opcional
- qué tiene valor por defecto
- a qué entorno pertenece cada valor

---

## Reglas de Estilo de Código

- nombres descriptivos
- funciones pequeñas y enfocadas
- tipado explícito
- código modular
- docstrings para clases y funciones públicas
- flujo de control legible
- responsabilidades claramente separadas

Preferir:

- simple antes que abstracto
- explícito antes que ingenioso
- legible antes que comprimido

Evitar:

- archivos gigantes sin razón
- cajones de sastre utilitarios
- caminos indirectos de código que oculten la responsabilidad

---

## Estrategia de Testing

Usar `pytest` por defecto.

Como mínimo, testear:

- parsing
- schemas
- servicios núcleo
- comportamiento de herramientas
- rutas críticas
- carga de configuración
- casos de falla

Para sistemas específicos de IA, testear:

- validación de esquemas de herramientas
- supuestos del contrato del prompt
- comportamiento del planner cuando una herramienta falla
- ejecución de fallbacks
- validación de salidas estructuradas

Para sistemas con muchas integraciones, priorizar:

- tests de contrato de lectura y escritura en Firestore cuando sea viable
- tests de parsing de Sheets
- tests de contrato de API
- tests de validación de configuración

Si todavía no existen tests automatizados completos, dejar:

- TODOs
- pasos de verificación manual
- notas de validación en `README.md`

---

## Stack de Python Preferido

Usar cuando corresponda:

- `pydantic` para esquemas y validación
- `fastapi` para APIs
- `httpx` para HTTP
- `pytest` para tests
- `python-dotenv` para manejo de entorno local
- `google-cloud-firestore` para Firestore
- `gspread` más `google-auth` para Sheets
- `streamlit` para UI operativa
- `uvicorn` para correr la API localmente
- `typer` o `rich` para CLIs pulidas

Usar alternativas solo cuando exista un beneficio claro.

---

## Guía de Despliegue

Antes de desplegar, verificar:

1. que la estructura del proyecto sea coherente
2. que las dependencias estén declaradas correctamente
3. que las variables de entorno requeridas estén documentadas
4. que el logging sea apropiado para producción
5. que existan health checks cuando hagan falta
6. que el objetivo de despliegue encaje con la carga de trabajo
7. que el manejo de secretos esté externalizado

Guía del objetivo de despliegue:

- Cloud Functions para tareas aisladas, webhooks y event handlers
- Cloud Run para APIs, servicios y componentes de orquestación de larga duración

---

## Expectativas de Respuesta para Agentes

Estructura de respuesta preferida al entregar trabajo de implementación:

1. breve resumen del objetivo
2. enfoque si hace falta
3. resultado de implementación
4. cómo correr o validar
5. siguiente mejora opcional

Si existen alternativas significativas, preferir presentar:

- opción simple
- opción robusta

Los agentes deben ser concisos, pero no omitir tradeoffs críticos.

---

## Higiene de Archivos y Git

No hacer commit de:

- `.env`
- `.env.*`
- `__pycache__/`
- `.pytest_cache/`
- `.mypy_cache/`
- `.ruff_cache/`
- `.venv/`
- archivos de credenciales
- claves privadas
- logs locales generados salvo que sea intencional

Incluir cuando corresponda:

- `README.md`
- `.env.example`
- `.gitignore`
- `pyproject.toml` o `requirements.txt`

Nunca asumir que los secretos deben vivir en control de versiones.

---

## Checklist de Preparación para Producción

Antes de considerar un proyecto listo para producción, confirmar:

- [ ] La configuración está centralizada
- [ ] Los secretos están externalizados
- [ ] Los logs son significativos
- [ ] Los flujos núcleo tienen tests
- [ ] Las salidas de herramientas o modelos están validadas
- [ ] Los errores tienen manejo explícito o comportamiento de fallback
- [ ] El README explica setup, ejecución y despliegue
- [ ] El objetivo de despliegue está documentado
- [ ] Existe health check cuando aplique
- [ ] Las librerías sensibles a Context7 fueron revisadas mediante documentación respaldada por MCP
- [ ] Los patrones de acceso a Firestore son intencionales
- [ ] Los esquemas de Sheets están documentados si se usa Sheets

---

## Regla Final

Construir como si el proyecto pudiera crecer:

- organizado desde el día 1
- entendible en una semana
- refactorizable en un mes
- desplegable en producción cuando madure

Pero nunca confundas claridad con complejidad.

Si una solución más pequeña resuelve bien el problema, preferir la solución más pequeña.
