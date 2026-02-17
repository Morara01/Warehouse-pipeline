import yaml
import pandas as pd

class SchemaValidationError(Exception):
    pass


def load_schema(schema_path: str) -> dict:
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def validate_schema(
    df: pd.DataFrame,
    dataset_name: str,
    schema_path: str,
):
    schema = load_schema(schema_path)[dataset_name]

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

    # Optional: light type checks
    for col, expected_type in schema.get("column_types", {}).items():
        if col not in df.columns:
            continue

        if expected_type == "int" and not pd.api.types.is_integer_dtype(df[col]):
            raise SchemaValidationError(f"Column {col} must be integer")

        if expected_type == "float" and not pd.api.types.is_float_dtype(df[col]):
            raise SchemaValidationError(f"Column {col} must be float")

        if expected_type == "bool" and not pd.api.types.is_bool_dtype(df[col]):
            raise SchemaValidationError(f"Column {col} must be boolean")

    return True
