import numpy as np

from clinical_ml.evaluation import evaluate_multiclass


def test_multiclass_evaluation_contains_required_metrics():
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 1, 1, 1])

    metrics = evaluate_multiclass(y_true, y_pred)

    assert set(("accuracy", "macro_f1", "weighted_f1", "per_class", "confusion_matrix")) <= set(metrics)
    assert metrics["per_class"]["0"]["support"] == 2
    assert metrics["confusion_matrix"] == [[1, 1], [0, 2]]
