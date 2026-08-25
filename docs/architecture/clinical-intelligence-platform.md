# Clinical Intelligence Platform — Architecture

## Objective

Evolve the original GRD university project into a portfolio-grade clinical data and machine-learning platform owned and maintained in this repository. The system remains one product and one repository, while code is split into explicit application and package boundaries.

## Architectural style

The repository uses a **monorepo** for source organization and a **modular monolith** for the initial backend runtime. Separate processes are introduced only when execution characteristics require them, such as streaming consumers or distributed data processing.

This avoids premature microservices while keeping package boundaries suitable for later extraction.

## Repository boundaries

```text
apps/
  api/                 FastAPI composition root and HTTP transport
packages/
  clinical-core/       Shared clinical contracts and cross-domain types
  clinical-drg/        GRD prediction domain and inference service
pipelines/
  training/            Batch preprocessing/training entry points
  analytics/           Data analytics jobs
  streaming/           Kafka event processing
infra/                 Container/runtime integration
tests/                 Cross-package behavior and API tests
docs/                  Architecture, decisions, and operating documentation
src/                   Legacy compatibility during migration
```

## Phase 1 scope

The first migration increment must deliver:

1. A root `pyproject.toml` managed as a uv workspace.
2. An HTTP application in `apps/api` using FastAPI and Pydantic.
3. A reusable `clinical-core` package for shared prediction contracts.
4. A reusable `clinical-drg` package containing inference orchestration independent of HTTP.
5. Dependency injection so GRD inference can be tested without model files.
6. A compatibility adapter capable of loading the existing model, label encoder, and feature extractor.
7. Health endpoints that distinguish API liveness from model readiness.
8. Automated tests and GitHub Actions CI.
9. Repository hygiene rules that exclude caches, local environments, generated model assets, generated datasets and secrets.

## API contract

### `GET /health`

```json
{
  "status": "ok",
  "drg_model_ready": true
}
```

### `POST /v1/predictions/drg`

Request:

```json
{
  "icd10_codes": ["E11.9"],
  "icd9_codes": [],
  "age": 65,
  "sex": "F"
}
```

Response:

```json
{
  "label": "123",
  "confidence": 0.84,
  "model_name": "legacy-grd",
  "model_version": "1"
}
```

If model assets are unavailable, prediction returns HTTP 503 while API liveness remains available.

## Domain boundaries

### `clinical-core`

Owns generic contracts shared by inference domains. It does not depend on FastAPI, Flask, Kafka, Spark, MLflow or application composition code.

### `clinical-drg`

Owns GRD feature orchestration, model invocation and result decoding. Model, encoder and extractor dependencies are injected so unit tests can use deterministic fakes.

The compatibility adapter may import `src.api.feature_extractor.GRDFeatureExtractor` until the feature implementation is fully migrated.

### `clinical-api`

Owns HTTP transport only: routing, HTTP error mapping, dependency composition and OpenAPI. It does not implement feature engineering or model logic.

## Data and Big Data direction

The platform does not preserve Hadoop/MapReduce merely as a portfolio keyword. Later increments use:

- Parquet as interoperable analytical storage;
- Polars and DuckDB for local analytical workloads;
- Spark only for workloads that justify distributed execution;
- Kafka with `confluent-kafka` for event streaming;
- MLflow for experiment tracking and model lifecycle.

These components are added only with real end-to-end data flows and tests.

## Migration rules

- Preserve current GRD behavior during the first migration.
- Do not copy source code from the external FAERS repository; capabilities are reimplemented from requirements and public datasets.
- New backend behavior goes into packages and composition roots, not the legacy Flask file.
- Generated files and secrets must never be committed.
- Documentation must describe the actual architecture; do not call the modular monolith a microservices architecture.
- Existing command-line and Flask entry points remain temporarily for compatibility and are deprecated migration paths.

## Testing strategy

- Unit-test GRD inference with fake model/encoder/extractor dependencies.
- API-test liveness, successful predictions and unavailable-model behavior with FastAPI `TestClient`.
- CI runs linting and tests on supported Python versions.
- Data-pipeline increments add fixture-based integration tests before introducing distributed dependencies.

## Completion criteria for Phase 1

Phase 1 is complete when the uv workspace resolves, all tests pass, FastAPI starts without requiring trained model assets, model readiness is reported correctly, existing model assets can be loaded when present and CI validates the branch automatically.
