import os
import logging
import pandas as pd
import yaml

# Logging Configuration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# merge helper that drops overlapping columns from right_df to prevent suffixes and allows cardinality-safe merges

def safe_merge(left_df, right_df, on, how="left", validate=None):
    overlapping_cols = set(left_df.columns).intersection(set(right_df.columns))
    overlapping_cols.discard(on)

    if overlapping_cols:
        right_df = right_df.drop(columns=list(overlapping_cols))

    return left_df.merge(
        right_df,
        on=on,
        how=how,
        validate=validate
    )

# Load Config

def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

# Helper: Get latest file by keyword

def get_latest_file(directory: str, keyword: str) -> str:
    files = sorted(
        [
            f for f in os.listdir(directory)
            if keyword in f.lower() and f.endswith(".csv")
        ],
        reverse=True
    )

    if not files:
        raise FileNotFoundError(
            f"No files found in {directory} matching keyword '{keyword}'"
        )

    return files[0]

# Enrichment Logic (CARDINALITY SAFE)

def enrich_pricing_data(cleaned_path: str, curated_path: str):
    os.makedirs(curated_path, exist_ok=True)

    logging.info("Locating cleaned input files")

    pricing_file = get_latest_file(cleaned_path, "unilever_products")
    finance_file = get_latest_file(cleaned_path, "finance_targets")
    model_file = get_latest_file(cleaned_path, "model_outputs")
    merged_file = get_latest_file(cleaned_path, "merged_pricing")

    logging.info("Reading cleaned datasets")

    pricing_df = pd.read_csv(os.path.join(cleaned_path, pricing_file))
    finance_df = pd.read_csv(os.path.join(cleaned_path, finance_file))
    model_df = pd.read_csv(os.path.join(cleaned_path, model_file))
    merged_df = pd.read_csv(os.path.join(cleaned_path, merged_file))

    logging.info("Controlling cardinality (dimension deduplication)")

    
    # DIMENSION TABLES: enforce 1 row per region

    finance_df = finance_df.drop_duplicates(subset=["region"])
    model_df = model_df.drop_duplicates(subset=["region"])
    merged_df = merged_df.drop_duplicates(subset=["region"])

    logging.info("Starting safe enrichment joins")

    # Controlled merges (many-to-one only)

    logging.info("Starting safe enrichment joins")

    enriched_df = safe_merge(
        pricing_df,
        merged_df,
        on="region",
        validate="many_to_one"
    )

    enriched_df = safe_merge(
        enriched_df,
        finance_df,
        on="region",
        validate="many_to_one"
    )
    enriched_df = safe_merge(
        enriched_df,
        model_df,
        on="region",
        validate="many_to_one"
    )

    
    # Derived Metrics
   
    if {"mark_up_pct_used", "max_allowed_mark_uppct"}.issubset(enriched_df.columns):
        enriched_df["markup_compliant"] = (
            enriched_df["mark_up_pct_used"]
            <= enriched_df["max_allowed_mark_uppct"]
        )

    if {"mark_up_pct_used", "target_margin"}.issubset(enriched_df.columns):
        enriched_df["margin_vs_target"] = (
            enriched_df["mark_up_pct_used"] - enriched_df["target_margin"]
        )
    
    # Output curated dataset
   
    output_file = "pricing_enriched_curated.csv"
    output_path = os.path.join(curated_path, output_file)

    enriched_df.to_csv(output_path, index=False)

    logging.info(
        f"Enrichment complete | Rows: {len(enriched_df)} → {output_file}"
    )

# Entry Point

def run_enrichment_pipeline():
    config = load_config()

    processed_path = config["paths"]["processed_data"]
    cleaned_path = os.path.join(processed_path, "cleaned")
    curated_path = os.path.join(processed_path, "curated")

    enrich_pricing_data(cleaned_path, curated_path)
