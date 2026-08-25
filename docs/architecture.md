# Architecture

## Scope

This document describes the architecture implemented in the repository today. It intentionally separates application composition, reusable clinical behavior, interoperability adapters and historical compatibility code.

## Repository model

```text
apps/
  api/
  runtime/
  web/
packages/
  clinical-core/
  clinical-drg/
  clinical-fhir/
src/
tests/
```

`apps/` owns executable application boundaries. `packages/` owns reusable behavior. The historical `src/` tree remains only for compatibility while concrete functionality is migrated.

## Application boundaries

### `apps/api`

FastAPI owns HTTP concerns only: validation, serialization, route definition, CORS for the local development web client, error mapping and dependency composition.

Current endpoints:

```text
GET  /health
POST /v1/predictions/drg
POST /v1/predictions/drg/fhir
```

Both prediction endpoints converge on the same `GRDPredictionRequest` domain contract before calling `clinical-drg`.

### `apps/web`

The browser application uses React, TypeScript, Vite and Tailwind CSS. It owns presentation and user interaction and consumes the API over HTTP.

The current design follows a clinical utility/evidence-first direction: structured context, persistent prediction results, restrained semantic color and SVG iconography. It does not contain prediction logic.

### `apps/runtime`

The local runtime owns developer lifecycle orchestration. It performs preboot checks, starts and stops API/web processes, provides an interactive console and performs graceful shutdown on termination signals.

It is not a domain package and does not contain clinical behavior.

## Package boundaries

### `packages/clinical-core`

Defines immutable shared contracts such as `GRDPredictionRequest` and `PredictionResult`. It does not depend on FastAPI, frontend code, model loading or FHIR.

### `packages/clinical-drg`

Owns prediction orchestration. `GRDPredictor` receives model, label encoder and feature extractor dependencies and returns a domain `PredictionResult`.

The current `load_legacy_predictor()` adapter still bridges to historical model artifacts and feature extraction code.

### `packages/clinical-fhir`

Owns interoperability adapters between FHIR-shaped input and internal domain contracts.

The implemented adapter intentionally supports only the subset required by the current predictor: a single-patient `Bundle` containing `Patient`, `Condition` and `Procedure` resources. It extracts age, administrative sex and recognized ICD coding systems and returns `GRDPredictionRequest`.

This package is not a generic FHIR validator, repository, terminology server or full FHIR server.

## Dependency flow

```text
browser
  |
  v
apps/web
  |
  v
apps/api ------------------> clinical-fhir
  |                              |
  |                              v
  +------------------------> clinical-core
  |
  v
clinical-drg --------------> clinical-core
  |
  v
legacy adapter -> src/api/feature_extractor.py
```

`apps/runtime` sits outside the clinical dependency flow and manages executable processes only.

## Data scale and interoperability

FHIR and data-processing scale are separate concerns.

FHIR is used as an interoperability boundary. The current local dataset remains appropriate for in-process/tabular processing. Distributed infrastructure should not be introduced solely to make the project appear to be a Big Data system.

The intended evolution path is:

1. local CSV/Excel-compatible ingestion for small academic or institutional extracts;
2. Parquet/NDJSON and an analytical engine such as DuckDB when columnar queries and larger local datasets justify it;
3. FHIR Bulk Data for population-scale interchange where a FHIR ecosystem is available;
4. streaming or distributed engines only when measurable throughput, latency or data-volume requirements justify them.

## Runtime readiness

The API can start without trained model artifacts. `/health` remains available and reports `drg_model_ready: false`; prediction endpoints return HTTP 503 until required assets are available.

The local runtime adds a second readiness layer before starting processes: supported Python, `uv`, `pnpm`, and required application boundaries must be present.

## Architectural rules

- Keep HTTP-specific logic inside `apps/api`.
- Keep browser presentation inside `apps/web`.
- Keep lifecycle/process orchestration inside `apps/runtime`.
- Keep reusable clinical prediction behavior inside `packages/`.
- Keep `clinical-core` free of transport, persistence and model-loading concerns.
- Keep FHIR conversion in `clinical-fhir`; do not leak FHIR resource dictionaries into prediction packages.
- Do not add Kafka, Spark, Hadoop, databases or additional services without a demonstrated requirement.
- Do not describe the system as microservices while it is deployed as one local platform boundary.
- Protect training/inference metadata and interoperability mappings with regression tests.

## Current limitations

- The GRD package still imports the historical feature extractor through a compatibility adapter.
- Training has not yet been extracted from `src/` into a maintained application/package boundary.
- Model assets are loaded from the local filesystem rather than a model registry.
- The FHIR adapter covers only the fields required by the current predictor and does not perform full profile validation.
- The data layer has not yet been abstracted into small-data and columnar analytical adapters.
