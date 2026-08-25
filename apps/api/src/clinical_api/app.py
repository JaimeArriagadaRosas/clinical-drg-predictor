from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from clinical_core import GRDPredictionRequest
from clinical_drg import GRDPredictor, PredictorUnavailableError, load_legacy_predictor
from clinical_fhir import FHIRAdapterError, prediction_request_from_bundle


class GRDPredictionPayload(BaseModel):
    icd10_codes: list[str] = Field(default_factory=list)
    icd9_codes: list[str] = Field(default_factory=list)
    age: int | None = Field(default=None, ge=0, le=120)
    sex: str | None = Field(default=None, pattern="^[MF]$")


class GRDPredictionResponse(BaseModel):
    label: str
    confidence: float
    model_name: str
    model_version: str


def create_app(predictor: GRDPredictor | None = None) -> FastAPI:
    drg_predictor = predictor or load_legacy_predictor()
    api = FastAPI(
        title="Clinical Intelligence Platform API",
        version="0.2.0",
        description="Modular API for clinical ML inference and interoperability.",
    )

    def predict(request: GRDPredictionRequest) -> GRDPredictionResponse:
        try:
            result = drg_predictor.predict(request)
        except PredictorUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        return GRDPredictionResponse(
            label=result.label,
            confidence=result.confidence,
            model_name=result.model_name,
            model_version=result.model_version,
        )

    @api.get("/health")
    def health() -> dict[str, str | bool]:
        return {"status": "ok", "drg_model_ready": drg_predictor.ready}

    @api.post("/v1/predictions/drg", response_model=GRDPredictionResponse)
    def predict_grd(payload: GRDPredictionPayload) -> GRDPredictionResponse:
        return predict(
            GRDPredictionRequest(
                icd10_codes=tuple(payload.icd10_codes),
                icd9_codes=tuple(payload.icd9_codes),
                age=payload.age,
                sex=payload.sex,
            )
        )

    @api.post("/v1/predictions/drg/fhir", response_model=GRDPredictionResponse)
    def predict_grd_from_fhir(bundle: dict[str, Any]) -> GRDPredictionResponse:
        try:
            request = prediction_request_from_bundle(bundle)
        except FHIRAdapterError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return predict(request)

    return api


app = create_app()
