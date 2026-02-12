import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
from utils.logger import get_logger

logger = get_logger("warehouse.load")

# ======================
# CONFIG
# ======================

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

# ======================
# LOAD SOURCE DATA
# ======================

def load_curated_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)

    # safety cleanup
    df = df.dropna(subset=["product_id", "region"])
    return df


# ======================
# DIMENSION LOADERS
# ======================

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


# ======================
# FACT LOADER
# ======================

def load_fact_pricing(conn, df: pd.DataFrame):
    region_lookup = pd.read_sql(
        "SELECT region_id, region_name FROM dim_region",
        conn,
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

    fact_df = fact_df[
        [
            "product_id",
            "region_id",
            "base_cost",
            "recommended_selling_price",
            "mark_up_pct_used",
            "max_allowed_mark_uppct",
            "markup_compliant",
            "margin_vs_target",
        ]
    ]

    fact_df.to_sql(
        "fact_pricing_performance",
        conn,
        if_exists="append",
        index=False,
        method="multi",
    )


# ======================
# PIPELINE ORCHESTRATION
# ======================

def load_to_database():
    logger.info("Starting warehouse load pipeline")

    engine = create_engine(DB_URL)

    df = load_curated_data()
    logger.info(f"Loaded curated dataset with {len(df)} rows")

    with engine.begin() as conn:
        logger.info("Loading dim_region")
        load_dim_region(conn, df)

        logger.info("Loading dim_product")
        load_dim_product(conn, df)

        logger.info("Loading fact_pricing_performance")
        load_fact_pricing(conn, df)

    logger.info("Warehouse load pipeline completed successfully")


