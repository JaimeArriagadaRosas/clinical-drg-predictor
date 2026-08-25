from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

from clinical_drg.service import GRDPredictor


class PublishedFeatureExtractor:
    def __init__(self, names: tuple[str, ...]) -> None:
        self._names = names

    def create_features(
        self,
        icd10_codes: list[str] | None = None,
        icd9_codes: list[str] | None = None,
        edad_num: int | None = None,
        sexo: str | None = None,
    ) -> dict[str, Any]:
        return {
            "icd10_codes": tuple(icd10_codes or ()),
            "icd9_codes": tuple(icd9_codes or ()),
            "age": edad_num,
            "sex": sexo,
        }

    def features_to_vector(self, features: dict[str, Any]) -> list[float]:
        age = features.get("age")
        sex = str(features.get("sex") or "").upper()
        # Preserve the legacy structured prediction contract: ICD-10 values are
        # diagnoses and ICD-9 values represent procedures. Do not activate the
        # same ICD-9 value in both feature families; training keeps diagnoses
        # and procedures as separate vocabularies.
        diagnoses = set(features.get("icd10_codes") or ())
        procedures = set(features.get("icd9_codes") or ())

        values: dict[str, float] = {
            "age_lt18": float(age is not None and age < 18),
            "age_18_44": float(age is not None and 18 <= age < 45),
            "age_45_64": float(age is not None and 45 <= age < 65),
            "age_65_plus": float(age is not None and age >= 65),
            "sex_f": float(sex == "F"),
            "sex_m": float(sex == "M"),
            "sex_unknown": float(sex not in {"F", "M"}),
        }
        for name in self._names:
            if name.startswith("dx:"):
                values[name] = float(name[3:] in diagnoses)
            elif name.startswith("px:"):
                values[name] = float(name[3:] in procedures)
        return [values.get(name, 0.0) for name in self._names]


class PublishedLabelDecoder:
    def __init__(self, label_mapping: dict[str, int]) -> None:
        self._labels = {int(index): label for label, index in label_mapping.items()}

    def inverse_transform(self, values: list[int]) -> list[str]:
        return [self._labels[int(value)] for value in values]


def load_published_predictor(path: Path | str) -> GRDPredictor:
    root = Path(path)
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        schema = json.loads((root / "feature-schema.json").read_text(encoding="utf-8"))
        labels = json.loads((root / "labels.json").read_text(encoding="utf-8"))
        model = joblib.load(root / "model.joblib")
        if manifest["feature_schema_version"] != schema["version"]:
            raise ValueError("feature schema version does not match model manifest")
        if manifest.get("label_mapping") != labels:
            raise ValueError("label mapping does not match model manifest")
        names = tuple(str(name) for name in schema["names"])
        return GRDPredictor(
            model,
            PublishedLabelDecoder(labels),
            PublishedFeatureExtractor(names),
            model_name=str(manifest["model_name"]),
            model_version=str(manifest["model_version"]),
        )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return GRDPredictor(None, None, None, model_name="unavailable", model_version="unknown")
