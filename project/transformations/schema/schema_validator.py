import os
import yaml
import pandas as pd


class SchemaValidationError(Exception):
    pass


def load_schema(schema_relative_path: str) -> dict:
    """
    Load schema file using BASE_DIR (works locally + Airflow)
    """
    base_dir = os.getenv("BASE_DIR", os.getcwd())
    schema_path = os.path.join(base_dir, schema_relative_path)

    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")

    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def validate_schema(
    df: pd.DataFrame,
    dataset_name: str,
    schema_relative_path: str,
):
    """
    Validate dataframe against schema definition
    """
    # Load full schema file
    full_schema = load_schema(schema_relative_path)

    if dataset_name not in full_schema:
        raise SchemaValidationError(
            f"Dataset '{dataset_name}' not found in schema file"
        )

    schema = full_schema[dataset_name]

    required_columns = set(schema["required_columns"])
    actual_columns = set(df.columns)

    missing = required_columns - actual_columns
    extra = actual_columns - required_columns

    if missing:
        raise SchemaValidationError(
            f"Missing required columns: {sorted(missing)}"
        )

    if extra:
        raise SchemaValidationError(
            f"Unexpected extra columns detected: {sorted(extra)}"
        )

    # Optional: type checks
    for col, expected_type in schema.get("column_types", {}).items():
        if col not in df.columns:
            continue

        if expected_type == "int" and not pd.api.types.is_integer_dtype(df[col]):
            raise SchemaValidationError(f"Column '{col}' must be integer")

        if expected_type == "float" and not pd.api.types.is_float_dtype(df[col]):
            raise SchemaValidationError(f"Column '{col}' must be float")

        if expected_type == "bool" and not pd.api.types.is_bool_dtype(df[col]):
            raise SchemaValidationError(f"Column '{col}' must be boolean")

    return True