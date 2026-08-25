from pathlib import Path

import pytest

pytest.importorskip("pyspark")

from clinical_data.engines.spark import SparkDataEngine


@pytest.mark.spark
def test_spark_engine_round_trips_parquet(tmp_path: Path):
    engine = SparkDataEngine()
    frame = engine.spark.createDataFrame([(1, "291"), (2, "291"), (3, "470")], ["id", "drg"])
    path = tmp_path / "encounters.parquet"

    engine.write_parquet(frame, path)
    restored = engine.read_parquet(path)

    counts = {row["drg"]: row["count"] for row in restored.groupBy("drg").count().collect()}
    assert counts == {"291": 2, "470": 1}
