from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ClinicalCode(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str = Field(min_length=1)
    coding_system: str = Field(min_length=1)
    sequence: int | None = Field(default=None, ge=1)


class PatientContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    patient_id: str = Field(min_length=1)
    age: int | None = Field(default=None, ge=0, le=130)
    sex: str | None = None


class AdmissionContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    admitted_at: datetime | None = None
    discharged_at: datetime | None = None
    discharge_disposition: str | None = None

    @model_validator(mode="after")
    def validate_chronology(self) -> "AdmissionContext":
        if (
            self.admitted_at is not None
            and self.discharged_at is not None
            and self.discharged_at < self.admitted_at
        ):
            raise ValueError("discharged_at cannot be earlier than admitted_at")
        return self


class DRGTarget(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str = Field(min_length=1)
    system: str = Field(min_length=1)


class HospitalEncounter(BaseModel):
    model_config = ConfigDict(frozen=True)

    encounter_id: str = Field(min_length=1)
    patient: PatientContext
    admission: AdmissionContext
    diagnoses: tuple[ClinicalCode, ...]
    procedures: tuple[ClinicalCode, ...] = ()
    target: DRGTarget | None = None
