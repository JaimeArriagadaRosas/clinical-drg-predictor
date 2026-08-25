# Clinical ML Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconstruct the project into an end-to-end GRD prediction platform using MIMIC-IV-oriented hospital encounter data, a reproducible Python training pipeline, versioned model artifacts, and separate product/runtime and training application boundaries.

**Architecture:** Source-specific clinical data is converted into a canonical `HospitalEncounter` contract inside `clinical-data`, then transformed into versioned GRD features inside `clinical-ml`. `apps/training` orchestrates the offline lifecycle; `clinical-drg` consumes only published model artifacts; `apps/runtime` starts inference/web/chat product services. Local processing uses Polars, DuckDB and Parquet first; distributed PySpark/Delta adapters are added only after the local pipeline contract is stable.

**Tech Stack:** Python 3.11-3.13, uv, Pydantic, Polars, PyArrow/Parquet, DuckDB, Typer, Rich, scikit-learn, LightGBM, MLflow, FastAPI, React, TypeScript, Vite, Tailwind CSS, pytest, Ruff, pnpm, GitHub Actions; later PySpark + Delta Lake behind the same data-engine interfaces.

**Spec:** `docs/clinical-ml-platform-design.md`

## Global Constraints

- GRD classification is the only predictive target in scope.
- Real clinical datasets must not be committed to Git.
- MIMIC-IV Demo is the default public development source; full MIMIC-IV is user-authorized external data.
- `apps/runtime` owns product lifecycle only; `apps/training` owns the Training Workbench.
- `clinical-core` must remain free of FastAPI, model-loading, UI and distributed-compute dependencies.
- FHIR is an interoperability boundary, not a storage or Big Data engine.
- Local execution must remain fully functional without cloud accounts.
- Spark/Delta are introduced only behind stable local pipeline contracts.
- Every behavioral change requires focused regression tests.

---

## File Structure Map

### New packages

- `packages/clinical-data/src/clinical_data/contracts.py` — canonical encounter data model and source-independent data types.
- `packages/clinical-data/src/clinical_data/sources/base.py` — dataset source protocol.
- `packages/clinical-data/src/clinical_data/sources/mimic.py` — MIMIC-IV Demo/full folder adapter.
- `packages/clinical-data/src/clinical_data/validation.py` — structural/data-quality validation.
- `packages/clinical-data/src/clinical_data/eda.py` — reproducible GRD-specific EDA report generation.
- `packages/clinical-data/src/clinical_data/storage.py` — Parquet/DuckDB local storage helpers.
- `packages/clinical-data/src/clinical_data/engines/base.py` — execution engine contract.
- `packages/clinical-data/src/clinical_data/engines/polars.py` — local execution engine.
- `packages/clinical-data/src/clinical_data/engines/spark.py` — later distributed engine adapter.
- `packages/clinical-ml/src/clinical_ml/features.py` — canonical encounter to versioned feature matrix.
- `packages/clinical-ml/src/clinical_ml/splitting.py` — grouped/temporal split policies.
- `packages/clinical-ml/src/clinical_ml/training.py` — candidate training orchestration.
- `packages/clinical-ml/src/clinical_ml/evaluation.py` — multiclass metrics and reports.
- `packages/clinical-ml/src/clinical_ml/artifacts.py` — versioned model manifest/publication.
- `packages/clinical-ml/src/clinical_ml/tracking.py` — local MLflow integration.

### New application

- `apps/training/src/clinical_training/cli.py` — Typer entry point and Training Workbench menu.
- `apps/training/src/clinical_training/pipeline.py` — stage orchestration only.
- `apps/training/src/clinical_training/state.py` — run/stage state rendering and persisted metadata.

### Dataset tooling

- `tools/datasets/fetch.py` — operator-facing dataset acquisition CLI.
- `tools/datasets/verify.py` — manifest/files/checksum verification.
- `tools/datasets/manifests/mimic-iv-demo.yaml` — source metadata and expected files.

### Existing code to migrate/update

