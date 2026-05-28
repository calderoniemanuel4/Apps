# Contrato de Google Sheets

Este documento define la forma minima esperada de la planilla usada por BotSaldos.

## Spreadsheet

- `GOOGLE_SHEETS_SPREADSHEET_ID`: id de la planilla configurado por entorno.
- `GOOGLE_SHEETS_WORKSHEET_NAME`: nombre de la hoja operativa. Valor por defecto: `Movimientos`.
- La planilla debe estar compartida solo con el email de la cuenta de servicio configurada.

## Worksheet `Movimientos`

La primera fila debe contener exactamente estos encabezados, en este orden:

```text
occurred_on
description
amount
currency
transaction_type
source
external_id
```

## Columnas

- `occurred_on`: fecha del movimiento en formato `YYYY-MM-DD`.
- `description`: descripcion legible del movimiento.
- `amount`: monto decimal normalizado, sin simbolo de moneda.
- `currency`: codigo ISO de tres letras. Por defecto `ARS`.
- `transaction_type`: `income` o `expense`.
- `source`: origen del dato, por ejemplo `api`, `web`, `manual` o el nombre de la integracion.
- `external_id`: identificador externo para deduplicacion cuando exista. Puede quedar vacio solo para pruebas o carga manual controlada.

## Reglas

- No escribir datos reales mientras `DRY_RUN=true`.
- Validar encabezados antes de leer o escribir.
- Normalizar movimientos con `Transaction` antes de convertirlos a filas.
- Deduplicar por `external_id` cuando la integracion lo provea.
- Probar primero contra una planilla de staging antes de usar la planilla real.
