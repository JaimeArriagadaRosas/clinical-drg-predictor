from pathlib import Path

from tools.datasets.verify import verify_dataset


def test_mimic_manifest_reports_missing_required_file(tmp_path: Path):
    manifest = Path("tools/datasets/manifests/mimic-iv-demo.yaml")
    result = verify_dataset(tmp_path, manifest)
    assert result.ok is False
    assert "hosp/admissions.csv.gz" in result.missing_files


def test_dataset_verification_passes_when_required_files_exist(tmp_path: Path):
    manifest = Path("tools/datasets/manifests/mimic-iv-demo.yaml")
    required = (
        "hosp/admissions.csv.gz",
        "hosp/patients.csv.gz",
        "hosp/diagnoses_icd.csv.gz",
        "hosp/procedures_icd.csv.gz",
        "hosp/drgcodes.csv.gz",
    )
    for relative in required:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture")

    result = verify_dataset(tmp_path, manifest)
    assert result.ok is True
    assert result.missing_files == ()
