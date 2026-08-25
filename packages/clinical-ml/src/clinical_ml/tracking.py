from __future__ import annotations

from pathlib import Path
from typing import Protocol

import mlflow


class ExperimentTracker(Protocol):
    def log_run(self, name: str, params: dict, metrics: dict[str, float]) -> str: ...


class MLflowTracker:
    def __init__(self, tracking_dir: Path, experiment_name: str = "clinical-grd") -> None:
        tracking_dir.mkdir(parents=True, exist_ok=True)
        mlflow.set_tracking_uri(tracking_dir.resolve().as_uri())
        mlflow.set_experiment(experiment_name)
        self.experiment_name = experiment_name

    def log_run(self, name: str, params: dict, metrics: dict[str, float]) -> str:
        with mlflow.start_run(run_name=name) as run:
            if params:
                mlflow.log_params(params)
            if metrics:
                mlflow.log_metrics(metrics)
            return run.info.run_id
