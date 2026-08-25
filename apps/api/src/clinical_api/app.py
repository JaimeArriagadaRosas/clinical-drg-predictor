from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from clinical_core import GRDPredictionRequest
from clinical_drg import GRDPredictor, PredictorUnavailableError, load_legacy_predictor


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
        version="0.1.0",
        description="Modular API for clinical ML inference and analytics.",
    )

    @api.get("/health")
    def health() -> dict[str, str | bool]:
        return {"status": "ok", "drg_model_ready": drg_predictor.ready}

    @api.post("/v1/predictions/drg", response_model=GRDPredictionResponse)
    def predict_grd(payload: GRDPredictionPayload) -> GRDPredictionResponse:
        try:
            result = drg_predictor.predict(
                GRDPredictionRequest(
                    icd10_codes=tuple(payload.icd10_codes),
                    icd9_codes=tuple(payload.icd9_codes),
                    age=payload.age,
                    sex=payload.sex,
                )
            )
        except PredictorUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        return GRDPredictionResponse(
            label=result.label,
            confidence=result.confidence,
            model_name=result.model_name,
            model_version=result.model_version,
        )

    return api


app = create_app()
