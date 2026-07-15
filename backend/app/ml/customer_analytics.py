import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from ..database.models import Sale, Customer

def calculate_rfm_segments(db: Session, dataset_id: str) -> list:
    """Calculates RFM (Recency, Frequency, Monetary) value cohorts for each customer."""
    # 1. Fetch raw metrics
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

    # Convert to dataframe
    df = pd.DataFrame(query, columns=["customer_id", "name", "segment", "last_order", "frequency", "monetary"])
    
    # Calculate Recency in days relative to latest order date in active dataset
    latest_order_date = pd.to_datetime(df["last_order"]).max()
    df["last_order"] = pd.to_datetime(df["last_order"])
    df["recency"] = (latest_order_date - df["last_order"]).dt.days

    # Scoring on 1-5 scale using quantiles (fallback to simple ranks if duplicates exist)
    try:
        df["r_score"] = pd.qcut(df["recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
        df["f_score"] = pd.qcut(df["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
        df["m_score"] = pd.qcut(df["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    except Exception:
        df["r_score"] = 3
        df["f_score"] = 3
        df["m_score"] = 3

    # Segment mapping
    segments = []
    for _, row in df.iterrows():
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        
        # Mapping rules
        if r >= 4 and f >= 4 and m >= 4:
            segment_name = "Champions"
        elif r >= 3 and f >= 3:
            segment_name = "Loyal Partners"
        elif r <= 2 and f >= 3:
            segment_name = "At-Risk Accounts"
        elif r <= 1:
            segment_name = "Hibernating"
        else:
            segment_name = "Standard Portfolio"

        segments.append({
            "customer_id": int(row["customer_id"]),
            "name": row["name"],
            "segment": row["segment"],
            "recency": int(row["recency"]),
            "frequency": int(row["frequency"]),
            "monetary": float(row["monetary"]),
            "cohort": segment_name
        })

    return segments

def predict_customer_churn(db: Session, dataset_id: str) -> list:
    """Predicts user inactivity/churn risk using interval statistics on order dates."""
    # Fetch all orders per customer sorted chronologically
    sales_query = db.query(
        Sale.customer_id,
        Customer.name,
        Sale.order_date
    ).join(Customer).filter(Sale.dataset_id == dataset_id).order_by(Sale.customer_id, Sale.order_date.asc()).all()

    if not sales_query:
        return []

    # Group order dates by customer
    cust_orders = {}
    for c_id, name, o_date in sales_query:
        if c_id not in cust_orders:
            cust_orders[c_id] = {"name": name, "dates": []}
        cust_orders[c_id]["dates"].append(pd.to_datetime(o_date))

    # Determine latest date in system for recency baseline
    latest_order_date = db.query(func.max(Sale.order_date)).filter(Sale.dataset_id == dataset_id).scalar()
    latest_order_date = pd.to_datetime(latest_order_date) if latest_order_date else pd.Timestamp.now()

    churn_profile = []
    for c_id, info in cust_orders.items():
        name = info["name"]
        dates = info["dates"]
        
        # Recency (days since last order)
        last_order = dates[-1]
        recency = (latest_order_date - last_order).days

        # Interval stats (difference between sequential dates)
        if len(dates) >= 3:
            diffs = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
            mean_gap = np.mean(diffs)
            std_gap = np.std(diffs) if len(diffs) > 1 else 10.0
            
            # 95% threshold calculation
            threshold = mean_gap + 1.96 * std_gap
            
            if recency > threshold:
                risk = "High"
            elif recency > mean_gap:
                risk = "Medium"
            else:
                risk = "Low"
        else:
            # Fallback for small orders: baseline default 90 days gap
            mean_gap = 90.0
            if recency > 180:
                risk = "High"
            elif recency > 90:
                risk = "Medium"
            else:
                risk = "Low"

        churn_profile.append({
            "customer_id": c_id,
            "name": name,
            "recency": recency,
            "avg_days_between_orders": round(float(mean_gap), 1),
            "churn_risk": risk
        })

    return churn_profile
