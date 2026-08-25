from datetime import datetime

import numpy as np

from clinical_data.contracts import (
    AdmissionContext,
    ClinicalCode,
    DRGTarget,
    HospitalEncounter,
    PatientContext,
)
from clinical_ml.features import FeatureSchema, build_grd_features


def make_encounter(
    encounter_id: str,
    patient_id: str,
    drg: str,
    diagnoses: tuple[str, ...],
    procedures: tuple[str, ...] = (),
) -> HospitalEncounter:
    return HospitalEncounter(
        encounter_id=encounter_id,
        patient=PatientContext(patient_id=patient_id, age=65, sex="F"),
        admission=AdmissionContext(admitted_at=datetime(2025, 1, 1)),
        diagnoses=tuple(
            ClinicalCode(code=code, coding_system="ICD10CM", sequence=index + 1)
            for index, code in enumerate(diagnoses)
        ),
        procedures=tuple(
            ClinicalCode(code=code, coding_system="ICD10PCS", sequence=index + 1)
            for index, code in enumerate(procedures)
        ),
        target=DRGTarget(code=drg, system="MS-DRG"),
    )


def test_feature_pipeline_is_deterministic_and_versioned(tmp_path):
    encounters = (
        make_encounter("e1", "p1", "291", ("I10", "E119"), ("0W3P8ZZ",)),
        make_encounter("e2", "p2", "292", ("I10",)),
    )
    first = build_grd_features(encounters)
    second = build_grd_features(tuple(reversed(tuple(reversed(encounters)))))

    assert first.schema.names == second.schema.names
    np.testing.assert_array_equal(first.X, second.X)
    assert first.schema.version == "grd-features/v1"

    path = tmp_path / "schema.json"
    first.schema.to_json(path)
    assert FeatureSchema.from_json(path) == first.schema


def test_feature_pipeline_rejects_unlabeled_training_case():
    labeled = make_encounter("e1", "p1", "291", ("I10",))
    unlabeled = labeled.model_copy(update={"encounter_id": "e2", "target": None})

    try:
        build_grd_features((labeled, unlabeled))
    except ValueError as exc:
        assert "labeled" in str(exc)
    else:
        raise AssertionError("expected unlabeled encounter to be rejected")
