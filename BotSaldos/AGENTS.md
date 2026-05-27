# AGENTS.md - BotSaldos

Este proyecto hereda las instrucciones del `AGENTS.md` del workspace raiz.

Prioridades especificas:

- Seguridad y proteccion de datos por encima de conveniencia.
- No commitear credenciales, `.env`, sesiones Playwright, cookies ni logs.
- Documentar cualquier integracion externa antes de usarla en datos reales.
- Validar todo dato leido de internet antes de escribirlo en Google Sheets.
- Mantener el proyecto proporcional: simple mientras sea pequeno, observable y testeable desde el inicio.
