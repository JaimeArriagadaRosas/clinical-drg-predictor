from __future__ import annotations

from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from clinical_data.contracts import (
    AdmissionContext,
    ClinicalCode,
    DRGTarget,
    HospitalEncounter,
    PatientContext,
)

SCHEMA_VERSION = "hospital-encounter/v1"


def _encounter_to_row(encounter: HospitalEncounter) -> dict:
    return {
        "encounter_id": encounter.encounter_id,
        "patient_id": encounter.patient.patient_id,
        "age": encounter.patient.age,
        "sex": encounter.patient.sex,
        "admitted_at": encounter.admission.admitted_at,
        "discharged_at": encounter.admission.discharged_at,
        "discharge_disposition": encounter.admission.discharge_disposition,
        "diagnoses": [code.model_dump() for code in encounter.diagnoses],
        "procedures": [code.model_dump() for code in encounter.procedures],
        "target_code": encounter.target.code if encounter.target else None,
        "target_system": encounter.target.system if encounter.target else None,
    }


def write_encounters_parquet(encounters: tuple[HospitalEncounter, ...] | list[HospitalEncounter], path: Path) -> None:
    rows = [_encounter_to_row(encounter) for encounter in encounters]
    table = pa.Table.from_pylist(rows)
    metadata = dict(table.schema.metadata or {})
    metadata[b"clinical_schema_version"] = SCHEMA_VERSION.encode("utf-8")
    table = table.replace_schema_metadata(metadata)
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


def read_encounters_parquet(path: Path) -> tuple[HospitalEncounter, ...]:
    table = pq.read_table(path)
    metadata = table.schema.metadata or {}
    version = metadata.get(b"clinical_schema_version", b"").decode("utf-8")
    if version != SCHEMA_VERSION:
        raise ValueError(f"unsupported encounter parquet schema version: {version!r}")

    encounters: list[HospitalEncounter] = []
    for row in table.to_pylist():
        target = None
        if row.get("target_code") is not None:
            target = DRGTarget(code=str(row["target_code"]), system=str(row["target_system"]))
        encounters.append(
            HospitalEncounter(
                encounter_id=str(row["encounter_id"]),
                patient=PatientContext(
                    patient_id=str(row["patient_id"]),
                    age=row.get("age"),
                    sex=row.get("sex"),
                ),
                admission=AdmissionContext(
                    admitted_at=row.get("admitted_at"),
                    discharged_at=row.get("discharged_at"),
                    discharge_disposition=row.get("discharge_disposition"),
                ),
                diagnoses=tuple(ClinicalCode(**code) for code in row.get("diagnoses") or ()),
                procedures=tuple(ClinicalCode(**code) for code in row.get("procedures") or ()),
                target=target,
            )
        )
    return tuple(encounters)


def open_analytics_database(parquet_path: Path) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect(database=":memory:")
    escaped = str(parquet_path).replace("'", "''")
    connection.execute(
        f"CREATE VIEW encounters AS SELECT * FROM read_parquet('{escaped}')"
    )
    return connection
