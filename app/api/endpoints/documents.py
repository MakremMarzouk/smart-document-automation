from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Document
from app.schemas.document import DocumentResponse, ReviewRequest
from app.services.text_extractor import TextExtractor
from app.services.validator import InvoiceValidator
from app.services.llm_extractor import LLMExtractor


router = APIRouter()

@router.get("/queue/review", response_model=list[DocumentResponse])
def get_review_queue(db: Session = Depends(get_db)):
    """Return all documents that require manual review."""
    documents = (
        db.query(Document)
        .filter(Document.status == "needs_review")
        .order_by(Document.created_at.desc())
        .all()
    )

    return documents

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Fetch document details and extracted text by ID."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.post("/{document_id}/process", response_model=DocumentResponse)
def process_document(document_id: int, db: Session = Depends(get_db)):
    """Extract raw text from an uploaded document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Extract text using our service
        extracted_text = TextExtractor.extract_text(doc.file_path)
        
        # Update database record
        doc.raw_text = extracted_text
        doc.status = "extracted"
        db.commit()
        db.refresh(doc)
        
        return doc
    except Exception as e:
        doc.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")


@router.post("/{document_id}/extract", response_model=DocumentResponse)
def extract_structured_data(document_id: int, db: Session = Depends(get_db)):
    """Use Ollama LLM to extract structured invoice JSON from document raw text."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc.raw_text:
        raise HTTPException(
            status_code=400, 
            detail="Document has no raw text. Please call /process first."
        )

    try:
        # Call LLM extraction
        structured_data = LLMExtractor.extract_invoice_data(doc.raw_text)
        
        # Save structured JSON to Postgres
        doc.extracted_data = structured_data
        doc.status = "structured"
        db.commit()
        db.refresh(doc)
        
        return doc
    except Exception as e:
        doc.status = "extraction_failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{document_id}/validate", response_model=DocumentResponse)
def validate_document(document_id: int, db: Session = Depends(get_db)):
    """Validate the extracted invoice data using business rules."""
    doc = db.query(Document).filter(Document.id == document_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc.extracted_data:
        raise HTTPException(
            status_code=400,
            detail="Document has no extracted data. Please call /extract first."
        )

    try:
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
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )

@router.patch("/{document_id}/review", response_model=DocumentResponse)
def review_document(
    document_id: int,
    review: ReviewRequest,
    db: Session = Depends(get_db)
):
    """Approve, reject, or correct a document requiring review."""
    doc = db.query(Document).filter(Document.id == document_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status != "needs_review":
        raise HTTPException(
            status_code=400,
            detail="Only documents requiring review can be reviewed."
        )

    if review.action == "approve":
        doc.status = "approved"
        doc.validation_errors = []

    elif review.action == "reject":
        doc.status = "rejected"

    elif review.action == "correct":
        if not review.extracted_data:
            raise HTTPException(
                status_code=400,
                detail="Corrected extracted_data is required."
            )

        validation_errors = InvoiceValidator.validate(review.extracted_data)

        doc.extracted_data = review.extracted_data
        doc.validation_errors = validation_errors

        if validation_errors:
            doc.status = "needs_review"
        else:
            doc.status = "approved"

    db.commit()
    db.refresh(doc)

    return doc