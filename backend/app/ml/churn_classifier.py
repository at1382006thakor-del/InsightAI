import os
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from typing import Dict, Any, List

from ..database.models import Sale, Customer

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

def train_churn_model(db: Session, dataset_id: str) -> Dict[str, Any]:
    """Trains a Random Forest Classifier to predict customer churn probability and persists it."""
    # 1. Fetch raw transaction metrics and tenure per customer
    query = db.query(
        Customer.customer_id,
        func.min(Sale.order_date).label("first_order"),
        func.max(Sale.order_date).label("last_order"),
        func.count(Sale.sale_id).label("frequency"),
        func.sum(Sale.revenue).label("monetary"),
        func.avg(Sale.discount).label("avg_discount")
    ).join(Sale).filter(Sale.dataset_id == dataset_id).group_by(Customer.customer_id).all()

    if len(query) < 15:
        return {
            "success": False,
            "message": f"Insufficient customers count ({len(query)}). Need at least 15 to train churn model."
        }

    # Convert to dataframe
    df = pd.DataFrame(query, columns=["customer_id", "first_order", "last_order", "frequency", "monetary", "avg_discount"])
    
    # Calculate days relative to latest order
    latest_order_date = pd.to_datetime(df["last_order"]).max()
    df["first_order"] = pd.to_datetime(df["first_order"])
    df["last_order"] = pd.to_datetime(df["last_order"])
    
    df["recency"] = (latest_order_date - df["last_order"]).dt.days
    df["tenure"] = (df["last_order"] - df["first_order"]).dt.days
    df["tenure"] = np.where(df["tenure"] <= 0, 1, df["tenure"]) # minimum 1 day tenure

    # Label target: Churned = 1 if recency > 180 days, else 0 (Lost customer threshold)
    df["churned"] = np.where(df["recency"] > 180, 1, 0)

    # Scenarios check: make sure we have both churned and active classes
    class_counts = df["churned"].value_counts()
    if len(class_counts) < 2:
        # Fallback synthetic label variation for testing/development if no one has churned yet
        # Label 30% of highest recency values as synthetic churn
        threshold = df["recency"].quantile(0.70)
        df["churned"] = np.where(df["recency"] >= threshold, 1, 0)

    features = ["frequency", "monetary", "avg_discount", "tenure", "recency"]
    X = df[features].copy()
    y = df["churned"]

    # 2. Scaling
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 3. Train-Test Split & Random Forest fit
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.25, random_state=42, stratify=y)
    
    model = RandomForestClassifier(n_estimators=80, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    # 4. Evaluation Metrics
    preds = model.predict(X_test)
    accuracy = float(accuracy_score(y_test, preds))
    precision = float(precision_score(y_test, preds, zero_division=0))
    recall = float(recall_score(y_test, preds, zero_division=0))
    f1 = float(f1_score(y_test, preds, zero_division=0))

    # Persist model and scaler
    model_path = os.path.join(MODEL_DIR, f"churn_classifier_{dataset_id}.joblib")
    scaler_path = os.path.join(MODEL_DIR, f"churn_scaler_{dataset_id}.joblib")
    
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    return {
        "success": True,
        "accuracy": accuracy * 100,
        "precision": precision * 100,
        "recall": recall * 100,
        "f1_score": f1 * 100,
        "features": features
    }

def predict_customer_churn_probabilities(db: Session, dataset_id: str) -> List[Dict[str, Any]]:
    """Loads Classifier and returns predictive probabilities of churn per customer."""
    model_path = os.path.join(MODEL_DIR, f"churn_classifier_{dataset_id}.joblib")
    scaler_path = os.path.join(MODEL_DIR, f"churn_scaler_{dataset_id}.joblib")

    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        train_res = train_churn_model(db, dataset_id)
        if not train_res.get("success", False):
            return []

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    query = db.query(
        Customer.customer_id,
        Customer.name,
        func.min(Sale.order_date).label("first_order"),
        func.max(Sale.order_date).label("last_order"),
        func.count(Sale.sale_id).label("frequency"),
        func.sum(Sale.revenue).label("monetary"),
        func.avg(Sale.discount).label("avg_discount")
    ).join(Sale).filter(Sale.dataset_id == dataset_id).group_by(Customer.customer_id).all()

    if not query:
        return []

    df = pd.DataFrame(query, columns=["customer_id", "name", "first_order", "last_order", "frequency", "monetary", "avg_discount"])
    
    latest_order_date = pd.to_datetime(df["last_order"]).max()
    df["first_order"] = pd.to_datetime(df["first_order"])
    df["last_order"] = pd.to_datetime(df["last_order"])
    
    df["recency"] = (latest_order_date - df["last_order"]).dt.days
    df["tenure"] = (df["last_order"] - df["first_order"]).dt.days
    df["tenure"] = np.where(df["tenure"] <= 0, 1, df["tenure"])

    X = df[["frequency", "monetary", "avg_discount", "tenure", "recency"]].copy()
    X_scaled = scaler.transform(X)
    
    # Predict Churn probability (class 1 index)
    probs = model.predict_proba(X_scaled)[:, 1]
    
    results = []
    for idx, row in df.iterrows():
        prob = float(probs[idx])
        risk = "Low"
        if prob >= 0.70:
            risk = "High"
        elif prob >= 0.40:
            risk = "Medium"

        results.append({
            "customer_id": int(row["customer_id"]),
            "name": row["name"],
            "recency": int(row["recency"]),
            "tenure": int(row["tenure"]),
            "churn_probability": round(prob * 100, 2),
            "churn_risk": risk
        })

    return results
