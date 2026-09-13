import os
import shutil
from datetime import datetime
from fastapi import (
    APIRouter,
    BackgroundTasks,
    UploadFile,
    File,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session
from app.db.database import get_db, SessionLocal
from app.db.models import Document
from app.schemas.document import DocumentResponse
from app.core.config import settings
from app.services.text_extractor import TextExtractor
from app.services.llm_extractor import LLMExtractor
from app.services.validator import InvoiceValidator
import logging
logger = logging.getLogger(__name__)


def process_document_in_background(document_id: int):
    """Process a document using a separate database session."""

    db = SessionLocal()
    doc = None
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        logger.info("Starting background processing for document %s", document_id)
        if not doc:
            return

        doc.raw_text = TextExtractor.extract_text(doc.file_path)
        doc.status = "extracted"
        db.commit()

        doc.extracted_data = LLMExtractor.extract_invoice_data(doc.raw_text)
        doc.status = "structured"
        db.commit()

        validation_errors = InvoiceValidator.validate(doc.extracted_data)
        doc.validation_errors = validation_errors

        if validation_errors:
            doc.status = "needs_review"
        else:
            doc.status = "valid"
        logger.info(
            "Finished processing document %s with status %s",
            document_id,
            doc.status,
        )
        db.commit()

    except Exception:
        logger.exception(
            "Background processing failed for document %s",
            document_id,
        )

        if doc:
            doc.status = "processing_failed"
            db.commit()

    finally:
        db.close()

router = APIRouter()

@router.post("/", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # 1. Ensure incoming directory exists
    incoming_dir = os.path.join(settings.STORAGE_DIR, "incoming")
    os.makedirs(incoming_dir, exist_ok=True)
    
    # 2. Make the filename unique by adding a timestamp so we don't overwrite files
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(incoming_dir, safe_filename)
    
    # 3. Save the physical file to disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
        
    # 4. Create the Database record
    db_document = Document(
        filename=file.filename,
        file_path=file_path,
        status="uploaded"
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document) # Reloads it from DB so we get the auto-generated ID
    
    # 5. Return the response (FastAPI uses our DocumentResponse schema automatically)
    return db_document

@router.post("/auto", response_model=DocumentResponse)
async def auto_process_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload, extract text, extract structured data, and validate automatically."""

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    incoming_dir = os.path.join(settings.STORAGE_DIR, "incoming")
    os.makedirs(incoming_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(incoming_dir, safe_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        doc = Document(
            filename=file.filename,
            file_path=file_path,
            status="uploaded"
        )

        db.add(doc)
        db.commit()
        db.refresh(doc)

        doc.raw_text = TextExtractor.extract_text(doc.file_path)
        doc.status = "extracted"
        db.commit()

        doc.extracted_data = LLMExtractor.extract_invoice_data(doc.raw_text)
        doc.status = "structured"
        db.commit()

        validation_errors = InvoiceValidator.validate(doc.extracted_data)
        doc.validation_errors = validation_errors

        if validation_errors:
            doc.status = "needs_review"
        else:
            doc.status = "valid"

        db.commit()
        db.refresh(doc)

        return doc

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Automatic document processing failed: {str(e)}"
        )

@router.post("/auto-background", response_model=DocumentResponse)
async def auto_background_process_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a document and process it in the background."""

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    incoming_dir = os.path.join(settings.STORAGE_DIR, "incoming")
    os.makedirs(incoming_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(incoming_dir, safe_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        doc = Document(
            filename=file.filename,
            file_path=file_path,
            status="uploaded"
        )

        db.add(doc)
        db.commit()
        db.refresh(doc)

        background_tasks.add_task(
            process_document_in_background,
            doc.id
        )

        return doc

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Could not start background processing: {str(e)}"
        )