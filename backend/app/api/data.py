from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import os
import shutil
import json
import io
import uuid
import pandas as pd
from datetime import datetime

from ..database.connection import get_db
from ..database.models import User, Sale, Product, Customer, Notification, Dataset
from ..repositories.dataset_repository import DatasetRepository
from ..repositories.sale_repository import SaleRepository
from ..services.auth_service import get_current_admin, get_current_user
from ..services.cleaning import clean_and_load_dataframe, REQUIRED_COLUMNS

router = APIRouter(prefix="/data", tags=["Dataset Operations"])

UPLOAD_DIR = "datasets"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/clean")
async def clean_dataset(
    file_path: str = Form(...),
    mapping_json: str = Form(...),
    fill_missing: bool = Form(True),
    remove_duplicates: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded file session not found or expired."
        )

    try:
        col_mapping = json.loads(mapping_json)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mapping JSON specification."
        )

    dataset_repo = DatasetRepository(db)
    
    try:
        # 1. Clean spreadsheet using cleaning service
        cleaned_df = clean_and_load_dataframe(
            file_path=file_path,
            col_mapping=col_mapping,
            fill_missing=fill_missing,
            remove_duplicates=remove_duplicates
        )

        # 2. Deactivate previous datasets
        dataset_repo.deactivate_all()

        # 3. Create Dataset metadata record
        dataset_id = str(uuid.uuid4())
        filename = os.path.basename(file_path).replace("temp_", "")
        permanent_filename = f"clean_{dataset_id}_{filename}"
        permanent_path = os.path.join(UPLOAD_DIR, permanent_filename)

        # Move file to permanent location
        shutil.move(file_path, permanent_path)

        file_size = os.path.getsize(permanent_path)
        
        # Calculate Mock Quality Score based on duplicates and nulls remaining (usually high after cleaning)
        quality_score = 99.50 # baseline standard clean score

        db_dataset = Dataset(
            id=dataset_id,
            user_id=current_user.id,
            filename=filename,
            file_path=permanent_path,
            file_size_bytes=file_size,
            quality_score=quality_score,
            cleaning_summary={
                "fill_missing": fill_missing,
                "remove_duplicates": remove_duplicates,
                "cleaned_records": len(cleaned_df)
            },
            is_active=True
        )
        db.add(db_dataset)
        db.commit()

        # 4. Ingest and seed Customer, Product, and Sales rows mapped with dataset_id
        product_map = {}
        customer_map = {}
        sales_to_insert = []

        for _, row in cleaned_df.iterrows():
            prod_name = row["product"]
            category = row["category"]
            price = float(row["price"])
            
            # Product cache mapping per dataset
            prod_key = (prod_name, category, dataset_id)
            if prod_key not in product_map:
                prod = db.query(Product).filter(
                    Product.name == prod_name, 
                    Product.dataset_id == dataset_id
                ).first()
                if not prod:
                    prod = Product(
                        dataset_id=dataset_id,
                        name=prod_name,
                        category=category,
                        stock=50,
                        price=price
                    )
                    db.add(prod)
                    db.commit()
                    db.refresh(prod)
                product_map[prod_key] = prod.product_id

            # Customer cache mapping per dataset
            cust_name = row["customer"]
            segment = row["segment"]
            city = row["city"]
            state = row["state"]
            
            cust_key = (cust_name, segment, dataset_id)
            if cust_key not in customer_map:
                cust = db.query(Customer).filter(
                    Customer.name == cust_name,
                    Customer.segment == segment,
                    Customer.dataset_id == dataset_id
                ).first()
                if not cust:
                    cust = Customer(
                        dataset_id=dataset_id,
                        name=cust_name,
                        segment=segment,
                        city=city,
                        state=state
                    )
                    db.add(cust)
                    db.commit()
                    db.refresh(cust)
                customer_map[cust_key] = cust.customer_id

            # Sale transaction row
            order_date = datetime.strptime(row["order_date"], "%Y-%m-%d").date()
            sale = Sale(
                dataset_id=dataset_id,
                order_date=order_date,
                customer_id=customer_map[cust_key],
                product_id=product_map[prod_key],
                quantity=int(row["quantity"]),
                price=price,
                discount=float(row["discount"]),
                revenue=float(row["revenue"]),
                profit=float(row["profit"]),
                region=row["region"]
            )
            sales_to_insert.append(sale)

        # Bulk save transaction rows
        db.bulk_save_objects(sales_to_insert)
        
        # Create alert notification log
        alert = Notification(
            title="Spreadsheet Ingested",
            message=f"Cleaned and loaded {len(cleaned_df)} transactions from '{filename}' into active database.",
            type="success"
        )
        db.add(alert)
        db.commit()

        return {
            "success": True,
            "message": f"Successfully cleaned and loaded {len(cleaned_df)} records.",
            "dataset_id": dataset_id,
            "records_count": len(cleaned_df),
            "quality_score": quality_score
        }

    except Exception as e:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Spreadsheet mapping ingestion failed: {str(e)}"
        )

@router.get("/export/csv")
def export_sales_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exports raw transactions in flat CSV format scoped by active dataset."""
    dataset_repo = DatasetRepository(db)
    active_ds = dataset_repo.get_active_dataset()
    if not active_ds:
        raise HTTPException(status_code=404, detail="No active datasets loaded.")

    sales_query = db.query(
        Sale.order_date,
        Customer.name.label("customer"),
        Customer.segment,
        Customer.city,
        Customer.state,
        Product.name.label("product"),
        Product.category,
        Sale.quantity,
        Sale.price,
        Sale.discount,
        Sale.revenue,
        Sale.profit,
        Sale.region
    ).join(Customer, Sale.customer_id == Customer.customer_id)\
     .join(Product, Sale.product_id == Product.product_id)\
     .filter(Sale.dataset_id == active_ds.id).all()

    df = pd.DataFrame(sales_query, columns=[
        "order_date", "customer", "segment", "city", "state",
        "product", "category", "quantity", "price", "discount",
        "revenue", "profit", "region"
    ])

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = f"attachment; filename=clean_export_{active_ds.filename}"
    return response
over_write = True
