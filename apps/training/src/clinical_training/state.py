from __future__ import annotations

from dataclasses import dataclass

from rich.table import Table

from clinical_training.pipeline import TrainingStage


@dataclass(frozen=True)
class WorkbenchState:
    dataset: str
    engine: str
    completed_stages: tuple[TrainingStage, ...] = ()
    latest_artifact: str | None = None

    def as_table(self) -> Table:
        table = Table(title="Clinical ML Training Workbench")
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("Dataset", self.dataset)
        table.add_row("Engine", self.engine)
        completed = ", ".join(stage.value for stage in self.completed_stages) or "none"
        table.add_row("Completed", completed)
        table.add_row("Latest artifact", self.latest_artifact or "none")
        return table
