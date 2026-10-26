"""A small ETL DAG showing task dependencies, XCom, and retries.

extract -> transform -> load

Each PythonOperator task's return value is automatically pushed to XCom
(Airflow's small key/value store for passing data between tasks), and the
next task pulls it in by declaring a matching parameter name via op_kwargs
would normally be used, but here we pull explicitly with `ti.xcom_pull`
to make the hand-off visible.
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

ORDERS = [
    {"id": 1, "item": "keyboard", "price": 49.99},
    {"id": 2, "item": "monitor", "price": 199.50},
    {"id": 3, "item": "mouse", "price": 19.99},
]


def extract(**context) -> list[dict]:
    print(f"Extracted {len(ORDERS)} orders")
    return ORDERS


def transform(**context) -> dict:
    ti = context["ti"]
    orders = ti.xcom_pull(task_ids="extract")
    total_revenue = round(sum(order["price"] for order in orders), 2)
    summary = {"order_count": len(orders), "total_revenue": total_revenue}
    print(f"Transformed data: {summary}")
    return summary


def load(**context) -> None:
    ti = context["ti"]
    summary = ti.xcom_pull(task_ids="transform")
    # In a real pipeline this would write to a database or warehouse.
    # Here we just prove the pipeline ran end-to-end.
    print(f"Loaded summary -> {summary}")


default_args = {
    "owner": "learner",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="etl_pipeline",
    description="Extract -> transform -> load demo DAG",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["learning", "etl"],
) as dag:
    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)

    # The >> operator sets task order: extract must finish before transform,
    # which must finish before load.
    extract_task >> transform_task >> load_task
