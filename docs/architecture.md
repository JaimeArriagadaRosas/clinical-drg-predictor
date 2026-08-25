# Architecture

## Scope

This document describes the architecture that exists in the repository today. It is intentionally limited to implemented boundaries and current runtime behavior.

## Repository model

The project is organized as a Python monorepo managed with a `uv` workspace.

```text
apps/
  api/
packages/
  clinical-core/
  clinical-drg/
src/
tests/
```

`apps/` contains executable application composition, while `packages/` contains reusable code with clearer dependency boundaries. The historical `src/` tree is still present because parts of the original academic implementation remain in use.

## Components

### `apps/api`

The FastAPI application lives in `apps/api/src/clinical_api/app.py`.

Its responsibilities are limited to HTTP concerns:

- request validation;
- response serialization;
- route definition;
- HTTP error mapping;
- dependency composition.

Current endpoints:

```text
GET  /health
POST /v1/predictions/drg
```

`GET /health` reports API liveness and whether the GRD predictor is ready.

`POST /v1/predictions/drg` accepts ICD-10 codes, ICD-9 codes, age and sex. The HTTP layer converts the payload into the shared domain request and delegates prediction to `clinical-drg`.

### `packages/clinical-core`

`clinical-core` defines shared immutable contracts used across the application.

Current contracts include:

- `GRDPredictionRequest`;
- `PredictionResult`.

This package does not own HTTP routing or model-loading behavior.

### `packages/clinical-drg`

`clinical-drg` owns the GRD prediction orchestration.

`GRDPredictor` receives three dependencies:

- model;
- label encoder;
- feature extractor.

A predictor is considered ready only when all three are available. Prediction performs feature creation, vector conversion, model inference, probability lookup and label decoding before returning a `PredictionResult`.

The package also contains `load_legacy_predictor()`, which adapts the current historical model artifacts into the new package boundary.

### `src/`

The `src/` tree still contains implementation inherited from the academic project, including the feature extractor and training flow used by compatibility code.

New application boundaries should prefer `apps/` and `packages/`. Existing `src/` code should be migrated only when there is a concrete refactor or feature that requires it.

## Dependency flow

```text
HTTP client
    |
    v
apps/api
    |
    +--> clinical-core
    |
    v
clinical-drg
    |
    +--> clinical-core
    |
    v
legacy adapter -> src/api/feature_extractor.py
```

The HTTP application depends on domain packages. Domain orchestration does not depend on FastAPI.

## Runtime readiness

The API can start without trained model artifacts.

`load_legacy_predictor()` attempts to load:

```text
models/best_model.pkl
dataset/processed/label_encoder.pkl
```

and instantiate the historical feature extractor. If any part of that process fails, it returns an unavailable `GRDPredictor` instead of preventing API startup.

This produces two distinct runtime states:

- API alive, GRD predictor ready;
- API alive, GRD predictor unavailable.

When the predictor is unavailable, `/health` remains successful with `drg_model_ready: false`, while prediction requests return HTTP 503.

## Training/inference schema contract

The current inference feature extractor reads training metadata from `dataset/processed/metadata.pkl`.

That metadata controls the feature order used to build inference vectors. The corresponding regression tests verify that inference preserves the training schema and age-bucket mapping.

Changes to preprocessing or feature metadata therefore affect both training and inference and must be treated as a shared contract.

## Architectural rules

- Keep HTTP-specific logic inside `apps/api`.
- Keep reusable prediction behavior inside `packages/`.
- Keep `clinical-core` free of FastAPI and model-loading concerns.
- Do not create additional top-level services or packages without implemented responsibilities.
- Do not describe the system as microservices while it runs as one application boundary.
- Preserve API startup when optional model artifacts are unavailable.
- Protect changes to training metadata or feature ordering with regression tests.

## Current limitations

- The GRD package still depends on a compatibility adapter that imports the historical feature extractor from `src/`.
- Model artifacts are loaded from local filesystem paths rather than a dedicated model registry.
- The training implementation has not yet been fully extracted into the new package layout.

These are current implementation constraints, not separate architectural components.
