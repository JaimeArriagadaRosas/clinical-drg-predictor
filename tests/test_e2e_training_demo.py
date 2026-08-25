from datetime import datetime, timedelta

from clinical_core import GRDPredictionRequest
from clinical_data.contracts import (
    AdmissionContext,
    ClinicalCode,
    DRGTarget,
    HospitalEncounter,
    PatientContext,
)
from clinical_drg import load_published_predictor
from clinical_ml.artifacts import publish_model
from clinical_ml.features import build_grd_features
from clinical_ml.splitting import split_by_patient
from clinical_ml.training import select_best_model, train_candidates


def _encounters() -> list[HospitalEncounter]:
    rows: list[HospitalEncounter] = []
    for index in range(12):
        label = "291" if index % 2 == 0 else "470"
        rows.append(
            HospitalEncounter(
                encounter_id=f"enc-{index}",
                patient=PatientContext(
                    patient_id=f"patient-{index}",
                    age=45 + index,
                    sex="F" if index % 2 == 0 else "M",
                ),
                admission=AdmissionContext(
                    admitted_at=datetime(2025, 1, 1) + timedelta(days=index),
                    discharged_at=datetime(2025, 1, 2) + timedelta(days=index),
                    discharge_disposition="HOME",
                ),
                diagnoses=(
                    ClinicalCode(
                        code="I10" if label == "291" else "J18.9",
                        coding_system="ICD10",
                        sequence=1,
                    ),
                ),
                procedures=(),
                target=DRGTarget(code=label, system="MS-DRG"),
            )
        )
    return rows


def test_end_to_end_training_publish_load_predict(tmp_path):
    encounters = _encounters()
    dataset = build_grd_features(encounters)
    split = split_by_patient(dataset, validation_fraction=0.2, test_fraction=0.2)

    train_patients = {dataset.patient_ids[index] for index in split.train_idx}
    validation_patients = {dataset.patient_ids[index] for index in split.validation_idx}
    test_patients = {dataset.patient_ids[index] for index in split.test_idx}
    assert train_patients.isdisjoint(validation_patients | test_patients)

    candidates = train_candidates(
        dataset.X[list(split.train_idx)],
        dataset.y[list(split.train_idx)],
        dataset.X[list(split.validation_idx)],
        dataset.y[list(split.validation_idx)],
    )
    selected = select_best_model(candidates)
    published = publish_model(
        selected,
        dataset.schema,
        {"source": "synthetic-mimic", "version": "test-v1"},
        tmp_path / "models",
        label_mapping=dataset.label_mapping,
        model_version="e2e-test-model",
    )

    predictor = load_published_predictor(published.path)
    assert predictor.ready is True

    result = predictor.predict(
        GRDPredictionRequest(icd10_codes=("I10",), age=52, sex="F")
    )
    assert result.label in dataset.label_mapping
    assert 0.0 <= result.confidence <= 1.0
    assert result.model_version == "e2e-test-model"
