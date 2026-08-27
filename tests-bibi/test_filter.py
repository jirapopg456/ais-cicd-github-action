# test_filter.py
from pyspark.sql import DataFrame
from pyspark.sql.functions import col


def filter_customers_under_300(df: DataFrame) -> DataFrame:
    """Keep only rows where customerID < 300, return just customerID."""
    return df.filter(col("customerID") < 300).select("customerID")


def test_filter_customers_under_300(spark):
    df = spark.createDataFrame(
        [(100,), (250,), (300,), (450,)],
        ["customerID"],
    )

    result = filter_customers_under_300(df)

    ids = {r["customerID"] for r in result.collect()}

    assert result.columns == ["customerID"]
    assert result.count() == 2          # 100 and 250
    assert ids == {100, 250}            # 300 excluded (strict <), 450 excluded
