import numpy as np

from clinical_ml.training import select_best_model, train_candidates


def test_candidate_training_runs_baseline_and_random_forest():
    X_train = np.array([[0.0], [0.1], [0.9], [1.0], [0.2], [0.8]])
    y_train = np.array([0, 0, 1, 1, 0, 1])
    X_validation = np.array([[0.05], [0.95]])
    y_validation = np.array([0, 1])

    results = train_candidates(X_train, y_train, X_validation, y_validation)
    names = {result.name for result in results}

    assert {"DummyClassifier", "RandomForest"} <= names
    best = select_best_model(results)
    assert best.name in names
    assert "macro_f1" in best.metrics
