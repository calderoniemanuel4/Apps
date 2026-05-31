# BotSaldos Financieros

Automatizacion local para actualizar una planilla de ingresos y gastos con datos obtenidos desde internet, APIs gratuitas y formularios web operados con Playwright.

El proyecto maneja informacion sensible. La prioridad inicial es construir una base segura, observable y facil de operar antes de automatizar movimientos reales sobre Google Sheets.

## Objetivo

Crear un bot en Python que:

- inicie sesion en portales web mediante Playwright cuando no exista API disponible
- consulte APIs gratuitas para obtener datos financieros o administrativos
- normalice los datos obtenidos
- actualice una planilla de Google Sheets usando una cuenta de servicio de GCP
- registre ejecuciones, errores y resultados en logs locales
- pueda ejecutarse de forma programada con cronjobs del sistema

## Plan De Ejecucion

1. Preparar base del proyecto
   - crear estructura modular
   - definir configuracion por variables de entorno
   - agregar `.gitignore` para secretos, logs y caches
   - documentar setup y politicas de seguridad

2. Configurar Google Cloud
   - crear un nuevo proyecto en GCP
   - habilitar Google Sheets API y Google Drive API si hace falta compartir archivos
   - crear una cuenta de servicio dedicada
   - descargar credenciales JSON solo al entorno local seguro
   - compartir la planilla unicamente con el email de la cuenta de servicio

3. Definir contrato de la planilla
   - documentar spreadsheet id
   - documentar worksheets esperadas
   - definir encabezados obligatorios
   - validar filas antes de escribir

4. Implementar integraciones
   - `integrations/sheets_client.py` para Google Sheets
   - `integrations/web_client.py` para Playwright
   - `integrations/api_client.py` para APIs gratuitas
   - timeouts, errores visibles y logs sin secretos

5. Implementar servicios de negocio
   - normalizar ingresos y gastos
   - deduplicar registros
   - validar saldos antes de escribir
   - generar resumen de ejecucion

6. Agregar ejecucion programada
   - crear script CLI idempotente
   - documentar comando cron
   - escribir logs por ejecucion
   - evitar ejecuciones simultaneas si hay riesgo de duplicados

7. Validar y endurecer
   - tests unitarios para parsing, configuracion y normalizacion
   - prueba manual con planilla de staging
   - checklist de permisos GCP
   - revision de logs para confirmar que no exponen datos sensibles

## Seguridad

Reglas obligatorias del proyecto:

- Nunca commitear credenciales JSON, `.env`, cookies, sesiones de Playwright ni logs con datos sensibles.
- Usar una cuenta de servicio de GCP con permisos minimos.
- Compartir la planilla solo con la cuenta de servicio necesaria.
- Guardar secretos fuera del repositorio, por ejemplo en `.env` local o en un secret manager si luego se despliega.
- Sanitizar logs: no registrar tokens, cookies, contrasenas, saldos completos si no son necesarios, documentos personales ni payloads crudos.
- Ejecutar primero contra una planilla de prueba antes de tocar datos reales.
- Mantener `DRY_RUN=true` hasta validar credenciales, planilla y mapeo de columnas.
- Diseñar escrituras idempotentes para evitar duplicados si cron ejecuta el script mas de una vez.
- Preferir APIs oficiales cuando existan antes que scraping con login.
- Mantener sesiones Playwright en una carpeta ignorada por Git y con permisos locales restringidos.

## Estructura

```text
BotSaldos/
├── app/
│   ├── core/
│   │   ├── config.py
│   │   └── logging_config.py
│   ├── integrations/
│   │   ├── api_client.py
│   │   ├── sheets_client.py
│   │   └── web_client.py
│   ├── schemas/
│   │   └── transaction.py
│   ├── services/
│   │   └── balance_sync_service.py
│   └── main.py
├── docs/
│   ├── security.md
│   └── sheets_contract.md
├── logs/
│   └── .gitkeep
├── scripts/
│   └── run_sync.sh
├── tests/
│   └── test_config.py
├── .env.example
├── .gitignore
├── AGENTS.md
├── pyproject.toml
└── README.md
```

## Setup Local

Requisitos previstos:

- Python 3.11+
- credenciales JSON de cuenta de servicio de GCP
- acceso a la planilla de Google Sheets compartida con esa cuenta
- Playwright instalado solo cuando se implemente automatizacion web

Pasos iniciales:

```bash
cd BotSaldos
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Luego completar `.env` con rutas y datos locales. No commitear `.env`.

Para usar integraciones reales con Google Sheets, Playwright o APIs HTTP, instalar tambien:

```bash
pip install -e ".[automation]"
```

Por defecto el proyecto corre en modo seguro:

```env
DRY_RUN=true
```

Con `DRY_RUN=true`, el bot puede obtener y normalizar datos, pero no debe escribir en Google Sheets. Para escritura real, cambiar a `DRY_RUN=false` y completar como minimo:

- `GOOGLE_APPLICATION_CREDENTIALS`
- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_SHEETS_WORKSHEET_NAME`

Antes de desactivar `DRY_RUN`, confirmar que la primera fila de la worksheet cumple el contrato documentado.

## Ejecucion Prevista

```bash
python -m app.main
```

Cron ejemplo, ajustando rutas absolutas:

```cron
0 8 * * * cd /ruta/a/BotSaldos && ./.venv/bin/python -m app.main >> logs/cron_stdout.log 2>&1
```

Antes de usar cron con datos reales, ejecutar manualmente contra una planilla de staging.

El entrypoint usa `LOCK_FILE` para evitar ejecuciones simultaneas desde cron. Si una ejecucion queda interrumpida, revisar que no haya un proceso activo antes de borrar manualmente el lock.

## Contrato De Planilla

El contrato operativo de Google Sheets esta documentado en `docs/sheets_contract.md`.

La worksheet por defecto es `Movimientos` y debe tener estos encabezados exactos en la primera fila:

```text
occurred_on, description, amount, currency, transaction_type, source, external_id
```

## Estado Actual

El scaffold inicial esta listo, el contrato minimo de Google Sheets ya esta definido en codigo y documentacion, y `SheetsClient` ya valida encabezados antes de escribir filas con `gspread`.

El servicio principal ya normaliza movimientos crudos con el esquema `Transaction`, descarta entradas invalidas con logs sanitizados, deduplica por `external_id` cuando existe y devuelve un resumen estructurado de ejecucion.

Las integraciones web/API especificas se implementaran en pasos posteriores.
