from datetime import datetime

from clinical_data.contracts import (
    AdmissionContext,
    ClinicalCode,
    DRGTarget,
    HospitalEncounter,
    PatientContext,
)
from clinical_data.validation import validate_encounters

_DEFAULT_DIAGNOSES = (
    ClinicalCode(code="I10", coding_system="ICD10CM", sequence=1),
)
_DEFAULT_TARGET = DRGTarget(code="291", system="MS-DRG")


def make_encounter(
    encounter_id: str,
    *,
    patient_id: str = "p1",
    diagnoses: tuple[ClinicalCode, ...] = _DEFAULT_DIAGNOSES,
    target: DRGTarget | None = _DEFAULT_TARGET,
) -> HospitalEncounter:
    return HospitalEncounter(
        encounter_id=encounter_id,
        patient=PatientContext(patient_id=patient_id, age=65, sex="F"),
        admission=AdmissionContext(admitted_at=datetime(2025, 1, 1)),
        diagnoses=diagnoses,
        target=target,
    )


def test_validation_detects_duplicate_encounters_and_missing_target():
    report = validate_encounters(
        (
            make_encounter("a", target=None),
            make_encounter("a", patient_id="p2"),
        )
    )
    assert report.encounter_count == 2
    assert report.labeled_count == 1
    assert any(issue.code == "duplicate_encounter_id" for issue in report.errors)
    assert any(issue.code == "missing_drg_target" for issue in report.warnings)


def test_validation_detects_missing_diagnoses_and_duplicate_sequences():
    duplicate_sequences = (
        ClinicalCode(code="I10", coding_system="ICD10CM", sequence=1),
        ClinicalCode(code="E119", coding_system="ICD10CM", sequence=1),
    )
    report = validate_encounters(
        (
            make_encounter("a", diagnoses=()),
            make_encounter("b", diagnoses=duplicate_sequences),
        )
    )
    codes = {issue.code for issue in report.errors}
    assert "missing_diagnoses" in codes
    assert "duplicate_diagnosis_sequence" in codes
