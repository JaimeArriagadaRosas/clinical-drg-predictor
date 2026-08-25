<p align="center">
  <img src=".github/assets/readme-banner.svg" alt="Clinical Intelligence Platform" width="100%" />
</p>

<p align="center">
  <a href="https://github.com/JaimeArriagadaRosas/clinical-drg-predictor/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/JaimeArriagadaRosas/clinical-drg-predictor/actions/workflows/ci.yml/badge.svg" /></a>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?logo=python&logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white" />
  <img alt="React" src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=111" />
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white" />
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green.svg" />
</p>

# Clinical Intelligence Platform

Plataforma modular de ingeniería de datos y Machine Learning clínico para predicción de **Grupos Relacionados por Diagnóstico (GRD)**, soporte a decisión e interoperabilidad clínica.

El proyecto moderniza una implementación académica previa con límites explícitos de aplicación, contratos reutilizables, frontend clínico independiente, runtime local y un adaptador FHIR acotado al caso de predicción actual.

## Capacidades actuales

- API HTTP con FastAPI y OpenAPI.
- Aplicación web con React, TypeScript, Vite y Tailwind CSS.
- Runtime local con setup, preboot, consola interactiva y graceful shutdown.
- Inferencia GRD desacoplada del transporte HTTP.
- Adaptador FHIR para `Bundle` de un caso clínico con `Patient`, `Condition` y `Procedure`.
- Contratos compartidos en paquetes reutilizables.
- Arranque de la API incluso cuando los artefactos del modelo no están disponibles.
- Pruebas automatizadas y CI separado para Python y web.
- Gestión Python con `uv` y frontend con `pnpm`.

## Estructura

```text
apps/
  api/                  aplicación FastAPI
  runtime/              lifecycle y consola local
  web/                  interfaz clínica React/TypeScript
packages/
  clinical-core/        contratos compartidos
  clinical-drg/         inferencia y orquestación GRD
  clinical-fhir/        adaptadores de interoperabilidad FHIR
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
- Node.js 22
- `uv`
- `pnpm` 10

## Inicio rápido

Instala ambos workspaces:

```bash
uv sync --all-packages --group dev
pnpm install
```

O utiliza el runtime:

```bash
uv run clinical-platform setup
uv run clinical-platform preboot
uv run clinical-platform run
```

La consola interactiva permite gestionar servicios locales:

```bash
uv run clinical-platform console
```

La API queda en `http://127.0.0.1:8000` y la web en `http://127.0.0.1:5173`.

Endpoints actuales:

```text
GET  /health
POST /v1/predictions/drg
POST /v1/predictions/drg/fhir
```

El endpoint FHIR es un adaptador de interoperabilidad para el contrato de predicción actual; no pretende implementar un servidor FHIR completo.

## Escala de datos

El dataset académico actual se mantiene como fuente local pequeña. La arquitectura separa interoperabilidad de almacenamiento para permitir evolucionar hacia formatos columnares y procesamiento analítico sin introducir infraestructura distribuida mientras el volumen no lo justifique.

FHIR se utiliza como frontera clínica. Para extracción masiva futura, el camino previsto es FHIR Bulk Data/NDJSON y procesamiento columnar; Kafka, Spark u otras tecnologías distribuidas sólo deben incorporarse cuando exista una necesidad de throughput, latencia o volumen medible.

## Entrenamiento

```bash
uv sync --all-packages --group dev --group training
uv run --group training python src/training/training_main.py --skip-lgbm
```

Los artefactos generados localmente no deben versionarse.

## Calidad

```bash
uv run ruff check apps packages tests
uv run pytest -q
pnpm web:lint
pnpm web:build
```

## Contribución y seguridad

- [Guía de contribución](.github/CONTRIBUTING.md)
- [Política de seguridad](.github/SECURITY.md)
- [Código de conducta](.github/CODE_OF_CONDUCT.md)

## Licencia

Este repositorio se distribuye bajo la [MIT License](LICENSE).

## Aviso clínico

Este proyecto es de carácter académico y de ingeniería de software/ML. No constituye una herramienta de diagnóstico médico ni sustituye evaluación clínica profesional.
