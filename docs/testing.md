# Testing

## Scope

This document describes the automated checks that exist in the repository today and the contracts they protect.

## Test suite

The repository currently contains four focused test modules under `tests/`.

### API behavior

`tests/test_api.py` verifies:

- `/health` works even when model assets are missing;
- a configured predictor is correctly exposed through the HTTP prediction endpoint;
- prediction returns HTTP 503 when the predictor is unavailable.

These tests instantiate FastAPI with injected fake dependencies, so they do not require trained model files.

### GRD domain behavior

`tests/test_drg_service.py` verifies:

- `GRDPredictor` returns the expected domain result;
- confidence is derived from model probabilities;
- prediction fails with `PredictorUnavailableError` when required dependencies are absent.

The model, encoder and feature extractor are replaced with deterministic fakes.

### Training/inference schema compatibility

`tests/test_feature_extractor_schema.py` protects the contract between training metadata and inference.

It verifies:

- inference vectors follow the feature order stored in `metadata.pkl`;
- age values map to the expected preprocessing buckets.

This test uses temporary metadata generated inside the test and does not depend on repository-local processed artifacts.

### Training orchestration

`tests/test_training_orchestration.py` verifies CLI argument routing in the historical training pipeline.

It checks that:

- `--data-path` is forwarded only to the data-loading stage;
- model-specific options are forwarded only to the training stage;
- optional values such as a missing `max_depth` are not forwarded incorrectly.

## Running tests locally

Install the development workspace:

```bash
uv sync --all-packages --group dev
```

Run the complete test suite:

```bash
uv run pytest -q
```

Run linting over the maintained application, packages and tests:

```bash
uv run ruff check apps packages tests
```

For changes that execute the historical training pipeline, also install the training dependency group:

```bash
uv sync --all-packages --group dev --group training
```

## Continuous integration

`.github/workflows/ci.yml` runs on pushes to `main` and on pull requests.

The CI matrix currently validates Python 3.11 and Python 3.12. For each version it:

1. checks out the repository;
2. installs Python;
3. installs `uv`;
4. synchronizes the workspace with development dependencies;
5. runs Ruff;
6. runs Pytest.

The CI commands are:

```bash
uv run ruff check apps packages tests
uv run pytest -q
```

## Test design rules

- Prefer dependency injection and small fakes over requiring trained model artifacts.
- Keep tests deterministic and independent from local `.env` files.
- Use temporary directories for generated metadata and fixtures.
- Add regression coverage when changing API behavior, prediction orchestration, preprocessing metadata, feature ordering or training-stage argument routing.
- Keep generated datasets and model artifacts out of the normal test path unless a deliberately small fixture is required.

## Pull request expectation

A behavior-changing pull request should pass the same Ruff and Pytest commands used by CI and include a regression test for the changed contract when practical.
