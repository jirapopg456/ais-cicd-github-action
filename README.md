# m5demo — the churn scoring bundle with its tests

The runnable example for Module 5 and the finished state of Challenges 2 to 5. It
is both the instructor's demo bundle and the catch-up artefact: a participant who
falls behind copies the missing piece from here and moves forward.

## Layout
## update 
```
databricks.yml              two targets; variables catalog, schema, cluster_id, corrupt;
                            nothing is excluded, so tests/ deploys with the bundle
pytest.ini                  pythonpath = src · testpaths = tests · the spark marker
requirements-dev.txt        pinned: pytest, pyspark, pandas, pyarrow, numpy
resources/scoring.job.yml   job `scoring`: data_checks -> score -> model_checks -> publish
resources/tests.job.yml     job `run_tests` (dev only): runs the deployed tests/ folder
src/churn/features.py       pure rule (churn_risk_score, risk_band) · Spark layer
                            (build_features, apply_scores) · I/O edge (main)
src/churn/checks.py         data-quality and model checks returning violation lists;
                            fail_on; the rank-statistic auc
src/churn/data.py           deterministic synthetic inputs; corrupt = none | null_ids | drift
src/*.py                    the four scoring notebooks, plus run_tests.py, the
                            notebook run_tests runs against the deployed suite
tests/                      58 tests: 23 unit · 13 transformation · 11 data-quality · 11 model
                            (the complete catalogue: ../test-catalog.md)
tests/fixtures/holdout.csv  18 labelled rows for the AUC test (current value 0.951)
```

## Run the suite

```bash
pip install -r requirements-dev.txt     # pinned set; Java 17+ needed for the spark tests
pytest -m "not spark" -q                # 29 passed, 29 deselected in ~0.5s
pytest -q                               # 58 passed in ~27s
```

## Deploy and run

The host comes from your profile or `DATABRICKS_HOST`; nothing here names a
workspace. Every task runs on the one existing all-purpose cluster through the
`cluster_id` variable, pinned to `Training_Cluster`'s id — the same pattern and
trade-off as `m4demo`: the id is workspace-specific, so the bundle cannot be
promoted as it stands, and the permission (this credential may not create
clusters) outranks that preference. If the cluster was recreated:

```bash
export BUNDLE_VAR_cluster_id=$(databricks clusters list -o json \
  | jq -r '.[] | select(.cluster_name=="Training_Cluster") | .cluster_id')
```

Then:

```bash
pytest -m "not spark" -q && databricks bundle deploy -t dev

databricks bundle run run_tests -t dev                        # the deployed suite: 58 passed
databricks bundle run scoring -t dev                          # clean: 4 x SUCCESS
databricks bundle run scoring -t dev --var corrupt=null_ids   # FAILED at data_checks
databricks bundle run scoring -t dev --var corrupt=drift      # FAILED at model_checks
```

The two corrupt runs are the S62/S63 demonstrations: `null_ids` is malformed input
caught before anything is computed; `drift` is well-formed input whose scores are
wrong, caught by the band-distribution guard after `score` and before `publish`.
In both cases the tasks below the failure report `UPSTREAM_FAILED`.

## Design notes

- **Checks serve two runners.** Every check returns a list of violation strings:
  the suite asserts the list is empty; the notebooks pass the lists to `fail_on`,
  which raises and fails the task. The failure text in the run history is the same
  string the suite's planted-fault tests assert.
- **No UDF.** `apply_scores` restates the rule in column expressions so no worker
  imports the package; the parity test in `tests/test_transform.py` pins the
  expression form to `churn_risk_score` over a 216-point grid.
- **Nothing is written to Unity Catalog.** Tasks rebuild the same deterministic
  frames from `src/churn/data.py` (no writable catalog exists to hand a table
  through), and `publish` reports its destination instead of writing. Every
  notebook ends with `dbutils.notebook.exit(...)`, because `print()` does not
  reach the Jobs API.
- **`tests/` deploys with the bundle.** Nothing excludes it, so `databricks
  bundle deploy` uploads the suite alongside `src/` and `pytest.ini`, and
  `databricks bundle run run_tests -t dev` executes it on the cluster. The
  `staging` target excludes it: the suite gates the promotion, it is not a
  production workload. `sync.exclude` is additive per target and cannot be
  cleared by one, so the exclusion is declared in the target that wants it.
- **Three gates, not one.** `pytest && bundle deploy` is the fast local gate;
  `bundle run run_tests` is the deployed suite on the real runtime; the
  `data_checks` and `model_checks` tasks apply the same check functions from
  `src/churn/checks.py` to the real data inside the run.

======
Test E2
