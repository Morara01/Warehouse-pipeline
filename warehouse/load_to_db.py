import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
from utils.logger import get_logger
from transformations.schema.schema_validator import validate_schema
from quality.data_quality import run_data_quality_checks
from utils.db import get_engine

logger = get_logger("warehouse.load")


# CONFIG


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "curated"
    / "pricing_enriched_curated.csv"
)

DB_CONFIG = {
    "user": "root",
    "password": "Unihub2023!!",
    "host": "localhost",
    "port": "3306",
    "database": "pricing_warehouse"
}

DB_URL = (
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)


# LOAD SOURCE DATA


def load_curated_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)

    # enforce warehouse column contract
    warehouse_columns = [
        "product_id",
        "region",
        "base_cost",
        "recommended_selling_price",
        "mark_up_pct_used",
        "max_allowed_mark_uppct",
        "markup_compliant",
        "margin_vs_target",
        "target_revenue",
        "target_margin",
        "category",
        "price_tier",
        "brand_strength_score",
    ]

    df = df[warehouse_columns]

    
    # TYPE ENFORCEMENT
    
    numeric_columns = [
        "base_cost",
        "recommended_selling_price",
        "mark_up_pct_used",
        "max_allowed_mark_uppct",
        "margin_vs_target",
        "target_revenue",
        "target_margin",
        "brand_strength_score",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)


    # boolean normalization
    df["markup_compliant"] = df["markup_compliant"].astype(bool)

    # safety cleanup
    df = df.dropna(subset=["product_id", "region"])
    return df



# DIMENSION LOADERS


def load_dim_region(conn, df: pd.DataFrame):
    regions = (
        df[["region", "target_revenue", "target_margin"]]
        .drop_duplicates()
        .rename(columns={"region": "region_name"})
    )

    # insert only new regions
    insert_sql = """
        INSERT INTO dim_region (region_name, target_revenue, target_margin)
        SELECT :region_name, :target_revenue, :target_margin
        WHERE NOT EXISTS (
            SELECT 1 FROM dim_region WHERE region_name = :region_name
        )
    """

    for _, row in regions.iterrows():
        conn.execute(
            text(insert_sql),
            {
                "region_name": row["region_name"],
                "target_revenue": row["target_revenue"],
                "target_margin": row["target_margin"],
            },
        )


def load_dim_product(conn, df: pd.DataFrame):
    products = (
        df[
            [
                "product_id",
                "category",
                "price_tier",
                "brand_strength_score",
            ]
        ]
        .drop_duplicates()
    )

    insert_sql = """
        INSERT INTO dim_product (
            product_id, category, price_tier, brand_strength_score
        )
        SELECT :product_id, :category, :price_tier, :brand_strength_score
        WHERE NOT EXISTS (
            SELECT 1 FROM dim_product WHERE product_id = :product_id
        )
    """

    for _, row in products.iterrows():
        conn.execute(
            text(insert_sql),
            {
                "product_id": int(row["product_id"]),
                "category": row["category"],
                "price_tier": row["price_tier"],
                "brand_strength_score": row["brand_strength_score"],
            },
        )



# FACT LOADER


def load_fact_pricing(engine, df):
    logger.info("Preparing fact_pricing_performance incremental load")

    sql = """
        SELECT region_id, region_name
        FROM dim_region
    """
    with engine.connect() as connection:
        region_lookup = pd.read_sql(sql, connection)


    region_lookup = pd.read_sql(
        "SELECT region_id, region_name FROM dim_region",
        engine,
    )

    fact_df = (
        df.merge(
            region_lookup,
            left_on="region",
            right_on="region_name",
            how="left",
        )
        .drop(columns=["region", "region_name"])
    )

    insert_sql = """
        INSERT INTO fact_pricing_performance (
            product_id,
            region_id,
            base_cost,
            recommended_selling_price,
            mark_up_pct_used,
            max_allowed_mark_uppct,
            markup_compliant,
            margin_vs_target
        )
        SELECT
            :product_id,
            :region_id,
            :base_cost,
            :recommended_selling_price,
            :mark_up_pct_used,
            :max_allowed_mark_uppct,
            :markup_compliant,
            :margin_vs_target
        WHERE NOT EXISTS (
            SELECT 1
            FROM fact_pricing_performance
            WHERE product_id = :product_id
              AND region_id = :region_id
        )
    """

    inserted = 0

    for _, row in fact_df.iterrows():
        result = engine.execute(
            text(insert_sql),
            {
                "product_id": int(row["product_id"]),
                "region_id": int(row["region_id"]),
                "base_cost": float(row["base_cost"]),
                "recommended_selling_price": float(row["recommended_selling_price"]),
                "mark_up_pct_used": float(row["mark_up_pct_used"]),
                "max_allowed_mark_uppct": float(row["max_allowed_mark_uppct"]),
                "markup_compliant": bool(row["markup_compliant"]),
                "margin_vs_target": float(row["margin_vs_target"]),
            },
        )

        if result.rowcount == 1:
            inserted += 1

    logger.info(f"Inserted {inserted} new fact records")



# PIPELINE ORCHESTRATION


def load_to_database():
    logger.info("Starting warehouse load pipeline")

    engine = create_engine(DB_URL)

    df = load_curated_data()
    logger.info(f"Loaded curated dataset with {len(df)} rows")
    
    

    # DATA QUALITY GATE
    logger.info("Running data quality checks")
    run_data_quality_checks(df)
    logger.info("Data quality checks passed")

    # SCHEMA GUARDRAIL
    validate_schema(
        df=df,
        dataset_name="pricing_enriched_curated",
        schema_path="transformations/schema/curated_schema.yaml",
    )

    logger.info("Schema validation passed")

    with engine.begin() as conn:
        logger.info("Loading dim_region")
        load_dim_region(conn, df)

        logger.info("Loading dim_product")
        load_dim_product(conn, df)

        logger.info("Loading fact_pricing_performance")
        load_fact_pricing(engine, df)

    logger.info("Warehouse load pipeline completed successfully")


