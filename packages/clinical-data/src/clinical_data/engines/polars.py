from pathlib import Path

import polars as pl


class PolarsDataEngine:
    name = "polars"

    def scan_csv(self, path: Path) -> pl.LazyFrame:
        return pl.scan_csv(path, infer_schema_length=1000)

    def collect(self, frame: pl.LazyFrame) -> pl.DataFrame:
        return frame.collect()
