from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from statistics import mean

from clinical_data.contracts import HospitalEncounter


@dataclass(frozen=True)
class EDAReport:
    encounter_count: int
    unique_patients: int
    repeated_patient_count: int
    labeled_count: int
    unlabeled_count: int
    drg_distribution: dict[str, int]
    diagnosis_frequency: dict[str, int]
    procedure_frequency: dict[str, int]
    sex_distribution: dict[str, int]
    age_min: int | None
    age_max: int | None
    age_mean: float | None
    mean_diagnoses_per_encounter: float
    mean_procedures_per_encounter: float
    minimum_class_support: int | None
    leakage_risks: tuple[str, ...]


def build_eda_report(encounters: Iterable[HospitalEncounter]) -> EDAReport:
    items = tuple(encounters)
    patient_counts = Counter(item.patient.patient_id for item in items)
    drgs = Counter(item.target.code for item in items if item.target is not None)
    diagnoses = Counter(code.code for item in items for code in item.diagnoses)
    procedures = Counter(code.code for item in items for code in item.procedures)
    sexes = Counter(item.patient.sex or "UNKNOWN" for item in items)
    ages = [item.patient.age for item in items if item.patient.age is not None]

    risks: list[str] = []
    if any(count > 1 for count in patient_counts.values()):
        risks.append("repeated_patients_require_grouped_split")
    if any(item.target is None for item in items):
        risks.append("unlabeled_encounters_present")
    if drgs and min(drgs.values()) < 2:
        risks.append("rare_drg_classes_present")

    return EDAReport(
        encounter_count=len(items),
        unique_patients=len(patient_counts),
        repeated_patient_count=sum(count > 1 for count in patient_counts.values()),
        labeled_count=sum(item.target is not None for item in items),
        unlabeled_count=sum(item.target is None for item in items),
        drg_distribution=dict(sorted(drgs.items())),
        diagnosis_frequency=dict(sorted(diagnoses.items())),
        procedure_frequency=dict(sorted(procedures.items())),
        sex_distribution=dict(sorted(sexes.items())),
        age_min=min(ages) if ages else None,
        age_max=max(ages) if ages else None,
        age_mean=mean(ages) if ages else None,
        mean_diagnoses_per_encounter=(
            mean(len(item.diagnoses) for item in items) if items else 0.0
        ),
        mean_procedures_per_encounter=(
            mean(len(item.procedures) for item in items) if items else 0.0
        ),
        minimum_class_support=min(drgs.values()) if drgs else None,
        leakage_risks=tuple(risks),
    )
