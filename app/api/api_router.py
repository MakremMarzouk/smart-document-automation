from fastapi import APIRouter
from app.api.endpoints import upload, documents

api_router = APIRouter()

# We map the upload.py file to the "/upload" URL path
api_router.include_router(upload.router, prefix="/upload", tags=["documents"])
# We map the documents.py file to the "/documents" URL path
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])