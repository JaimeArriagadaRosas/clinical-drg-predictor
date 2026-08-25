from datetime import date

import pytest

from clinical_fhir import FHIRAdapterError, bundle_to_encounter, prediction_request_from_bundle


def sample_bundle() -> dict:
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-1",
                    "gender": "female",
                    "birthDate": "1980-08-26",
                }
            },
            {
                "resource": {
                    "resourceType": "Encounter",
                    "id": "encounter-1",
                    "period": {
                        "start": "2026-08-25T10:00:00+00:00",
                        "end": "2026-08-26T10:00:00+00:00",
                    },
                    "hospitalization": {"dischargeDisposition": {"text": "HOME"}},
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "code": {
                        "coding": [
                            {"system": "http://hl7.org/fhir/sid/icd-10", "code": "I10"},
                            {"system": "http://hl7.org/fhir/sid/icd-10", "code": "I10"},
                        ]
                    },
                }
            },
            {
                "resource": {
                    "resourceType": "Procedure",
                    "code": {
                        "coding": [
                            {"system": "http://hl7.org/fhir/sid/icd-9-cm", "code": "39.61"}
                        ]
                    },
                }
            },
        ],
    }


def test_fhir_bundle_maps_to_canonical_encounter() -> None:
    encounter = bundle_to_encounter(sample_bundle(), reference_date=date(2026, 8, 25))

    assert encounter.encounter_id == "encounter-1"
    assert encounter.patient.patient_id == "patient-1"
    assert encounter.patient.age == 45
    assert encounter.patient.sex == "F"
    assert encounter.diagnoses[0].code == "I10"
    assert encounter.diagnoses[0].coding_system == "ICD10CM"
    assert encounter.procedures[0].code == "39.61"
    assert encounter.procedures[0].coding_system == "ICD9PCS"
    assert encounter.target is None


def test_compatibility_prediction_request_uses_canonical_mapping() -> None:
    request = prediction_request_from_bundle(sample_bundle(), reference_date=date(2026, 8, 25))
    assert request.icd10_codes == ("I10",)
    assert request.icd9_codes == ("39.61",)
    assert request.age == 45
    assert request.sex == "F"


def test_fhir_adapter_rejects_non_bundle_payload() -> None:
    with pytest.raises(FHIRAdapterError, match="FHIR Bundle"):
        bundle_to_encounter({"resourceType": "Patient"})


def test_fhir_adapter_requires_one_patient_and_encounter() -> None:
    bundle = {"resourceType": "Bundle", "entry": []}
    with pytest.raises(FHIRAdapterError, match="exactly one Patient"):
        bundle_to_encounter(bundle)
