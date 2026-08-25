from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date
from typing import Any

from clinical_core import GRDPredictionRequest

ICD10_SYSTEMS = {
    "http://hl7.org/fhir/sid/icd-10",
    "http://hl7.org/fhir/sid/icd-10-cm",
    "http://hl7.org/fhir/sid/icd-10-ca",
}
ICD9_SYSTEMS = {"http://hl7.org/fhir/sid/icd-9-cm"}


class FHIRAdapterError(ValueError):
    """Raised when a FHIR payload cannot be mapped safely to the prediction contract."""


def prediction_request_from_bundle(
    bundle: Mapping[str, Any], *, reference_date: date | None = None
) -> GRDPredictionRequest:
    """Map a single-patient FHIR Bundle subset to the GRD prediction contract.

    This adapter intentionally supports only the resources needed by the current model:
    Patient, Condition and Procedure. It is not a general FHIR validator.
    """
    if bundle.get("resourceType") != "Bundle":
        raise FHIRAdapterError("Expected a FHIR Bundle resource.")

    resources = tuple(_iter_resources(bundle))
    patients = [resource for resource in resources if resource.get("resourceType") == "Patient"]
    if len(patients) > 1:
        raise FHIRAdapterError("Prediction bundles must contain at most one Patient resource.")

    patient = patients[0] if patients else None
    age = _patient_age(patient, reference_date or date.today()) if patient else None
    sex = _patient_sex(patient) if patient else None

    icd10_codes: list[str] = []
    icd9_codes: list[str] = []
    for resource in resources:
        resource_type = resource.get("resourceType")
        if resource_type not in {"Condition", "Procedure"}:
            continue
        for system, code in _codings(resource.get("code")):
            if system in ICD10_SYSTEMS and resource_type == "Condition":
                _append_unique(icd10_codes, code)
            elif system in ICD9_SYSTEMS:
                _append_unique(icd9_codes, code)

    return GRDPredictionRequest(
        icd10_codes=tuple(icd10_codes),
        icd9_codes=tuple(icd9_codes),
        age=age,
        sex=sex,
    )


def _iter_resources(bundle: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    entries = bundle.get("entry", [])
    if not isinstance(entries, list):
        raise FHIRAdapterError("FHIR Bundle.entry must be an array when present.")
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        resource = entry.get("resource")
        if isinstance(resource, Mapping):
            yield resource


def _codings(codeable_concept: Any) -> Iterable[tuple[str, str]]:
    if not isinstance(codeable_concept, Mapping):
        return
    codings = codeable_concept.get("coding", [])
    if not isinstance(codings, list):
        return
    for coding in codings:
        if not isinstance(coding, Mapping):
            continue
        system = coding.get("system")
        code = coding.get("code")
        if isinstance(system, str) and isinstance(code, str) and code.strip():
            yield system, code.strip()


def _patient_sex(patient: Mapping[str, Any]) -> str | None:
    gender = patient.get("gender")
    if gender == "male":
        return "M"
    if gender == "female":
        return "F"
    return None


def _patient_age(patient: Mapping[str, Any], reference_date: date) -> int | None:
    raw_birth_date = patient.get("birthDate")
    if not isinstance(raw_birth_date, str) or len(raw_birth_date) != 10:
        return None
    try:
        birth_date = date.fromisoformat(raw_birth_date)
    except ValueError as exc:
        raise FHIRAdapterError("Patient.birthDate must be a valid FHIR date.") from exc
    if birth_date > reference_date:
        raise FHIRAdapterError("Patient.birthDate cannot be after the prediction reference date.")
    return reference_date.year - birth_date.year - (
        (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day)
    )


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)