- `packages/clinical-core/src/clinical_core/contracts.py`
- `packages/clinical-drg/src/clinical_drg/*`
- `packages/clinical-fhir/src/clinical_fhir/*`
- `apps/api/src/clinical_api/app.py`
- `apps/runtime/src/clinical_runtime/*`
- `apps/web/src/*`
- `pyproject.toml`
- `.gitignore`
- `.github/workflows/ci.yml`
- `README.md`
- `docs/architecture.md`
- `docs/development.md`
- `docs/testing.md`

---

### Task 1: Canonical Hospital Encounter Contracts

**Files:**
- Create: `packages/clinical-data/pyproject.toml`
- Create: `packages/clinical-data/src/clinical_data/__init__.py`
- Create: `packages/clinical-data/src/clinical_data/contracts.py`
- Modify: `pyproject.toml`
- Test: `tests/test_clinical_data_contracts.py`

**Interfaces:**
- Produces: `ClinicalCode`, `PatientContext`, `AdmissionContext`, `HospitalEncounter`, `DRGTarget`.
- `HospitalEncounter` is source-independent and is consumed by validation, EDA, features and FHIR adapters.

- [ ] **Step 1: Write failing contract tests**

```python
from datetime import datetime

import pytest
from pydantic import ValidationError

from clinical_data.contracts import (
    AdmissionContext,
    ClinicalCode,
    DRGTarget,
    HospitalEncounter,
    PatientContext,
)


def test_hospital_encounter_accepts_valid_grd_case():
    encounter = HospitalEncounter(
        encounter_id="hadm-1",
        patient=PatientContext(patient_id="subject-1", age=65, sex="F"),
        admission=AdmissionContext(
            admitted_at=datetime(2025, 1, 1),
            discharged_at=datetime(2025, 1, 4),
            discharge_disposition="HOME",
        ),
        diagnoses=[ClinicalCode(code="I10", coding_system="ICD10", sequence=1)],
        procedures=[ClinicalCode(code="0W3P8ZZ", coding_system="ICD10PCS", sequence=1)],
        target=DRGTarget(code="291", system="MS-DRG"),
    )
    assert encounter.target.code == "291"


def test_hospital_encounter_rejects_negative_age():
    with pytest.raises(ValidationError):
        PatientContext(patient_id="subject-1", age=-1, sex="F")
```

- [ ] **Step 2: Run tests and verify failure**

Run: `uv run pytest tests/test_clinical_data_contracts.py -q`
Expected: import failure for `clinical_data`.

- [ ] **Step 3: Implement Pydantic contracts**

Implement immutable/frozen Pydantic models with:

```python
class ClinicalCode(BaseModel):
    model_config = ConfigDict(frozen=True)
    code: str
    coding_system: str
    sequence: int | None = Field(default=None, ge=1)

class PatientContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    patient_id: str
    age: int | None = Field(default=None, ge=0, le=130)
    sex: str | None = None

class AdmissionContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    admitted_at: datetime | None = None
    discharged_at: datetime | None = None
    discharge_disposition: str | None = None

class DRGTarget(BaseModel):
    model_config = ConfigDict(frozen=True)
    code: str
    system: str

class HospitalEncounter(BaseModel):
    model_config = ConfigDict(frozen=True)
    encounter_id: str
    patient: PatientContext
    admission: AdmissionContext
    diagnoses: tuple[ClinicalCode, ...]
    procedures: tuple[ClinicalCode, ...] = ()
    target: DRGTarget | None = None
```

Add `pydantic>=2.11,<3` to `clinical-data`.

- [ ] **Step 4: Register workspace and test**

Add `packages/clinical-data` to `[tool.uv.workspace].members` and `packages/clinical-data/src` to pytest `pythonpath`.

Run: `uv run pytest tests/test_clinical_data_contracts.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/clinical-data pyproject.toml tests/test_clinical_data_contracts.py
git commit -m "feat: add canonical clinical encounter contracts"
```

---

### Task 2: Externalize Dataset Storage and Add MIMIC Manifest

**Files:**
- Modify: `.gitignore`
- Create: `tools/datasets/manifests/mimic-iv-demo.yaml`
- Create: `tools/datasets/verify.py`
- Test: `tests/test_dataset_manifest.py`

**Interfaces:**
- Produces: manifest structure with `name`, `source`, `version`, `files`, `license_url`, `access`.
- Produces function: `verify_dataset(root: Path, manifest_path: Path) -> DatasetVerification`.

