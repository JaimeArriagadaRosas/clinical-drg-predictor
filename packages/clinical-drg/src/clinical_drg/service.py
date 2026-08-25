from typing import Any, Protocol

from clinical_core import GRDPredictionRequest, PredictionResult


class FeatureExtractor(Protocol):
    def create_features(
        self,
        icd10_codes: list[str] | None = None,
        icd9_codes: list[str] | None = None,
        edad_num: int | None = None,
        sexo: str | None = None,
    ) -> dict[str, Any]: ...

    def features_to_vector(self, features: dict[str, Any]) -> list[int]: ...


class PredictorUnavailableError(RuntimeError):
    """Raised when prediction assets are not available."""


class GRDPredictor:
    def __init__(
        self,
        model: Any | None,
        label_encoder: Any | None,
        feature_extractor: FeatureExtractor | None,
        *,
        model_name: str = "legacy-grd",
        model_version: str = "1",
    ) -> None:
        self._model = model
        self._label_encoder = label_encoder
        self._feature_extractor = feature_extractor
        self._model_name = model_name
        self._model_version = model_version

    @property
    def ready(self) -> bool:
        return all(
            component is not None
            for component in (self._model, self._label_encoder, self._feature_extractor)
        )

    def predict(self, request: GRDPredictionRequest) -> PredictionResult:
        if not self.ready:
            raise PredictorUnavailableError("GRD model assets are not available")

        features = self._feature_extractor.create_features(
            icd10_codes=list(request.icd10_codes),
            icd9_codes=list(request.icd9_codes),
            edad_num=request.age,
            sexo=request.sex,
        )
        vector = self._feature_extractor.features_to_vector(features)
        prediction = self._model.predict([vector])[0]
        probabilities = self._model.predict_proba([vector])[0]
        confidence = float(max(probabilities))
        label = str(self._label_encoder.inverse_transform([prediction])[0])

        return PredictionResult(
            label=label,
            confidence=confidence,
            model_name=self._model_name,
            model_version=self._model_version,
        )
