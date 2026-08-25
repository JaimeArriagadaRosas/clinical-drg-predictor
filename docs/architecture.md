# Clinical Intelligence Platform — Architecture

## Purpose

This repository evolves the original academic GRD predictor into a portfolio-grade clinical data and machine-learning platform while preserving working behavior during migration.

The system is intentionally kept as **one repository and one product**. Source code is separated into explicit application and package boundaries, while deployment remains a **modular monolith** until a real operational need justifies independent services.

## Architectural principles

- Prefer a modular monolith over premature microservices.
- Keep HTTP concerns separate from domain and model orchestration.
- Keep shared clinical contracts independent from web frameworks and infrastructure.
- Preserve compatibility while moving new behavior out of the historical `src/` layer.
- Treat training metadata and inference feature ordering as one explicit contract.
- Introduce infrastructure only when an end-to-end use case requires it.
- Keep generated datasets, models, caches, credentials, and local environments outside Git.

## Current repository boundaries

```text
apps/
  api/                  FastAPI composition root and HTTP transport
packages/
  clinical-core/        shared clinical contracts and cross-domain types
  clinical-drg/         GRD prediction domain and inference orchestration
dataset/                source dataset and local generated artifacts
docs/                   current technical documentation
notebook/               historical exploratory analysis
src/                    temporary compatibility layer for academic code
tests/                  cross-package, API, schema, and orchestration tests
```

Directories for future capabilities should not be created pre-emptively. New top-level boundaries are justified only when corresponding production code and ownership actually exist.

## Dependency direction

```text
HTTP / FastAPI
    │
    ▼
clinical-api
    │
    ├──────────────► clinical-core
    │
    ▼
clinical-drg ──────► clinical-core
    │
    ▼
legacy compatibility adapters (`src/`) while migration remains incomplete
```

The dependency direction should remain inward toward reusable contracts and domain behavior. Domain packages must not depend on FastAPI route composition.

## Domain responsibilities

### `clinical-core`

Owns generic contracts shared by clinical inference domains. It must remain independent from FastAPI, Flask, Kafka, Spark, MLflow, command-line composition, and application bootstrap code.

### `clinical-drg`

Owns GRD feature orchestration, model invocation, result decoding, and the interfaces required to inject model/encoder/extractor dependencies.

Compatibility adapters may temporarily import historical implementations from `src/` while migration is incomplete, but this dependency should not spread into new domain logic.

### `clinical-api`

Owns HTTP transport only: route composition, request/response validation, HTTP error mapping, dependency wiring, and OpenAPI exposure.

It must not own feature engineering, model training, or GRD business logic.

### `src/`

`src/` contains academic compatibility paths such as the original chatbot, training orchestration, and feature extraction code that has not yet been fully migrated.

It is a transitional boundary, not the preferred destination for new platform features.

## Runtime model

The backend runs as a modular monolith. Package separation exists to make dependencies explicit and testable, not to simulate distributed services inside a single repository.

A capability should become a separate process or service only when it has an independent operational requirement such as a distinct scaling profile, lifecycle, reliability boundary, or asynchronous workload.

## API contract

### `GET /health`

The health endpoint reports API liveness and whether the GRD model is ready for prediction.

Example:

```json
{
  "status": "ok",
  "drg_model_ready": true
}
```

### `POST /v1/predictions/drg`

Example request:

```json
{
  "icd10_codes": ["E11.9"],
  "icd9_codes": [],
  "age": 65,
  "sex": "F"
}
```

Example response:

```json
{
  "label": "123",
  "confidence": 0.84,
  "model_name": "legacy-grd",
  "model_version": "1"
}
```

If required model assets are unavailable, prediction returns HTTP 503 while the API itself remains live.

## Training and inference contract

The generated training metadata is part of the runtime contract, not an incidental implementation detail.

`dataset/processed/metadata.pkl` preserves the codes and exact feature order used during training so inference can reconstruct inputs consistently. Any change to encoding, feature order, metadata shape, or artifact location must include regression tests.

Generated artifacts such as processed datasets and trained models must not be committed unless a future test fixture explicitly requires a small, reviewed artifact.

## Data and infrastructure evolution

Technologies such as Parquet, DuckDB, Polars, Spark, Kafka, or MLflow may be introduced later, but only together with a concrete end-to-end capability.

The repository should not create placeholder services or directories merely to advertise technologies. Architecture documentation must describe what actually exists or clearly mark future decisions as proposals.

## Testing boundary

Testing is organized around observable contracts:

- unit tests for domain and inference orchestration;
- API tests for liveness, readiness, validation, and prediction behavior;
- schema tests for feature and metadata compatibility;
- orchestration tests for historical training behavior while that path remains supported.

See [`testing.md`](testing.md) for commands and detailed expectations.

## Migration rules

- Preserve working GRD behavior during migration.
- New HTTP behavior belongs in `apps/api`.
- Reusable domain behavior belongs in `packages/`.
- Avoid adding new product architecture to the historical Flask entry point.
- Generated files and secrets must never be committed.
- Do not describe the system as microservices while it remains a modular monolith.
- Remove obsolete migration documentation instead of preserving duplicate historical READMEs in `docs/`.
- Update this document when an architectural boundary actually changes.

## Completion criteria for the current foundation

The foundation is considered healthy when:

1. the `uv` workspace resolves cleanly;
2. FastAPI starts without requiring trained model assets;
3. model readiness is reported independently from API liveness;
4. inference uses the same feature schema produced by training;
5. automated tests cover API, domain, schema, and training orchestration contracts;
6. CI validates supported Python versions;
7. documentation matches the actual repository structure.
