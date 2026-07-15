from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

from ..database.connection import get_db
from ..database.models import Sale, Product, Customer, Notification, User
from ..repositories.dataset_repository import DatasetRepository
from ..repositories.sale_repository import SaleRepository
from ..schemas.dashboard import (
    SummaryMetrics, 
    TimeseriesDataPoint, 
    CategorySalesPoint, 
    RegionalSalesPoint,
    ProductPerformancePoint,
    CustomerPerformancePoint,
    NotificationResponse
)
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])

def get_active_dataset_id(db: Session) -> str:
    repo = DatasetRepository(db)
    active_ds = repo.get_active_dataset()
    if not active_ds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active datasets loaded. Please upload and clean a CSV or Excel dataset."
        )
    return active_ds.id

@router.get("/summary", response_model=SummaryMetrics)
def get_summary_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset_id = get_active_dataset_id(db)
    
    query = db.query(Sale).filter(Sale.dataset_id == dataset_id)
    
    if start_date:
        query = query.filter(Sale.order_date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        query = query.filter(Sale.order_date <= datetime.strptime(end_date, "%Y-%m-%d").date())
    if region:
        query = query.filter(Sale.region == region)

    stats = query.with_entities(
        func.sum(Sale.revenue).label("revenue"),
        func.sum(Sale.profit).label("profit"),
        func.count(Sale.sale_id).label("orders"),
        func.count(distinct(Sale.customer_id)).label("customers")
    ).first()

    total_revenue = float(stats.revenue or 0.0)
    total_profit = float(stats.profit or 0.0)
    total_orders = int(stats.orders or 0)
    total_customers = int(stats.customers or 0)
    average_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

    # Monthly comparison comparisons
    max_date_row = db.query(func.max(Sale.order_date)).filter(Sale.dataset_id == dataset_id).first()
    max_date = max_date_row[0] if max_date_row[0] else date.today()
    
    t30_start = max_date - timedelta(days=30)
    t60_start = max_date - timedelta(days=60)
    
    t30_rev_query = db.query(func.sum(Sale.revenue)).filter(
        Sale.dataset_id == dataset_id, Sale.order_date >= t30_start, Sale.order_date <= max_date
    )
    t60_rev_query = db.query(func.sum(Sale.revenue)).filter(
        Sale.dataset_id == dataset_id, Sale.order_date >= t60_start, Sale.order_date < t30_start
    )
    
    if region:
        t30_rev_query = t30_rev_query.filter(Sale.region == region)
        t60_rev_query = t60_rev_query.filter(Sale.region == region)
        
    t30_rev = float(t30_rev_query.scalar() or 0.0)
    t60_rev = float(t60_rev_query.scalar() or 0.0)
    
    growth_percent = round(((t30_rev - t60_rev) / t60_rev * 100), 2) if t60_rev > 0 else 0.0

    # Category returns estimates
    sales_by_cat = db.query(Product.category, func.count(Sale.sale_id)).join(Sale).filter(
        Sale.dataset_id == dataset_id
    ).group_by(Product.category)
    
    if region:
        sales_by_cat = sales_by_cat.filter(Sale.region == region)
        
    rates = {"Apparel": 8.3, "Furniture": 4.5, "Technology": 2.1, "Office Supplies": 1.2}
    total_sales_count = 0
    weighted_returns = 0.0
    
    for cat, count in sales_by_cat.all():
        total_sales_count += count
        weighted_returns += count * rates.get(cat, 2.0)
        
    return_rate = round((weighted_returns / total_sales_count), 2) if total_sales_count > 0 else 2.5

    return SummaryMetrics(
        total_sales=total_revenue,
        total_revenue=total_revenue,
        total_profit=total_profit,
        total_orders=total_orders,
        total_customers=total_customers,
        average_order_value=average_order_value,
        growth_percent=growth_percent,
        return_rate=return_rate
    )

@router.get("/charts/timeseries", response_model=List[TimeseriesDataPoint])
def get_timeseries_chart(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset_id = get_active_dataset_id(db)
    query = db.query(
        Sale.order_date,
        func.sum(Sale.revenue).label("revenue"),
        func.sum(Sale.profit).label("profit"),
        func.count(Sale.sale_id).label("orders")
    ).filter(Sale.dataset_id == dataset_id).group_by(Sale.order_date)

    if start_date:
        query = query.filter(Sale.order_date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        query = query.filter(Sale.order_date <= datetime.strptime(end_date, "%Y-%m-%d").date())
    if region:
        query = query.filter(Sale.region == region)

    results = query.order_by(Sale.order_date).all()
    
    # If results are too dense, group them by month
    if len(results) > 60:
        monthly_data = {}
        for r_date, rev, prof, ords in results:
            month_str = r_date.strftime("%Y-%m")
            if month_str not in monthly_data:
                monthly_data[month_str] = {"revenue": 0.0, "profit": 0.0, "orders": 0}
            monthly_data[month_str]["revenue"] += float(rev)
            monthly_data[month_str]["profit"] += float(prof)
            monthly_data[month_str]["orders"] += int(ords)
            
        return [
            TimeseriesDataPoint(
                date=k,
                revenue=round(v["revenue"], 2),
                profit=round(v["profit"], 2),
                orders=v["orders"]
            ) for k, v in sorted(monthly_data.items())
        ]

    return [
        TimeseriesDataPoint(
            date=r_date.strftime("%Y-%m-%d"),
            revenue=round(rev, 2),
            profit=round(prof, 2),
            orders=ords
        ) for r_date, rev, prof, ords in results
    ]

@router.get("/charts/category", response_model=List[CategorySalesPoint])
def get_category_sales(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset_id = get_active_dataset_id(db)
    query = db.query(
        Product.category,
        func.sum(Sale.revenue).label("revenue"),
        func.sum(Sale.profit).label("profit"),
        func.sum(Sale.quantity).label("quantity")
    ).join(Sale).filter(Sale.dataset_id == dataset_id).group_by(Product.category)

    if start_date:
        query = query.filter(Sale.order_date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        query = query.filter(Sale.order_date <= datetime.strptime(end_date, "%Y-%m-%d").date())
    if region:
        query = query.filter(Sale.region == region)

    results = query.all()
    return [
        CategorySalesPoint(
            category=cat,
            revenue=round(rev or 0.0, 2),
            profit=round(prof or 0.0, 2),
            quantity=int(qty or 0)
        ) for cat, rev, prof, qty in results
    ]

@router.get("/charts/regional", response_model=List[RegionalSalesPoint])
def get_regional_sales(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset_id = get_active_dataset_id(db)
    query = db.query(
        Sale.region,
        func.sum(Sale.revenue).label("revenue"),
        func.sum(Sale.profit).label("profit"),
        func.count(Sale.sale_id).label("orders")
    ).filter(Sale.dataset_id == dataset_id).group_by(Sale.region)

    if start_date:
        query = query.filter(Sale.order_date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        query = query.filter(Sale.order_date <= datetime.strptime(end_date, "%Y-%m-%d").date())

    results = query.all()
    return [
        RegionalSalesPoint(
            region=reg,
            revenue=round(rev or 0.0, 2),
            profit=round(prof or 0.0, 2),
            orders=ords
        ) for reg, rev, prof, ords in results
    ]

@router.get("/products/performance", response_model=List[ProductPerformancePoint])
def get_products_performance(
    limit: int = Query(10),
    sort_by: str = Query("revenue"),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset_id = get_active_dataset_id(db)
    query = db.query(
        Product.product_id,
        Product.name,
        Product.category,
        Product.stock,
        func.sum(Sale.revenue).label("revenue"),
        func.sum(Sale.profit).label("profit"),
        func.sum(Sale.quantity).label("quantity")
    ).join(Sale).filter(Sale.dataset_id == dataset_id).group_by(Product.product_id)

    if category:
        query = query.filter(Product.category == category)

    if sort_by == "profit":
        query = query.order_by(func.sum(Sale.profit).desc())
    elif sort_by == "quantity":
        query = query.order_by(func.sum(Sale.quantity).desc())
    else:
        query = query.order_by(func.sum(Sale.revenue).desc())

    results = query.limit(limit).all()
    return [
        ProductPerformancePoint(
            product_id=p_id,
            name=name,
            category=cat,
            stock=stock,
            revenue=round(rev or 0.0, 2),
            profit=round(prof or 0.0, 2),
            quantity=int(qty or 0)
        ) for p_id, name, cat, stock, rev, prof, qty in results
    ]

@router.get("/customers/performance", response_model=List[CustomerPerformancePoint])
def get_customers_performance(
    limit: int = Query(10),
    segment: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset_id = get_active_dataset_id(db)
    query = db.query(
        Customer.customer_id,
        Customer.name,
        Customer.city,
        Customer.state,
        Customer.segment,
        func.sum(Sale.revenue).label("revenue"),
        func.count(Sale.sale_id).label("orders")
    ).join(Sale).filter(Sale.dataset_id == dataset_id).group_by(Customer.customer_id)

    if segment:
        query = query.filter(Customer.segment == segment)

    query = query.order_by(func.sum(Sale.revenue).desc())
    results = query.limit(limit).all()
    
    return [
        CustomerPerformancePoint(
            customer_id=c_id,
            name=name,
            city=city,
            state=state,
            segment=segment,
            revenue=round(rev or 0.0, 2),
            orders=ords
        ) for c_id, name, city, state, segment, rev, ords in results
    ]

@router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(
    limit: int = Query(10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Auto-generate notifications for low stock dynamically to ensure fresh alerts
    repo = DatasetRepository(db)
    active_ds = repo.get_active_dataset()
    if active_ds:
        low_stock_products = db.query(Product).filter(
            Product.dataset_id == active_ds.id, Product.stock <= 25
        ).limit(3).all()
        
        for prod in low_stock_products:
            exists = db.query(Notification).filter(
                Notification.title == "Low Stock Warning",
                Notification.message.like(f"%{prod.name}%")
            ).first()
            if not exists:
                alert = Notification(
                    title="Low Stock Warning",
                    message=f"Product '{prod.name}' is running low on stock ({prod.stock} units left). Reorder recommended.",
                    type="warning"
                )
                db.add(alert)
                db.commit()

    results = db.query(Notification).order_by(Notification.created_at.desc()).limit(limit).all()
    return [
        NotificationResponse(
            id=n.id,
            title=n.title,
            message=n.message,
            type=n.type,
            created_at=n.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            is_read=n.is_read
        ) for n in results
    ]

@router.post("/notifications/read/{notification_id}")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    n = db.query(Notification).filter(Notification.id == notification_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.commit()
    return {"success": True}
