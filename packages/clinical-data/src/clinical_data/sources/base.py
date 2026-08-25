from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from clinical_data.contracts import HospitalEncounter


class EncounterSource(Protocol):
    def iter_encounters(self) -> Iterator[HospitalEncounter]: ...
