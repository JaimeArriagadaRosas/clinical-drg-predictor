# Clinical ML Platform Design

## Status

Approved architectural direction for the reconstruction of the Clinical Intelligence Platform.

This document defines the target architecture before implementation continues. The project remains a **predictive GRD platform**. It is not a generic clinical-data framework and it is not a pharmacovigilance system.

## Product goal

Build an end-to-end clinical machine-learning platform that can:

1. acquire hospital encounter data reproducibly;
2. validate and explore those data;
3. clean and transform them into a canonical encounter representation;
4. engineer features for GRD classification;
5. train, evaluate, select and publish a predictive GRD model;
6. serve the selected model through an API;
7. expose the prediction workflow through a clinical web application and conversational assistant;
8. execute the same data pipeline locally or with distributed compute when scale justifies it.

The normal product runtime and the training lifecycle are separate application concerns.

## Primary data source

The target public research dataset is **MIMIC-IV** because it represents hospital encounters and includes the kinds of data required for GRD work, such as admissions, diagnoses, procedures, demographics and DRG codes.

Development should begin against the public MIMIC-IV demo where possible. Full MIMIC-IV access is treated as an external, user-authorized data source and must never be committed to the repository.

The historical Hospital El Pino dataset is also externalized from Git. The repository must not redistribute clinical datasets whose licensing or redistribution rights are not explicitly established.

## Repository data policy

Real datasets are runtime assets, not source code.

```text
tools/
  datasets/
    manifests/
    fetch.py
    verify.py

data/
  raw/          # gitignored
  interim/      # gitignored
  processed/    # gitignored

artifacts/
  models/       # gitignored
  reports/      # gitignored
```

The repository may contain only:

- dataset manifests;
- source metadata and provenance;
- expected schemas;
- checksums when stable and useful;
- download/import tooling;
- deliberately small synthetic or public test fixtures.

Dataset acquisition logic that is reusable by applications belongs in `clinical-data`. `tools/datasets` provides operator-facing entry points and must not duplicate pipeline logic.

## Canonical clinical contract

All supported ingestion paths must produce the same internal representation before feature engineering.

Conceptually:

```text
HospitalEncounter
├── encounter_id
├── patient
│   ├── patient_id
│   ├── age
│   └── sex
├── admission
│   ├── admitted_at
│   ├── discharged_at
│   └── discharge_disposition
├── diagnoses[]
│   ├── code
│   ├── coding_system
│   └── sequence
├── procedures[]
│   ├── code
│   ├── coding_system
│   └── sequence
└── target
    └── drg
```

FHIR, CSV/Parquet and MIMIC-specific schemas are adapters around this contract. The predictive model must not depend directly on MIMIC table layouts.

## Application boundaries

Target monorepo shape:

```text
apps/
  api/
  runtime/
  training/
  web/

packages/
  clinical-core/
  clinical-data/
  clinical-fhir/
  clinical-ml/
  clinical-drg/

tools/
  datasets/
  dev/
```

### `apps/runtime`

Owns the **product lifecycle**, not model training.

Responsibilities:

- environment preflight;
- preboot hooks;
- start API and web processes;
- process status;
- interactive operator console for the running product;
- graceful shutdown on explicit exit, SIGINT and SIGTERM;
- restart/stop/status operations.

The default product command starts inference capabilities and the chatbot/web experience.

### `apps/training`

Owns the **Training Workbench** interactive CLI.

Responsibilities:

- present pipeline state;
- run individual stages;
- run the complete training lifecycle;
- show prior run metadata and generated artifacts;
- select execution engine/configuration;
- never contain data-cleaning or ML algorithms directly.

Preferred CLI stack: Python + Typer + Rich.

### `apps/api`

Owns HTTP concerns only:

- request validation;
- OpenAPI;
- prediction endpoints;
- health/readiness;
- FHIR-facing endpoints where appropriate;
- mapping application errors to HTTP responses.

### `apps/web`

Owns the clinical user interface.

Preferred stack:

- React;
- TypeScript;
- Vite;
- Tailwind CSS;
- SVG iconography;
- clinical utility / evidence-first visual design.

The chatbot is one interaction mode inside the product, not the model itself.

## Package boundaries

### `clinical-core`

Contains stable domain contracts and shared value objects. It must remain free of FastAPI, UI, model-loading and distributed-compute dependencies.

### `clinical-data`

Owns data engineering.

Responsibilities:

