import os
import pandas as pd
import numpy as np
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_percentage_error, r2_score
import joblib
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Tuple, List, Dict, Any

from ..database.models import Sale, Product

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

def prepare_time_series_data(db: Session, dataset_id: str, region: str = None, category: str = None) -> pd.DataFrame:
    """Extracts historical sales data from active dataset in DB and aggregates by Month."""
    query = db.query(Sale.order_date, Sale.revenue).filter(Sale.dataset_id == dataset_id)
    
    if region:
        query = query.filter(Sale.region == region)
    if category:
        query = query.join(Product).filter(Product.category == category)
        
    results = query.all()
    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results, columns=["order_date", "revenue"])
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["month"] = df["order_date"].dt.to_period("M")
    
    monthly_df = df.groupby("month")["revenue"].sum().reset_index()
    monthly_df["month"] = monthly_df["month"].dt.to_timestamp()
    monthly_df = monthly_df.sort_values("month").reset_index(drop=True)
    
    return monthly_df

def build_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Engineers time-series features (Lags, rolling stats, month indicators)."""
    df = df.copy()
    
    # 1. Lags
    df["lag_1"] = df["revenue"].shift(1)
    df["lag_2"] = df["revenue"].shift(2)
    df["lag_3"] = df["revenue"].shift(3)
    df["lag_12"] = df["revenue"].shift(12)  # Yearly seasonality
    
    # 2. Rolling
    df["rolling_mean_3"] = df["revenue"].shift(1).rolling(window=3).mean()
    df["rolling_std_3"] = df["revenue"].shift(1).rolling(window=3).bold_std() if hasattr(pd.Series, 'bold_std') else df["revenue"].shift(1).rolling(window=3).std()
    
    # 3. Calendar
    df["month_number"] = df["month"].dt.month
    df["year"] = df["month"].dt.year
    
    df_clean = df.dropna().reset_index(drop=True)
    
    if len(df_clean) < 5:
        df = df.copy()
        df["lag_1"] = df["revenue"].shift(1)
        df["lag_2"] = df["revenue"].shift(2)
        df["rolling_mean_2"] = df["revenue"].shift(1).rolling(window=2).mean()
        df["month_number"] = df["month"].dt.month
        df["year"] = df["month"].dt.year
        df_clean = df.dropna().reset_index(drop=True)

    X = df_clean.drop(columns=["month", "revenue"])
    y = df_clean["revenue"]
    
    return df_clean, X, y

def train_forecaster(db: Session, dataset_id: str, model_type: str = "xgboost", region: str = None, category: str = None) -> Dict[str, Any]:
    """Trains forecasting model on active dataset."""
    monthly_df = prepare_time_series_data(db, dataset_id, region, category)
    
    if len(monthly_df) < 6:
        return {
            "success": False,
            "message": f"Insufficient historical data ({len(monthly_df)} months found). Need at least 6 months."
        }

    df_clean, X, y = build_features(monthly_df)
    
    if len(df_clean) < 3:
        return {
            "success": False,
            "message": "Insufficient feature-engineered records. Need longer sales history (at least 13 months)."
        }

    test_size = min(3, max(1, int(len(df_clean) * 0.2)))
    X_train, X_test = X.iloc[:-test_size], X.iloc[-test_size:]
    y_train, y_test = y.iloc[:-test_size], y.iloc[-test_size:]

    if model_type == "linear":
        model = Ridge(alpha=1.0)
    elif model_type == "random_forest":
        model = RandomForestRegressor(n_estimators=100, random_state=42)
    else:  # xgboost
        model = XGBRegressor(n_estimators=100, learning_rate=0.08, max_depth=4, random_state=42)

    model.fit(X_train, y_train)
    
    predictions = model.predict(X_test)
    mape = float(mean_absolute_percentage_error(y_test, predictions))
    r2 = float(r2_score(y_test, predictions))
    
    model.fit(X, y)
    
    # Standard deviation of residuals for confidence boundaries
    train_preds = model.predict(X)
    residuals = y - train_preds
    std_residual = float(np.std(residuals))

    # Serialize
    meta_name = f"meta_{model_type}_{region or 'all'}_{category or 'all'}_{dataset_id}.joblib"
    model_name = f"model_{model_type}_{region or 'all'}_{category or 'all'}_{dataset_id}.joblib"
    
    joblib.dump(model, os.path.join(MODEL_DIR, model_name))
    
    meta_data = {
        "mape": mape,
        "r2_score": r2,
        "std_residual": std_residual,
        "features": list(X.columns),
        "last_known_data": monthly_df.tail(15).to_dict(orient="records")
    }
    joblib.dump(meta_data, os.path.join(MODEL_DIR, meta_name))

    return {
        "success": True,
        "mape": mape * 100,
        "r2_score": max(0.0, r2),
        "model_type": model_type
    }

def run_predictions(db: Session, dataset_id: str, months_ahead: int = 6, model_type: str = "xgboost", region: str = None, category: str = None) -> List[Dict[str, Any]]:
    """Loads forecaster and projects sales paths."""
    model_name = f"model_{model_type}_{region or 'all'}_{category or 'all'}_{dataset_id}.joblib"
    meta_name = f"meta_{model_type}_{region or 'all'}_{category or 'all'}_{dataset_id}.joblib"
    model_path = os.path.join(MODEL_DIR, model_name)
    meta_path = os.path.join(MODEL_DIR, meta_name)

    if not os.path.exists(model_path):
        train_res = train_forecaster(db, dataset_id, model_type, region, category)
        if not train_res.get("success", False):
            return []

    model = joblib.load(model_path)
    meta = joblib.load(meta_path)
    
    features = meta["features"]
    std_res = meta["std_residual"]
    last_known = meta["last_known_data"]
    
    hist_df = pd.DataFrame(last_known)
    hist_df["month"] = pd.to_datetime(hist_df["month"])
    
    predictions = []
    for i in range(months_ahead):
        last_date = hist_df["month"].iloc[-1]
        next_date = last_date + relativedelta(months=1)
        
        lag_1 = hist_df["revenue"].iloc[-1]
        lag_2 = hist_df["revenue"].iloc[-2] if len(hist_df) > 1 else lag_1
        lag_3 = hist_df["revenue"].iloc[-3] if len(hist_df) > 2 else lag_1
        
        if len(hist_df) >= 12:
            lag_12 = hist_df["revenue"].iloc[-12]
        else:
            m = next_date.month
            baseline = hist_df["revenue"].mean()
            if m in [11, 12]:
                lag_12 = baseline * 1.25
            elif m in [1, 2]:
                lag_12 = baseline * 0.8
            else:
                lag_12 = baseline
                
        rolling_mean_3 = hist_df["revenue"].iloc[-3:].mean() if len(hist_df) >= 3 else hist_df["revenue"].mean()
        rolling_std_3 = hist_df["revenue"].iloc[-3:].std() if len(hist_df) >= 3 else 0.0
        
        row_dict = {
            "lag_1": lag_1,
            "lag_2": lag_2,
            "lag_3": lag_3,
            "lag_12": lag_12,
            "rolling_mean_3": rolling_mean_3,
            "rolling_std_3": rolling_std_3,
            "month_number": next_date.month,
            "year": next_date.year,
            "rolling_mean_2": hist_df["revenue"].iloc[-2:].mean() if len(hist_df) >= 2 else lag_1
        }
        
        feat_vector = [row_dict[f] for f in features]
        feat_df = pd.DataFrame([feat_vector], columns=features)
        
        predicted_rev = float(model.predict(feat_df)[0])
        predicted_rev = max(0.0, round(predicted_rev, 2))
        
        uncertainty_factor = np.sqrt(i + 1)
        lower_bound = max(0.0, round(predicted_rev - (1.96 * std_res * uncertainty_factor), 2))
        upper_bound = round(predicted_rev + (1.96 * std_res * uncertainty_factor), 2)
        
        new_row = pd.DataFrame([{"month": next_date, "revenue": predicted_rev}])
        hist_df = pd.concat([hist_df, new_row]).reset_index(drop=True)
        
        predictions.append({
            "month": next_date.strftime("%Y-%m"),
            "predicted_sales": predicted_rev,
            "confidence_lower": lower_bound,
            "confidence_upper": upper_bound
        })
        
    return predictions
