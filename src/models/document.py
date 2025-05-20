from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    INVOICE = "invoice"
    PURCHASE_ORDER = "purchase_order"
    GOODS_RECEIPT = "goods_receipt"
    VENDOR_POLICY = "vendor_policy"
    UNKNOWN = "unknown"


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class LineItem(BaseModel):
    item_id: str
    description: str
    quantity: float
    unit_price: float
    total_price: float
    unit: str = "EA"
    metadata: Dict[str, Union[str, float, int]] = Field(default_factory=dict)


class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str
    document_type: DocumentType
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # Document metadata
    document_number: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_id: Optional[str] = None
    issue_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    total_amount: Optional[float] = None
    currency: str = "USD"
    
    # Document content
    line_items: List[LineItem] = Field(default_factory=list)
    raw_text: Optional[str] = None
    extracted_data: Dict[str, Union[str, float, int, List, Dict]] = Field(default_factory=dict)
    
    # Document relationships
    related_documents: List[UUID] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class DocumentMatch(BaseModel):
    source_document: UUID
    target_document: UUID
    match_confidence: float
    match_type: str
    match_criteria: Dict[str, Union[str, float, int]]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        } 