- [ ] **Step 1: Write failing manifest verification tests**

```python
from pathlib import Path

from tools.datasets.verify import verify_dataset


def test_mimic_manifest_reports_missing_required_file(tmp_path: Path):
    manifest = Path("tools/datasets/manifests/mimic-iv-demo.yaml")
    result = verify_dataset(tmp_path, manifest)
    assert result.ok is False
    assert "hosp/admissions.csv.gz" in result.missing_files
```

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/test_dataset_manifest.py -q`
Expected: module/file not found.

- [ ] **Step 3: Add manifest and verifier**

Manifest must list at least:

```yaml
name: mimic-iv-demo
version: "2.2"
access: public-demo
source: https://physionet.org/content/mimic-iv-demo/2.2/
license_url: https://physionet.org/content/mimic-iv-demo/2.2/
files:
  - hosp/admissions.csv.gz
  - hosp/patients.csv.gz
  - hosp/diagnoses_icd.csv.gz
  - hosp/procedures_icd.csv.gz
  - hosp/drgcodes.csv.gz
```

`verify.py` parses YAML with `PyYAML>=6.0`, checks every required path and returns a frozen dataclass:

```python
@dataclass(frozen=True)
class DatasetVerification:
    ok: bool
    missing_files: tuple[str, ...]
