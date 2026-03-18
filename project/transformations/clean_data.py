import os
import logging
import pandas as pd
import yaml
import re


# Logging Configuration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)



# Load Config

def load_config():
    with open("config/config.yaml", "r") as file:
        return yaml.safe_load(file)



# Column Standardisation

def standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("%", "pct")
    )
    return df



# Business Rule Validation

def apply_business_rules(df: pd.DataFrame, pricing_rules: dict) -> pd.DataFrame:
    if "mark_up_pct_used" in df.columns and "max_allowed_mark_uppct" in df.columns:
        df["markup_violation"] = (
            df["mark_up_pct_used"] > df["max_allowed_mark_uppct"]
        )
    else:
        df["markup_violation"] = False

    return df


def get_latest_ingested_files(processed_path):
    latest_files = {}

    for file_name in os.listdir(processed_path):

        if not (file_name.endswith(".csv") and "ingested" in file_name):
            continue

        # Example: merged_pricing_data8_ingested
        dataset = file_name.split("_ingested_")[0]

        match = re.search(r"\d{14}", file_name)
        if not match:
            continue

        timestamp = match.group()

        if dataset not in latest_files:
            latest_files[dataset] = (timestamp, file_name)
        else:
            if timestamp > latest_files[dataset][0]:
                latest_files[dataset] = (timestamp, file_name)

    return [file[1] for file in latest_files.values()]

# Cleaning Pipeline

def clean_files(processed_path: str, cleaned_path: str, pricing_rules: dict):
    os.makedirs(cleaned_path, exist_ok=True)

    latest_files = get_latest_ingested_files(processed_path)
    
    for file_name in latest_files:
            try:
                file_path = os.path.join(processed_path, file_name)
                logging.info(f"Cleaning file: {file_name}")

                df = pd.read_csv(file_path)
                original_rows = len(df)

                if df.empty:
                    raise ValueError("Dataset is empty")

                df = standardise_columns(df)
                df = apply_business_rules(df, pricing_rules)

                cleaned_file = file_name.replace("ingested", "cleaned")
                output_path = os.path.join(cleaned_path, cleaned_file)

                df.to_csv(output_path, index=False)

                logging.info(
                    f"Cleaned {file_name} | Rows: {original_rows} → {len(df)}"
                )

            except Exception as e:
                logging.error(f"Failed to clean {file_name}: {str(e)}")



# Entry Function

def run_cleaning_pipeline():
    config = load_config()

    processed_path = config["paths"]["processed_data"]
    cleaned_path = os.path.join(processed_path, "cleaned")
    pricing_rules = config.get("pricing", {})

    logging.info("Starting data cleaning pipeline")
    clean_files(processed_path, cleaned_path, pricing_rules)
    logging.info("Data cleaning pipeline completed")
