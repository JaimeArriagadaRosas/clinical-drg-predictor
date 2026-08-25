# SDD ledger — plan: docs/superpowers/plans/2026-08-25-clinical-ml-platform.md

Execution mode: isolated feature branch `feat/platform-runtime-web-fhir` through GitHub connector. Local worktree creation was attempted but blocked because the sandbox cannot resolve github.com. No work will be applied to `main` during execution.

Merge policy: preserve granular commits; no squash merge. Documentation is updated incrementally with implementation stages.

Ruling: use the GitHub feature branch as the isolated workspace because the sandbox cannot resolve github.com for a local worktree — cost if wrong: local-only verification is unavailable, so GitHub Actions must provide executable validation.

Ruling: map MIMIC `HCFA` DRG rows to the domain target system `MS-DRG`, while keeping APR separate — MIMIC distinguishes these DRG families and the predictor must not mix targets — cost if wrong: incompatible DRG labels could be learned as one target space.

Task 1: complete (commit f733860 — canonical `HospitalEncounter` contracts).
Task 2: complete (commit 1bc0241 — external dataset manifest and runtime-data policy).
Task 3: complete (commit 72ea663 — MIMIC-IV encounter adapter with synthetic fixtures).
Task 4: complete (commit 9e50376 — validation and GRD-specific EDA reports).
Task 5: complete (commit 856e172 — Parquet/DuckDB local data layer and engine boundary).
Task 6: complete (commit 67740ff — deterministic versioned GRD feature pipeline).
Task 7: complete (commit c1ae311 — patient-grouped and temporal leakage-safe splits).
Task 8: complete (commit a65dbb5 — baseline/RandomForest/optional LightGBM training and multiclass evaluation).
Task 9: complete (commit 63a937a — versioned model publication and local MLflow tracking).
Task 10: complete (commits 3580ac8..c0207af — Typer/Rich Training Workbench boundary and routing tests).
