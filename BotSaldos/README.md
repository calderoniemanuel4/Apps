# BotSaldos Financieros

Automatizacion local para actualizar una planilla de Google Sheets con la cotizacion del dolar obtenida desde una API publica.

El proyecto maneja informacion sensible. La prioridad inicial es construir una base segura, observable y facil de operar antes de automatizar movimientos reales sobre Google Sheets.

## Objetivo

Crear un bot en Python que:

- consulte DolarApi para obtener la cotizacion del dolar
- consulte portales bancarios con Selenium cuando esten habilitados
- registre saldos monetarios o causas de fallo normalizadas por portal
- valide que la respuesta incluya al menos un valor de cotizacion
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
   - `integrations/selenium_client.py` para automatizacion base con Selenium
   - `integrations/santander_selenium_client.py` para Santander Personas
   - `integrations/balance_portal.py` para contratos compartidos de portales de saldos
   - `integrations/galicia_selenium_client.py` para Galicia
   - `integrations/api_client.py` para consultar DolarApi
   - timeouts, errores visibles y logs sin secretos

5. Implementar servicios de negocio
   - obtener cotizacion del dolar
   - obtener saldo de Santander cuando este habilitado
   - limitar reintentos automaticos ante fallos de login
   - validar presencia de un valor numerico de cotizacion
   - escribir la respuesta de la API en la planilla
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

- Nunca commitear credenciales JSON, `.env`, cookies, perfiles de navegador ni logs con datos sensibles.
- Usar una cuenta de servicio de GCP con permisos minimos.
- Compartir la planilla solo con la cuenta de servicio necesaria.
- Guardar secretos fuera del repositorio, por ejemplo en `.env` local o en un secret manager si luego se despliega.
- Sanitizar logs: no registrar tokens, cookies, contrasenas, saldos completos si no son necesarios, documentos personales ni payloads crudos.
- Ejecutar primero contra una planilla de prueba antes de tocar datos reales.
- Mantener `DRY_RUN=true` hasta validar credenciales, planilla y mapeo de columnas.
- Diseñar escrituras idempotentes para evitar duplicados si cron ejecuta el script mas de una vez.
- Preferir APIs oficiales cuando existan antes que scraping con login.
- Preferir sesiones efimeras de navegador y cerrar sesion al terminar cada consulta.

## Estructura

```text
BotSaldos/
├── app/
│   ├── core/
│   │   ├── config.py
│   │   └── logging_config.py
│   ├── integrations/
│   │   ├── api_client.py
│   │   ├── balance_portal.py
│   │   ├── galicia_selenium_client.py
│   │   ├── santander_selenium_client.py
│   │   ├── selenium_client.py
│   │   └── sheets_client.py
│   ├── schemas/
│   │   ├── sheet_contract.py
│   │   └── transaction.py
│   ├── services/
│   │   └── balance_sync_service.py
│   └── main.py
├── docs/
│   ├── santander.md
│   ├── galicia.md
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
- Google Chrome instalado localmente para automatizacion Selenium

Pasos iniciales:

```bash
cd BotSaldos
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Luego completar `.env` con rutas y datos locales. No commitear `.env`.

Para usar integraciones reales con Google Sheets, Selenium o APIs HTTP, instalar tambien:

```bash
pip install -e ".[automation]"
```

Por defecto el proyecto corre en modo seguro:

```env
DRY_RUN=true
```

Con `DRY_RUN=true`, el bot puede obtener datos, pero no debe escribir en Google Sheets. Para escritura real, cambiar a `DRY_RUN=false` y completar como minimo:

