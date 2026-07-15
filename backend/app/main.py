from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .database.connection import Base, engine
from .database.seeder import init_db
from .api import auth, data, dashboard, kpis, predict, reports, settings, datasets, chat, users

app = FastAPI(
    title="InsightAI API",
    description="FastAPI backend for InsightAI - Sales Dashboard & Business Intelligence Platform",
    version="1.0.0"
)

# Enable CORS for Next.js local development server and API requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Automatically create schema tables and seed default sample dataset on API startup
@app.on_event("startup")
def startup_event():
    print("Database startup initialization...")
    try:
        init_db()
        print("Database initialized and checked successfully.")
    except Exception as e:
        print(f"Error during database startup initialization: {str(e)}")

# Include REST Routers
app.include_router(auth.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(data.router, prefix="/api")
app.include_router(datasets.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(kpis.router, prefix="/api")
app.include_router(predict.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(users.router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "message": "Welcome to InsightAI Business Intelligence REST API",
        "status": "Online",
        "docs_url": "/docs"
    }
