from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class DatasetVerification:
    ok: bool
    missing_files: tuple[str, ...]


def load_manifest(manifest_path: Path) -> dict:
    with manifest_path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError("dataset manifest must be a mapping")
    files = data.get("files")
    if not isinstance(files, list) or not all(isinstance(item, str) for item in files):
        raise ValueError("dataset manifest files must be a list of paths")
    return data


def verify_dataset(root: Path, manifest_path: Path) -> DatasetVerification:
    manifest = load_manifest(manifest_path)
    missing = tuple(path for path in manifest["files"] if not (root / path).is_file())
    return DatasetVerification(ok=not missing, missing_files=missing)
