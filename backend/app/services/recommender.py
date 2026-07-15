from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

from ..database.models import Sale, Product, Customer

def get_business_anomalies(db: Session) -> Dict[str, Any]:
    """Scans the database tables and returns list of actionable warnings and statistics."""
    warnings = []
    opportunities = []

    # 1. Low stock inventory check
    low_stock = db.query(Product).filter(Product.stock <= 25).all()
    for prod in low_stock:
        warnings.append({
            "type": "inventory_risk",
            "impact": "High",
            "message": f"Product '{prod.name}' is low on stock ({prod.stock} units left). Reorder immediately to avoid stockouts."
        })

    # 2. Get latest sales date to compare recent performance
    max_date_row = db.query(func.max(Sale.order_date)).first()
    max_date = max_date_row[0] if max_date_row and max_date_row[0] else date.today()
    t30 = max_date - timedelta(days=30)
    t60 = max_date - timedelta(days=60)

    # 3. Declining Category Sales (MoM drops > 10%)
    cat_sales_t30 = db.query(
        Product.category,
        func.sum(Sale.revenue).label("revenue")
    ).join(Sale).filter(Sale.order_date >= t30, Sale.order_date <= max_date).group_by(Product.category).all()

    cat_sales_t60 = db.query(
        Product.category,
        func.sum(Sale.revenue).label("revenue")
    ).join(Sale).filter(Sale.order_date >= t60, Sale.order_date < t30).group_by(Product.category).all()

    t60_map = {cat: float(rev or 0.0) for cat, rev in cat_sales_t60}
    for cat, rev_t30 in cat_sales_t30:
        rev_t30 = float(rev_t30 or 0.0)
        rev_t60 = t60_map.get(cat, 0.0)
        if rev_t60 > 1000.0:  # Only flag categories with substantial historical volume
            change = (rev_t30 - rev_t60) / rev_t60
            if change < -0.10:
                warnings.append({
                    "type": "declining_category",
                    "impact": "Medium",
                    "message": f"Sales for category '{cat}' dropped by {abs(round(change * 100, 1))}% this month. Consider launching targeted promotions."
                })
            elif change > 0.15:
                opportunities.append({
                    "type": "surging_category",
                    "impact": "High",
                    "message": f"Sales for category '{cat}' increased by {round(change * 100, 1)}% this month. Increase stock and marketing spend."
                })

    # 4. Regional drops (MoM drops > 15%)
    reg_sales_t30 = db.query(Sale.region, func.sum(Sale.revenue)).filter(
        Sale.order_date >= t30, Sale.order_date <= max_date
    ).group_by(Sale.region).all()

    reg_sales_t60 = db.query(Sale.region, func.sum(Sale.revenue)).filter(
        Sale.order_date >= t60, Sale.order_date < t30
    ).group_by(Sale.region).all()

    reg_t60_map = {reg: float(rev or 0.0) for reg, rev in reg_sales_t60}
    for reg, rev_t30 in reg_sales_t30:
        rev_t30 = float(rev_t30 or 0.0)
        rev_t60 = reg_t60_map.get(reg, 0.0)
        if rev_t60 > 1000.0:
            change = (rev_t30 - rev_t60) / rev_t60
            if change < -0.15:
                warnings.append({
                    "type": "declining_region",
                    "impact": "High",
                    "message": f"Revenue in the '{reg}' region has declined by {abs(round(change * 100, 1))}% MoM. Sales team focus recommended."
                })

    # 5. Discount efficacy check
    # Flag products that have high discount rates (>15%) but low margins / negative profits
    ineffective_discounts = db.query(
        Product.name,
        func.avg(Sale.discount).label("avg_discount"),
        func.sum(Sale.profit).label("total_profit")
    ).join(Sale).group_by(Product.product_id).having(
        func.avg(Sale.discount) > 0.15
    ).all()

    for name, avg_disc, tot_prof in ineffective_discounts:
        tot_prof = float(tot_prof or 0.0)
        if tot_prof < 0:
            warnings.append({
                "type": "ineffective_discount",
                "impact": "Medium",
                "message": f"Product '{name}' is unprofitable (Net Profit: ${tot_prof:.2f}) due to high average discounts ({round(avg_disc * 100, 1)}%). Reduce discount rates."
            })

    # Default opportunities if empty
    if not opportunities:
        opportunities.append({
            "type": "general_strategy",
            "impact": "Medium",
            "message": "Implement referral reward systems to boost repeat customers and increase customer lifetime value."
        })

    return {
        "warnings": warnings,
        "opportunities": opportunities,
        "latest_sales_date": max_date.strftime("%Y-%m-%d")
    }
