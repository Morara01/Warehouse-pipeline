from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Make project importable
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

from ingestion.extract_excel import run_excel_ingestion
from transformations.clean_data import run_cleaning_pipeline
from transformations.enrich_data import run_enrichment_pipeline
from warehouse.load_to_db import load_to_database


default_args = {
    "owner": "data_engineer",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    dag_id="pricing_end_to_end_pipeline",
    default_args=default_args,
    description="End-to-end pricing data warehouse pipeline",
    schedule_interval="@daily",
    start_date=datetime(2026, 2, 1),
    catchup=False,
    tags=["pricing", "warehouse", "etl"],
) as dag:

    ingest_task = PythonOperator(
        task_id="ingest_excels",
        python_callable=run_excel_ingestion,
    )

    clean_task = PythonOperator(
        task_id="clean_data",
        python_callable=run_cleaning_pipeline,
    )

    enrich_task = PythonOperator(
        task_id="enrich_data",
        python_callable=run_enrichment_pipeline,
    )

    warehouse_task = PythonOperator(
        task_id="load_to_warehouse",
        python_callable=load_to_database,
    )

    ingest_task >> clean_task >> enrich_task >> warehouse_task
