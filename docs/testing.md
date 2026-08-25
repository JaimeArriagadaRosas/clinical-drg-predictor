# Testing Strategy

## Purpose

Testing protects the public API contract, GRD inference orchestration, training-schema compatibility, and the repository boundaries used by the modular monolith.

## Test levels

### Unit tests

Use unit tests for deterministic domain behavior in `packages/`, especially model orchestration, decoding, validation, and compatibility adapters. External model artifacts should be replaced with fakes or fixtures whenever possible.

### API tests

Use FastAPI tests for HTTP behavior in `apps/api`, including:

- liveness through `GET /health`;
- model-readiness reporting;
- successful GRD prediction responses;
- expected failure behavior when model assets are unavailable;
- validation and error mapping at the HTTP boundary.

### Training and schema tests

Training tests must protect the contract between preprocessing, generated metadata, and inference. Any change to feature ordering, encoding, metadata shape, or generated artifact paths requires a regression test.

## Local checks

Install development dependencies:

```bash
uv sync --all-packages --group dev
```

Run the complete automated test suite:

```bash
uv run pytest -q
```

Run repository linting:

```bash
uv run ruff check apps packages tests
```

When changing training behavior, install the training group and run the relevant tests:

```bash
uv sync --all-packages --group dev --group training
uv run pytest -q tests/test_training_orchestration.py tests/test_feature_extractor_schema.py
```

## Continuous integration

GitHub Actions runs linting and tests on the supported Python versions declared by the repository CI matrix. Pull requests should not rely on generated model files, processed datasets, local environment state, or private credentials to pass CI.

## Test data rules

- Prefer synthetic or minimal fixtures.
- Do not commit patient-identifiable data.
- Do not make tests depend on locally generated model artifacts unless the artifact itself is intentionally part of a fixture.
- Keep fixtures small enough for fast local and CI execution.

## Definition of done

A behavior-changing pull request is considered test-complete when the affected layer has regression coverage, existing tests remain green, linting passes, and any changed API/data/model contract is documented.
