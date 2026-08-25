from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from clinical_data.contracts import HospitalEncounter


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    message: str
    encounter_id: str | None = None


@dataclass(frozen=True)
class ValidationReport:
    encounter_count: int
    labeled_count: int
    errors: tuple[ValidationIssue, ...]
    warnings: tuple[ValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_encounters(encounters: Iterable[HospitalEncounter]) -> ValidationReport:
    items = tuple(encounters)
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    encounter_ids = Counter(item.encounter_id for item in items)
    for encounter_id, count in sorted(encounter_ids.items()):
        if count > 1:
            errors.append(
                ValidationIssue(
                    severity="error",
                    code="duplicate_encounter_id",
                    message=f"encounter id appears {count} times",
                    encounter_id=encounter_id,
                )
            )

    for encounter in items:
        if not encounter.diagnoses:
            errors.append(
                ValidationIssue(
                    severity="error",
                    code="missing_diagnoses",
                    message="encounter has no diagnosis codes",
                    encounter_id=encounter.encounter_id,
                )
            )

        age = encounter.patient.age
        if age is not None and not 0 <= age <= 130:
            errors.append(
                ValidationIssue(
                    severity="error",
                    code="invalid_age",
                    message=f"patient age {age} is outside 0..130",
                    encounter_id=encounter.encounter_id,
                )
            )

        diagnosis_sequences = [
            code.sequence for code in encounter.diagnoses if code.sequence is not None
        ]
        duplicated_sequences = sorted(
            sequence
            for sequence, count in Counter(diagnosis_sequences).items()
            if count > 1
        )
        if duplicated_sequences:
            errors.append(
                ValidationIssue(
                    severity="error",
                    code="duplicate_diagnosis_sequence",
                    message=f"duplicate diagnosis sequence(s): {duplicated_sequences}",
                    encounter_id=encounter.encounter_id,
                )
            )

        if encounter.target is None:
            warnings.append(
                ValidationIssue(
                    severity="warning",
                    code="missing_drg_target",
                    message="encounter cannot be used as a labeled GRD training case",
                    encounter_id=encounter.encounter_id,
                )
            )

    return ValidationReport(
        encounter_count=len(items),
        labeled_count=sum(item.target is not None for item in items),
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
