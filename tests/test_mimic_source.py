from pathlib import Path

import pytest

from clinical_data.sources.mimic import MimicEncounterSource


FIXTURE_ROOT = Path("tests/fixtures/mimic")


def test_mimic_source_joins_hospital_tables_into_encounter():
    source = MimicEncounterSource(FIXTURE_ROOT)
    encounters = list(source.iter_encounters())

    assert len(encounters) == 1
    encounter = encounters[0]
    assert encounter.encounter_id == "100001"
    assert encounter.patient.patient_id == "200001"
    assert encounter.patient.age == 65
    assert [code.code for code in encounter.diagnoses] == ["I10", "E119"]
    assert encounter.diagnoses[0].sequence == 1
    assert encounter.procedures[0].coding_system == "ICD10PCS"
    assert encounter.target is not None
    assert encounter.target.code == "291"
    assert encounter.target.system == "MS-DRG"


def test_mimic_source_rejects_ambiguous_drg_targets(tmp_path: Path):
    hosp = tmp_path / "hosp"
    hosp.mkdir()
    for name in ("admissions", "patients", "diagnoses_icd", "procedures_icd"):
        (hosp / f"{name}.csv").write_text(
            (FIXTURE_ROOT / "hosp" / f"{name}.csv").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    (hosp / "drgcodes.csv").write_text(
        "subject_id,hadm_id,drg_type,drg_code,description,drg_severity,drg_mortality\n"
        "200001,100001,HCFA,291,Example A,,\n"
        "200001,100001,HCFA,292,Example B,,\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="ambiguous MS-DRG target"):
        list(MimicEncounterSource(tmp_path).iter_encounters())
