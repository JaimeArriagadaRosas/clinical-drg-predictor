from datetime import datetime

import pytest
from pydantic import ValidationError

from clinical_data.contracts import (
    AdmissionContext,
    ClinicalCode,
    DRGTarget,
    HospitalEncounter,
    PatientContext,
)


def test_hospital_encounter_accepts_valid_grd_case():
    encounter = HospitalEncounter(
        encounter_id="hadm-1",
        patient=PatientContext(patient_id="subject-1", age=65, sex="F"),
        admission=AdmissionContext(
            admitted_at=datetime(2025, 1, 1),
            discharged_at=datetime(2025, 1, 4),
            discharge_disposition="HOME",
        ),
        diagnoses=(ClinicalCode(code="I10", coding_system="ICD10", sequence=1),),
        procedures=(ClinicalCode(code="0W3P8ZZ", coding_system="ICD10PCS", sequence=1),),
        target=DRGTarget(code="291", system="MS-DRG"),
    )
    assert encounter.target is not None
    assert encounter.target.code == "291"


def test_hospital_encounter_rejects_negative_age():
    with pytest.raises(ValidationError):
        PatientContext(patient_id="subject-1", age=-1, sex="F")


def test_admission_rejects_discharge_before_admission():
    with pytest.raises(ValidationError):
        AdmissionContext(
            admitted_at=datetime(2025, 1, 4),
            discharged_at=datetime(2025, 1, 1),
        )
