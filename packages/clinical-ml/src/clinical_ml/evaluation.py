from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)


def evaluate_multiclass(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    labels: list[int] | tuple[int, ...] | None = None,
) -> dict[str, Any]:
    resolved_labels = list(labels) if labels is not None else sorted(set(map(int, y_true)))
    precision, recall, per_class_f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=resolved_labels,
        zero_division=0,
    )
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(
            f1_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "per_class": {
            str(label): {
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(per_class_f1[index]),
                "support": int(support[index]),
            }
            for index, label in enumerate(resolved_labels)
        },
        "confusion_matrix": confusion_matrix(
            y_true,
            y_pred,
            labels=resolved_labels,
        ).tolist(),
    }
