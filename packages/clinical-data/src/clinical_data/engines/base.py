from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class DataEngine(Protocol):
    name: str

    def scan_csv(self, path: Path) -> Any: ...

    def collect(self, frame: Any) -> Any: ...