- data-source contracts and adapters;
- MIMIC-IV acquisition/import integration;
- schema validation;
- EDA orchestration and reports;
- cleaning;
- canonical encounter construction;
- transformations;
- Parquet/Arrow storage;
- execution-engine abstractions.

Planned local technologies:

- Polars;
- PyArrow/Parquet;
- DuckDB.

Planned distributed adapter when justified:

- PySpark DataFrames / Spark SQL;
- Delta Lake for lakehouse-style storage where it provides a concrete benefit.

### `clinical-ml`

Owns reusable machine-learning workflow behavior.

Responsibilities:

- feature engineering;
- feature-schema versioning;
- train/validation/test splitting;
- imbalance handling applied only to training data where appropriate;
- experiment execution;
- hyperparameter search;
- evaluation;
- calibration where useful;
- model comparison;
- model metadata;
- publication/registry integration.

Candidate stack:

- scikit-learn;
- LightGBM;
- imbalanced-learn only where justified;
- MLflow for experiment and model metadata once the first reproducible training loop exists.

### `clinical-drg`

Owns the GRD predictive capability.

It defines the GRD-specific model contract, feature expectations, inference orchestration and artifact-loading adapter. It depends on shared contracts but does not own generic data-engineering infrastructure.

GRD is the only predictive capability in scope for this reconstruction.

### `clinical-fhir`

Owns healthcare interoperability adapters.

FHIR is an interchange boundary, not the storage engine and not the Big Data framework.

Initial relevant resources center on encounter-oriented data such as:

- Patient;
- Encounter;
- Condition;
- Procedure;
- Observation where needed.

FHIR Bulk Data / NDJSON is a future scale-oriented ingestion path, not a requirement for the first local training loop.

## Training pipeline

The new Training Workbench replaces the historical four-script sequence with an explicit staged pipeline.

```text
01 Acquire / Import
02 Validate
03 EDA
04 Clean
05 Transform to canonical encounters
06 Feature engineering
07 Dataset preparation and split
08 Train candidate models
09 Evaluate
10 Select best model
11 Publish versioned model artifact
```

### Stage 01 — Acquire / Import

- download public/demo data when permitted;
- import restricted/local data without redistributing it;
- record source, version and provenance;
- verify expected files and checksums where practical.

### Stage 02 — Validate

Validate structural and clinical-data assumptions before transformation:

- schema;
- required fields;
- nulls;
- duplicate identifiers;
- invalid or unsupported code systems;
- impossible demographic values;
- broken relational references.

### Stage 03 — EDA

EDA is specific to GRD prediction and hospital encounters.

Required analyses include:

- dataset overview and quality;
- demographics;
- diagnosis frequency/cardinality;
- procedure frequency/cardinality;
- GRD distribution and long tail;
- diagnosis/procedure relationships with GRD;
- missingness and duplicate patterns;
- class imbalance;
- target leakage investigation;
- repeated-patient/encounter leakage risk;
- temporal/cohort drift where timestamps permit it;
- training-readiness summary.

EDA outputs are reproducible artifacts, not manual notebook-only observations.

### Stage 04 — Clean

- normalize missing values;
- remove or reconcile duplicates;
- normalize coding-system metadata;
- enforce valid ranges and types;
- preserve an auditable distinction between source and cleaned data.

### Stage 05 — Transform

Convert source-specific data into `HospitalEncounter` records.

MIMIC table joins live behind this stage rather than leaking into downstream ML code.

### Stage 06 — Feature engineering

Produce versioned model features from canonical encounters.

The feature schema is an explicit artifact shared by training and inference.

### Stage 07 — Dataset preparation and split

Default random stratified splitting is not assumed safe.

The pipeline must detect/consider:

- repeated patients;
- repeated encounters;
- temporal ordering;
- class rarity.

Use patient-grouped or time-based splitting when the dataset supports and requires it. Any resampling/balancing occurs only after splitting and only on the training partition.

### Stage 08 — Train

At minimum:

- simple baseline;
- Random Forest;
- LightGBM where justified.

Model choice is determined by measured performance and operational constraints rather than by a hard-coded preferred algorithm.

### Stage 09 — Evaluate

For multiclass GRD prediction, evaluation should include more than accuracy:

- macro F1;
- weighted F1;
- per-class precision/recall/F1;
- confusion matrix;
- class support;
- calibration/confidence analysis where applicable;
- train-vs-validation/test gap;
- inference latency and artifact size where useful.

