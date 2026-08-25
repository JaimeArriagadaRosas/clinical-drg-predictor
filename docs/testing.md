# Testing

## Python

Run the normal lightweight suite without Spark:

```bash
uv run ruff check apps packages tools tests
uv run pytest -q -m "not spark"
```

Coverage includes canonical encounter contracts, MIMIC mapping, dataset manifest/acquisition behavior, validation, EDA, Parquet/DuckDB, feature schemas, leakage-safe splitting, model training/evaluation, artifact publication, FHIR mapping, API behavior, runtime lifecycle and Training Workbench routing.

## End-to-end training regression

```bash
uv run pytest tests/test_e2e_training_demo.py -q
```

The E2E test is network-free and uses synthetic hospital encounters. It verifies:

```text
HospitalEncounter -> features -> patient split -> train -> evaluate
-> publish -> load -> predict
```

It must never download MIMIC-IV in CI.

## Frontend

```bash
pnpm --dir apps/web lint
pnpm --dir apps/web test --run
pnpm --dir apps/web build
```

The UI tests explicitly protect the distinction between GRD model confidence and disease probability.

## Spark contract

Spark is tested separately to keep the standard CI path lightweight:

```bash
uv run --with "pyspark>=4.0,<4.1" pytest tests/test_spark_engine_contract.py -q -m spark
```

The contract uses a tiny local Spark session and verifies Parquet interoperability. Delta functionality is configuration-gated and remains optional.

## CI jobs

GitHub Actions runs independent jobs for:

1. Python quality on Python 3.11 and 3.12.
2. Web lint/test/build on Node 22.
3. Spark contract on Python 3.12 + Java 17.

A merge is not considered ready while any required job is failing.
