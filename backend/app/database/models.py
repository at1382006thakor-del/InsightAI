from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey, Numeric, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")  # "admin", "analyst", "viewer"
    created_at = Column(DateTime, default=datetime.utcnow)

    datasets = relationship("Dataset", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, index=True) # UUID string
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    quality_score = Column(Float, nullable=False, default=100.0)
    cleaning_summary = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=False)
    upload_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="datasets")
    sales = relationship("Sale", back_populates="dataset", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="dataset", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="dataset", cascade="all, delete-orphan")

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    city = Column(String(255))
    state = Column(String(255))
    segment = Column(String(50))  # "Consumer", "Corporate", "Home Office"

    dataset = relationship("Dataset", back_populates="customers")
    sales = relationship("Sale", back_populates="customer", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # "Technology", "Office Supplies", "Furniture", "Apparel"
    stock = Column(Integer, default=0)
    price = Column(Float, nullable=False)

    dataset = relationship("Dataset", back_populates="products")
    sales = relationship("Sale", back_populates="product", cascade="all, delete-orphan")

class Sale(Base):
    __tablename__ = "sales"

    sale_id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    order_date = Column(Date, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    revenue = Column(Float, nullable=False)
    profit = Column(Float, nullable=False)
    region = Column(String(100), nullable=False, index=True)

    dataset = relationship("Dataset", back_populates="sales")
    customer = relationship("Customer", back_populates="sales")
    product = relationship("Product", back_populates="sales")

class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id = Column(Integer, primary_key=True, index=True)
    month = Column(Date, nullable=False, index=True)
    predicted_sales = Column(Float, nullable=False)
    confidence_lower = Column(Float)
    confidence_upper = Column(Float)
    model_used = Column(String(50), nullable=False)

class Report(Base):
    __tablename__ = "reports"

    report_id = Column(String(36), primary_key=True, index=True) # UUID string
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # "daily", "weekly", "monthly", "quarterly", "annual"
    file_format = Column(String(10), nullable=False, default="pdf") # "pdf", "pptx"
    file_path = Column(String(512), nullable=False)
    summary_text = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reports")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info")  # "info", "warning", "success", "error"
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False, default="New Discussion")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(20), nullable=False)  # "user", "assistant"
    message = Column(Text, nullable=False)
    chart_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
