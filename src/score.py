# Databricks notebook source
# score — build the feature table and attach churn scores.
#
# This task holds no checks. It runs only if data_checks succeeded, and its
# output is validated by model_checks before publish runs. The functions are
# the same ones the test suite exercises locally.
# Comment for testing e4-filter

# COMMAND ----------

dbutils.widgets.text("src_root", "")
dbutils.widgets.text("corrupt", "none")

import sys

src_root = dbutils.widgets.get("src_root")
if src_root and src_root not in sys.path:
    sys.path.append(src_root)

from churn import data
from churn.data import AS_OF
from churn.features import apply_scores, build_features

# COMMAND ----------

corrupt = dbutils.widgets.get("corrupt")
events = data.make_events(spark, corrupt)
revenue = data.make_revenue(spark, corrupt)

features = build_features(events, revenue, as_of=AS_OF)
scored = apply_scores(features)

bands = {r["risk_band"]: r["count"] for r in scored.groupBy("risk_band").count().collect()}

# COMMAND ----------

dbutils.notebook.exit(
    f"scored {scored.count()} customers: "
    f"high={bands.get('high', 0)} medium={bands.get('medium', 0)} low={bands.get('low', 0)}"
)
