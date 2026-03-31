# Hola Mundo

Proyecto Python minimo para validar una estructura simple, limpia y alineada con `AGENTS.md`.

## Objetivo

Este proyecto demuestra una base pequena en Python con:

- punto de entrada claro
- configuracion centralizada
- esquema tipado para el mensaje
- tests basicos

## Ejecutar

```bash
python3 -m app.main
```

Para personalizar el saludo:

```bash
APP_GREETING="Hola equipo" python3 -m app.main
```

## Test

```bash
python3 -m pytest
```

## Estructura

```text
hola mundo/
├── app/
│   ├── config.py
│   ├── main.py
│   └── schemas.py
├── tests/
│   ├── test_config.py
│   └── test_main.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```
