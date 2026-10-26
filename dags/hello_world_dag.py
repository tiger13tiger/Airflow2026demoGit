"""The smallest possible Airflow DAG: one task, no dependencies.

Start here before looking at dags/etl_pipeline_dag.py.
"""
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def say_hello() -> None:
    print("Hello from your first Airflow task!")


# A DAG (Directed Acyclic Graph) is just a container that describes *when*
# and *in what order* a set of tasks should run. Airflow discovers this
# object because it's a module-level variable in a file under dags/.
with DAG(
    dag_id="hello_world",
    description="Minimal one-task DAG to sanity-check an Airflow setup",
    start_date=datetime(2024, 1, 1),
    schedule=None,  # None = only runs when triggered manually or via the API/CLI
    catchup=False,  # don't backfill runs for past schedule dates
    tags=["learning", "hello-world"],
) as dag:
    # A task is an Operator bound to this DAG. PythonOperator just calls a
    # Python callable when the task runs.
    hello_task = PythonOperator(
        task_id="say_hello",
        python_callable=say_hello,
    )
