# Mercado Pago API

BotSaldos consulta Mercado Pago mediante la API de reportes de dinero liberado
(`release_report`). No usa Selenium ni login web para esta integracion.

## Flujo

1. Calcula un rango de fechas para las ultimas 24 horas tomando como referencia
   el horario Argentina (`America/Argentina/Buenos_Aires`) y envia
   `begin_date`/`end_date` convertidos a UTC con sufijo `Z`, que es el formato
   documentado por Mercado Pago.
2. Consulta `GET /v1/account/release_report/list`.
3. Valida el primer reporte de la lista, que Mercado Pago devuelve como el mas
   reciente. Ese `id` es el `id` del informe descargable que BotSaldos compara
   contra `MERCADOPAGO_REPORT_STATE_FILE`.
4. Si ese reporte mas reciente esta descargable y su `id` no fue procesado,
   descarga ese CSV sin generar otro informe.
5. Si `/list` no trae un reporte descargable, primero configura el reporte con
   `POST /v1/account/release_report/config` usando separador `;`,
   `display_timezone=GMT-03`, columnas explicitas y `BALANCE_AMOUNT`.
   Si Mercado Pago responde `409 Conflict` porque la configuracion ya existe,
   BotSaldos actualiza esa configuracion con `PUT /v1/account/release_report/config`.
6. Solicita la generacion de uno con `POST /v1/account/release_report`.
   El `id` que puede devolver esta respuesta identifica el pedido de generacion,
   no el informe descargable.
7. Espera `MERCADOPAGO_REPORT_WAIT_SECONDS` segundos.
8. Repite la consulta a `/list` cada `MERCADOPAGO_REPORT_WAIT_SECONDS` segundos hasta
   `MERCADOPAGO_REPORT_MAX_ATTEMPTS` veces.
9. Toma siempre el primer reporte de la lista y valida que:
   - tenga estado descargable: `enabled` o `processed`
   - coincida con el rango solicitado, si `MERCADOPAGO_VALIDATE_REPORT_RANGE=true`
   - su `id` no haya sido procesado antes
   Si el ultimo reporte esta descargable pero no coincide con el rango, BotSaldos
   lo trata como reporte anterior, genera uno nuevo y espera un `id` distinto.
10. Descarga el CSV con `GET /v1/account/release_report/{file_name}`.
11. Lee el CSV con `pandas` y toma el ultimo valor no vacio de la columna `BALANCE_AMOUNT`.
12. Escribe el saldo en las columnas `mercadopago_*` de Google Sheets.

## Configuracion

```env
MERCADOPAGO_ENABLED=false
MERCADOPAGO_ACCESS_TOKEN=
MERCADOPAGO_RELEASE_REPORT_URL=https://api.mercadopago.com/v1/account/release_report
MERCADOPAGO_RELEASE_REPORT_CONFIG_URL=https://api.mercadopago.com/v1/account/release_report/config
MERCADOPAGO_RELEASE_REPORT_LIST_URL=https://api.mercadopago.com/v1/account/release_report/list
MERCADOPAGO_RELEASE_REPORT_DOWNLOAD_URL=https://api.mercadopago.com/v1/account/release_report
MERCADOPAGO_TIMEOUT_SECONDS=30
MERCADOPAGO_REPORT_WAIT_SECONDS=30
MERCADOPAGO_REPORT_MAX_ATTEMPTS=5
MERCADOPAGO_CONFIGURE_REPORT=true
MERCADOPAGO_REPORT_DISPLAY_TIMEZONE=GMT-03
MERCADOPAGO_VALIDATE_REPORT_RANGE=true
MERCADOPAGO_REPORT_STATE_FILE=tmp/mercadopago_release_reports.json
```

El rango de `begin_date` y `end_date` no se configura por entorno en esta
version: siempre contempla las ultimas 24 horas al momento de ejecutar el cron.
El payload se envia a Mercado Pago en formato UTC `Z`.
Si se necesita descargar un reporte ya generado manualmente desde Mercado Pago,
por ejemplo uno con `created_from=manual` y `origin=date_range`, usar
`MERCADOPAGO_VALIDATE_REPORT_RANGE=false` para que BotSaldos tome el ultimo
reporte descargable de la lista aunque el rango no coincida exactamente con el
pedido automatico.

El token se envia como header `Authorization: Bearer <token>` y nunca debe
loguearse ni versionarse.

## Estado Persistido

`MERCADOPAGO_REPORT_STATE_FILE` guarda los ids de reportes ya descargados. El
id persistido es el `id` del informe recibido en `GET /v1/account/release_report/list`,
no el id del pedido devuelto por el `POST`. Esto evita volver a procesar el
mismo CSV en ejecuciones posteriores del cron.

El mismo archivo persiste tambien `last_balance_amount` y
`last_balance_currency`. Si el ultimo reporte de Mercado Pago ya fue descargado,
BotSaldos solicita un reporte nuevo y espera a que `/list` devuelva un `id`
distinto. Esto evita quedarse con una foto vieja cuando hubo movimientos
posteriores a la generacion del CSV anterior. Si Mercado Pago todavia no publica
un nuevo `id`, la ejecucion reutiliza `last_balance_amount` con estado `success`
para poder escribir la fila operativa en Google Sheets. Si existe un estado viejo
que solo tenia el `id` y todavia no tiene saldo cacheado, BotSaldos vuelve a
descargar ese CSV una vez para completar el cache.

## Fallas Observables

La integracion registra fallas controladas como:

- `report_generation_failed`
- `report_generation_rejected`
- `report_list_failed`
- `report_list_empty`
- `report_not_ready`
- `latest_report_mismatch`
- `file_name_not_found`
- `report_download_failed`
- `balance_amount_not_found`
- `balance_amount_empty`
- `pandas_not_installed`

Ante una falla de Mercado Pago, BotSaldos continua con DolarApi y Google Sheets,
dejando el estado `failed` y la causa en las columnas `mercadopago_*`.
