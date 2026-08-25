from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GRDPredictionRequest:
    icd10_codes: tuple[str, ...]
    icd9_codes: tuple[str, ...] = ()
    age: int | None = None
    sex: str | None = None


@dataclass(frozen=True, slots=True)
class PredictionResult:
    label: str
    confidence: float
    model_name: str
    model_version: str
