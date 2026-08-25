<p align="center">
  <img src=".github/assets/readme-banner.svg" alt="Clinical Intelligence Platform" width="100%" />
</p>

<p align="center">
  <a href="https://github.com/JaimeArriagadaRosas/clinical-drg-predictor/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/JaimeArriagadaRosas/clinical-drg-predictor/actions/workflows/ci.yml/badge.svg" /></a>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?logo=python&logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white" />
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green.svg" />
</p>

# Clinical Intelligence Platform

Plataforma modular de ingeniería de datos y Machine Learning clínico para predicción de **Grupos Relacionados por Diagnóstico (GRD)**.

El código actual está organizado como un workspace Python con una API FastAPI, contratos compartidos y una capa de inferencia GRD desacoplada del transporte HTTP. Parte del código académico original permanece temporalmente en `src/` mientras se completa su migración.

## Capacidades actuales

- API HTTP con FastAPI y OpenAPI.
- Inferencia GRD desacoplada del transporte HTTP.
- Contratos compartidos en paquetes reutilizables.
- Arranque de la API incluso cuando los artefactos del modelo no están disponibles.
- Compatibilidad entre el esquema de entrenamiento y el vector utilizado durante inferencia.
- Pruebas automatizadas y CI para Python 3.11 y 3.12.
- Gestión del workspace con `uv`.

## Estructura

```text
apps/
  api/                  aplicación FastAPI
packages/
  clinical-core/        contratos compartidos
  clinical-drg/         inferencia y orquestación GRD
dataset/                dataset fuente y artefactos locales
notebook/               análisis exploratorio histórico
src/                    implementación académica aún utilizada por compatibilidad
tests/                  pruebas automatizadas
docs/                   documentación técnica vigente
```

Documentación técnica:

- [Arquitectura](docs/architecture.md)
- [Testing](docs/testing.md)
- [Desarrollo](docs/development.md)

## Requisitos

- Python 3.11 o 3.12 para paridad con CI
- [`uv`](https://docs.astral.sh/uv/)

## Inicio rápido

Instala el workspace:

```bash
uv sync --all-packages --group dev
```

Inicia la API:

```bash
uv run uvicorn clinical_api.app:app --app-dir apps/api/src --reload
```

Endpoints actuales:

```text
GET  /health
POST /v1/predictions/drg
```

La API puede arrancar sin un modelo entrenado. En ese estado `/health` sigue disponible e informa `drg_model_ready: false`; las predicciones responden HTTP 503 hasta que los artefactos requeridos estén disponibles.

## Entrenamiento

Instala las dependencias del pipeline histórico:

```bash
uv sync --all-packages --group dev --group training
```

Ejecuta su entry point actual:

```bash
uv run --group training python src/training/training_main.py --skip-lgbm
```

Los artefactos generados localmente no deben versionarse.

## Calidad

```bash
uv run ruff check apps packages tests
uv run pytest -q
```

GitHub Actions ejecuta estas validaciones sobre Python 3.11 y 3.12.

## Contribución y seguridad

- [Guía de contribución](.github/CONTRIBUTING.md)
- [Política de seguridad](.github/SECURITY.md)
- [Código de conducta](.github/CODE_OF_CONDUCT.md)

## Licencia

Este repositorio se distribuye bajo la [MIT License](LICENSE).

## Aviso clínico

Este proyecto es de carácter académico y de ingeniería de software/ML. No constituye una herramienta de diagnóstico médico ni sustituye evaluación clínica profesional.
