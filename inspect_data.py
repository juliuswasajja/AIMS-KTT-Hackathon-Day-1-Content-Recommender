"""Simple data inspection script for Tier 1 hackathon CSVs."""

from pathlib import Path

import pandas as pd


DATA_DIR = Path("data")
FILES = ["catalog.csv", "queries.csv", "click_log.csv"]


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_basic_info(file_name: str, df: pd.DataFrame) -> None:
    print(f"File: {file_name}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print("\nDtypes:")
    print(df.dtypes.to_string())
    print("\nMissing values per column:")
    print(df.isna().sum().to_string())
    print("\nFirst 5 rows:")
    print(df.head(5).to_string(index=False))


def inspect_catalog(df: pd.DataFrame) -> None:
    print_section("Catalog-specific checks")

    for col in ["category", "material", "origin_district", "artisan_id"]:
        if col in df.columns:
            print(f"Unique count - {col}: {df[col].nunique(dropna=True)}")
        else:
            print(f"Column not found: {col}")

    if "price_rwf" in df.columns:
        price_series = pd.to_numeric(df["price_rwf"], errors="coerce").dropna()
        if price_series.empty:
            print("price_rwf exists but has no valid numeric values.")
        else:
            print(f"price_rwf min: {price_series.min():.2f}")
            print(f"price_rwf max: {price_series.max():.2f}")
            print(f"price_rwf median: {price_series.median():.2f}")
    else:
        print("Column not found: price_rwf")


def inspect_queries(df: pd.DataFrame) -> None:
    print_section("Queries-specific checks")

    lower_cols = {c: c.lower() for c in df.columns}
    query_cols = [c for c in df.columns if "query" in lower_cols[c]]
    label_cols = [
        c
        for c in df.columns
        if any(token in lower_cols[c] for token in ["label", "baseline", "product", "sku", "id"])
    ]

    print(f"Query text columns: {query_cols if query_cols else 'None found'}")
    print(f"Label/Baseline/Product-ID columns: {label_cols if label_cols else 'None found'}")
    print("\nFirst 10 rows:")
    print(df.head(10).to_string(index=False))


def inspect_click_log(df: pd.DataFrame) -> None:
    print_section("Click-log specific checks")

    print(f"Columns: {list(df.columns)}")
    print("\nFirst 10 rows:")
    print(df.head(10).to_string(index=False))

    lower_cols = {c: c.lower() for c in df.columns}
    likely_fields = [
        c
        for c in df.columns
        if any(token in lower_cols[c] for token in ["sku", "query", "product", "item"])
    ]

    if not likely_fields:
        print("\nNo likely SKU/query fields found for value counts.")
        return

    print("\nValue counts (top 10) for likely SKU/query fields:")
    for col in likely_fields:
        print(f"\n- {col}")
        print(df[col].astype(str).value_counts(dropna=False).head(10).to_string())


def inspect_file(path: Path) -> None:
    file_name = path.name
    print_section(f"Inspecting {file_name}")

    if not path.exists():
        print(f"Missing file: {path}")
        return

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        print(f"Could not read {path}: {exc}")
        return

    print_basic_info(file_name, df)

    if file_name == "catalog.csv":
        inspect_catalog(df)
    elif file_name == "queries.csv":
        inspect_queries(df)
    elif file_name == "click_log.csv":
        inspect_click_log(df)


def main() -> None:
    print_section("Tier 1 Dataset Inspection")
    print(f"Data directory: {DATA_DIR.resolve()}")

    if not DATA_DIR.exists():
        print(f"Data directory is missing: {DATA_DIR}")
        return

    for file_name in FILES:
        inspect_file(DATA_DIR / file_name)


if __name__ == "__main__":
    main()
