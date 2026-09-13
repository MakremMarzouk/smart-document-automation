from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Any, Dict, Optional, List, Literal


class DocumentResponse(BaseModel):
    id: int
    filename: str
    status: str
    raw_text: Optional[str] = None 
    extracted_data: Optional[Dict[str, Any]] = None
    validation_errors: Optional[List[str]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ReviewRequest(BaseModel):
    action: Literal["approve", "reject", "correct"]
    extracted_data: Optional[Dict[str, Any]] = None
