import json

import numpy as np
from sklearn.dummy import DummyClassifier

from clinical_ml.artifacts import load_manifest, publish_model
from clinical_ml.features import FeatureSchema
from clinical_ml.training import CandidateModelResult


def test_model_publication_writes_versioned_manifest(tmp_path):
    model = DummyClassifier(strategy="most_frequent")
    model.fit(np.array([[0.0], [1.0]]), np.array([0, 1]))
    result = CandidateModelResult(
        name="DummyClassifier",
        model=model,
        metrics={"macro_f1": 0.5, "weighted_f1": 0.5},
    )
    schema = FeatureSchema(version="grd-features/v1", names=("age_65_plus",))

    published = publish_model(
        result,
        schema,
        {"source": "mimic-iv-demo", "version": "2.2"},
        tmp_path,
        label_mapping={"291": 0, "292": 1},
        model_version="test-v1",
    )

    assert (published.path / "model.joblib").is_file()
    assert (published.path / "feature-schema.json").is_file()
    assert json.loads((published.path / "labels.json").read_text())["291"] == 0
    manifest = load_manifest(published.path)
    assert manifest.model_version == "test-v1"
    assert manifest.dataset_source == "mimic-iv-demo"
    assert manifest.feature_schema_version == "grd-features/v1"
