import typer
from rich.console import Console

from clinical_training.pipeline import TrainingPipeline, TrainingStage

app = typer.Typer(no_args_is_help=True, help="Clinical GRD Training Workbench")
console = Console()


@app.callback()
def main() -> None:
    """Clinical GRD Training Workbench."""


def create_pipeline() -> TrainingPipeline:
    return TrainingPipeline()


@app.command("run")
def run_pipeline(
    stage: str | None = typer.Option(None, "--stage"),
    all_stages: bool = typer.Option(False, "--all"),
) -> None:
    if bool(stage) == all_stages:
        raise typer.BadParameter("choose exactly one of --stage or --all")

    pipeline = create_pipeline()
    try:
        if all_stages:
            results = pipeline.run_all()
        else:
            selected = TrainingStage(stage)
            results = [pipeline.run_stage(selected)]
    except (RuntimeError, ValueError) as exc:
        console.print(f"Training configuration error: {exc}")
        raise typer.Exit(code=2) from exc

    for result in results:
        console.print(f"{result.stage.value}: {result.status}")


if __name__ == "__main__":
    app()
