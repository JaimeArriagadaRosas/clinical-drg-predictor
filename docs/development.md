# Development

## Requirements

The workspace supports Python 3.11 through Python 3.13 according to the root project configuration. Continuous integration currently validates Python 3.11 and 3.12.

The repository uses `uv` for workspace and dependency management.

## Install the workspace

For API, package and test development:

```bash
uv sync --all-packages --group dev
```

For work involving the historical training pipeline:

```bash
uv sync --all-packages --group dev --group training
```

For work involving the historical Flask/Gemini chatbot:

```bash
uv sync --all-packages --group training --group legacy-chatbot
```

## Run the API

Start the FastAPI application from the repository root:

```bash
uv run uvicorn clinical_api.app:app --app-dir apps/api/src --reload
```

The API exposes:

```text
GET  /health
POST /v1/predictions/drg
```

The API does not require trained model assets to start. If the predictor cannot load its local artifacts, `/health` still responds and reports `drg_model_ready: false`.

## Run the training pipeline

The current training entry point remains under the historical `src/` tree:

```bash
uv run --group training python src/training/training_main.py --skip-lgbm
```

Training-related changes should be validated against the orchestration and feature-schema tests.

## Optional environment configuration

`.env.example` contains settings used by the historical Gemini integration.

Create a local `.env` only when that integration is required:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Never commit `.env` or real API keys.

## Quality checks

Run the same core checks used by CI:

```bash
uv run ruff check apps packages tests
uv run pytest -q
```

Ruff currently targets maintained code under `apps`, `packages` and `tests`; the root configuration excludes the historical `src`, `dataset` and `notebook` trees from Ruff.

## Workspace boundaries

When adding new code:

- executable HTTP composition belongs under `apps/api`;
- reusable clinical contracts belong in `packages/clinical-core`;
- reusable GRD prediction behavior belongs in `packages/clinical-drg`;
- avoid adding new functionality to `src/` unless it is specifically part of maintaining or migrating the historical implementation;
- add tests under `tests/` for externally visible behavior and shared contracts.

## Generated files

The repository ignores generated ML and data artifacts such as processed datasets, model files, caches and local environments.

Do not commit generated artifacts unless they are intentionally introduced as a small reviewed test fixture.
