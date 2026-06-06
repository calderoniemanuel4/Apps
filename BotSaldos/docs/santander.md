# Santander Personas

Esta integracion usa Selenium con Chrome para ingresar a Santander Personas, extraer un saldo monetario por XPath configurable y cerrar sesion.

## Configuracion

Variables requeridas cuando `SANTANDER_ENABLED=true`:

- `SANTANDER_USERNAME`
- `SANTANDER_PASSWORD`
- `SANTANDER_USERNAME_SELECTOR`
- `SANTANDER_PASSWORD_SELECTOR`
- `SANTANDER_SUBMIT_SELECTOR`
- `SANTANDER_BALANCE_XPATH`
- `SANTANDER_LOGOUT_SELECTOR`
- `SANTANDER_LOGOUT_CONFIRM_SELECTOR`

Variables opcionales:

- `SELENIUM_HEADLESS`: usar `false` en staging para observar el navegador. Valor recomendado: `false`.
- `SELENIUM_LAUNCH_ARGS`: flags opcionales de Chrome. Valor actual recomendado: `--disable-http2`.
- `SANTANDER_POST_LOGIN_URL`: URL esperada luego de ingresar. Valor esperado: `#!/home`.
- `SANTANDER_INPUT_MODE`: modo de ingreso. `human` usa mouse, click, pausas y tipeo caracter por caracter.
- `SANTANDER_SUBMIT_STRATEGY`: forma de enviar login. Valores: `click` o `enter`.
- `SANTANDER_TYPE_DELAY_MS`: demora entre teclas al completar el login. Valor por defecto: `60`.
- `SANTANDER_LOGIN_ERROR_SELECTOR`: selector visible cuando Santander rechaza credenciales.
- `SANTANDER_OFFLINE_SELECTOR`: selector visible cuando Santander informa servicio fuera de linea.
- `SANTANDER_MAX_LOGIN_ATTEMPTS`: limite de intentos automaticos. Valor por defecto: `2`.
- `SANTANDER_ATTEMPT_STATE_FILE`: archivo local que persiste intentos fallidos.
- `SANTANDER_LOGOUT_SUCCESS_URL`: URL opcional esperada al cerrar sesion. Se usa como una señal mas, no como unica condicion.
- `SANTANDER_LOGOUT_TIMEOUT_MS`: espera corta para confirmar cierre de sesion. Valor recomendado: `3000`.

## Flujo

1. El servicio chequea si Santander esta habilitado.
2. Si el contador de fallos llego al limite, no intenta login y continua con DolarApi.
3. Si puede intentar, abre Santander con Selenium.
4. Completa usuario y password. Con `SANTANDER_INPUT_MODE=human`, usa mouse, click, pausas y tipeo caracter por caracter.
5. Envia el formulario con click o Enter segun `SANTANDER_SUBMIT_STRATEGY`.
6. Detecta errores configurados de credenciales o servicio fuera de linea.
7. Extrae el saldo desde `SANTANDER_BALANCE_XPATH`.
8. Cierra sesion y confirma logout. Si llego a home, el cierre se intenta tambien aunque falle la lectura del saldo.
9. Escribe una fila con estado de Santander y cotizacion de DolarApi.

## Reintentos

Cada fallo registra una causa normalizada:

- `incorrect_password`
- `service_offline`
- `no_internet`
- `timeout`
- `missing_configuration`
- `balance_not_found`
- `login_not_completed`
- `logout_failed`
- `unknown`

Cuando el contador llega a `SANTANDER_MAX_LOGIN_ATTEMPTS`, las siguientes ejecuciones no vuelven a intentar login. El bot continua con DolarApi y deja `santander_status=blocked`.

Los fallos `balance_not_found` y `logout_failed` no incrementan el contador de login porque ocurren despues del ingreso o dependen del contrato de extraccion.

Para rehabilitar intentos luego de revision manual, borrar o resetear el archivo definido en `SANTANDER_ATTEMPT_STATE_FILE`.

## Seguridad

- No loguear usuario, password, HTML ni saldos completos fuera de la planilla.
- Mantener `.env` fuera de Git.
- Si Santander cambia el DOM, actualizar selectores en `.env` sin tocar codigo.
