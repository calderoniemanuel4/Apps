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
compra
venta
casa
nombre
moneda
fecha_actualizacion
raw_response
```

## Columnas

- `fetched_at`: fecha y hora UTC en que el bot obtuvo la respuesta.
- `compra`: valor de compra devuelto por la API cuando exista.
- `venta`: valor de venta devuelto por la API cuando exista.
- `casa`: identificador de la cotizacion devuelto por la API.
- `nombre`: nombre legible de la cotizacion.
- `moneda`: codigo de moneda devuelto por la API.
- `fecha_actualizacion`: timestamp original de actualizacion devuelto por la API.
- `raw_response`: respuesta JSON completa de la API, serializada para auditoria simple.

## Reglas

- No escribir datos reales mientras `DRY_RUN=true`.
- Validar encabezados antes de leer o escribir.
- Validar que la respuesta de la API tenga al menos una cotizacion numerica antes de escribir.
- Guardar la respuesta cruda para poder auditar cambios de formato de la API.
- Probar primero contra una planilla de staging antes de usar la planilla real.
