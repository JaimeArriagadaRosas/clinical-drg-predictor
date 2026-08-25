from typer.testing import CliRunner

import clinical_training.cli as cli
from clinical_training.pipeline import StageResult, TrainingStage

runner = CliRunner()


class FakePipeline:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def run_stage(self, stage: TrainingStage) -> StageResult:
        self.calls.append(stage.value)
        return StageResult(stage=stage, status="completed")

    def run_all(self) -> list[StageResult]:
        self.calls.append("all")
        return [StageResult(stage=stage, status="completed") for stage in TrainingStage]


def test_training_cli_routes_single_stage(monkeypatch):
    pipeline = FakePipeline()
    monkeypatch.setattr(cli, "create_pipeline", lambda: pipeline)

    result = runner.invoke(cli.app, ["run", "--stage", "eda"])

    assert result.exit_code == 0
    assert pipeline.calls == ["eda"]
    assert "eda: completed" in result.stdout


def test_training_cli_routes_complete_pipeline(monkeypatch):
    pipeline = FakePipeline()
    monkeypatch.setattr(cli, "create_pipeline", lambda: pipeline)

    result = runner.invoke(cli.app, ["run", "--all"])

    assert result.exit_code == 0
    assert pipeline.calls == ["all"]
    assert "publish: completed" in result.stdout


def test_training_cli_requires_exactly_one_mode():
    result = runner.invoke(cli.app, ["run"])
    assert result.exit_code != 0
    assert "choose exactly one" in result.output