### Stage 10 — Select

Selection uses a documented metric policy. No model is promoted only because it has the highest training score.

### Stage 11 — Publish

Published model artifacts include:

- model binary;
- model name/version;
- training dataset/source version;
- feature-schema version;
- label mapping;
- metrics;
- training timestamp;
- code/commit identifier where available;
- dependency/runtime metadata.

The product runtime consumes only published artifacts.

## Product inference flow

The product remains a predictive GRD system.

Structured API flow:

```text
clinical encounter data
        ↓
canonical request
        ↓
GRD feature adapter
        ↓
published model
        ↓
GRD prediction + model confidence
```

Conversational flow:

```text
user narrative
    ↓
LLM clinical extraction / coding assistance
    ↓
structured clinical data
    ↓
GRD predictor
    ↓
GRD result
    ↓
user-facing explanation
```

The LLM and GRD classifier are separate components with separate uncertainty. Model confidence must not be presented as probability that the patient has a particular disease.

## Scaling strategy

Big Data support is an execution concern for the same pipeline, not a separate product.

### Local baseline

Use Polars + DuckDB + Parquet for development and datasets that fit comfortably on a workstation or can be processed with streaming/out-of-core execution.

### Distributed execution

Introduce PySpark only when data volume, joins, repeated experiments or memory pressure justify distributed compute.

The distributed engine must implement the same stage contracts used by the local engine. Business and clinical transformation logic must not be duplicated in a separate Spark-only pipeline.

### Cloud execution

Cloud backends are optional adapters. The project must retain a complete local path.

Candidate free learning/prototyping integrations may include Databricks Free Edition or other zero-cost environments, but they are never required for core correctness and must not receive restricted clinical data unless the applicable data-use terms explicitly permit it.

## Model and experiment observability

After the first reproducible local training loop works, add experiment and model lineage rather than ad-hoc files only.

The target capability includes:

- training run identifiers;
- parameters;
- metrics;
- dataset version/provenance;
- feature-schema version;
- artifact version;
- selected/published model state.

MLflow is the preferred initial implementation because it can run locally and later use a remote backend without changing the training semantics.

## CI and testing

The architecture requires tests at boundaries, not only model accuracy checks.

Required coverage categories:

- canonical contract validation;
- MIMIC adapter mapping;
- dataset acquisition/import behavior without downloading restricted data in CI;
- validation rules;
- transformation determinism;
- feature-schema stability;
- train/test leakage protections;
- model evaluation contracts;
- artifact manifest serialization;
- API prediction behavior;
- runtime lifecycle and graceful shutdown;
- Training Workbench command routing;
- frontend typecheck/lint/build.

CI must use synthetic/small public fixtures and never require the full MIMIC-IV dataset.

## Migration from the historical implementation

The historical `src/training` scripts remain compatibility code only while the new packages are implemented.

Migration order:

1. introduce canonical encounter contracts;
2. introduce `clinical-data` and MIMIC demo adapter;
3. implement reproducible EDA/validation pipeline;
4. introduce `clinical-ml` and migrate preprocessing/features;
5. implement split, train, evaluate and publish stages;
6. add `apps/training` Training Workbench;
7. make `clinical-drg` load the published artifact format;
8. remove obsolete historical training code after parity is verified;
9. remove the repository-committed clinical dataset after acquisition/import tooling is in place and its history/removal strategy is documented.

The legacy chatbot may be migrated independently after the structured prediction path remains stable.

## Non-goals for the current reconstruction

Do not add technology without an implemented responsibility.

Not required in the first implementation wave:

- Kafka;
- Hadoop MapReduce / mrjob;
- Kubernetes;
- Ray;
- microservices decomposition;
- FHIR Bulk Data ingestion;
- distributed model training;
- additional predictive targets beyond GRD.

These may be introduced later only when a measured need appears.

## Success criteria

The reconstruction is successful when a developer can:

1. clone the repository without bundled clinical datasets;
2. acquire/import an authorized MIMIC-compatible dataset through supported tooling;
3. run validation and EDA reproducibly;
4. execute the complete GRD training pipeline locally;
5. inspect evaluation results and model lineage;
6. publish a versioned GRD model artifact;
7. start the product runtime;
8. obtain the same GRD model behavior through structured API and the conversational UI;
9. switch data-processing execution engines later without rewriting clinical or ML domain logic.
