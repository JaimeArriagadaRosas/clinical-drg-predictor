from datetime import datetime, timedelta

from clinical_data.contracts import (
    AdmissionContext,
    ClinicalCode,
    DRGTarget,
    HospitalEncounter,
    PatientContext,
)
from clinical_ml.features import build_grd_features
from clinical_ml.splitting import split_by_patient, split_temporally


def encounter(index: int, patient_id: str, day: int) -> HospitalEncounter:
    return HospitalEncounter(
        encounter_id=f"e{index}",
        patient=PatientContext(patient_id=patient_id, age=40 + index, sex="F"),
        admission=AdmissionContext(admitted_at=datetime(2025, 1, 1) + timedelta(days=day)),
        diagnoses=(ClinicalCode(code="I10", coding_system="ICD10CM", sequence=1),),
        target=DRGTarget(code="291" if index % 2 == 0 else "292", system="MS-DRG"),
    )


def test_grouped_split_keeps_patient_in_single_partition():
    encounters = (
        encounter(0, "p1", 0),
        encounter(1, "p1", 1),
        encounter(2, "p2", 2),
        encounter(3, "p3", 3),
        encounter(4, "p4", 4),
        encounter(5, "p5", 5),
        encounter(6, "p6", 6),
    )
    dataset = build_grd_features(encounters)
    split = split_by_patient(dataset, random_state=7)

    partitions = {
        "train": split.train_idx,
        "validation": split.validation_idx,
        "test": split.test_idx,
    }
    patient_locations: dict[str, set[str]] = {}
    for name, indices in partitions.items():
        for index in indices:
            patient_locations.setdefault(dataset.patient_ids[index], set()).add(name)
    assert all(len(locations) == 1 for locations in patient_locations.values())


def test_temporal_split_orders_train_before_validation_and_test():
    encounters = tuple(encounter(index, f"p{index}", index) for index in range(10))
    split = split_temporally(encounters)

    train_dates = [encounters[index].admission.admitted_at for index in split.train_idx]
    validation_dates = [encounters[index].admission.admitted_at for index in split.validation_idx]
    test_dates = [encounters[index].admission.admitted_at for index in split.test_idx]

    assert max(train_dates) < min(validation_dates)
    assert max(validation_dates) < min(test_dates)
