from argparse import Namespace

from src.training.training_main import build_stage_args


def _args(**overrides):
    values = {
        "data_path": None,
        "n_estimators": 50,
        "max_depth": None,
        "skip_lgbm": False,
    }
    values.update(overrides)
    return Namespace(**values)


def test_data_path_is_only_forwarded_to_load_stage():
    args = _args(data_path="custom.csv")

    assert build_stage_args("Load Data", args) == ["--data-path", "custom.csv"]
    assert build_stage_args("Quality Analysis", args) == []
    assert build_stage_args("Preprocessing", args) == []


def test_model_options_are_only_forwarded_to_training_stage():
    args = _args(n_estimators=120, max_depth=40, skip_lgbm=True)

    assert build_stage_args("Load Data", args) == []
    assert build_stage_args("Train Models", args) == [
        "--n-estimators",
        "120",
        "--max-depth",
        "40",
        "--skip-lgbm",
    ]


def test_none_max_depth_is_not_forwarded():
    args = _args(max_depth=None)

    assert "--max-depth" not in build_stage_args("Train Models", args)
