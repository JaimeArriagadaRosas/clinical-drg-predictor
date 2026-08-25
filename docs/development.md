# Development

## Prerequisites

- Python 3.11 or 3.12 for CI parity
- `uv`
- Node.js 22
- `pnpm` 10
- Java 17 only when running the optional Spark contract

## Setup

```bash
uv sync --all-packages --group dev
pnpm install
```

## Clinical data

Real clinical datasets are external runtime assets. Do not commit raw, interim, processed or model artifact directories.

Public demo acquisition:

```bash
python tools/datasets/fetch.py mimic-iv-demo --destination data/raw/mimic-iv-demo
```

Authorized full MIMIC import:

```bash
python tools/datasets/fetch.py mimic-iv --destination data/raw/mimic-iv --from-directory /path/to/mimic
```

The import path verifies an already-authorized local tree. It never bypasses PhysioNet credentials or data-use requirements.

## Product runtime

```bash
uv run clinical-platform preboot
uv run clinical-platform run
```

`clinical-platform run` owns API + web only. Training belongs to the Training Workbench.

## Training Workbench

```bash
uv run clinical-train status
uv run clinical-train run --stage validate
uv run clinical-train run --stage eda
uv run clinical-train run --all
```

Application code in `apps/training` should only orchestrate package APIs. Put reusable data operations in `clinical-data` and reusable ML behavior in `clinical-ml`.

## Model artifacts

Published artifacts live under `artifacts/models/` and are gitignored. Use `CLINICAL_MODEL_PATH` to point the API at an explicit published model directory.

Do not reintroduce implicit dependencies on historical `models/best_model.pkl` or `dataset/processed/*` paths.

## Distributed data processing

Install/use distributed dependencies only when needed. The supported compatibility line is Spark 4.0.x with Delta Lake 4.0.x.

The local path remains the source of truth for correctness. Spark is an execution adapter, not a second pipeline.

## Contribution rules

- keep application boundaries narrow;
- prefer immutable/domain contracts;
- add focused tests for behavior changes;
- do not add a new package or service without an implemented responsibility;
- preserve granular commits for this reconstruction; do not squash the integration PR.
