# Contributing

Gracias por contribuir a Clinical Intelligence Platform.

## Flujo recomendado

1. Crea una rama desde `main` con un nombre descriptivo, por ejemplo `feat/...`, `fix/...`, `docs/...` o `refactor/...`.
2. Instala el workspace con `uv sync --all-packages --group dev`.
3. Mantén los cambios dentro del límite arquitectónico correspondiente (`apps/`, `packages/`, `tests/` o `docs/`).
4. Ejecuta antes de abrir un pull request:

```bash
uv run ruff check apps packages tests
uv run pytest -q
```

5. Abre un pull request pequeño, enfocado y con una explicación clara del motivo del cambio.

## Criterios de contribución

- No versionar secretos, entornos locales, modelos entrenados ni artefactos generados.
- No introducir dependencias de infraestructura en `clinical-core`.
- Mantener la lógica de dominio fuera de la capa HTTP.
- Actualizar documentación solo cuando describa comportamiento o arquitectura vigentes.
- Agregar o actualizar pruebas cuando cambie comportamiento observable.

## Commits

Se recomiendan mensajes breves e imperativos, idealmente siguiendo una convención simple como:

```text
feat: add prediction endpoint
fix: preserve training feature order
docs: clarify local setup
refactor: isolate model adapter
```
