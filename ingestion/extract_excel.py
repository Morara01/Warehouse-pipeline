import os
import logging
import yaml
import pandas as pd
from datetime import datetime



# Logging Configuration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)



# Load Config

def load_config():
    with open("config/config.yaml", "r") as file:
        return yaml.safe_load(file)



# Excel Ingestion Logic

def ingest_excel_files(raw_path: str, processed_path: str):
    os.makedirs(processed_path, exist_ok=True)

    for file_name in os.listdir(raw_path):
        if file_name.endswith(".xlsx"):
            try:
                file_path = os.path.join(raw_path, file_name)
                logging.info(f"Ingesting file: {file_name}")

                df = pd.read_excel(file_path)

                if df.empty:
                    raise ValueError("File contains no data")

                output_file = (
                    file_name.replace(".xlsx", "")
                    + f"_ingested_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
                )

                output_path = os.path.join(processed_path, output_file)
                df.to_csv(output_path, index=False)

                logging.info(f"Successfully ingested → {output_file}")

            except Exception as e:
                logging.error(f"Failed to ingest {file_name}: {str(e)}")


# Entry Function

def run_excel_ingestion():
    config = load_config()

    raw_path = config["paths"]["raw_data"]
    processed_path = config["paths"]["processed_data"]

    logging.info("Starting Excel ingestion pipeline")
    ingest_excel_files(raw_path, processed_path)
    logging.info("Excel ingestion pipeline completed")