- `GOOGLE_APPLICATION_CREDENTIALS`
- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_SHEETS_WORKSHEET_NAME`

Antes de desactivar `DRY_RUN`, confirmar que la primera fila de la worksheet cumple el contrato documentado.

Si el contrato de columnas cambia, actualizar la primera fila de la worksheet configurada con:

```bash
./scripts/update_sheet_headers.sh
```

## Validacion De Setup

Antes de escribir contra una planilla de staging o real, ejecutar:

```bash
python -m app.check_setup
```

o:

```bash
./scripts/check_setup.sh
```

Este chequeo no escribe datos. Valida:

- ruta local de `GOOGLE_APPLICATION_CREDENTIALS`
- presencia de `GOOGLE_SHEETS_SPREADSHEET_ID`
- respuesta de DolarApi
- acceso a la worksheet configurada
- encabezados esperados en la primera fila

Si falta configuracion local, el comando termina con codigo de salida `1` y muestra que chequeos fallaron.

## Escritura De Staging

Para probar permisos de escritura contra una planilla de staging, primero completar `.env` con credenciales y spreadsheet de prueba. Luego validar:

```bash
python -m app.check_setup
```

Si todo responde `OK`, cambiar `DRY_RUN=false` solo apuntando a la planilla de staging y ejecutar:

```bash
python -m app.staging_write
```

o:

```bash
./scripts/staging_write.sh
```

Para hacer una prueba puntual sin modificar `.env`, usar:

```bash
env DRY_RUN=false python -m app.staging_write
```

Este comando vuelve a correr los chequeos de setup, rechaza escribir si `DRY_RUN=true` y espera escribir exactamente una fila de cotizacion.

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

Para instalar o actualizar el cron de staging en esta maquina:

```bash
./scripts/install_staging_cron.sh
```

Por defecto instala una ejecucion diaria a las 08:00. Para cambiar el horario:

```bash
BOTSALDOS_CRON_SCHEDULE="0 9 * * *" ./scripts/install_staging_cron.sh
```

El instalador reemplaza solo el bloque marcado `BotSaldos staging` y conserva otros cronjobs del usuario.

## API Externa

`EXTERNAL_API_DOLLAR_QUOTE_URL` define la URL usada para obtener la cotizacion. Valor por defecto:

```text
https://dolarapi.com/v1/dolares/oficial
```

La respuesta esperada es un objeto JSON similar a:

```json
{
  "compra": 1410,
  "venta": 1430,
  "casa": "oficial",
  "nombre": "Oficial",
  "moneda": "USD",
  "fechaActualizacion": "2026-05-31T17:59:00Z"
}
```

El bot no valida exhaustivamente todos los campos: solo exige que exista `venta` o `compra` con valor numerico antes de escribir.

## Selenium

La automatizacion web usa Selenium con Chrome visible por defecto. El flujo comun de cada portal es:

1. abrir URL de login
2. completar campos de login configurados
3. esperar la URL o pantalla posterior al login
4. extraer saldo por XPath configurable
5. cerrar sesion y confirmar logout con una espera corta

Diagnostico con Chrome visible:

```bash
./scripts/diagnose_santander_selenium.sh
./scripts/diagnose_santander_selenium_manual.sh
```

## Santander

La integracion Santander esta documentada en `docs/santander.md`.

Para habilitarla, completar en `.env`:

```env
SANTANDER_ENABLED=true
SANTANDER_USERNAME=
SANTANDER_PASSWORD=
SANTANDER_USERNAME_SELECTOR=
SANTANDER_PASSWORD_SELECTOR=
SANTANDER_SUBMIT_SELECTOR=
SANTANDER_INPUT_MODE=direct
SANTANDER_SUBMIT_STRATEGY=click
SANTANDER_TYPE_DELAY_MS=60
SANTANDER_BALANCE_XPATH=
SANTANDER_LOGOUT_SELECTOR=
SANTANDER_LOGOUT_CONFIRM_SELECTOR=
```

El bot intenta login solo si no se supero `SANTANDER_MAX_LOGIN_ATTEMPTS`. Si falla dos veces por defecto, las siguientes ejecuciones saltean Santander y continuan con DolarApi.

Luego de revision manual, resetear intentos con:

```bash
./scripts/reset_santander_attempts.sh
```

## Galicia

La integracion Galicia esta documentada en `docs/galicia.md`.

Para habilitarla, completar en `.env`:

```env
GALICIA_ENABLED=true
GALICIA_LOGIN_URL=
GALICIA_POST_LOGIN_URL=
GALICIA_DOCUMENT_NUMBER=
GALICIA_DOCUMENT_NUMBER_SELECTOR=
GALICIA_USERNAME=
GALICIA_PASSWORD=
GALICIA_USERNAME_SELECTOR=
GALICIA_PASSWORD_SELECTOR=
GALICIA_SUBMIT_SELECTOR=
GALICIA_INPUT_MODE=human
GALICIA_SUBMIT_STRATEGY=click
GALICIA_TYPE_DELAY_MS=60
GALICIA_BALANCE_XPATH=
GALICIA_LOGOUT_SELECTOR=
```

Galicia usa `GALICIA_ATTEMPT_STATE_FILE`, separado del estado de Santander. Para resetearlo:

```bash
./scripts/reset_galicia_attempts.sh
```

## Contrato De Planilla

El contrato operativo de Google Sheets esta documentado en `docs/sheets_contract.md`.

La worksheet por defecto es `Cotizaciones` y debe tener estos encabezados exactos en la primera fila:

```text
fetched_at, santander_balance, santander_currency, santander_status, santander_failure_reason, galicia_balance, galicia_currency, galicia_status, galicia_failure_reason, mercadopago_balance, mercadopago_currency, mercadopago_status, mercadopago_failure_reason, compra, venta, casa, nombre, moneda, fecha_actualizacion, raw_response
```

Las columnas `mercadopago_*` quedan reservadas para la integracion por API.

## Estado Actual

El scaffold inicial esta listo, el contrato minimo de Google Sheets ya esta definido en codigo y documentacion, y `SheetsClient` ya valida encabezados antes de escribir filas con `gspread`.

Existe un chequeo local de setup con `python -m app.check_setup` para validar credenciales, API externa, acceso a Sheets y contrato de headers sin escribir datos.

Existe una escritura controlada de staging con `python -m app.staging_write`, pensada para validar permisos antes de usar el entrypoint programado.

El servicio principal obtiene saldos bancarios cuando cada portal esta habilitado, continua con DolarApi, respeta `DRY_RUN` y devuelve un resumen estructurado de ejecucion.

`ExternalApiClient` ya puede consultar la API HTTP configurable con timeout, validar que exista una cotizacion numerica y devolver la respuesta cruda.

Las integraciones web especificas disponibles son Santander Personas y Galicia, con selectores configurables por entorno y limite de intentos persistido por portal. Mercado Pago queda reservado para integracion por API.
