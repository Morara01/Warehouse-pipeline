import pandas as pd

class DataQualityException(Exception):
    """Raised when data quality checks fail"""
    pass


def check_not_null(df: pd.DataFrame, columns: list):
    for col in columns:
        if df[col].isnull().any():
            raise DataQualityException(f"NULL values found in column: {col}")


def check_positive_values(df: pd.DataFrame, columns: list):
    for col in columns:
        if (df[col] < 0).any():
            raise DataQualityException(f"Negative values found in column: {col}")


def check_percentage_range(df: pd.DataFrame, columns: list, min_val=0, max_val=100):
    for col in columns:
        if not df[col].between(min_val, max_val).all():
            raise DataQualityException(
                f"Values out of range [{min_val}, {max_val}] in column: {col}"
            )


def check_uniqueness(df: pd.DataFrame, columns: list):
    duplicates = df.duplicated(subset=columns)
    if duplicates.any():
        raise DataQualityException(
            f"Duplicate records found for columns: {columns}"
        )


def run_data_quality_checks(df: pd.DataFrame):
    """
    Central quality gate — pipeline stops here if checks fail
    """

    # 1️ Critical fields must not be null
    check_not_null(
        df,
        columns=[
            "product_id",
            "region",
            "base_cost",
            "recommended_selling_price",
        ],
    )

    # 2️ Numeric sanity
    check_positive_values(
        df,
        columns=[
            "base_cost",
            "recommended_selling_price",
        ],
    )

    # 3️ Percentage sanity
    check_percentage_range(
        df,
        columns=[
            "mark_up_pct_used",
            "max_allowed_mark_uppct",
        ],
        min_val=0,
        max_val=100,
    )

    # 4️ Natural key uniqueness
    check_uniqueness(
        df,
        columns=["product_id", "region"],
    )

    return True
