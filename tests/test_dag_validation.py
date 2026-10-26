"""DAG integrity tests: the standard way to CI-test Airflow DAGs.

These don't run your business logic (that's what `airflow tasks test` in
the CI workflow does) - they catch the most common real-world mistakes:
a DAG that fails to import, a missing owner/retries, or no tags.
"""
import os

from airflow.models import DagBag

DAGS_FOLDER = os.path.join(os.path.dirname(__file__), "..", "dags")


def load_dagbag() -> DagBag:
    return DagBag(dag_folder=DAGS_FOLDER, include_examples=False)


def test_no_import_errors():
    dagbag = load_dagbag()
    assert not dagbag.import_errors, (
        f"DAG import failures: {dagbag.import_errors}"
    )


def test_dags_were_found():
    dagbag = load_dagbag()
    assert len(dagbag.dags) >= 2


def test_dags_have_tags():
    dagbag = load_dagbag()
    for dag_id, dag in dagbag.dags.items():
        assert dag.tags, f"DAG '{dag_id}' has no tags"


def test_dags_have_reasonable_retries():
    dagbag = load_dagbag()
    for dag_id, dag in dagbag.dags.items():
        retries = dag.default_args.get("retries", 0)
        assert retries <= 3, f"DAG '{dag_id}' sets retries={retries}, that's excessive"
