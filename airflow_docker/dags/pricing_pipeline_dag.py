from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

# project to Python path

sys.path.append("/Users/george/Data_engineering_portfolio")

# pipeline functions
from project.ingestion.extract_excel import run_excel_ingestion
from project.transformations.clean_data import run_cleaning_pipeline
from project.transformations.enrich_data import run_enrichment_pipeline
from project.quality.data_quality import run_data_quality_checks
from project.warehouse.load_to_db import load_to_database

default_args = {
    "owner": "george",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),

    # monitoring & alerting
    "email": ["georgejustus254@gmail.com"],
    "email_on_failure": True,
    "email_on_retry": False,
}

with DAG(
    dag_id="data_engineering_pricing_pipeline",
    description="Excel → Transform → Quality → MySQL Warehouse",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval="@daily",  # change later if needed
    catchup=False,
    tags=["data-engineering", "pricing", "mysql"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract_excel",
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

    quality_task = PythonOperator(
        task_id="data_quality_checks",
        python_callable=run_data_quality_checks,
    )

    load_task = PythonOperator(
        task_id="load_to_warehouse",
        python_callable=load_to_database,
    )

    # DAG ORDER
    extract_task >> clean_task >> enrich_task >> quality_task >> load_task