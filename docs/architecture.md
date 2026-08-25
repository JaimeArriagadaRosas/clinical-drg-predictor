# Architecture

## Purpose

The repository is an end-to-end clinical ML platform whose only predictive target in this reconstruction is GRD classification.

## Application boundaries

`apps/runtime` owns the product lifecycle and starts only API + web. `apps/training` owns offline pipeline orchestration. `apps/api` maps HTTP/FHIR requests to inference. `apps/web` owns the clinical UI.

## Package boundaries

- `clinical-core`: stable shared inference contracts.
- `clinical-data`: source-independent `HospitalEncounter`, MIMIC adapter, validation, EDA, Parquet/DuckDB and execution engines.
- `clinical-ml`: feature schema, leakage-safe splitting, candidate training, evaluation, model publication and MLflow tracking.
- `clinical-drg`: GRD-specific inference and published-artifact loading.
- `clinical-fhir`: FHIR Bundle -> canonical encounter interoperability.

## Canonical flow

```text
source data
  -> HospitalEncounter
  -> validation / EDA
  -> feature schema + matrix
  -> split
  -> train / evaluate / select
  -> published model artifact
  -> clinical-drg
  -> API / conversational boundary / web
```

Source-specific layouts must not leak into `clinical-ml` or `clinical-drg`.

## Model publication

A published model directory contains:

```text
model.joblib
manifest.json
feature-schema.json
labels.json
```

The manifest carries model identity, dataset provenance, feature schema version, metrics, label mapping and runtime metadata. The product consumes only this published format.

## Data scale

Local execution is the default and remains fully functional without cloud accounts:

```text
Polars -> Parquet -> DuckDB
```

Distributed execution is optional:

```text
PySpark DataFrames / Spark SQL -> Parquet or Delta Lake
```

The Spark adapter implements the same engine boundary; it does not duplicate clinical transformation or ML business logic.

## FHIR

FHIR is an interoperability adapter around the canonical encounter. It is not the warehouse, lakehouse or distributed compute engine.

## Conversational boundary

Narrative extraction and GRD prediction are independent uncertainty sources. `ClinicalExtraction` may carry extraction confidence; `PredictionResult` carries GRD model confidence. They must never be presented as the same probability.

## Legacy

`src/` and historical notebooks remain migration references only where still required. New application/package responsibilities belong under `apps/` and `packages/`.
