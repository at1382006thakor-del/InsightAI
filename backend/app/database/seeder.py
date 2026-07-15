import os
import csv
import random
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import Base, User, Customer, Product, Sale, Notification, Dataset
from .connection import engine, SessionLocal
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# Sample data pools
CUSTOMER_NAMES = [
    "John Doe", "Jane Smith", "Robert Johnson", "Emily Davis", "Michael Brown",
    "Sarah Miller", "David Wilson", "Taylor Anderson", "James Thomas", "Jessica Jackson",
    "Daniel White", "Amanda Harris", "Mark Martin", "Ashley Thompson", "Paul Garcia",
    "Megan Martinez", "Steven Robinson", "Elizabeth Clark", "Andrew Rodriguez", "Laura Lewis",
    "William Lee", "Olivia Walker", "Joseph Hall", "Sophia Allen", "Charles Young",
    "Isabella Hernandez", "Christopher King", "Mia Wright", "Matthew Lopez", "Charlotte Hill",
    "Joshua Scott", "Amelia Green", "Nathan Adams", "Harper Baker", "Brian Gonzalez",
    "Evelyn Nelson", "Kevin Carter", "Abigail Mitchell", "Ronald Perez", "Emily Roberts",
    "Edward Turner", "Elizabeth Phillips", "Donald Campbell", "Sofia Parker", "George Evans"
]

CITIES_STATES = [
    ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"), ("Houston", "TX"),
    ("Phoenix", "AZ"), ("Philadelphia", "PA"), ("San Antonio", "TX"), ("San Diego", "CA"),
    ("Dallas", "TX"), ("San Jose", "CA"), ("Austin", "TX"), ("Jacksonville", "FL"),
    ("San Francisco", "CA"), ("Indianapolis", "IN"), ("Columbus", "OH"), ("Fort Worth", "TX"),
    ("Charlotte", "NC"), ("Seattle", "WA"), ("Denver", "CO"), ("El Paso", "TX"),
    ("Boston", "MA"), ("Detroit", "MI"), ("Nashville", "TN"), ("Memphis", "TN"),
    ("Portland", "OR"), ("Oklahoma City", "OK"), ("Las Vegas", "NV"), ("Baltimore", "MD")
]

SEGMENTS = ["Consumer", "Corporate", "Home Office"]
REGIONS = ["East", "West", "Central", "South"]

PRODUCTS_POOL = [
    {"name": "SmartPhone X1", "category": "Technology", "price": 899.99, "margin": 0.35},
    {"name": "ProBook Laptop", "category": "Technology", "price": 1299.99, "margin": 0.30},
    {"name": "4K UltraMonitor", "category": "Technology", "price": 399.99, "margin": 0.40},
    {"name": "Wireless Audio Pods", "category": "Technology", "price": 149.99, "margin": 0.45},
    {"name": "SmartWatch Pro", "category": "Technology", "price": 249.99, "margin": 0.38},
    {"name": "Ergonomic Office Chair", "category": "Furniture", "price": 299.99, "margin": 0.18},
    {"name": "L-Shaped Wooden Desk", "category": "Furniture", "price": 499.99, "margin": 0.15},
    {"name": "Bookshelf 5-Tier", "category": "Furniture", "price": 159.99, "margin": 0.20},
    {"name": "LED Desk Lamp", "category": "Furniture", "price": 49.99, "margin": 0.25},
    {"name": "Standing Desk Frame", "category": "Furniture", "price": 349.99, "margin": 0.17},
    {"name": "Heavy Duty Binder 3-Pack", "category": "Office Supplies", "price": 19.99, "margin": 0.50},
    {"name": "Premium Printer Paper Case", "category": "Office Supplies", "price": 45.99, "margin": 0.40},
    {"name": "Gel Ink Pens Box of 20", "category": "Office Supplies", "price": 14.99, "margin": 0.55},
    {"name": "Dry Erase Board 3x2", "category": "Office Supplies", "price": 39.99, "margin": 0.45},
    {"name": "Wireless Presenter Clicker", "category": "Office Supplies", "price": 29.99, "margin": 0.48},
    {"name": "Waterproof Tech Jacket", "category": "Apparel", "price": 119.99, "margin": 0.35},
    {"name": "Athletic Running Shoes", "category": "Apparel", "price": 89.99, "margin": 0.30},
    {"name": "Organic Cotton Tee 3-Pack", "category": "Apparel", "price": 29.99, "margin": 0.40},
    {"name": "Classic Fit Denim Jeans", "category": "Apparel", "price": 59.99, "margin": 0.32},
    {"name": "Smart Travel Backpack", "category": "Apparel", "price": 79.99, "margin": 0.38}
]

