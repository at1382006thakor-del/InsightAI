import os
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
import joblib
from sklearn.ensemble import IsolationForest
from typing import Dict, Any, List

from ..database.models import Sale, Customer, Product

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

def train_anomaly_detector(db: Session, dataset_id: str) -> Dict[str, Any]:
    """Trains an Isolation Forest model to detect transaction anomalies and outliers."""
    query = db.query(
        Sale.sale_id,
        Sale.revenue,
        Sale.profit,
        Sale.quantity,
        Sale.discount
    ).filter(Sale.dataset_id == dataset_id).all()

    if len(query) < 20:
        return {"success": False, "message": "Insufficient transactions to train anomaly detector."}

    df = pd.DataFrame(query, columns=["sale_id", "revenue", "profit", "quantity", "discount"])
    X = df[["revenue", "profit", "quantity", "discount"]].copy()

    # Fit Isolation Forest (contamination represents expected % of outliers, e.g. 1%)
    detector = IsolationForest(contamination=0.01, random_state=42)
    detector.fit(X)

    model_path = os.path.join(MODEL_DIR, f"anomaly_detector_{dataset_id}.joblib")
    joblib.dump(detector, model_path)

    # Count outliers predicted on training data
    preds = detector.predict(X)
    outliers_count = int(np.sum(preds == -1))

    return {
        "success": True,
        "outliers_found": outliers_count,
        "contamination": 0.01
    }

def detect_transaction_anomalies(db: Session, dataset_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Loads Isolation Forest model and returns transactional outliers flagged as anomalous."""
    model_path = os.path.join(MODEL_DIR, f"anomaly_detector_{dataset_id}.joblib")
    if not os.path.exists(model_path):
        train_res = train_anomaly_detector(db, dataset_id)
        if not train_res.get("success", False):
            return []

    detector = joblib.load(model_path)

    # Query details to present useful outlier details on UI
    query = db.query(
        Sale.sale_id,
        Sale.order_date,
        Customer.name.label("customer"),
        Product.name.label("product"),
        Sale.revenue,
        Sale.profit,
        Sale.quantity,
        Sale.discount,
        Sale.region
    ).join(Customer).join(Product).filter(Sale.dataset_id == dataset_id).all()

    if not query:
        return []

    df = pd.DataFrame(query, columns=[
        "sale_id", "order_date", "customer", "product", 
        "revenue", "profit", "quantity", "discount", "region"
    ])

    X = df[["revenue", "profit", "quantity", "discount"]].copy()
    
    # Predict flags: -1 is outlier, 1 is normal
    df["flag"] = detector.predict(X)
    df["score"] = detector.decision_function(X) # lower score means more anomalous

    anomalies_df = df[df["flag"] == -1].sort_values("score").head(limit)

    results = []
    for _, row in anomalies_df.iterrows():
        results.append({
            "sale_id": int(row["sale_id"]),
            "order_date": row["order_date"].strftime("%Y-%m-%d"),
            "customer": row["customer"],
            "product": row["product"],
            "revenue": float(row["revenue"]),
            "profit": float(row["profit"]),
            "quantity": int(row["quantity"]),
            "discount": float(row["discount"]),
            "region": row["region"],
            "anomaly_score": round(float(row["score"]), 4)
        })

    return results
