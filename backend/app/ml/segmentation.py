import os
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from typing import Dict, Any, List

from ..database.models import Sale, Customer

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

def train_segmentation_model(db: Session, dataset_id: str) -> Dict[str, Any]:
    """Trains a K-Means clustering model on customer RFM metrics and persists the model and scaler."""
    # 1. Fetch raw metrics
    query = db.query(
        Customer.customer_id,
        func.max(Sale.order_date).label("last_order"),
        func.count(Sale.sale_id).label("frequency"),
        func.sum(Sale.revenue).label("monetary")
    ).join(Sale).filter(Sale.dataset_id == dataset_id).group_by(Customer.customer_id).all()

    if len(query) < 10:
        return {
            "success": False,
            "message": f"Insufficient customers ({len(query)} found). Need at least 10 customers to segment."
        }

    # Convert to dataframe
    df = pd.DataFrame(query, columns=["customer_id", "last_order", "frequency", "monetary"])
    
    # Recency in days
    latest_date = pd.to_datetime(df["last_order"]).max()
    df["last_order"] = pd.to_datetime(df["last_order"])
    df["recency"] = (latest_date - df["last_order"]).dt.days

    # Features for clustering
    features = ["recency", "frequency", "monetary"]
    X = df[features].copy()

    # 2. Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 3. Fit K-Means
    k = 4  # Standard segment groups: Champions, Loyal, At-Risk, Lost
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(X_scaled)

    # Evaluate using Silhouette Score
    labels = kmeans.labels_
    score = float(silhouette_score(X_scaled, labels)) if len(np.unique(labels)) > 1 else 0.0

    # Persist scaler and model
    model_path = os.path.join(MODEL_DIR, f"kmeans_segmentation_{dataset_id}.joblib")
    scaler_path = os.path.join(MODEL_DIR, f"kmeans_scaler_{dataset_id}.joblib")
    
    joblib.dump(kmeans, model_path)
    joblib.dump(scaler, scaler_path)

    # Analyze Cluster Centroids
    centroids = scaler.inverse_transform(kmeans.cluster_centers_)
    cluster_profiles = []
    for i in range(k):
        cluster_profiles.append({
            "cluster_id": i,
            "avg_recency": float(centroids[i][0]),
            "avg_frequency": float(centroids[i][1]),
            "avg_monetary": float(centroids[i][2])
        })

    return {
        "success": True,
        "silhouette_score": score,
        "cluster_profiles": cluster_profiles,
        "num_customers": len(df)
    }

def predict_customer_segments(db: Session, dataset_id: str) -> List[Dict[str, Any]]:
    """Loads K-Means model and scaler to assign segments to all customers."""
    model_path = os.path.join(MODEL_DIR, f"kmeans_segmentation_{dataset_id}.joblib")
    scaler_path = os.path.join(MODEL_DIR, f"kmeans_scaler_{dataset_id}.joblib")

    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        train_res = train_segmentation_model(db, dataset_id)
        if not train_res.get("success", False):
            return []

    kmeans = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    query = db.query(
        Customer.customer_id,
        Customer.name,
        Customer.segment,
        func.max(Sale.order_date).label("last_order"),
        func.count(Sale.sale_id).label("frequency"),
        func.sum(Sale.revenue).label("monetary")
    ).join(Sale).filter(Sale.dataset_id == dataset_id).group_by(Customer.customer_id).all()

    if not query:
        return []

    df = pd.DataFrame(query, columns=["customer_id", "name", "market_segment", "last_order", "frequency", "monetary"])
    
    latest_date = pd.to_datetime(df["last_order"]).max()
    df["last_order"] = pd.to_datetime(df["last_order"])
    df["recency"] = (latest_date - df["last_order"]).dt.days

    X = df[["recency", "frequency", "monetary"]].copy()
    X_scaled = scaler.transform(X)
    
    df["cluster"] = kmeans.predict(X_scaled)

    # Map clusters to descriptive names based on centroids monetary and recency values
    centroids = scaler.inverse_transform(kmeans.cluster_centers_)
    cluster_monetary = {i: centroids[i][2] for i in range(len(centroids))}
    cluster_recency = {i: centroids[i][0] for i in range(len(centroids))}

    # Order cluster ids by average monetary value (high to low)
    sorted_by_monetary = sorted(cluster_monetary.items(), key=lambda item: item[1], reverse=True)
    
    cluster_labels = {}
    for rank, (cluster_id, _) in enumerate(sorted_by_monetary):
        if rank == 0:
            cluster_labels[cluster_id] = "High-Value Champions"
        elif rank == 1:
            cluster_labels[cluster_id] = "Loyal Accounts"
        elif rank == 2:
            # Check recency for remaining
            if cluster_recency[cluster_id] > 180:
                cluster_labels[cluster_id] = "At-Risk/Slipping"
            else:
                cluster_labels[cluster_id] = "Average Retail"
        else:
            cluster_labels[cluster_id] = "Low-Value Inactive"

    results = []
    for _, row in df.iterrows():
        c_id = row["cluster"]
        results.append({
            "customer_id": int(row["customer_id"]),
            "name": row["name"],
            "market_segment": row["market_segment"],
            "recency": int(row["recency"]),
            "frequency": int(row["frequency"]),
            "monetary": float(row["monetary"]),
            "cluster_id": int(c_id),
            "segment_label": cluster_labels.get(c_id, "Standard Portfolio")
        })

    return results
