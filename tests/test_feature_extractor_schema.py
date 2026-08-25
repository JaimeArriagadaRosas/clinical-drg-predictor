import pickle

from src.api.feature_extractor import GRDFeatureExtractor


def _write_training_metadata(tmp_path):
    processed = tmp_path / "dataset" / "processed"
    processed.mkdir(parents=True)
    metadata = {
        "diag_codes": ["E11"],
        "proc_codes": ["39.95"],
        "feature_names": [
            "AGE_neonate",
            "AGE_infant",
            "AGE_child",
            "AGE_young_adult",
            "AGE_middle_adult",
            "AGE_senior",
            "AGE_elderly",
            "SEX_MALE",
            "DIAG_E11",
            "PROC_39.95",
        ],
    }
    with (processed / "metadata.pkl").open("wb") as metadata_file:
        pickle.dump(metadata, metadata_file)


def test_inference_vector_uses_training_feature_order(tmp_path):
    _write_training_metadata(tmp_path)
    extractor = GRDFeatureExtractor(model_path=str(tmp_path))

    features = extractor.create_features(
        icd10_codes=["E11.9"],
        icd9_codes=["39.95"],
        edad_num=65,
        sexo="M",
    )

    assert extractor.features_to_vector(features) == [0, 0, 0, 0, 0, 1, 0, 1, 1, 1]


def test_age_buckets_match_training_preprocessing(tmp_path):
    _write_training_metadata(tmp_path)
    extractor = GRDFeatureExtractor(model_path=str(tmp_path))

    assert extractor.create_features(edad_num=1)["edad"] == "neonate"
    assert extractor.create_features(edad_num=5)["edad"] == "infant"
    assert extractor.create_features(edad_num=18)["edad"] == "child"
    assert extractor.create_features(edad_num=40)["edad"] == "young_adult"
    assert extractor.create_features(edad_num=60)["edad"] == "middle_adult"
    assert extractor.create_features(edad_num=80)["edad"] == "senior"
    assert extractor.create_features(edad_num=81)["edad"] == "elderly"
