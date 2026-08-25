<p align="center">
  <img src=".github/assets/readme-banner.svg" alt="Clinical Intelligence Platform" width="100%" />
</p>

# Clinical Intelligence Platform

Plataforma de ingeniería de datos y Machine Learning clínico orientada a la predicción de **Grupos Relacionados por Diagnóstico (GRD)** a partir de episodios hospitalarios.

La reconstrucción separa el ciclo offline de datos/entrenamiento del producto de inferencia. MIMIC-IV es la fuente hospitalaria de referencia para desarrollo reproducible; los datasets clínicos reales se mantienen fuera de Git.

## Arquitectura actual

```text
apps/
  api/                  FastAPI / inferencia
  runtime/              lifecycle del producto
  training/             Training Workbench Python
  web/                  React + TypeScript
packages/
  clinical-core/        contratos compartidos
  clinical-data/        encuentros, MIMIC, validación, EDA y almacenamiento
  clinical-drg/         inferencia GRD y carga de modelos publicados
  clinical-fhir/        interoperabilidad FHIR
  clinical-ml/          features, split, entrenamiento, evaluación y publicación
tools/
  datasets/             adquisición y verificación de datasets externos
```

## Flujo ML

```text
MIMIC-IV / fuente autorizada
  -> HospitalEncounter
  -> validación + EDA
  -> Parquet / DuckDB
  -> features versionadas
  -> split seguro por paciente o tiempo
  -> baseline / RandomForest / LightGBM opcional
  -> evaluación multiclasificación
  -> modelo versionado + MLflow
  -> clinical-drg
  -> FastAPI / web / chatbot
```

## Datos clínicos

Los datasets clínicos no se distribuyen en este repositorio. Para descargar los archivos públicos necesarios de MIMIC-IV Demo 2.2:

```bash
uv run python tools/datasets/fetch.py mimic-iv-demo \
  --destination data/raw/mimic-iv-demo
```

Para una copia de MIMIC obtenida legítimamente por el usuario:

```bash
uv run python tools/datasets/fetch.py mimic-iv-demo \
  --destination data/raw/mimic-iv-demo \
  --from-directory /ruta/a/mimic
```

La segunda modalidad sólo verifica e importa archivos ya autorizados; no gestiona ni evade credenciales de PhysioNet.

El antiguo CSV académico fue retirado del árbol actual. Puede seguir existiendo en commits históricos; este cambio no reescribe el historial de Git.

## Requisitos

- Python 3.11–3.13
- `uv`
- Node.js 22
- `pnpm` 10

## Instalación

```bash
uv sync --all-packages --group dev
pnpm install
```

Para LightGBM y compatibilidad con entrenamiento histórico durante la migración:

```bash
uv sync --all-packages --group dev --group training
```

## Producto

```bash
uv run clinical-platform setup
uv run clinical-platform preboot
uv run clinical-platform run
```

API local: `http://127.0.0.1:8000`  
Web local: `http://127.0.0.1:5173`

Endpoints:

```text
GET  /health
POST /v1/predictions/drg
POST /v1/predictions/drg/fhir
```

El API carga un artefacto publicado desde `CLINICAL_MODEL_PATH` o, por defecto, `artifacts/models/current`. Si el artefacto no está disponible o es incompatible, `/health` continúa respondiendo con `drg_model_ready: false`.

## Training Workbench

El entry point moderno es:

```bash
uv run clinical-train --help
```

La aplicación de entrenamiento es una capa de orquestación; la transformación de datos y los algoritmos ML pertenecen a `clinical-data` y `clinical-ml`.

## Escala

El backend local usa Polars, PyArrow/Parquet y DuckDB. La arquitectura reserva un contrato de motor para incorporar PySpark/Delta cuando el volumen justifique ejecución distribuida, sin duplicar el pipeline clínico.

FHIR se mantiene como frontera de interoperabilidad y no como motor de almacenamiento o Big Data.

## Calidad

```bash
uv run ruff check apps packages tools tests
uv run pytest -q
pnpm web:lint
pnpm web:build
```

## Documentación

- [Arquitectura](docs/architecture.md)
- [Desarrollo](docs/development.md)
- [Testing](docs/testing.md)
- [Diseño de reconstrucción](docs/clinical-ml-platform-design.md)

## Licencia

Este repositorio se distribuye bajo la [MIT License](LICENSE).

## Aviso clínico

Proyecto académico/de ingeniería de software y ML. No constituye diagnóstico médico ni sustituye evaluación clínica profesional.
