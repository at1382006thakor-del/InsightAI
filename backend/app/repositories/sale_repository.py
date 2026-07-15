from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from datetime import datetime, date, timedelta
from ..database.models import Sale, Product, Customer

class SaleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_scoped_sales_query(self, dataset_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None, region: Optional[str] = None):
        """Scopes sales query by active dataset and filters."""
        query = self.db.query(Sale).filter(Sale.dataset_id == dataset_id)
        if start_date:
            query = query.filter(Sale.order_date >= datetime.strptime(start_date, "%Y-%m-%d").date())
        if end_date:
            query = query.filter(Sale.order_date <= datetime.strptime(end_date, "%Y-%m-%d").date())
        if region:
            query = query.filter(Sale.region == region)
        return query

    def get_summary_metrics(self, dataset_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None, region: Optional[str] = None) -> Dict[str, Any]:
        """Calculates total sales, profit, margin, unique client, and order counts."""
        query = self.get_scoped_sales_query(dataset_id, start_date, end_date, region)
        
        stats = query.with_entities(
            func.sum(Sale.revenue).label("revenue"),
            func.sum(Sale.profit).label("profit"),
            func.count(Sale.sale_id).label("orders"),
            func.count(distinct(Sale.customer_id)).label("customers")
        ).first()

        total_rev = float(stats.revenue or 0.0)
        total_profit = float(stats.profit or 0.0)
        total_orders = int(stats.orders or 0)
        total_customers = int(stats.customers or 0)
        
        aov = round(total_rev / total_orders, 2) if total_orders > 0 else 0.0
        margin = round(total_profit / total_rev * 100, 2) if total_rev > 0 else 0.0

        return {
            "total_revenue": total_rev,
            "total_profit": total_profit,
            "total_orders": total_orders,
            "total_customers": total_customers,
            "average_order_value": aov,
            "profit_margin": margin
        }

    def delete_by_dataset(self, dataset_id: str) -> None:
        """Deletes all sales, products, and customers associated with a dataset."""
        self.db.query(Sale).filter(Sale.dataset_id == dataset_id).delete(synchronize_session=False)
        self.db.query(Product).filter(Product.dataset_id == dataset_id).delete(synchronize_session=False)
        self.db.query(Customer).filter(Customer.dataset_id == dataset_id).delete(synchronize_session=False)
        self.db.commit()
over_write = True
