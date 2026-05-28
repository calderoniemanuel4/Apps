# Seguridad Operativa

## Secretos

- Las credenciales JSON de GCP deben vivir fuera de Git.
- La ruta al JSON se configura con `GOOGLE_APPLICATION_CREDENTIALS`.
- Los archivos `.env` son solo locales y estan ignorados.
- Si el proyecto se despliega en el futuro, migrar secretos a Secret Manager o mecanismo equivalente.

## Google Sheets

- Usar una cuenta de servicio dedicada al bot.
- Compartir solo la planilla necesaria con esa cuenta.
- Evitar permisos de editor sobre documentos no relacionados.
- Mantener una planilla de staging para pruebas.

## Playwright

- No guardar cookies o estados de sesion en Git.
- Usar perfiles o storage state locales ignorados.
- No loguear HTML completo de paginas autenticadas.
- Preferir APIs oficiales antes que login automatizado cuando existan.

## Logging

- Los logs deben explicar que paso sin exponer secretos.
- No registrar tokens, cookies, contrasenas ni credenciales.
- Evitar payloads crudos de bancos, planillas o portales sensibles.
- Registrar conteos, estados y errores sanitizados.

## Cron

- Usar rutas absolutas.
- Redirigir stdout/stderr a archivos de logs controlados.
- Evitar ejecuciones solapadas si la escritura no es idempotente.
- Revisar permisos del usuario que ejecuta el cronjob.
- Mantener `DRY_RUN=true` durante pruebas y solo desactivarlo cuando el mapeo de datos este validado.
- Si existe un lockfile, confirmar que no haya un proceso activo antes de eliminarlo.
