from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api_router import api_router
from app.core.config import settings
from app.db.database import engine, Base
from app.core.logging_config import configure_logging

configure_logging()
# This line creates all the tables in Postgres based on our models.py
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for Document Upload and processing",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect our endpoints to the main app
app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "Welcome to Smart Document Automation API"}