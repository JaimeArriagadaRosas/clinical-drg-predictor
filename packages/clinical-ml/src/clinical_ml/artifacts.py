from __future__ import annotations

import json
import os
import platform
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import joblib

from clinical_ml.features import FeatureSchema
from clinical_ml.training import CandidateModelResult


@dataclass(frozen=True)
class ModelManifest:
    model_version: str
    model_name: str
    feature_schema_version: str
    dataset_source: str
    dataset_version: str
    metrics: dict
    label_mapping: dict[str, int]
    created_at: str
    commit_sha: str | None
    python_version: str


@dataclass(frozen=True)
class PublishedModel:
    path: Path
    manifest: ModelManifest


def publish_model(
    result: CandidateModelResult,
    feature_schema: FeatureSchema,
    dataset_metadata: dict,
    output_dir: Path,
    *,
    label_mapping: dict[str, int],
    model_version: str | None = None,
) -> PublishedModel:
    version = model_version or (
        f"{result.name.lower()}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    target_dir = output_dir / version
    target_dir.mkdir(parents=True, exist_ok=False)

    joblib.dump(result.model, target_dir / "model.joblib")
    feature_schema.to_json(target_dir / "feature-schema.json")
    (target_dir / "labels.json").write_text(
        json.dumps(label_mapping, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    manifest = ModelManifest(
        model_version=version,
        model_name=result.name,
        feature_schema_version=feature_schema.version,
        dataset_source=str(dataset_metadata["source"]),
        dataset_version=str(dataset_metadata["version"]),
        metrics=result.metrics,
        label_mapping=dict(label_mapping),
        created_at=datetime.now(UTC).isoformat(),
        commit_sha=os.getenv("GITHUB_SHA"),
        python_version=platform.python_version(),
    )
    (target_dir / "manifest.json").write_text(
        json.dumps(asdict(manifest), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return PublishedModel(path=target_dir, manifest=manifest)


def load_manifest(path: Path) -> ModelManifest:
    data = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    return ModelManifest(**data)
