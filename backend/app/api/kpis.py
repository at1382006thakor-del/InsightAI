from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

from ..database.connection import get_db
from ..database.models import Sale, Product, Customer, User
from ..repositories.dataset_repository import DatasetRepository
from ..services.auth_service import get_current_user
from .dashboard import get_active_dataset_id

router = APIRouter(prefix="/kpis", tags=["KPI Monitoring"])

MONTHLY_REVENUE_TARGET = 150000.0

@router.get("/metrics")
def get_kpi_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset_id = get_active_dataset_id(db)

    # Scoped stats
    overall_stats = db.query(
        func.sum(Sale.revenue).label("revenue"),
        func.sum(Sale.profit).label("profit"),
        func.count(Sale.sale_id).label("orders"),
        func.count(distinct(Sale.customer_id)).label("customers")
    ).filter(Sale.dataset_id == dataset_id).first()

    total_revenue = float(overall_stats.revenue or 0.0)
    total_profit = float(overall_stats.profit or 0.0)
    total_orders = int(overall_stats.orders or 0)
    total_customers = int(overall_stats.customers or 0)

    # 1. Profit Margin %
    profit_margin = round((total_profit / total_revenue * 100), 2) if total_revenue > 0 else 0.0

    # 2. Customer Retention Rate %
    cust_orders = db.query(Sale.customer_id, func.count(Sale.sale_id).label("order_count")).filter(
        Sale.dataset_id == dataset_id
    ).group_by(Sale.customer_id).subquery()
    
    repeat_customers = db.query(func.count(cust_orders.c.customer_id)).filter(cust_orders.c.order_count > 1).scalar()
    retention_rate = round((repeat_customers / total_customers * 100), 2) if total_customers > 0 else 0.0

    # 3. Top Category
    top_cat_row = db.query(
        Product.category,
        func.sum(Sale.revenue).label("revenue")
    ).join(Sale).filter(Sale.dataset_id == dataset_id).group_by(Product.category).order_by(func.sum(Sale.revenue).desc()).first()
    top_category = top_cat_row[0] if top_cat_row else "N/A"

    # 4. Top Product
    top_prod_row = db.query(
        Product.name,
        func.sum(Sale.revenue).label("revenue")
    ).join(Sale).filter(Sale.dataset_id == dataset_id).group_by(Product.name).order_by(func.sum(Sale.revenue).desc()).first()
    top_product = top_prod_row[0] if top_prod_row else "N/A"

    # 5. Best/Worst Region
    regional_sales = db.query(
        Sale.region,
        func.sum(Sale.revenue).label("revenue")
    ).filter(Sale.dataset_id == dataset_id).group_by(Sale.region).order_by(func.sum(Sale.revenue).desc()).all()
    
    best_region = regional_sales[0][0] if len(regional_sales) > 0 else "N/A"
    worst_region = regional_sales[-1][0] if len(regional_sales) > 0 else "N/A"

    # 6. Monthly Growth
    max_date_row = db.query(func.max(Sale.order_date)).filter(Sale.dataset_id == dataset_id).first()
    if max_date_row and max_date_row[0]:
        latest_date = max_date_row[0]
        start_current = date(latest_date.year, latest_date.month, 1)
        if latest_date.month == 1:
            start_prev = date(latest_date.year - 1, 12, 1)
            end_prev = date(latest_date.year - 1, 12, 31)
        else:
            start_prev = date(latest_date.year, latest_date.month - 1, 1)
            end_prev = start_current - timedelta(days=1)
            
        current_month_sales = float(db.query(func.sum(Sale.revenue)).filter(
            Sale.dataset_id == dataset_id, Sale.order_date >= start_current, Sale.order_date <= latest_date
        ).scalar() or 0.0)
        
        prev_month_sales = float(db.query(func.sum(Sale.revenue)).filter(
            Sale.dataset_id == dataset_id, Sale.order_date >= start_prev, Sale.order_date <= end_prev
        ).scalar() or 0.0)
        
        monthly_growth = round(((current_month_sales - prev_month_sales) / prev_month_sales * 100), 2) if prev_month_sales > 0 else 0.0
    else:
        monthly_growth = 0.0

    # 7. Targets monthly achievements
    monthly_sales_history = db.query(
        func.strftime("%Y-%m", Sale.order_date).label("month"),
        func.sum(Sale.revenue).label("revenue")
    ).filter(Sale.dataset_id == dataset_id).group_by(func.strftime("%Y-%m", Sale.order_date)).order_by("month").all()

    target_history = []
    for month_str, revenue in monthly_sales_history:
        target_history.append({
            "month": month_str,
            "actual": round(revenue or 0.0, 2),
            "target": MONTHLY_REVENUE_TARGET,
            "achievement_rate": round(((revenue or 0.0) / MONTHLY_REVENUE_TARGET * 100), 2)
        })

    return {
        "metrics": {
            "revenue": {
                "current": total_revenue,
                "target": MONTHLY_REVENUE_TARGET * 12,
                "status": "on_track" if total_revenue > (MONTHLY_REVENUE_TARGET * 6) else "needs_attention"
            },
            "profit_margin": {
                "value": profit_margin,
                "target": 30.0,
                "status": "healthy" if profit_margin >= 25.0 else "warning"
            },
            "customer_retention": {
                "value": retention_rate,
                "target": 50.0,
                "status": "healthy" if retention_rate >= 40.0 else "warning"
            },
            "monthly_growth": {
                "value": monthly_growth,
                "target": 5.0,
                "status": "healthy" if monthly_growth > 0 else "decline"
            }
        },
        "highlights": {
            "top_product": top_product,
            "top_category": top_category,
            "best_region": best_region,
            "worst_region": worst_region
        },
        "target_history": target_history
    }
