from fastapi.testclient import TestClient

from clinical_api.app import create_app
from clinical_drg import GRDPredictor


class FakeExtractor:
    def create_features(self, **kwargs):
        return kwargs

    def features_to_vector(self, features):
        return [1]


class FakeModel:
    def predict(self, rows):
        return [0]

    def predict_proba(self, rows):
        return [[0.91]]


class FakeEncoder:
    def inverse_transform(self, values):
        return ["GRD-DEMO"]


def test_health_does_not_require_model_assets():
    client = TestClient(create_app(GRDPredictor(None, None, None)))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "drg_model_ready": False}


def test_prediction_maps_domain_result_to_http():
    predictor = GRDPredictor(FakeModel(), FakeEncoder(), FakeExtractor())
    client = TestClient(create_app(predictor))
    response = client.post(
        "/v1/predictions/drg",
        json={"icd10_codes": ["E11.9"], "icd9_codes": [], "age": 65, "sex": "F"},
    )
    assert response.status_code == 200
    assert response.json()["label"] == "GRD-DEMO"
    assert response.json()["confidence"] == 0.91


def test_fhir_prediction_uses_the_same_domain_predictor():
    predictor = GRDPredictor(FakeModel(), FakeEncoder(), FakeExtractor())
    client = TestClient(create_app(predictor))
    response = client.post(
        "/v1/predictions/drg/fhir",
        json={
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Condition",
                        "code": {
                            "coding": [
                                {"system": "http://hl7.org/fhir/sid/icd-10", "code": "I10"}
                            ]
                        },
                    }
                }
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["label"] == "GRD-DEMO"


def test_prediction_returns_503_when_assets_are_missing():
    client = TestClient(create_app(GRDPredictor(None, None, None)))
    response = client.post("/v1/predictions/drg", json={"icd10_codes": ["E11.9"]})
    assert response.status_code == 503
