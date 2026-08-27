# test_spark_session.py
from pyspark.sql import SparkSession


def test_spark_session_works():
    spark = SparkSession.builder.master("local[1]").appName("smoke-test").getOrCreate()

    df = spark.createDataFrame([(1,), (2,), (3,)], ["n"])

    assert df.count() == 3

    spark.stop()
