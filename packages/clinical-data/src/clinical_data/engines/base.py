from __future__ import annotations

from pathlib import Path
from typing import Protocol

import polars as pl


class DataEngine(Protocol):
    name: str

    def scan_csv(self, path: Path) -> pl.LazyFrame: ...

    def collect(self, frame: pl.LazyFrame) -> pl.DataFrame: ...
