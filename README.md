# Clinical Intelligence Platform

Plataforma modular de ingeniería de datos y Machine Learning clínico, evolucionada a partir del proyecto universitario original de predicción de Grupos Relacionados por Diagnóstico (GRD).

El repositorio conserva la capacidad de clasificación GRD original y la transforma en una base reproducible para ML Engineering, analítica clínica y futuras capacidades de procesamiento clínico.

## Estado

La primera fase de migración a una base limpia ya está completada.

- `apps/api` es el punto de entrada HTTP oficial mediante FastAPI.
- `packages/clinical-core` concentra contratos compartidos.
- `packages/clinical-drg` contiene la orquestación de inferencia GRD.
- `src/` conserva temporalmente el pipeline y chatbot académicos como capa de compatibilidad.
- El esquema exacto de entrenamiento se reutiliza durante inferencia mediante `dataset/processed/metadata.pkl`, evitando divergencias en el orden de features.
- Los modelos y datos procesados son artefactos generados y no se versionan.

## Estructura

```text
apps/
  api/                  FastAPI / OpenAPI
packages/
  clinical-core/        contratos clínicos compartidos
  clinical-drg/         dominio e inferencia GRD
dataset/                 dataset fuente y artefactos procesados locales
docs/                    arquitectura y decisiones
notebook/                análisis exploratorio histórico
src/                     pipeline y chatbot de compatibilidad
tests/                   pruebas automatizadas
```

La organización es un **monorepo** y el backend utiliza un **monolito modular**. Los procesos solo deberían separarse cuando exista una necesidad operacional distinta.

## Requisitos

- Python 3.11 o 3.12
- [`uv`](https://docs.astral.sh/uv/)

## Instalación

Para instalar el workspace y las herramientas de desarrollo:

```bash
uv sync --all-packages --group dev
```

Para trabajar también con el pipeline de entrenamiento:

```bash
uv sync --all-packages --group dev --group training
```

El chatbot Flask/Gemini histórico es opcional:

```bash
uv sync --all-packages --group training --group legacy-chatbot
```

Copia `.env.example` a `.env` únicamente si utilizarás Gemini y configura la clave localmente. `.env` no debe versionarse.

## API FastAPI

Inicia la API oficial desde la raíz:

```bash
uv run uvicorn clinical_api.app:app --app-dir apps/api/src --reload
```

Comprobación básica:

```text
GET /health
```

Predicción GRD:

```text
POST /v1/predictions/drg
```

La API puede arrancar sin un modelo entrenado; en ese caso `/health` informa que el modelo GRD aún no está disponible y el endpoint de predicción responde como servicio no preparado.

## Entrenamiento

El pipeline histórico sigue disponible mientras se completa su extracción hacia una capa dedicada:

```bash
uv run --group training python src/training/training_main.py --skip-lgbm
```

Parámetros principales:

```text
--data-path PATH
--n-estimators N
--max-depth N
--skip-quality
--skip-lgbm
```

El entrenamiento genera localmente, entre otros artefactos:

```text
dataset/processed/metadata.pkl
models/best_model.pkl
```

`metadata.pkl` es parte del contrato entre entrenamiento e inferencia: contiene los códigos y el orden real de las features usadas por el modelo.

## Chatbot histórico

La interfaz académica original se mantiene para compatibilidad:

```bash
uv run --group training --group legacy-chatbot python src/main.py
```

No es el transporte HTTP recomendado para nuevas funcionalidades; el desarrollo nuevo debe integrarse a `apps/api` y a los paquetes del dominio.

## Pruebas

```bash
uv run pytest -q
uv run ruff check apps packages tests
```

GitHub Actions ejecuta ambas validaciones sobre Python 3.11 y 3.12.

## Documentación

La arquitectura y las reglas de evolución están documentadas en `docs/architecture/clinical-intelligence-platform.md`.

## Aviso

Este proyecto es de carácter académico y de ingeniería de software/ML. No constituye una herramienta de diagnóstico médico ni sustituye evaluación clínica profesional.
