import json

import joblib
import numpy as np
from sklearn.dummy import DummyClassifier

from clinical_core import GRDPredictionRequest
from clinical_drg import (
    GRDPredictor,
    PredictorUnavailableError,
    load_published_predictor,
)


class FakeExtractor:
    def create_features(self, **kwargs):
        return kwargs

    def features_to_vector(self, features):
        return [1, 0, 1]


class FakeModel:
    def predict(self, rows):
        return [1]

    def predict_proba(self, rows):
        return [[0.2, 0.8]]


class FakeEncoder:
    def inverse_transform(self, values):
        return ["GRD-001"]


def test_predictor_returns_domain_result():
    predictor = GRDPredictor(FakeModel(), FakeEncoder(), FakeExtractor())
    result = predictor.predict(GRDPredictionRequest(icd10_codes=("E11.9",), age=65, sex="F"))
    assert result.label == "GRD-001"
    assert result.confidence == 0.8
    assert result.model_name == "legacy-grd"


def test_predictor_reports_unavailable_assets():
    predictor = GRDPredictor(None, None, None)
    try:
        predictor.predict(GRDPredictionRequest(icd10_codes=("E11.9",)))
    except PredictorUnavailableError:
        return
    raise AssertionError("PredictorUnavailableError was not raised")


def test_published_artifact_loads_ready_predictor(tmp_path):
    model = DummyClassifier(strategy="most_frequent")
    model.fit(np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]), np.array([0, 0]))
    joblib.dump(model, tmp_path / "model.joblib")
    (tmp_path / "feature-schema.json").write_text(
        json.dumps(
            {
                "version": "grd-features/v1",
                "names": ["age_65_plus", "sex_f", "dx:E11.9"],
            }
        ),
        encoding="utf-8",
    )
    labels = {"GRD-001": 0}
    (tmp_path / "labels.json").write_text(json.dumps(labels), encoding="utf-8")
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "model_version": "demo-v1",
                "model_name": "DummyClassifier",
                "feature_schema_version": "grd-features/v1",
                "label_mapping": labels,
            }
        ),
        encoding="utf-8",
    )

    predictor = load_published_predictor(tmp_path)
    result = predictor.predict(
        GRDPredictionRequest(icd10_codes=("E11.9",), age=65, sex="F")
    )

    assert predictor.ready is True
    assert result.label == "GRD-001"
    assert result.model_name == "DummyClassifier"
    assert result.model_version == "demo-v1"


def test_invalid_published_artifact_returns_unavailable_predictor(tmp_path):
    predictor = load_published_predictor(tmp_path)
    assert predictor.ready is False
