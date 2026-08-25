from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, datetime
from typing import Any

from clinical_core import GRDPredictionRequest
from clinical_data import AdmissionContext, ClinicalCode, HospitalEncounter, PatientContext

ICD10_SYSTEMS = {
    "http://hl7.org/fhir/sid/icd-10",
    "http://hl7.org/fhir/sid/icd-10-cm",
    "http://hl7.org/fhir/sid/icd-10-ca",
}
ICD9_SYSTEMS = {"http://hl7.org/fhir/sid/icd-9-cm"}


class FHIRAdapterError(ValueError):
    """Raised when a FHIR payload cannot be mapped safely to the clinical contract."""


def bundle_to_encounter(
    bundle: Mapping[str, Any], *, reference_date: date | None = None
) -> HospitalEncounter:
    if bundle.get("resourceType") != "Bundle":
        raise FHIRAdapterError("Expected a FHIR Bundle resource.")

    resources = tuple(_iter_resources(bundle))
    patients = [resource for resource in resources if resource.get("resourceType") == "Patient"]
    encounters = [resource for resource in resources if resource.get("resourceType") == "Encounter"]
    if len(patients) != 1:
        raise FHIRAdapterError("Prediction bundles must contain exactly one Patient resource.")
    if len(encounters) != 1:
        raise FHIRAdapterError("Prediction bundles must contain exactly one Encounter resource.")

    patient_resource = patients[0]
    encounter_resource = encounters[0]
    patient_id = patient_resource.get("id")
    encounter_id = encounter_resource.get("id")
    if not isinstance(patient_id, str) or not patient_id.strip():
        raise FHIRAdapterError("Patient.id is required for canonical encounter mapping.")
    if not isinstance(encounter_id, str) or not encounter_id.strip():
        raise FHIRAdapterError("Encounter.id is required for canonical encounter mapping.")

    effective_date = reference_date or _encounter_reference_date(encounter_resource) or date.today()
    diagnoses: list[ClinicalCode] = []
    procedures: list[ClinicalCode] = []

    for resource in resources:
        resource_type = resource.get("resourceType")
        if resource_type not in {"Condition", "Procedure"}:
            continue
        for system, code in _codings(resource.get("code")):
            normalized = _clinical_code(resource_type, system, code, len(diagnoses), len(procedures))
            if normalized is None:
                continue
            if resource_type == "Condition":
                diagnoses.append(normalized)
            else:
                procedures.append(normalized)

    return HospitalEncounter(
        encounter_id=encounter_id.strip(),
        patient=PatientContext(
            patient_id=patient_id.strip(),
            age=_patient_age(patient_resource, effective_date),
            sex=_patient_sex(patient_resource),
        ),
        admission=AdmissionContext(
            admitted_at=_parse_fhir_datetime(_period_value(encounter_resource, "start")),
            discharged_at=_parse_fhir_datetime(_period_value(encounter_resource, "end")),
            discharge_disposition=_discharge_disposition(encounter_resource),
        ),
        diagnoses=tuple(diagnoses),
        procedures=tuple(procedures),
        target=None,
    )


def prediction_request_from_bundle(
    bundle: Mapping[str, Any], *, reference_date: date | None = None
) -> GRDPredictionRequest:
    encounter = bundle_to_encounter(bundle, reference_date=reference_date)
    icd10_codes = tuple(
        code.code for code in encounter.diagnoses if code.coding_system.startswith("ICD10")
    )
    icd9_codes = tuple(
        code.code
        for code in (*encounter.diagnoses, *encounter.procedures)
        if code.coding_system.startswith("ICD9")
    )
    return GRDPredictionRequest(
        icd10_codes=icd10_codes,
        icd9_codes=icd9_codes,
        age=encounter.patient.age,
        sex=encounter.patient.sex,
    )


def _clinical_code(
    resource_type: str,
    system: str,
    code: str,
    diagnosis_count: int,
    procedure_count: int,
) -> ClinicalCode | None:
    if system in ICD10_SYSTEMS:
        coding_system = "ICD10CM" if resource_type == "Condition" else "ICD10PCS"
    elif system in ICD9_SYSTEMS:
        coding_system = "ICD9CM" if resource_type == "Condition" else "ICD9PCS"
    else:
        return None
    sequence = diagnosis_count + 1 if resource_type == "Condition" else procedure_count + 1
    return ClinicalCode(code=code, coding_system=coding_system, sequence=sequence)


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
    seen: set[tuple[str, str]] = set()
    for coding in codings:
        if not isinstance(coding, Mapping):
            continue
        system = coding.get("system")
        code = coding.get("code")
        pair = (system, code)
        if isinstance(system, str) and isinstance(code, str) and code.strip() and pair not in seen:
            seen.add(pair)
            yield system, code.strip()


def _patient_sex(patient: Mapping[str, Any]) -> str | None:
    return {"male": "M", "female": "F"}.get(patient.get("gender"))


def _patient_age(patient: Mapping[str, Any], reference_date: date) -> int | None:
    raw_birth_date = patient.get("birthDate")
    if not isinstance(raw_birth_date, str) or len(raw_birth_date) != 10:
        return None
    try:
        birth_date = date.fromisoformat(raw_birth_date)
    except ValueError as exc:
        raise FHIRAdapterError("Patient.birthDate must be a valid FHIR date.") from exc
    if birth_date > reference_date:
        raise FHIRAdapterError("Patient.birthDate cannot be after the encounter reference date.")
    return reference_date.year - birth_date.year - (
        (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day)
    )


def _period_value(encounter: Mapping[str, Any], key: str) -> Any:
    period = encounter.get("period")
    return period.get(key) if isinstance(period, Mapping) else None


def _parse_fhir_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FHIRAdapterError(f"Encounter period contains invalid dateTime: {value}") from exc


def _encounter_reference_date(encounter: Mapping[str, Any]) -> date | None:
    start = _parse_fhir_datetime(_period_value(encounter, "start"))
    return start.date() if start else None


def _discharge_disposition(encounter: Mapping[str, Any]) -> str | None:
    hospitalization = encounter.get("hospitalization")
    if not isinstance(hospitalization, Mapping):
        return None
    disposition = hospitalization.get("dischargeDisposition")
    if not isinstance(disposition, Mapping):
        return None
    text = disposition.get("text")
    return text.strip() if isinstance(text, str) and text.strip() else None