def generate_sample_csv(file_path: str, num_records: int = 2500): # reduced count for faster seeds during local tests
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 6, 30)
    delta_days = (end_date - start_date).days

    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "order_date", "customer", "segment", "city", "state", 
            "product", "category", "quantity", "price", "discount", 
            "revenue", "profit", "region"
        ])
        
        for _ in range(num_records):
            rand_day = random.randint(0, delta_days)
            order_date = start_date + timedelta(days=rand_day)
            
            years_diff = (order_date - start_date).days / 365.25
            trend_multiplier = 1.0 + (0.12 * years_diff)
            
            month = order_date.month
            if month in [11, 12]:
                season_multiplier = 1.35
            elif month in [1, 2]:
                season_multiplier = 0.75
            else:
                season_multiplier = 1.0

            cust_name = random.choice(CUSTOMER_NAMES)
            segment = random.choice(SEGMENTS)
            city, state = random.choice(CITIES_STATES)

            prod_info = random.choice(PRODUCTS_POOL)
            prod_name = prod_info["name"]
            category = prod_info["category"]
            unit_price = prod_info["price"]
            
            unit_price = round(unit_price * random.uniform(0.95, 1.05), 2)
            
            if category == "Office Supplies":
                quantity = random.randint(2, 12)
            elif category == "Technology":
                quantity = random.randint(1, 3)
            elif category == "Furniture":
                quantity = random.randint(1, 4)
            else:
                quantity = random.randint(1, 5)

            boost_prob = trend_multiplier * season_multiplier - 1.0
            if boost_prob > 0 and random.random() < boost_prob:
                quantity += random.randint(1, 2)
            elif boost_prob < 0 and random.random() < abs(boost_prob):
                quantity = max(1, quantity - 1)

            discount = 0.0
            if random.random() < 0.35:
                discount = random.choice([0.05, 0.10, 0.15, 0.20, 0.25])

            gross_rev = quantity * unit_price
            revenue = round(gross_rev * (1 - discount), 2)
            
            margin = prod_info["margin"] + random.uniform(-0.05, 0.05)
            cost = gross_rev * (1 - margin)
            profit = round(revenue - cost, 2)
            
            region = random.choice(REGIONS)
            
            writer.writerow([
                order_date.strftime("%Y-%m-%d"), cust_name, segment, city, state,
                prod_name, category, quantity, unit_price, discount,
                revenue, profit, region
            ])

def seed_db_from_csv(db: Session, csv_path: str):
    # 1. Check if we have users, if not add admin/user
    admin = db.query(User).filter(User.email == "admin@insightai.com").first()
    if not admin:
        admin = User(
            name="Admin User",
            email="admin@insightai.com",
            password_hash=hash_password("admin123"),
            role="admin"
        )
        staff = User(
            name="Sales Executive",
            email="user@insightai.com",
            password_hash=hash_password("user123"),
            role="analyst" # analyst access default
        )
        db.add(admin)
        db.add(staff)
        db.commit()
        db.refresh(admin)

    # Clear previous transactional data
    db.query(Sale).delete()
    db.query(Product).delete()
    db.query(Customer).delete()
    db.query(Dataset).delete()
    db.query(Notification).delete()
    db.commit()

    # 2. Add active Dataset row
    dataset_id = str(uuid.uuid4())
    db_dataset = Dataset(
        id=dataset_id,
        user_id=admin.id,
        filename="sample_sales.csv",
        file_path=csv_path,
        file_size_bytes=os.path.getsize(csv_path),
        quality_score=100.0,
        cleaning_summary={"is_seeded": True},
        is_active=True
    )
    db.add(db_dataset)
    db.commit()

    product_map = {}
    customer_map = {}

    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        sales_to_insert = []
        
        for row in reader:
            # Product cache mapping per dataset
            prod_name = row["product"]
            category = row["category"]
            price = float(row["price"])
            
            prod_key = (prod_name, category, dataset_id)
            if prod_key not in product_map:
                prod = Product(
                    dataset_id=dataset_id,
                    name=prod_name,
                    category=category,
                    stock=random.randint(20, 150),
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

        # Batch insert sales
        db.bulk_save_objects(sales_to_insert)
        db.commit()

    alert = Notification(
        title="Database Seeded Successfully",
        message="InsightAI loaded the default sample dataset under active workspace scoping.",
        type="success"
    )
    db.add(alert)
    db.commit()

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    csv_dir = "datasets"
    csv_name = "sample_sales.csv"
    csv_path = os.path.join(csv_dir, csv_name)
    
    if not os.path.exists(csv_path):
        generate_sample_csv(csv_path)
        
    seed_db_from_csv(db, csv_path)
    db.close()

if __name__ == "__main__":
    print("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    csv_path = os.path.join("datasets", "sample_sales.csv")
    if not os.path.exists(csv_path):
        print("Generating sample sales CSV...")
        generate_sample_csv(csv_path)
    print("Seeding database...")
    db_session = SessionLocal()
    seed_db_from_csv(db_session, csv_path)
    db_session.close()
    print("Database seeding completed successfully!")
