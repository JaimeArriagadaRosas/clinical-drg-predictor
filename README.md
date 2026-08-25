<p align="center">
  <img src=".github/assets/readme-banner.svg" alt="Clinical Intelligence Platform" width="100%" />
</p>

# Clinical Intelligence Platform

Plataforma de ingeniería de datos y Machine Learning clínico orientada a **predicción de Grupos Relacionados por Diagnóstico (GRD)** a partir de episodios hospitalarios.

El proyecto reconstruye una implementación académica previa como un monorepo moderno con pipeline reproducible de datos, entrenamiento offline, artefactos de modelo versionados, interoperabilidad FHIR y una aplicación de inferencia separada del Training Workbench.

## Flujo principal

```text
MIMIC-IV / datos hospitalarios autorizados
  -> validación
  -> EDA reproducible
  -> limpieza / transformación
  -> HospitalEncounter canónico
  -> feature engineering versionado
  -> split seguro contra leakage
  -> entrenamiento y evaluación
  -> publicación de modelo
  -> FastAPI
  -> React / interfaz conversacional
```

La confianza reportada por el producto corresponde al **clasificador GRD**; no es una probabilidad de enfermedad ni constituye diagnóstico médico.

## Stack

- Python 3.11–3.13, `uv`, Pydantic
- Polars, PyArrow/Parquet, DuckDB
- scikit-learn, Random Forest, LightGBM opcional, MLflow
- FastAPI + OpenAPI
- React 19, TypeScript, Vite, Tailwind CSS
- Typer + Rich para el Training Workbench
- FHIR como frontera de interoperabilidad
- PySpark 4.0.x + Delta Lake 4.0.x como extra distribuido opcional
- pytest, Ruff, Vitest, Testing Library y GitHub Actions

## Monorepo

```text
apps/
  api/          HTTP e inferencia
  runtime/      lifecycle del producto: API + web
  training/     Training Workbench interactivo
  web/          interfaz clínica React/TypeScript

packages/
  clinical-core/  contratos compartidos de inferencia
  clinical-data/  contratos de episodio, MIMIC, EDA, validación y motores de datos
  clinical-ml/    features, splitting, entrenamiento, evaluación, tracking y publicación
  clinical-drg/   capacidad predictiva GRD y carga de artefactos
  clinical-fhir/  adaptadores FHIR -> HospitalEncounter

tools/
  datasets/       adquisición, importación y verificación de datasets
```

## Datos

Los datasets clínicos reales **no se versionan en Git**.

Para trabajar con MIMIC-IV Demo:

```bash
python tools/datasets/fetch.py mimic-iv-demo --destination data/raw/mimic-iv-demo
```

Para una copia completa de MIMIC-IV obtenida de forma autorizada:

```bash
python tools/datasets/fetch.py mimic-iv --destination data/raw/mimic-iv --from-directory /ruta/autorizada/mimic
```

El repositorio conserva manifests, validadores y fixtures sintéticos, no credenciales ni datasets restringidos.

## Training Workbench

```bash
uv sync --all-packages --group dev
uv run clinical-train status
uv run clinical-train run --stage eda
uv run clinical-train run --all
```

Etapas del pipeline:

```text
acquire -> validate -> eda -> clean -> transform -> features -> split
-> train -> evaluate -> select -> publish
```

`apps/training` sólo orquesta. La lógica de datos vive en `clinical-data` y la lógica de ML en `clinical-ml`.

## Runtime del producto

```bash
uv run clinical-platform setup
uv run clinical-platform preboot
uv run clinical-platform run
```

El runtime gestiona únicamente:

- API: `http://127.0.0.1:8000`
- Web: `http://127.0.0.1:5173`

El entrenamiento no es un proceso hijo del runtime de producción.

## API

```text
GET  /health
POST /v1/predictions/drg
POST /v1/predictions/drg/fhir
```

El predictor carga un artefacto publicado mediante `CLINICAL_MODEL_PATH` o la convención local `artifacts/models/current`. Si no existe un modelo válido, la API puede arrancar y `/health` informa `drg_model_ready: false` mientras los endpoints de predicción devuelven indisponibilidad.

## FHIR

FHIR se utiliza como **frontera de interoperabilidad**, no como almacenamiento ni motor Big Data.

El adaptador actual transforma un Bundle con recursos relevantes —Patient, Encounter, Condition y Procedure— al contrato canónico `HospitalEncounter` antes de inferencia.

## Escalado de datos

El baseline local usa Polars + Parquet + DuckDB. Para cargas que justifiquen distribución existe un adapter opcional PySpark/Delta detrás del mismo contrato de motor.

```text
local:       Polars / DuckDB / Parquet
scale-out:   PySpark DataFrames / Spark SQL / Delta Lake
```

Spark no es necesario para el dataset pequeño ni para desarrollar el producto localmente.

## Calidad

Python:

```bash
uv run ruff check apps packages tools tests
uv run pytest -q -m "not spark"
```

Frontend:

```bash
pnpm --dir apps/web lint
pnpm --dir apps/web test --run
pnpm --dir apps/web build
```

Spark contract:

```bash
uv run --with "pyspark>=4.0,<4.1" pytest tests/test_spark_engine_contract.py -q -m spark
```

CI ejecuta Python, web y Spark contract como jobs separados.

## Documentación

- `docs/architecture.md`
- `docs/development.md`
- `docs/testing.md`
- `docs/clinical-ml-platform-design.md`
- `docs/superpowers/plans/2026-08-25-clinical-ml-platform.md`
- `docs/superpowers/sdd/progress.md`

## Licencia y aviso clínico

El código del repositorio se distribuye bajo la licencia MIT. Los datasets externos mantienen sus propios términos de acceso y uso.

Este proyecto es académico y de ingeniería de software/ML. No constituye una herramienta de diagnóstico médico ni sustituye evaluación clínica profesional.
