from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from clinical_data.contracts import HospitalEncounter


@dataclass(frozen=True)
class FeatureSchema:
    version: str
    names: tuple[str, ...]

    def to_json(self, path: Path) -> None:
        path.write_text(
            json.dumps({"version": self.version, "names": list(self.names)}, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def from_json(cls, path: Path) -> "FeatureSchema":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(version=str(data["version"]), names=tuple(data["names"]))


@dataclass(frozen=True)
class FeatureDataset:
    X: np.ndarray
    y: np.ndarray
    patient_ids: tuple[str, ...]
    encounter_ids: tuple[str, ...]
    schema: FeatureSchema
    label_mapping: dict[str, int]


def _age_bucket(age: int | None) -> tuple[float, float, float, float]:
    if age is None:
        return (0.0, 0.0, 0.0, 0.0)
    if age < 18:
        return (1.0, 0.0, 0.0, 0.0)
    if age < 45:
        return (0.0, 1.0, 0.0, 0.0)
    if age < 65:
        return (0.0, 0.0, 1.0, 0.0)
    return (0.0, 0.0, 0.0, 1.0)


def build_grd_features(encounters: tuple[HospitalEncounter, ...] | list[HospitalEncounter]) -> FeatureDataset:
    items = tuple(encounters)
    if not items:
        raise ValueError("at least one encounter is required")
    if any(item.target is None for item in items):
        raise ValueError("GRD feature training requires labeled encounters")

    diagnosis_vocab = tuple(sorted({code.code for item in items for code in item.diagnoses}))
    procedure_vocab = tuple(sorted({code.code for item in items for code in item.procedures}))
    names = (
        "age_lt18",
        "age_18_44",
        "age_45_64",
        "age_65_plus",
        "sex_f",
        "sex_m",
        "sex_unknown",
        *(f"dx:{code}" for code in diagnosis_vocab),
        *(f"px:{code}" for code in procedure_vocab),
    )
    schema = FeatureSchema(version="grd-features/v1", names=tuple(names))

    labels = tuple(sorted({item.target.code for item in items if item.target is not None}))
    label_mapping = {label: index for index, label in enumerate(labels)}
    rows: list[list[float]] = []
    targets: list[int] = []

    for item in items:
        sex = (item.patient.sex or "").upper()
        row = [*_age_bucket(item.patient.age), float(sex == "F"), float(sex == "M"), float(sex not in {"F", "M"})]
        diagnosis_codes = {code.code for code in item.diagnoses}
        procedure_codes = {code.code for code in item.procedures}
        row.extend(float(code in diagnosis_codes) for code in diagnosis_vocab)
        row.extend(float(code in procedure_codes) for code in procedure_vocab)
        rows.append(row)
        assert item.target is not None
        targets.append(label_mapping[item.target.code])

    return FeatureDataset(
        X=np.asarray(rows, dtype=float),
        y=np.asarray(targets, dtype=int),
        patient_ids=tuple(item.patient.patient_id for item in items),
        encounter_ids=tuple(item.encounter_id for item in items),
        schema=schema,
        label_mapping=label_mapping,
    )
