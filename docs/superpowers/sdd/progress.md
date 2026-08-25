# SDD ledger — plan: docs/superpowers/plans/2026-08-25-clinical-ml-platform.md

Execution mode: isolated feature branch `feat/platform-runtime-web-fhir` through GitHub connector. Local worktree creation was attempted but blocked because the sandbox cannot resolve github.com. No work will be applied to `main` during execution.

Merge policy: preserve granular commits; no squash merge. Documentation is updated incrementally with implementation stages.

Ruling: use the GitHub feature branch as the isolated workspace because the sandbox cannot resolve github.com for a local worktree — cost if wrong: local-only verification is unavailable, so GitHub Actions must provide executable validation.

Ruling: map MIMIC `HCFA` DRG rows to the domain target system `MS-DRG`, while keeping APR separate — MIMIC distinguishes these DRG families and the predictor must not mix targets — cost if wrong: incompatible DRG labels could be learned as one target space.

Ruling: preserve the historical El Pino dataset in Git history but remove it from the current tree, rather than rewriting history — cost if wrong: historic commits still contain the file, but regression/bisect history remains intact and no destructive repository rewrite occurs.

Ruling: keep the conversational extractor and GRD classifier as separate uncertainty boundaries — cost if wrong: callers must handle two result objects, but model confidence cannot be misrepresented as disease probability.

Ruling: use Spark 4.0.x with Delta Lake 4.0.x for the optional distributed extra because Delta's stable compatibility matrix pairs those release lines — cost if wrong: the project intentionally does not use the newest Spark 4.2 line until Delta compatibility catches up.

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
Task 11: complete (commit 0bfdb1c — `clinical-drg` loads published model artifacts and API keeps unavailable-startup behavior).
Task 12: complete (commits 56bdb96..321fd2e — reproducible MIMIC acquisition/import, current-tree dataset removal, and data workflow docs).
Task 13: complete (commit 99beab7 — FHIR adapter aligned to canonical `HospitalEncounter`).
Task 14: complete (commit 4269e20 — product runtime restricted to API/web and conversational extraction separated from prediction).
Task 15: complete (commit 17d0b0a — web components aligned to encounter -> GRD workflow with confidence semantics test).
Task 16: complete (commit 9c55b00 — optional Spark/Delta engine and dedicated Spark CI contract).
Task 17: implementation complete (commit fdba8ce — offline E2E training regression and final architecture/development/testing docs); final CI/review pending.
