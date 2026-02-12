from ingestion.extract_excel import run_excel_ingestion
from transformations.clean_data import run_cleaning_pipeline
from transformations.enrich_data import run_enrichment_pipeline
from warehouse.load_to_db import load_to_database

if __name__ == "__main__":
    run_excel_ingestion()
    run_cleaning_pipeline()
    run_enrichment_pipeline()
    load_to_database()
