import mlflow

from clinical_ml.tracking import MLflowTracker


def test_mlflow_tracker_logs_local_run(tmp_path):
    tracker = MLflowTracker(tmp_path / "mlruns", experiment_name="test-experiment")
    run_id = tracker.log_run(
        "baseline",
        params={"model": "dummy"},
        metrics={"macro_f1": 0.5},
    )

    run = mlflow.get_run(run_id)
    assert run.data.params["model"] == "dummy"
    assert run.data.metrics["macro_f1"] == 0.5
