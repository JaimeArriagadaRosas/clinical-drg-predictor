from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from clinical_core import GRDPredictionRequest, PredictionResult
from clinical_drg import GRDPredictor


@dataclass(frozen=True, slots=True)
class ClinicalExtraction:
    icd10_codes: tuple[str, ...]
    icd9_codes: tuple[str, ...] = ()
    age: int | None = None
    sex: str | None = None
    extraction_confidence: float | None = None


@dataclass(frozen=True, slots=True)
class ConversationalPrediction:
    extraction: ClinicalExtraction
    prediction: PredictionResult


class ClinicalExtractionClient(Protocol):
    def extract(self, narrative: str) -> ClinicalExtraction: ...


class ConversationalGRDService:
    """Coordinate language extraction and GRD inference without conflating their uncertainty."""

    def __init__(self, extractor: ClinicalExtractionClient, predictor: GRDPredictor) -> None:
        self._extractor = extractor
        self._predictor = predictor

    def predict(self, narrative: str) -> ConversationalPrediction:
        extraction = self._extractor.extract(narrative)
        prediction = self._predictor.predict(
            GRDPredictionRequest(
                icd10_codes=extraction.icd10_codes,
                icd9_codes=extraction.icd9_codes,
                age=extraction.age,
                sex=extraction.sex,
            )
        )
        return ConversationalPrediction(extraction=extraction, prediction=prediction)
