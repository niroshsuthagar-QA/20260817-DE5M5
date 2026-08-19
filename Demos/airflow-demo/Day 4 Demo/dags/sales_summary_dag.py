"""
sales_summary_dag.py
--------------------------------------------------------------------------
A deliberately small DAG with TWO tasks so learners can see a real graph:

    extract_totals  >>  write_summary

  1. extract_totals : reads the `sales` table from our app database and
                      computes the total revenue and number of orders.
  2. write_summary  : takes those numbers and inserts ONE row into the
                      `sales_summary` table, stamped with the run time.

The arrow (>>) defines the dependency: write_summary will not start until
extract_totals has finished successfully. That ordering is the whole point
of an orchestrator like Airflow.

Data is passed between tasks using XCom (Airflow's built-in mechanism for
small bits of data handed from one task to the next).
--------------------------------------------------------------------------
"""

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


# A PostgresHook is Airflow's helper for talking to a Postgres database.
# "app_postgres" matches the connection we pre-registered in docker-compose
# (the AIRFLOW_CONN_APP_POSTGRES environment variable).
def extract_totals(**context):
    hook = PostgresHook(postgres_conn_id="app_postgres")
    # get_first runs the query and returns the first row as a tuple.
    total, count = hook.get_first(
        "SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM sales;"
    )
    print(f"Extracted: total={total}, orders={count}")
    # Return values are automatically pushed to XCom so the next task can read them.
    return {"total": float(total), "count": int(count)}


def write_summary(**context):
    # Pull the dict returned by the previous task off XCom.
    ti = context["ti"]
    data = ti.xcom_pull(task_ids="extract_totals")

    hook = PostgresHook(postgres_conn_id="app_postgres")
    hook.run(
        """
        INSERT INTO sales_summary (run_timestamp, total_sales, order_count)
        VALUES (%s, %s, %s);
        """,
        parameters=(datetime.utcnow(), data["total"], data["count"]),
    )
    print(f"Wrote summary row: {data}")


# The DAG definition itself. Everything inside the `with` block belongs to it.
with DAG(
    dag_id="sales_summary",
    start_date=datetime(2024, 1, 1),
    schedule=None,          # None = only runs when YOU trigger it manually
    catchup=False,          # don't backfill past dates
    tags=["demo"],
) as dag:

    task_extract = PythonOperator(
        task_id="extract_totals",
        python_callable=extract_totals,
    )

    task_write = PythonOperator(
        task_id="write_summary",
        python_callable=write_summary,
    )

    # Define the dependency / order. This is what draws the graph in the UI.
    task_extract >> task_write
