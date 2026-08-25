from __future__ import annotations

from pathlib import Path
from typing import Any


class SparkDataEngine:
    """Optional distributed data engine using Spark DataFrames/SQL.

    Imports are intentionally lazy so the core/local installation does not
    require Java, PySpark or Delta Lake.
    """

    name = "spark"

    def __init__(self, spark: Any | None = None, *, enable_delta: bool = False) -> None:
        self._spark = spark or self._build_session(enable_delta=enable_delta)
        self._delta_enabled = enable_delta

    @staticmethod
    def _build_session(*, enable_delta: bool) -> Any:
        try:
            from pyspark.sql import SparkSession
        except ImportError as exc:
            raise RuntimeError(
                "Spark support is optional. Install the clinical-data distributed extra."
            ) from exc

        builder = SparkSession.builder.appName("clinical-data").master("local[*]")
        if not enable_delta:
            return builder.getOrCreate()

        try:
            from delta import configure_spark_with_delta_pip
        except ImportError as exc:
            raise RuntimeError(
                "Delta support requires the clinical-data distributed extra."
            ) from exc

        builder = (
            builder.config(
                "spark.sql.extensions",
                "io.delta.sql.DeltaSparkSessionExtension",
            )
            .config(
                "spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.delta.catalog.DeltaCatalog",
            )
        )
        return configure_spark_with_delta_pip(builder).getOrCreate()

    @property
    def spark(self) -> Any:
        return self._spark

    def scan_csv(self, path: Path) -> Any:
        return self._spark.read.option("header", True).option("inferSchema", True).csv(str(path))

    def collect(self, frame: Any) -> Any:
        return frame

    def write_parquet(self, frame: Any, path: Path, *, mode: str = "overwrite") -> None:
        frame.write.mode(mode).parquet(str(path))

    def read_parquet(self, path: Path) -> Any:
        return self._spark.read.parquet(str(path))

    def write_delta(self, frame: Any, path: Path, *, mode: str = "overwrite") -> None:
        if not self._delta_enabled:
            raise RuntimeError("Delta support is not enabled for this SparkDataEngine instance")
        frame.write.format("delta").mode(mode).save(str(path))

    def read_delta(self, path: Path) -> Any:
        if not self._delta_enabled:
            raise RuntimeError("Delta support is not enabled for this SparkDataEngine instance")
        return self._spark.read.format("delta").load(str(path))
