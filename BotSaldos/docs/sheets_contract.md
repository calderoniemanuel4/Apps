# Contrato de Google Sheets

Este documento define la forma minima esperada de la planilla usada por BotSaldos.

## Spreadsheet

- `GOOGLE_SHEETS_SPREADSHEET_ID`: id de la planilla configurado por entorno.
- `GOOGLE_SHEETS_WORKSHEET_NAME`: nombre de la hoja operativa. Valor por defecto: `Cotizaciones`.
- La planilla debe estar compartida solo con el email de la cuenta de servicio configurada.

## Worksheet `Cotizaciones`

La primera fila debe contener exactamente estos encabezados, en este orden:

```text
fetched_at
santander_balance
santander_currency
santander_status
santander_failure_reason
galicia_balance
galicia_currency
galicia_status
galicia_failure_reason
mercadopago_balance
mercadopago_currency
mercadopago_status
mercadopago_failure_reason
compra
venta
casa
nombre
moneda
fecha_actualizacion
raw_response
```

## Columnas

- `fetched_at`: fecha y hora Argentina en que el bot obtuvo la respuesta, formato `dd-mm-yyyy  hh:mm:ss`.
- `santander_balance`: saldo extraido desde Santander cuando la consulta web fue exitosa.
- `santander_currency`: moneda del saldo de Santander. Valor esperado inicial: `ARS`.
- `santander_status`: `success`, `cached`, `skipped`, `failed` o `blocked`.
- `santander_failure_reason`: causa normalizada si Santander fallo o quedo bloqueado.
- `galicia_balance`: saldo extraido desde Galicia cuando la consulta web fue exitosa.
- `galicia_currency`: moneda del saldo de Galicia. Valor esperado inicial: `ARS`.
- `galicia_status`: `success`, `cached`, `skipped`, `failed` o `blocked`.
- `galicia_failure_reason`: causa normalizada si Galicia fallo o quedo bloqueado.
- `mercadopago_balance`: saldo obtenido desde Mercado Pago cuando la consulta por API fue exitosa.
- `mercadopago_currency`: moneda del saldo de Mercado Pago. Valor esperado inicial: `ARS`.
- `mercadopago_status`: `success`, `cached`, `skipped`, `failed` o `blocked`.
- `mercadopago_failure_reason`: causa normalizada si Mercado Pago fallo o quedo bloqueado.
- `compra`: valor de compra devuelto por la API cuando exista.
- `venta`: valor de venta devuelto por la API cuando exista.
- `casa`: identificador de la cotizacion devuelto por la API.
- `nombre`: nombre legible de la cotizacion.
- `moneda`: codigo de moneda devuelto por la API.
- `fecha_actualizacion`: timestamp original de actualizacion devuelto por la API.
- `raw_response`: respuesta JSON completa de la API, serializada para auditoria simple.

Cuando un cliente falla pero existe un saldo exitoso persistido en
`BALANCE_STATE_FILE`, BotSaldos escribe ese ultimo saldo con estado `cached` y
deja la causa original en `*_failure_reason`.

## Reglas

- No escribir datos reales mientras `DRY_RUN=true`.
- Validar encabezados antes de leer o escribir.
- Consultar cada portal solo si su `*_ENABLED=true` y no se supero su limite de intentos.
- Si un portal falla, registrar causa y continuar con DolarApi.
- Si un portal supera `*_MAX_LOGIN_ATTEMPTS`, no volver a intentar ese portal hasta revision manual.
- Validar que la respuesta de la API tenga al menos una cotizacion numerica antes de escribir.
- Guardar la respuesta cruda para poder auditar cambios de formato de la API.
- Probar primero contra una planilla de staging antes de usar la planilla real.
