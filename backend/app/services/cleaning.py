import pandas as pd
import numpy as np
import os
from typing import Dict, Any, Tuple

# Required database columns
REQUIRED_COLUMNS = [
    "order_date", "customer", "segment", "city", "state", 
    "product", "category", "quantity", "price", "discount", 
    "revenue", "profit", "region"
]

COLUMN_MAPPING_SUGGESTIONS = {
    "order_date": ["order date", "orderdate", "date", "sale date", "saledate", "transaction date"],
    "customer": ["customer name", "customername", "client", "buyer", "customer_name"],
    "segment": ["customer segment", "customersegment", "market", "segment type"],
    "city": ["city name", "town", "location city"],
    "state": ["state name", "province", "region state"],
    "product": ["product name", "productname", "item", "item name", "product_name"],
    "category": ["product category", "productcategory", "item category", "type"],
    "quantity": ["qty", "quant", "units", "items count", "number of items"],
    "price": ["unit price", "unitprice", "rate", "cost per item", "price per unit"],
    "discount": ["disc", "discount rate", "discount percent", "promo discount"],
    "revenue": ["sales", "sales revenue", "turnover", "total price", "amount"],
    "profit": ["earnings", "net profit", "gain", "net profit margin"],
    "region": ["sales region", "area", "zone", "territory"]
}

def analyze_dataset(file_path: str) -> Dict[str, Any]:
    """Analyzes a CSV or Excel file and returns metadata, issue counts, and suggested column mapping."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(file_path)
    elif ext in [".xls", ".xlsx"]:
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload CSV or Excel.")

    original_cols = list(df.columns)
    mapped_cols, missing_cols = auto_map_columns(original_cols)

    # Temporary dataframe with mapped columns for statistics
    temp_df = df.rename(columns=mapped_cols)

    total_rows = len(df)
    total_cells = total_rows * len(REQUIRED_COLUMNS)
    
    # Check duplicates
    duplicate_count = int(df.duplicated().sum())

    # Missing values count per required column
    missing_counts = {}
    total_missing = 0
    for req_col in REQUIRED_COLUMNS:
        if req_col in temp_df.columns:
            count = int(temp_df[req_col].isnull().sum())
            missing_counts[req_col] = count
            total_missing += count
        else:
            missing_counts[req_col] = total_rows  # Column is completely missing
            total_missing += total_rows

    # Outlier Detection (using IQR method) on key numeric columns if mapped
    outlier_counts = {}
    total_outliers = 0
    for num_col in ["revenue", "profit", "quantity", "price"]:
        if num_col in temp_df.columns:
            series = pd.to_numeric(temp_df[num_col], errors="coerce").dropna()
            if len(series) > 4:
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers = series[(series < lower_bound) | (series > upper_bound)]
                count = int(len(outliers))
                outlier_counts[num_col] = count
                total_outliers += count
            else:
                outlier_counts[num_col] = 0
        else:
            outlier_counts[num_col] = 0

    # Calculate Data Quality Score
    # Deduct points for duplicates, missing values, and statistical outliers
    total_issues = duplicate_count + total_missing + total_outliers
    quality_score = 100.0
    if total_cells > 0:
        quality_score = max(0.0, round(100.0 - (total_issues / total_cells * 100.0), 2))

    # Sample rows for UI preview (max 10 rows)
    preview_df = df.head(10).replace({np.nan: None})
    preview_data = preview_df.to_dict(orient="records")

    return {
        "total_rows": total_rows,
        "total_columns": len(original_cols),
        "duplicate_count": duplicate_count,
        "missing_counts": missing_counts,
        "outlier_counts": outlier_counts,
        "quality_score": quality_score,
        "columns": original_cols,
        "mapped_columns": mapped_cols,
        "missing_required_columns": missing_cols,
        "preview": preview_data,
        "file_path": file_path
    }

def auto_map_columns(columns: list) -> Tuple[Dict[str, str], list]:
    """Tries to automatically map raw columns to required schema columns."""
    mapped = {}
    missing = []
    
    normalized_cols = {c.strip().lower(): c for c in columns}
    
    for req_col in REQUIRED_COLUMNS:
        found = False
        if req_col in normalized_cols:
            mapped[normalized_cols[req_col]] = req_col
            found = True
        else:
            suggestions = COLUMN_MAPPING_SUGGESTIONS.get(req_col, [])
            for sug in suggestions:
                if sug in normalized_cols:
                    mapped[normalized_cols[sug]] = req_col
                    found = True
                    break
        
        if not found:
            missing.append(req_col)
            
    return mapped, missing

def clean_and_load_dataframe(
    file_path: str, 
    col_mapping: Dict[str, str], 
    fill_missing: bool = True, 
    remove_duplicates: bool = True
) -> pd.DataFrame:
    """Cleans a DataFrame based on custom options and matches the required schema."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(file_path)
    elif ext in [".xls", ".xlsx"]:
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format.")

    # 1. Rename columns according to mapping
    actual_mapping = {k: v for k, v in col_mapping.items() if k in df.columns}
    df = df.rename(columns=actual_mapping)

    # 2. Add missing required columns
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            if col in ["quantity", "discount", "revenue", "profit", "price"]:
                df[col] = 0.0
            elif col == "order_date":
                df[col] = pd.Timestamp.now().strftime("%Y-%m-%d")
            else:
                df[col] = "Unknown"

    # 3. Deduplication
    if remove_duplicates:
        df = df.drop_duplicates()

    # 4. Fill missing values & clean fields
    if fill_missing:
        # Strings
        cat_cols = ["customer", "segment", "city", "state", "product", "category", "region"]
        for col in cat_cols:
            df[col] = df[col].fillna("Unknown").astype(str).str.strip()

        # Numerics
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0).astype(float)
        df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0.0).astype(float)
        
        # Enforce validation: no negative values, discount <= 100%
        df["quantity"] = np.where(df["quantity"] <= 0, 1, df["quantity"])
        df["price"] = np.where(df["price"] < 0.0, 0.0, df["price"])
        df["discount"] = np.where((df["discount"] < 0.0) | (df["discount"] > 1.0), 0.0, df["discount"])

        # Recalculate calculations formulas
        df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0.0)
        calc_revenue = df["quantity"] * df["price"] * (1 - df["discount"])
        df["revenue"] = np.where(df["revenue"] == 0, calc_revenue, df["revenue"])
        df["revenue"] = df["revenue"].round(2)

        df["profit"] = pd.to_numeric(df["profit"], errors="coerce").fillna(0.0)
        calc_profit = df["revenue"] * 0.25  # default 25% margin estimate
        df["profit"] = np.where(df["profit"] == 0, calc_profit, df["profit"])
        df["profit"] = df["profit"].round(2)

    # 5. Dates normalization
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["order_date"] = df["order_date"].fillna(pd.Timestamp.now())
    df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")

    # Limit to required columns
    df = df[REQUIRED_COLUMNS]

    return df