```

- [ ] **Step 4: Ignore real runtime data**

Add:

```gitignore
/data/raw/
/data/interim/
/data/processed/
/artifacts/models/
/artifacts/reports/
```

Do not delete the historical committed dataset yet; removal is Task 12 after replacement tooling is verified.

- [ ] **Step 5: Test and commit**

Run: `uv run pytest tests/test_dataset_manifest.py -q`
Expected: PASS.

```bash
git add .gitignore tools/datasets tests/test_dataset_manifest.py
git commit -m "feat: add external dataset manifest verification"
```

---

### Task 3: MIMIC-IV Adapter to Canonical Encounters

**Files:**
- Create: `packages/clinical-data/src/clinical_data/sources/__init__.py`
- Create: `packages/clinical-data/src/clinical_data/sources/base.py`
- Create: `packages/clinical-data/src/clinical_data/sources/mimic.py`
- Test: `tests/test_mimic_source.py`
- Fixtures: `tests/fixtures/mimic/*` with tiny synthetic rows only.

**Interfaces:**
- Produces protocol: `EncounterSource.iter_encounters() -> Iterator[HospitalEncounter]`.
- Produces: `MimicEncounterSource(root: Path, drg_system: str = "MS")`.

- [ ] **Step 1: Create synthetic fixture tables and failing adapter test**

Fixture rows should include one patient, one admission, two diagnoses, one procedure and one DRG row with shared `subject_id`/`hadm_id`.

```python
from pathlib import Path

from clinical_data.sources.mimic import MimicEncounterSource


def test_mimic_source_joins_hospital_tables_into_encounter():
    source = MimicEncounterSource(Path("tests/fixtures/mimic"))
    encounters = list(source.iter_encounters())
    assert len(encounters) == 1
    encounter = encounters[0]
    assert encounter.encounter_id == "100001"
    assert encounter.diagnoses[0].sequence == 1
    assert encounter.target is not None
```

- [ ] **Step 2: Run failing test**

Run: `uv run pytest tests/test_mimic_source.py -q`
Expected: import failure.

- [ ] **Step 3: Implement source using Polars lazy scans**

Use `polars.scan_csv` for `.csv`/`.csv.gz`, normalize identifiers to strings, aggregate diagnoses/procedures by `hadm_id`, join admissions/patients/DRG, and yield canonical encounters.

Add dependency: `polars>=1.32,<2`.

- [ ] **Step 4: Add target-system filtering**

The adapter must reject ambiguous mixed DRG systems unless explicitly filtered. A missing target yields `target=None`; training later rejects unlabeled encounters.

- [ ] **Step 5: Test and commit**

Run: `uv run pytest tests/test_mimic_source.py -q`
Expected: PASS.

```bash
git add packages/clinical-data tests/test_mimic_source.py tests/fixtures/mimic
git commit -m "feat: add MIMIC encounter adapter"
```

---

### Task 4: Validation and Reproducible GRD EDA

**Files:**
- Create: `packages/clinical-data/src/clinical_data/validation.py`
- Create: `packages/clinical-data/src/clinical_data/eda.py`
- Test: `tests/test_validation.py`
- Test: `tests/test_eda.py`

**Interfaces:**
- Produces: `validate_encounters(encounters) -> ValidationReport`.
- Produces: `build_eda_report(encounters) -> EDAReport`.
- Both return serializable Pydantic/dataclass results; plotting is separate from metric computation.

- [ ] **Step 1: Write validation tests**

Test duplicate encounter IDs, missing diagnoses, invalid age, unlabeled training cases, and duplicate diagnosis sequence numbers.

- [ ] **Step 2: Implement deterministic validation report**

`ValidationReport` includes counts/severity for `errors`, `warnings`, `encounter_count`, `labeled_count`.

- [ ] **Step 3: Write EDA tests**

Test that a synthetic 3-case input produces:

```python
assert report.encounter_count == 3
assert report.unique_patients == 2
assert report.drg_distribution["291"] == 2
assert report.diagnosis_frequency["I10"] == 2
```

- [ ] **Step 4: Implement EDA metrics**

Include overview, demographics, diagnosis/procedure cardinality, GRD distribution, class support, repeated-patient counts, missingness and leakage-risk indicators. Keep charts derived from report data.

- [ ] **Step 5: Test and commit**

Run: `uv run pytest tests/test_validation.py tests/test_eda.py -q`
Expected: PASS.

```bash
git add packages/clinical-data tests/test_validation.py tests/test_eda.py
git commit -m "feat: add clinical validation and GRD EDA"
```

---

### Task 5: Local Parquet/DuckDB Data Layer

**Files:**
- Create: `packages/clinical-data/src/clinical_data/storage.py`
- Create: `packages/clinical-data/src/clinical_data/engines/__init__.py`
- Create: `packages/clinical-data/src/clinical_data/engines/base.py`
- Create: `packages/clinical-data/src/clinical_data/engines/polars.py`
- Test: `tests/test_local_data_engine.py`

**Interfaces:**
- Produces: `DataEngine` protocol.
- Produces: `PolarsDataEngine`.
- Produces: `write_encounters_parquet(encounters, path)` and `open_analytics_database(path)`.

- [ ] **Step 1: Write failing storage round-trip test**

```python
def test_encounters_round_trip_through_parquet(tmp_path, sample_encounters):
    path = tmp_path / "encounters.parquet"
    write_encounters_parquet(sample_encounters, path)
    restored = read_encounters_parquet(path)
    assert restored == sample_encounters
```

- [ ] **Step 2: Implement Arrow/Parquet serialization**

Flatten nested code lists into stable list/struct columns; store schema version metadata.

Add `pyarrow>=19,<22`.

- [ ] **Step 3: Write DuckDB aggregation test**

Verify a SQL query can compute DRG counts from the generated Parquet without loading all rows into Python.

- [ ] **Step 4: Implement DuckDB helper**

Add `duckdb>=1.3,<2` and expose read-only analytics connection helpers.

- [ ] **Step 5: Test and commit**

Run: `uv run pytest tests/test_local_data_engine.py -q`
Expected: PASS.

```bash
git add packages/clinical-data tests/test_local_data_engine.py
git commit -m "feat: add local parquet and duckdb data engine"
```

---

### Task 6: Versioned GRD Feature Pipeline

**Files:**
- Create: `packages/clinical-ml/pyproject.toml`
- Create: `packages/clinical-ml/src/clinical_ml/__init__.py`
- Create: `packages/clinical-ml/src/clinical_ml/features.py`
- Modify: `pyproject.toml`
- Test: `tests/test_feature_pipeline.py`

**Interfaces:**
- Produces: `FeatureSchema(version: str, names: tuple[str, ...])`.
- Produces: `FeatureDataset(X, y, patient_ids, encounter_ids, schema, label_mapping)`.
- Produces: `build_grd_features(encounters) -> FeatureDataset`.

- [ ] **Step 1: Write failing deterministic feature test**

Use two encounters with known diagnoses/procedures and assert feature names/order are identical across repeated calls.

- [ ] **Step 2: Implement minimal source-independent feature pipeline**

Start with explicit, inspectable features: age bucket, sex encoding, diagnosis-code multi-hot representation and procedure-code multi-hot representation derived from the training vocabulary. Do not introduce embeddings in this wave.

- [ ] **Step 3: Persist schema metadata**

The schema version and ordered feature names must serialize to JSON and be loadable independently of model binary.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_feature_pipeline.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/clinical-ml pyproject.toml tests/test_feature_pipeline.py
git commit -m "feat: add versioned GRD feature pipeline"
```

---

### Task 7: Leakage-Safe Dataset Splitting

**Files:**
- Create: `packages/clinical-ml/src/clinical_ml/splitting.py`
- Test: `tests/test_splitting.py`

**Interfaces:**
- Produces: `DatasetSplit(train_idx, validation_idx, test_idx, policy)`.
- Produces: `split_by_patient(...)`.
- Produces: `split_temporally(...)`.

- [ ] **Step 1: Write patient leakage test**

Create encounters where one patient has multiple admissions and assert no patient appears in more than one partition.

- [ ] **Step 2: Implement grouped stratified strategy**

Use patient IDs as groups. If exact class stratification cannot be preserved, keep groups intact and record class-support diagnostics.

- [ ] **Step 3: Write temporal split test**

Assert training admission timestamps precede validation/test windows.

- [ ] **Step 4: Implement temporal policy**

Require non-null admission timestamps and fail with a clear domain error if absent.

- [ ] **Step 5: Commit**

```bash
git add packages/clinical-ml/src/clinical_ml/splitting.py tests/test_splitting.py
git commit -m "feat: add leakage-safe dataset splitting"
```

---

### Task 8: Model Training, Evaluation and Selection

**Files:**
- Create: `packages/clinical-ml/src/clinical_ml/training.py`
- Create: `packages/clinical-ml/src/clinical_ml/evaluation.py`
- Test: `tests/test_model_training.py`
- Test: `tests/test_model_evaluation.py`

**Interfaces:**
- Produces: `CandidateModelResult(name, model, metrics)`.
- Produces: `train_candidates(...)`.
- Produces: `evaluate_multiclass(...)`.
- Produces: `select_best_model(results, primary_metric="macro_f1")`.

- [ ] **Step 1: Write evaluation-contract test**

Assert metrics contain `accuracy`, `macro_f1`, `weighted_f1`, per-class support and confusion matrix.

- [ ] **Step 2: Implement evaluation using sklearn metrics**

Use deterministic labels and `zero_division=0`.

- [ ] **Step 3: Write candidate-training test**

Use tiny synthetic arrays and verify at least baseline + RandomForest run without external assets.

- [ ] **Step 4: Implement candidate training**

Candidates:
- DummyClassifier baseline;
- RandomForestClassifier;
- LightGBM only when installed/enabled.

- [ ] **Step 5: Implement selection policy and commit**

Select by validation `macro_f1`, break ties by weighted F1, then smaller artifact size if measured.

```bash
git add packages/clinical-ml/src/clinical_ml tests/test_model_training.py tests/test_model_evaluation.py
git commit -m "feat: add GRD model training and evaluation"
```

---

### Task 9: Versioned Model Artifact Publication + MLflow

**Files:**
- Create: `packages/clinical-ml/src/clinical_ml/artifacts.py`
- Create: `packages/clinical-ml/src/clinical_ml/tracking.py`
- Test: `tests/test_model_artifacts.py`
- Test: `tests/test_tracking.py`

**Interfaces:**
- Produces: `ModelManifest`.
- Produces: `publish_model(result, feature_schema, dataset_metadata, output_dir) -> PublishedModel`.
- Produces: `ExperimentTracker` abstraction and `MLflowTracker` implementation.

- [ ] **Step 1: Write manifest serialization test**

Assert manifest contains model version/name, feature schema version, dataset source/version, metrics, timestamp and label mapping.

- [ ] **Step 2: Implement publication format**

Output directory shape:

```text
artifacts/models/<model-version>/
  model.joblib
  manifest.json
  feature-schema.json
  labels.json
```

- [ ] **Step 3: Add local MLflow test with temporary tracking directory**

Verify run parameters/metrics can be logged without remote infrastructure.

- [ ] **Step 4: Implement MLflow tracker**

Add `mlflow>=3,<4`; configure local file-backed tracking by default.

- [ ] **Step 5: Commit**

```bash
git add packages/clinical-ml/src/clinical_ml tests/test_model_artifacts.py tests/test_tracking.py
git commit -m "feat: add model publication and experiment tracking"
```

---

### Task 10: Training Workbench Application

**Files:**
- Create: `apps/training/pyproject.toml`
- Create: `apps/training/src/clinical_training/__init__.py`
- Create: `apps/training/src/clinical_training/cli.py`
- Create: `apps/training/src/clinical_training/pipeline.py`
- Create: `apps/training/src/clinical_training/state.py`
- Modify: `pyproject.toml`
- Test: `tests/test_training_workbench.py`

**Interfaces:**
- Produces CLI: `clinical-train`.
- Produces stage names: `acquire`, `validate`, `eda`, `clean`, `transform`, `features`, `split`, `train`, `evaluate`, `select`, `publish`.
- Consumes `clinical-data` and `clinical-ml` only through package APIs.

- [ ] **Step 1: Write Typer CLI routing tests**

Use `typer.testing.CliRunner` and injected fake pipeline to verify `run --stage eda` and `run --all` route correctly.

- [ ] **Step 2: Implement pipeline orchestration class**

```python
class TrainingPipeline:
    def run_stage(self, stage: TrainingStage) -> StageResult: ...
    def run_all(self) -> list[StageResult]: ...
```

Each stage delegates to package functions; no data manipulation lives in this app.

- [ ] **Step 3: Implement Rich status UI**

Show dataset, engine, stage state and latest artifact paths. No emoji; use text/SVG irrelevant in terminal, rely on Rich symbols only where ASCII-safe fallback exists.

- [ ] **Step 4: Register workspace/entry point**

Add dependencies `typer>=0.16,<1`, `rich>=14,<15`, `clinical-data`, `clinical-ml`.

- [ ] **Step 5: Test and commit**

Run: `uv run pytest tests/test_training_workbench.py -q`
Expected: PASS.

```bash
git add apps/training pyproject.toml tests/test_training_workbench.py
git commit -m "feat: add interactive training workbench"
```

---

### Task 11: Migrate `clinical-drg` to Published Artifact Format

**Files:**
- Modify: `packages/clinical-drg/src/clinical_drg/*`
- Modify: `apps/api/src/clinical_api/app.py`
- Test: `tests/test_drg_service.py`
- Test: `tests/test_api.py`

**Interfaces:**
- `clinical-drg` loads `PublishedModel` manifests instead of implicit legacy paths.
- Existing API response shape remains backward compatible unless spec tests explicitly change it.

- [ ] **Step 1: Write failing artifact-loading test**

Create a temporary published model directory and assert `load_published_predictor(path)` returns a ready predictor.

- [ ] **Step 2: Implement manifest-driven loader**

Validate model/feature schema/labels compatibility before returning ready state.

- [ ] **Step 3: Preserve unavailable startup behavior**

Missing/invalid artifact must keep `/health` alive with `drg_model_ready: false` and prediction endpoints returning 503.

- [ ] **Step 4: Run API/domain tests**

Run: `uv run pytest tests/test_drg_service.py tests/test_api.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/clinical-drg apps/api tests/test_drg_service.py tests/test_api.py
git commit -m "refactor: load GRD models from published artifacts"
```

---

### Task 12: Replace Committed Dataset with Acquisition/Import Tooling

**Files:**
- Create: `tools/datasets/fetch.py`
- Modify: `README.md`
- Modify: `docs/development.md`
- Delete from branch: `dataset/dataset_elpino.csv`
- Test: `tests/test_dataset_fetch.py`

**Interfaces:**
- Produces command: `python tools/datasets/fetch.py mimic-iv-demo --destination data/raw/mimic-iv-demo`.
- Restricted/full MIMIC uses import/verification, not automated credential bypass.

- [ ] **Step 1: Write downloader test with injected HTTP client**

Do not hit PhysioNet in CI. Inject a fake downloader and assert expected relative paths are created.

- [ ] **Step 2: Implement public-demo acquisition**

Download only manifest-listed public demo files. Persist a local provenance receipt beside the data.

- [ ] **Step 3: Implement restricted import path**

`--from-directory PATH` verifies an already authorized local MIMIC tree without credentials or redistribution.

- [ ] **Step 4: Remove committed El Pino CSV from current tree**

Do not rewrite Git history in this task. Document that historic commits may still contain the file and that history rewriting requires a separate explicit repository-maintenance decision.

- [ ] **Step 5: Test and commit**

Run: `uv run pytest tests/test_dataset_fetch.py tests/test_dataset_manifest.py -q`
Expected: PASS.

```bash
git add tools/datasets README.md docs/development.md tests/test_dataset_fetch.py
git rm dataset/dataset_elpino.csv
git commit -m "refactor: externalize clinical datasets"
```

---

### Task 13: Align FHIR Adapter with Canonical Encounter Contract

**Files:**
- Modify: `packages/clinical-fhir/src/clinical_fhir/adapter.py`
- Modify: `packages/clinical-fhir/pyproject.toml`
- Test: `tests/test_fhir_adapter.py`

**Interfaces:**
- Produces: `bundle_to_encounter(bundle: Mapping[str, Any]) -> HospitalEncounter`.
- Existing direct `Bundle -> GRDPredictionRequest` adapter becomes compatibility-only or is removed after API migration.

- [ ] **Step 1: Update failing FHIR test**

Use Patient + Encounter + Condition + Procedure resources and assert canonical encounter fields.

- [ ] **Step 2: Implement canonical adapter**

Map resource IDs/references, demographics, diagnosis/procedure codes and encounter dates. Do not fabricate a DRG target for inference-only bundles.

- [ ] **Step 3: Update API FHIR route**

Route: FHIR Bundle -> canonical encounter -> GRD feature/inference adapter.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_fhir_adapter.py tests/test_api.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/clinical-fhir apps/api tests/test_fhir_adapter.py tests/test_api.py
git commit -m "refactor: align FHIR with canonical encounters"
```

---

### Task 14: Product Runtime and Conversational Boundary Cleanup

**Files:**
- Modify: `apps/runtime/src/clinical_runtime/cli.py`
- Modify: `apps/runtime/src/clinical_runtime/lifecycle.py`
- Create/Modify modern chatbot boundary under `apps/api/src/clinical_api/` as appropriate.
- Test: `tests/test_runtime_lifecycle.py`
- Test: conversational adapter tests with fake LLM client.

**Interfaces:**
- `clinical run` starts API + web only.
- Training is never a runtime child process by default.
- Conversational adapter returns structured extraction separately from GRD model result.

- [ ] **Step 1: Add lifecycle test asserting training is not started by product runtime**

- [ ] **Step 2: Add graceful shutdown tests for API/web child processes**

- [ ] **Step 3: Refactor runtime process registry**

Explicit services: `api`, `web`; configurable ports/commands; SIGINT/SIGTERM cleanup.

- [ ] **Step 4: Isolate LLM extraction contract**

Represent extracted clinical data independently from `PredictionResult`; no model-confidence-as-disease-probability copy.

- [ ] **Step 5: Commit**

```bash
git add apps/runtime apps/api tests
git commit -m "refactor: separate product runtime and clinical extraction"
```

---

### Task 15: Frontend Reflects Encounter → GRD Workflow

**Files:**
- Modify: `apps/web/src/App.tsx`
- Create: focused components under `apps/web/src/components/`
- Modify: `apps/web/src/api.ts`
- Modify: `apps/web/src/styles.css`
- Test: add Vitest/Testing Library configuration and focused component tests.

**Interfaces:**
- UI separates clinical input/extraction from GRD result.
- Prediction displays GRD class, confidence, model/version and input evidence summary.

- [ ] **Step 1: Add frontend test tooling and failing component tests**

Use Vitest + Testing Library. Verify model confidence is labeled as model confidence, not disease probability.

- [ ] **Step 2: Split current monolithic `App.tsx`**

Create components such as:
- `ClinicalIntakePanel`
- `EncounterSummary`
- `PredictionPanel`
- `ModelStatus`

- [ ] **Step 3: Preserve approved clinical utility/evidence-first design**

No emojis, gradients, glassmorphism or decorative dashboard metrics. SVG iconography only.

- [ ] **Step 4: Run frontend checks**

Run:

```bash
pnpm --dir apps/web lint
pnpm --dir apps/web test --run
pnpm --dir apps/web build
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/web
git commit -m "refactor: align web UI with GRD inference workflow"
```

---

### Task 16: Distributed PySpark/Delta Adapter

**Files:**
- Create: `packages/clinical-data/src/clinical_data/engines/spark.py`
- Test: `tests/test_spark_engine_contract.py`
- Modify: `packages/clinical-data/pyproject.toml` with optional dependency group only.

**Interfaces:**
- Implements the same `DataEngine` contract as `PolarsDataEngine`.
- Produces canonical/intermediate Parquet or Delta-compatible tables without changing downstream ML interfaces.

- [ ] **Step 1: Write engine contract tests against a tiny Spark local session**

Mark with `pytest.mark.spark` so normal lightweight CI can separate it.

- [ ] **Step 2: Implement Spark DataFrame adapter**

Use DataFrames/Spark SQL; do not use RDD or Hadoop MapReduce APIs.

- [ ] **Step 3: Add Delta write/read support behind explicit configuration**

Keep Parquet as the baseline interchange format.

- [ ] **Step 4: Add optional CI job**

Run Spark contract tests in one Python version to control CI cost.

- [ ] **Step 5: Commit**

```bash
git add packages/clinical-data tests/test_spark_engine_contract.py .github/workflows/ci.yml
git commit -m "feat: add distributed spark data engine"
```

---

### Task 17: End-to-End Demo Pipeline and Documentation

**Files:**
- Create: `tests/test_e2e_training_demo.py`
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/development.md`
- Modify: `docs/testing.md`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Demonstrates synthetic/public-demo data -> canonical encounters -> features -> split -> train -> evaluate -> publish -> load -> predict.

- [ ] **Step 1: Write E2E test with tiny synthetic MIMIC fixture**

The test must not download data or require network access.

- [ ] **Step 2: Run E2E and fix only contract integration issues**

Run: `uv run pytest tests/test_e2e_training_demo.py -q`
Expected: PASS.

- [ ] **Step 3: Run full Python quality checks**

```bash
uv run ruff check apps packages tools tests
uv run pytest -q
```

Expected: PASS.

- [ ] **Step 4: Run full frontend checks**

```bash
pnpm --dir apps/web lint
pnpm --dir apps/web test --run
pnpm --dir apps/web build
```

Expected: PASS.

- [ ] **Step 5: Update docs to describe only implemented behavior and commit**

```bash
git add README.md docs .github/workflows/ci.yml tests/test_e2e_training_demo.py
git commit -m "docs: complete clinical ML platform workflow"
```

---

## Self-Review

### Spec coverage

- Dataset externalization: Tasks 2 and 12.
- Canonical encounter contract: Task 1.
- MIMIC-IV adapter: Task 3.
- Validation/EDA: Task 4.
- Local data stack Polars/DuckDB/Parquet: Task 5.
- Feature engineering: Task 6.
- Leakage-safe splitting: Task 7.
- Training/evaluation/selection: Task 8.
- Model publication + lineage: Task 9.
- Training Workbench: Task 10.
- Product artifact consumption: Task 11.
- FHIR canonical mapping: Task 13.
- Product runtime separation: Task 14.
- Clinical web UX: Task 15.
- Distributed Spark/Delta path: Task 16.
- Full integration and CI/docs: Task 17.

### Scope sequencing

Tasks 1-15 form the complete local production-quality reconstruction. Task 16 is intentionally later and optional until the local contracts are stable. Task 17 verifies the integrated result.

### Type consistency

The plan consistently uses `HospitalEncounter` as the canonical domain object, `FeatureDataset` as the ML dataset boundary, `DatasetSplit` as split metadata, and `ModelManifest`/`PublishedModel` as model publication boundaries.
