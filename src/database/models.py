from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from src.database.config import Base
from src.models.document import DocumentStatus, DocumentType
from src.models.rule import RuleType
from src.models.validation import ValidationStatus


# Association table for document relationships
document_relationships = Table(
    "document_relationships",
    Base.metadata,
    Column("source_document_id", PGUUID, ForeignKey("documents.id"), primary_key=True),
    Column("target_document_id", PGUUID, ForeignKey("documents.id"), primary_key=True),
    Column("relationship_type", String, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow)
)


class Document(Base):
    """Document model."""
    __tablename__ = "documents"

    id = Column(PGUUID, primary_key=True, default=uuid4)
    filename = Column(String, nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    document_number = Column(String)
    vendor_name = Column(String)
    vendor_id = Column(String)
    total_amount = Column(Float)
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.PENDING)
    processed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    line_items = relationship("LineItem", back_populates="document", cascade="all, delete-orphan")
    source_relationships = relationship(
        "Document",
        secondary=document_relationships,
        primaryjoin=id == document_relationships.c.source_document_id,
        secondaryjoin=id == document_relationships.c.target_document_id,
        backref="target_relationships"
    )


class LineItem(Base):
    """Line item model."""
    __tablename__ = "line_items"

    id = Column(PGUUID, primary_key=True, default=uuid4)
    document_id = Column(PGUUID, ForeignKey("documents.id"), nullable=False)
    item_id = Column(String)
    description = Column(String)
    quantity = Column(Integer)
    unit_price = Column(Float)
    total_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="line_items")


class Rule(Base):
    """Rule model."""
    __tablename__ = "rules"

    id = Column(PGUUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    rule_type = Column(Enum(RuleType), nullable=False)
    source_document_type = Column(String, nullable=False)
    target_document_types = Column(JSONB)
    conditions = Column(JSONB)
    natural_language_instruction = Column(Text)
    error_message_template = Column(Text)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ValidationReport(Base):
    """Validation report model."""
    __tablename__ = "validation_reports"

    id = Column(PGUUID, primary_key=True, default=uuid4)
    job_id = Column(PGUUID, nullable=False)
    document_id = Column(PGUUID, ForeignKey("documents.id"), nullable=False)
    overall_status = Column(Enum(ValidationStatus), nullable=False)
    validation_results = Column(JSONB)
    summary = Column(JSONB)
    report_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document") 