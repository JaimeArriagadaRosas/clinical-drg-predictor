import json
from pathlib import Path

from tools.datasets.fetch import acquire_public_dataset, import_authorized_dataset


MANIFEST = Path("tools/datasets/manifests/mimic-iv-demo.yaml")
REQUIRED = (
    "hosp/admissions.csv.gz",
    "hosp/patients.csv.gz",
    "hosp/diagnoses_icd.csv.gz",
    "hosp/procedures_icd.csv.gz",
    "hosp/drgcodes.csv.gz",
)


def test_public_demo_download_uses_manifest_files(tmp_path: Path):
    seen: list[str] = []

    def fake_downloader(url: str, destination: Path) -> None:
        seen.append(url)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"fixture")

    destination = tmp_path / "mimic"
    receipt = acquire_public_dataset(MANIFEST, destination, downloader=fake_downloader)

    assert len(seen) == len(REQUIRED)
    assert all((destination / relative).is_file() for relative in REQUIRED)
    provenance = json.loads(receipt.read_text(encoding="utf-8"))
    assert provenance["dataset"] == "mimic-iv-demo"
    assert provenance["mode"] == "download"


def test_authorized_import_verifies_and_copies_manifest_files(tmp_path: Path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    for relative in REQUIRED:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(relative.encode())

    receipt = import_authorized_dataset(source, destination, MANIFEST)

    assert all((destination / relative).is_file() for relative in REQUIRED)
    assert json.loads(receipt.read_text(encoding="utf-8"))["mode"] == "authorized-import"
