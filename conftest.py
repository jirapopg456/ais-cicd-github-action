"""Shared fixtures for the Module 5 test suite.

pytest injects a fixture into any test that names it as an argument. The
Spark session is session-scoped, so the JVM starts once for the whole run;
the configuration keeps it small and quiet enough for a laptop:

  local[2]                        two local threads, no cluster
  spark.sql.shuffle.partitions=2  the default 200 makes tiny joins slow
  spark.ui.enabled=false          no web UI on port 4040
"""
from __future__ import annotations

from datetime import date

import pytest
from pyspark.sql import SparkSession

AS_OF = date(2026, 6, 30)


@pytest.fixture(scope="session")
def spark():
    session = (
        SparkSession.builder.master("local[2]")
        .appName("m5-tests")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


@pytest.fixture()
def as_of() -> date:
    return AS_OF


@pytest.fixture()
def events_df(spark):
    """Hand-written events for four customers.

    c1 is recent and active; c2 is the worked middle case; c3 has events but
    no revenue rows; c4's only event is outside the 90-day window.
    """
    rows = [
        ("c1", date(2026, 6, 29)), ("c1", date(2026, 6, 25)), ("c1", date(2026, 6, 20)),
        ("c2", date(2026, 6, 15)), ("c2", date(2026, 6, 1)), ("c2", date(2026, 5, 10)),
        ("c3", date(2026, 5, 21)),
        ("c4", date(2026, 1, 15)),
    ]
    return spark.createDataFrame(rows, "customer_id string, event_ts date")


@pytest.fixture()
def revenue_df(spark):
    """Revenue rows. c3 and c4 have none."""
    rows = [
        ("c1", 800.0), ("c1", 400.0),
        ("c2", 500.0),
    ]
    return spark.createDataFrame(rows, "customer_id string, amount double")
