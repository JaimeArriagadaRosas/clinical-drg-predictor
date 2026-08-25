from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier

from clinical_ml.evaluation import evaluate_multiclass


@dataclass(frozen=True)
class CandidateModelResult:
    name: str
    model: Any
    metrics: dict[str, Any]
    artifact_size_bytes: int | None = None


def _fit_and_evaluate(
    name: str,
    model: Any,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_validation: np.ndarray,
    y_validation: np.ndarray,
) -> CandidateModelResult:
    model.fit(X_train, y_train)
    predictions = model.predict(X_validation)
    return CandidateModelResult(
        name=name,
        model=model,
        metrics=evaluate_multiclass(y_validation, predictions),
    )


def train_candidates(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_validation: np.ndarray,
    y_validation: np.ndarray,
    *,
    include_lightgbm: bool = False,
    random_state: int = 42,
) -> tuple[CandidateModelResult, ...]:
    results = [
        _fit_and_evaluate(
            "DummyClassifier",
            DummyClassifier(strategy="most_frequent"),
            X_train,
            y_train,
            X_validation,
            y_validation,
        ),
        _fit_and_evaluate(
            "RandomForest",
            RandomForestClassifier(
                n_estimators=200,
                class_weight="balanced",
                n_jobs=-1,
                random_state=random_state,
            ),
            X_train,
            y_train,
            X_validation,
            y_validation,
        ),
    ]

    if include_lightgbm:
        try:
            import lightgbm as lgb
        except ImportError as exc:
            raise RuntimeError("LightGBM was requested but is not installed") from exc
        results.append(
            _fit_and_evaluate(
                "LightGBM",
                lgb.LGBMClassifier(
                    n_estimators=150,
                    learning_rate=0.1,
                    class_weight="balanced",
                    random_state=random_state,
                    verbosity=-1,
                ),
                X_train,
                y_train,
                X_validation,
                y_validation,
            )
        )

    return tuple(results)


def select_best_model(
    results: tuple[CandidateModelResult, ...] | list[CandidateModelResult],
    *,
    primary_metric: str = "macro_f1",
) -> CandidateModelResult:
    if not results:
        raise ValueError("at least one candidate model result is required")

    def rank(result: CandidateModelResult) -> tuple[float, float, float]:
        artifact_size = result.artifact_size_bytes
        return (
            float(result.metrics[primary_metric]),
            float(result.metrics.get("weighted_f1", 0.0)),
            -float(artifact_size if artifact_size is not None else 10**30),
        )

    return max(results, key=rank)
