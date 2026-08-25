from datetime import date

import pytest

from clinical_fhir import FHIRAdapterError, prediction_request_from_bundle


def test_fhir_bundle_maps_patient_conditions_and_procedures() -> None:
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "gender": "female",
                    "birthDate": "1980-08-26",
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

    request = prediction_request_from_bundle(bundle, reference_date=date(2026, 8, 25))

    assert request.icd10_codes == ("I10",)
    assert request.icd9_codes == ("39.61",)
    assert request.age == 45
    assert request.sex == "F"


def test_fhir_adapter_rejects_non_bundle_payload() -> None:
    with pytest.raises(FHIRAdapterError, match="FHIR Bundle"):
        prediction_request_from_bundle({"resourceType": "Patient"})


def test_fhir_adapter_rejects_multiple_patients() -> None:
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {"resource": {"resourceType": "Patient"}},
            {"resource": {"resourceType": "Patient"}},
        ],
    }

    with pytest.raises(FHIRAdapterError, match="at most one Patient"):
        prediction_request_from_bundle(bundle)
