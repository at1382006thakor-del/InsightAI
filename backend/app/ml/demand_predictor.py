import os
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func
import joblib
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_percentage_error
from typing import Dict, Any, List

from ..database.models import Sale, Product

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

def prepare_demand_series(db: Session, dataset_id: str, category: str = None) -> pd.DataFrame:
    """Prepares demand series by aggregating quantity sold monthly from active dataset."""
    query = db.query(Sale.order_date, Sale.quantity).filter(Sale.dataset_id == dataset_id)
    if category:
        query = query.join(Product).filter(Product.category == category)

    results = query.all()
    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results, columns=["order_date", "quantity"])
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["month"] = df["order_date"].dt.to_period("M")
    
    monthly_df = df.groupby("month")["quantity"].sum().reset_index()
    monthly_df["month"] = monthly_df["month"].dt.to_timestamp()
    monthly_df = monthly_df.sort_values("month").reset_index(drop=True)
    
    return monthly_df

def build_demand_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["lag_1"] = df["quantity"].shift(1)
    df["lag_2"] = df["quantity"].shift(2)
    df["rolling_mean_3"] = df["quantity"].shift(1).rolling(window=3).mean()
    df["month_number"] = df["month"].dt.month
    return df.dropna().reset_index(drop=True)

def train_demand_model(db: Session, dataset_id: str, category: str = None) -> Dict[str, Any]:
    """Trains a demand model to forecast monthly quantity requested."""
    df = prepare_demand_series(db, dataset_id, category)
    if len(df) < 6:
        return {"success": False, "message": "Insufficient records to forecast demand."}

    df_clean = build_demand_features(df)
    if len(df_clean) < 2:
        return {"success": False, "message": "Insufficient features records."}

    X = df_clean.drop(columns=["month", "quantity"])
    y = df_clean["quantity"]

    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)

    # Evaluate residuals standard dev
    train_preds = model.predict(X)
    mape = float(mean_absolute_percentage_error(y, train_preds))

    model_name = f"demand_rf_{category or 'all'}_{dataset_id}.joblib"
    meta_name = f"demand_meta_{category or 'all'}_{dataset_id}.joblib"

    joblib.dump(model, os.path.join(MODEL_DIR, model_name))
    joblib.dump({
        "mape": mape * 100,
        "features": list(X.columns),
        "last_data": df.tail(10).to_dict(orient="records")
    }, os.path.join(MODEL_DIR, meta_name))

    return {
        "success": True,
        "mape": mape * 100,
        "features": list(X.columns)
    }

def run_demand_forecast(db: Session, dataset_id: str, months_ahead: int = 6, category: str = None) -> List[Dict[str, Any]]:
    """Loads model and returns future units demanded quantities predictions."""
    model_name = f"demand_rf_{category or 'all'}_{dataset_id}.joblib"
    meta_name = f"demand_meta_{category or 'all'}_{dataset_id}.joblib"
    model_path = os.path.join(MODEL_DIR, model_name)
    meta_path = os.path.join(MODEL_DIR, meta_name)

    if not os.path.exists(model_path):
        train_res = train_demand_model(db, dataset_id, category)
        if not train_res.get("success", False):
            return []

    model = joblib.load(model_path)
    meta = joblib.load(meta_path)

    features = meta["features"]
    last_data = meta["last_data"]

    hist_df = pd.DataFrame(last_data)
    hist_df["month"] = pd.to_datetime(hist_df["month"])

    predictions = []
    for i in range(months_ahead):
        last_date = hist_df["month"].iloc[-1]
        next_date = last_date + relativedelta(months=1)

        lag_1 = hist_df["quantity"].iloc[-1]
        lag_2 = hist_df["quantity"].iloc[-2] if len(hist_df) > 1 else lag_1
        rolling_mean_3 = hist_df["quantity"].iloc[-3:].mean() if len(hist_df) >= 3 else hist_df["quantity"].mean()

        row_dict = {
            "lag_1": lag_1,
            "lag_2": lag_2,
            "rolling_mean_3": rolling_mean_3,
            "month_number": next_date.month
        }

        feat_vector = [row_dict[f] for f in features]
        feat_df = pd.DataFrame([feat_vector], columns=features)
        
        pred_qty = max(0.0, round(float(model.predict(feat_df)[0]), 1))
        
        new_row = pd.DataFrame([{"month": next_date, "quantity": pred_qty}])
        hist_df = pd.concat([hist_df, new_row]).reset_index(drop=True)

        predictions.append({
            "month": next_date.strftime("%Y-%m"),
            "predicted_quantity": pred_qty
        })

    return predictions
