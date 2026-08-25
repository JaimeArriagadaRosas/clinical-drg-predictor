from clinical_api.conversation import ClinicalExtraction, ConversationalGRDService
from clinical_drg import GRDPredictor


class FakeExtractorClient:
    def extract(self, narrative: str) -> ClinicalExtraction:
        assert narrative
        return ClinicalExtraction(
            icd10_codes=("I10",),
            age=65,
            sex="F",
            extraction_confidence=0.72,
        )


class FakeFeatureExtractor:
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
        return ["291"]


def test_conversational_service_keeps_extraction_and_model_confidence_separate():
    predictor = GRDPredictor(
        FakeModel(),
        FakeEncoder(),
        FakeFeatureExtractor(),
        model_name="demo",
        model_version="v1",
    )
    service = ConversationalGRDService(FakeExtractorClient(), predictor)

    result = service.predict("Paciente con antecedente de hipertensión")

    assert result.extraction.extraction_confidence == 0.72
    assert result.prediction.confidence == 0.91
    assert result.prediction.label == "291"
