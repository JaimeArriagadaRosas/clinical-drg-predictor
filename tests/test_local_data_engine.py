from datetime import datetime

from clinical_data.contracts import (
    AdmissionContext,
    ClinicalCode,
    DRGTarget,
    HospitalEncounter,
    PatientContext,
)
from clinical_data.storage import (
    open_analytics_database,
    read_encounters_parquet,
    write_encounters_parquet,
)


def sample_encounter() -> HospitalEncounter:
    return HospitalEncounter(
        encounter_id="h1",
        patient=PatientContext(patient_id="p1", age=70, sex="M"),
        admission=AdmissionContext(
            admitted_at=datetime(2025, 1, 1),
            discharged_at=datetime(2025, 1, 2),
            discharge_disposition="HOME",
        ),
        diagnoses=(ClinicalCode(code="I10", coding_system="ICD10CM", sequence=1),),
        procedures=(ClinicalCode(code="0W3P8ZZ", coding_system="ICD10PCS", sequence=1),),
        target=DRGTarget(code="291", system="MS-DRG"),
    )


def test_encounters_round_trip_through_parquet(tmp_path):
    path = tmp_path / "encounters.parquet"
    encounters = (sample_encounter(),)
    write_encounters_parquet(encounters, path)
    restored = read_encounters_parquet(path)
    assert restored == encounters


def test_duckdb_can_aggregate_drg_counts_from_parquet(tmp_path):
    path = tmp_path / "encounters.parquet"
    write_encounters_parquet((sample_encounter(), sample_encounter().model_copy(update={"encounter_id": "h2"})), path)
    connection = open_analytics_database(path)
    try:
        rows = connection.execute(
            "SELECT target_code, COUNT(*) FROM encounters GROUP BY target_code"
        ).fetchall()
    finally:
        connection.close()
    assert rows == [("291", 2)]
