# Galicia

Esta integracion usa Selenium con Chrome para ingresar a Galicia, extraer un saldo monetario por XPath configurable y cerrar sesion.

## Configuracion

Variables requeridas cuando `GALICIA_ENABLED=true`:

- `GALICIA_LOGIN_URL`
- `GALICIA_POST_LOGIN_URL`
- `GALICIA_DOCUMENT_NUMBER`
- `GALICIA_DOCUMENT_NUMBER_SELECTOR`
- `GALICIA_USERNAME`
- `GALICIA_PASSWORD`
- `GALICIA_USERNAME_SELECTOR`
- `GALICIA_PASSWORD_SELECTOR`
- `GALICIA_SUBMIT_SELECTOR`
- `GALICIA_BALANCE_XPATH`
- `GALICIA_LOGOUT_SELECTOR`

Variables operativas:

- `GALICIA_INPUT_MODE`: valor recomendado `human`.
- `GALICIA_SUBMIT_STRATEGY`: `click` o `enter`.
- `GALICIA_TYPE_DELAY_MS`: demora entre teclas al completar el login. Valor por defecto: `60`.
- `GALICIA_LOGIN_ERROR_SELECTOR`: selector visible cuando Galicia rechaza credenciales.
- `GALICIA_OFFLINE_SELECTOR`: selector visible cuando Galicia informa servicio fuera de linea.
- `GALICIA_MAX_LOGIN_ATTEMPTS`: limite de intentos automaticos. Valor por defecto: `2`.
- `GALICIA_ATTEMPT_STATE_FILE`: archivo local que persiste intentos fallidos. Por defecto: `tmp/galicia_login_attempts.json`.
- `GALICIA_LOGOUT_SUCCESS_URL`: URL opcional esperada al cerrar sesion.
- `GALICIA_LOGOUT_TIMEOUT_MS`: espera corta para confirmar cierre de sesion. Valor recomendado: `3000`.

## Flujo

1. El servicio chequea si Galicia esta habilitado.
2. Si el contador de fallos llego al limite, no intenta login y continua con DolarApi.
3. Si puede intentar, abre Galicia con Selenium.
4. Completa documento, usuario y password con estrategia humana por defecto.
5. Envia el formulario con click o Enter segun `GALICIA_SUBMIT_STRATEGY`.
6. Espera `GALICIA_POST_LOGIN_URL`.
7. Extrae el saldo desde `GALICIA_BALANCE_XPATH`.
8. Cierra sesion con un click y confirma logout por URL, texto de login o señal de logout.
9. Escribe una fila con estado de Galicia, estado de Santander y cotizacion de DolarApi.

Para rehabilitar intentos luego de revision manual:

```bash
./scripts/reset_galicia_attempts.sh
```
