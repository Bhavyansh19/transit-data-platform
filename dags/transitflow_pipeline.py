"""
Week 6 starting point — orchestrate ingest -> dbt -> warehouse as one DAG.

Fill this in once the individual pieces (src/ingest_static_gtfs.py,
src/ingest_realtime_gtfs.py, the dbt project) work standalone. Don't try to write the DAG
before the pieces it's calling actually run on their own.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "transitflow",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="transitflow_pipeline",
    default_args=default_args,
    schedule="*/15 * * * *",  # every 15 min for the real-time feed; tune once ingestion works
    start_date=datetime(2026, 9, 20),
    catchup=False,
    tags=["transitflow"],
) as dag:

    # TODO: ingest_static = PythonOperator(...)
    # TODO: ingest_realtime = PythonOperator(...)
    # TODO: run_dbt = BashOperator(bash_command="dbt run", ...)
    # TODO: test_dbt = BashOperator(bash_command="dbt test", ...)
    #
    # ingest_static >> ingest_realtime >> run_dbt >> test_dbt

    pass
