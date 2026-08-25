from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import polars as pl

from clinical_data.contracts import (
    AdmissionContext,
    ClinicalCode,
    DRGTarget,
    HospitalEncounter,
    PatientContext,
)


class MimicEncounterSource:
    """Adapt MIMIC-IV hosp tables into source-independent hospital encounters."""

    def __init__(self, root: Path, drg_system: str = "MS") -> None:
        self.root = Path(root)
        self.drg_system = drg_system.upper()

    def iter_encounters(self) -> Iterator[HospitalEncounter]:
        admissions = self._read("admissions")
        patients = self._read("patients")
        diagnoses = self._read("diagnoses_icd")
        procedures = self._read("procedures_icd")
        drgs = self._read("drgcodes")

        patients_by_id = {str(row["subject_id"]): row for row in patients.iter_rows(named=True)}
        diagnoses_by_hadm = self._codes_by_hadm(diagnoses, kind="diagnosis")
        procedures_by_hadm = self._codes_by_hadm(procedures, kind="procedure")
        targets_by_hadm = self._targets_by_hadm(drgs)

        for admission in admissions.iter_rows(named=True):
            hadm_id = str(admission["hadm_id"])
            subject_id = str(admission["subject_id"])
            patient_row = patients_by_id[subject_id]
            admitted_at = self._parse_datetime(admission.get("admittime"))
            discharged_at = self._parse_datetime(admission.get("dischtime"))
            age = self._age_at_admission(patient_row, admitted_at)

            yield HospitalEncounter(
                encounter_id=hadm_id,
                patient=PatientContext(
                    patient_id=subject_id,
                    age=age,
                    sex=self._optional_text(patient_row.get("gender")),
                ),
                admission=AdmissionContext(
                    admitted_at=admitted_at,
                    discharged_at=discharged_at,
                    discharge_disposition=self._optional_text(
                        admission.get("discharge_location")
                    ),
                ),
                diagnoses=tuple(diagnoses_by_hadm.get(hadm_id, ())),
                procedures=tuple(procedures_by_hadm.get(hadm_id, ())),
                target=targets_by_hadm.get(hadm_id),
            )

    def _table_path(self, name: str) -> Path:
        for suffix in (".csv.gz", ".csv"):
            candidate = self.root / "hosp" / f"{name}{suffix}"
            if candidate.is_file():
                return candidate
        raise FileNotFoundError(f"missing MIMIC table: hosp/{name}.csv[.gz]")

    def _read(self, name: str) -> pl.DataFrame:
        return pl.scan_csv(self._table_path(name), infer_schema_length=1000).collect()

    def _codes_by_hadm(
        self,
        frame: pl.DataFrame,
        *,
        kind: str,
    ) -> dict[str, list[ClinicalCode]]:
        grouped: dict[str, list[ClinicalCode]] = defaultdict(list)
        for row in frame.iter_rows(named=True):
            hadm_id = str(row["hadm_id"])
            version = str(row["icd_version"])
            if kind == "diagnosis":
                system = "ICD10CM" if version == "10" else "ICD9CM"
            else:
                system = "ICD10PCS" if version == "10" else "ICD9PCS"
            sequence = row.get("seq_num")
            grouped[hadm_id].append(
                ClinicalCode(
                    code=str(row["icd_code"]).strip(),
                    coding_system=system,
                    sequence=int(sequence) if sequence is not None else None,
                )
            )
        for codes in grouped.values():
            codes.sort(key=lambda item: item.sequence or 10**9)
        return grouped

    def _targets_by_hadm(self, frame: pl.DataFrame) -> dict[str, DRGTarget]:
        accepted_types = {self.drg_system}
        target_system = self.drg_system
        if self.drg_system in {"MS", "MS-DRG"}:
            accepted_types = {"MS", "HCFA"}
            target_system = "MS-DRG"
        elif self.drg_system in {"APR", "APR-DRG"}:
            accepted_types = {"APR"}
            target_system = "APR-DRG"

        grouped: dict[str, list[str]] = defaultdict(list)
        for row in frame.iter_rows(named=True):
            if str(row["drg_type"]).upper() not in accepted_types:
                continue
            grouped[str(row["hadm_id"])].append(str(row["drg_code"]))

        targets: dict[str, DRGTarget] = {}
        for hadm_id, codes in grouped.items():
            unique = tuple(dict.fromkeys(codes))
            if len(unique) > 1:
                raise ValueError(
                    f"ambiguous {target_system} target for encounter {hadm_id}: {unique}"
                )
            targets[hadm_id] = DRGTarget(code=unique[0], system=target_system)
        return targets

    @staticmethod
    def _parse_datetime(value: object) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        text = str(value).strip()
        if not text:
            return None
        return datetime.fromisoformat(text)

    @staticmethod
    def _optional_text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _age_at_admission(patient: dict, admitted_at: datetime | None) -> int | None:
        anchor_age = patient.get("anchor_age")
        if anchor_age is None:
            return None
        age = int(anchor_age)
        anchor_year = patient.get("anchor_year")
        if admitted_at is not None and anchor_year is not None:
            age += admitted_at.year - int(anchor_year)
        return age
