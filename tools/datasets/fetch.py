from __future__ import annotations

import argparse
import json
import shutil
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from tools.datasets.verify import load_manifest, verify_dataset

Downloader = Callable[[str, Path], None]
SUPPORTED_DATASETS = ("mimic-iv-demo", "mimic-iv")


def _http_download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


def acquire_public_dataset(
    manifest_path: Path,
    destination: Path,
    *,
    downloader: Downloader = _http_download,
) -> Path:
    manifest = load_manifest(manifest_path)
    if manifest.get("access") != "public-demo":
        raise ValueError("automatic download is allowed only for public-demo datasets")
    download_base = str(manifest.get("download_base") or "").rstrip("/")
    if not download_base:
        raise ValueError("public dataset manifest requires download_base")

    for relative in manifest["files"]:
        target = destination / relative
        downloader(f"{download_base}/{relative}", target)

    verification = verify_dataset(destination, manifest_path)
    if not verification.ok:
        raise RuntimeError(f"download incomplete: {verification.missing_files}")
    return _write_receipt(destination, manifest, mode="download")


def import_authorized_dataset(
    source: Path,
    destination: Path,
    manifest_path: Path,
) -> Path:
    verification = verify_dataset(source, manifest_path)
    if not verification.ok:
        raise ValueError(f"source dataset is incomplete: {verification.missing_files}")
    manifest = load_manifest(manifest_path)
    for relative in manifest["files"]:
        source_file = source / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target)
    return _write_receipt(destination, manifest, mode="authorized-import")


def _write_receipt(destination: Path, manifest: dict, *, mode: str) -> Path:
    receipt = destination / ".provenance.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(
        json.dumps(
            {
                "dataset": manifest["name"],
                "version": str(manifest["version"]),
                "source": manifest["source"],
                "access": manifest["access"],
                "mode": mode,
                "acquired_at": datetime.now(UTC).isoformat(),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Acquire or import clinical datasets")
    parser.add_argument("dataset", choices=SUPPORTED_DATASETS)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--from-directory", type=Path)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    manifest = Path(__file__).parent / "manifests" / f"{args.dataset}.yaml"
    if args.from_directory:
        import_authorized_dataset(args.from_directory, args.destination, manifest)
    elif args.dataset == "mimic-iv-demo":
        acquire_public_dataset(manifest, args.destination)
    else:
        raise SystemExit("full MIMIC-IV must be supplied with --from-directory")


if __name__ == "__main__":
    main()
