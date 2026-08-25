from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any


class TrainingStage(str, Enum):
    ACQUIRE = "acquire"
    VALIDATE = "validate"
    EDA = "eda"
    CLEAN = "clean"
    TRANSFORM = "transform"
    FEATURES = "features"
    SPLIT = "split"
    TRAIN = "train"
    EVALUATE = "evaluate"
    SELECT = "select"
    PUBLISH = "publish"


@dataclass(frozen=True)
class StageResult:
    stage: TrainingStage
    status: str
    detail: str | None = None
    payload: Any = None


class TrainingPipeline:
    def __init__(self, handlers: Mapping[TrainingStage, Callable[[], Any]] | None = None) -> None:
        self._handlers = dict(handlers or {})

    @property
    def stages(self) -> tuple[TrainingStage, ...]:
        return tuple(TrainingStage)

    def run_stage(self, stage: TrainingStage) -> StageResult:
        handler = self._handlers.get(stage)
        if handler is None:
            raise RuntimeError(f"training stage is not configured: {stage.value}")
        payload = handler()
        return StageResult(stage=stage, status="completed", payload=payload)

    def run_all(self) -> list[StageResult]:
        return [self.run_stage(stage) for stage in self.stages]
