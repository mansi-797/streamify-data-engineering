from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator


default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    dag_id="streamify_local_pipeline",
    description="Streamify local data pipeline: Parquet -> PostgreSQL -> dbt",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    schedule="@hourly",
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["streamify", "local", "postgres", "dbt"],
) as dag:

    load_listen = BashOperator(
        task_id="load_listen_events",
        bash_command="""
        cd /opt/airflow &&
        python scripts/load_parquet_to_postgres.py listen
        """,
    )

    load_page = BashOperator(
        task_id="load_page_view_events",
        bash_command="""
        cd /opt/airflow &&
        python scripts/load_parquet_to_postgres.py page
        """,
    )

    load_auth = BashOperator(
        task_id="load_auth_events",
        bash_command="""
        cd /opt/airflow &&
        python scripts/load_parquet_to_postgres.py auth
        """,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="""
        cd /dbt &&
        mkdir -p /tmp/dbt-logs /tmp/dbt-target &&
        dbt run \
          --profiles-dir . \
          --target airflow \
          --log-path /tmp/dbt-logs \
          --target-path /tmp/dbt-target
        """,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="""
        cd /dbt &&
        mkdir -p /tmp/dbt-logs /tmp/dbt-target &&
        dbt test \
          --profiles-dir . \
          --target airflow \
          --log-path /tmp/dbt-logs \
          --target-path /tmp/dbt-target
        """,
    )

    [load_listen, load_page, load_auth] >> dbt_run >> dbt_test
