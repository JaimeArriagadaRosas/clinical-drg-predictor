from clinical_core import GRDPredictionRequest
from clinical_drg import GRDPredictor, PredictorUnavailableError


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
