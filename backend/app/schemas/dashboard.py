from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import date

class SummaryMetrics(BaseModel):
    total_sales: float
    total_revenue: float
    total_profit: float
    total_orders: int
    total_customers: int
    average_order_value: float
    growth_percent: float
    return_rate: float

class TimeseriesDataPoint(BaseModel):
    date: str
    revenue: float
    profit: float
    orders: int

class CategorySalesPoint(BaseModel):
    category: str
    revenue: float
    profit: float
    quantity: int

class RegionalSalesPoint(BaseModel):
    region: str
    revenue: float
    profit: float
    orders: int

class ProductPerformancePoint(BaseModel):
    product_id: int
    name: str
    category: str
    revenue: float
    profit: float
    quantity: int
    stock: int

class CustomerPerformancePoint(BaseModel):
    customer_id: int
    name: str
    city: str
    state: str
    segment: str
    revenue: float
    orders: int

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    created_at: str
    is_read: bool

    class Config:
        from_attributes = True
