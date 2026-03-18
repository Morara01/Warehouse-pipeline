from project.ingestion.extract_excel import run_excel_ingestion
from project.transformations.clean_data import run_cleaning_pipeline
from project.transformations.enrich_data import run_enrichment_pipeline
from project.warehouse.load_to_db import load_to_database


if __name__ == "__main__":
    run_excel_ingestion()
    run_cleaning_pipeline()
    run_enrichment_pipeline()
    load_to_database()
