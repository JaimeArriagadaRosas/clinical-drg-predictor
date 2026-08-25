from datetime import datetime

from clinical_data.contracts import (
    AdmissionContext,
    ClinicalCode,
    DRGTarget,
    HospitalEncounter,
    PatientContext,
)
from clinical_data.eda import build_eda_report


def encounter(
    encounter_id: str,
    patient_id: str,
    drg: str,
    diagnosis: str,
    *,
    age: int,
) -> HospitalEncounter:
    return HospitalEncounter(
        encounter_id=encounter_id,
        patient=PatientContext(patient_id=patient_id, age=age, sex="F"),
        admission=AdmissionContext(admitted_at=datetime(2025, 1, 1)),
        diagnoses=(ClinicalCode(code=diagnosis, coding_system="ICD10CM", sequence=1),),
        target=DRGTarget(code=drg, system="MS-DRG"),
    )


def test_eda_report_counts_grd_and_diagnosis_frequency():
    report = build_eda_report(
        (
            encounter("e1", "p1", "291", "I10", age=65),
            encounter("e2", "p1", "291", "I10", age=66),
            encounter("e3", "p2", "292", "E119", age=50),
        )
    )

    assert report.encounter_count == 3
    assert report.unique_patients == 2
    assert report.drg_distribution["291"] == 2
    assert report.diagnosis_frequency["I10"] == 2
    assert "repeated_patients_require_grouped_split" in report.leakage_risks
