# Playwright

BotSaldos incluye una base de Playwright para futuras integraciones web cuando no exista API oficial.

## Instalacion De Browsers

Despues de instalar el extra `automation`, instalar Chromium:

```bash
./scripts/install_playwright_browsers.sh
```

Validar que Chromium puede arrancar:

```bash
./scripts/check_playwright.sh
```

En macOS, el lanzamiento del navegador puede requerir ejecutarse fuera del sandbox de Codex.

## Configuracion

Variables relevantes:

- `PLAYWRIGHT_HEADLESS`: `true` para ejecuciones automaticas, `false` para login manual.
- `PLAYWRIGHT_BROWSER`: `chromium`, `firefox` o `webkit`. Para Santander usar `firefox`.
- `PLAYWRIGHT_CHANNEL`: canal de navegador real cuando `PLAYWRIGHT_BROWSER=chromium`, por ejemplo `chrome`.
- `PLAYWRIGHT_LAUNCH_ARGS`: flags opcionales de lanzamiento, separados por espacios. Para probar fallback HTTP/1.1 en Chrome: `--disable-http2`.
- `PLAYWRIGHT_STORAGE_STATE_PATH`: ruta local donde se guarda la sesion autenticada.
- `PLAYWRIGHT_DEFAULT_TIMEOUT_MS`: timeout por defecto para acciones de Playwright.
- `PLAYWRIGHT_LOCALE`: locale usado por el contexto del navegador.
- `PLAYWRIGHT_TIMEZONE_ID`: zona horaria usada por el contexto del navegador.
- `PLAYWRIGHT_VIEWPORT_WIDTH` y `PLAYWRIGHT_VIEWPORT_HEIGHT`: tamaño de ventana estable.
- `PLAYWRIGHT_ACCEPT_LANGUAGE`: header HTTP `Accept-Language`.
- `SANTANDER_SUBMIT_STRATEGY`: `click` o `enter` para enviar el login de Santander.
- `SANTANDER_TYPE_DELAY_MS`: demora entre teclas al completar el formulario de Santander.

La ruta `playwright/.auth/` esta ignorada por Git porque puede contener cookies y tokens de sesion.

## Login Manual

Para portales autenticados, primero guardar una sesion local:

```bash
PLAYWRIGHT_LOGIN_URL="https://portal.example.com/login" ./scripts/playwright_login.sh
```

El navegador se abre visible. Completar el login manualmente y luego continuar desde el inspector de Playwright para que se guarde el storage state.

## Diagnostico Con Selenium

Selenium esta disponible como alternativa de diagnostico cuando Santander rechaza o cambia el comportamiento del contexto Playwright.

Configuracion relevante:

- `SELENIUM_HEADLESS`: usar `false` para ver Chrome durante diagnosticos.
- `SELENIUM_PAGE_LOAD_TIMEOUT_MS`: timeout de carga y esperas explicitas.
- `SELENIUM_WINDOW_WIDTH` y `SELENIUM_WINDOW_HEIGHT`: tamaño de ventana Chrome.
- `SELENIUM_ACCEPT_LANGUAGE`: header `Accept-Language` aplicado por CDP.
- `SELENIUM_USER_AGENT`: User-Agent opcional. Si queda vacio, Selenium usa el de Chrome.
- `SELENIUM_LAUNCH_ARGS`: flags opcionales de Chrome. Para Santander se prueba `--disable-http2`.
- `SANTANDER_INPUT_MODE`: `direct` para `send_keys` simple o `human` para mouse, click y tipeo caracter por caracter.

Ejecutar:

```bash
./scripts/diagnose_santander_selenium.sh
```

Para comparar contra una interaccion manual dentro del mismo Chrome controlado por Selenium:

```bash
./scripts/diagnose_santander_selenium_manual.sh
```

## Reglas De Seguridad

- No commitear storage state, cookies, sesiones ni capturas con datos sensibles.
- No loguear HTML completo ni payloads autenticados.
- Preferir APIs oficiales antes que automatizacion web.
- Crear una integracion web por portal, con contrato de salida explicito y tests de parsing separados.
