from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.database.models import Document, LineItem, Rule, ValidationReport
from src.models.document import DocumentStatus, DocumentType
from src.models.rule import RuleType
from src.models.validation import ValidationStatus


class DocumentRepository:
    """Repository for document operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, document: Document) -> Document:
        """Create a new document."""
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def get_by_id(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID."""
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def get_by_type(self, document_type: DocumentType) -> List[Document]:
        """Get documents by type."""
        return self.db.query(Document).filter(Document.document_type == document_type).all()
    
    def update_status(self, document_id: UUID, status: DocumentStatus) -> Optional[Document]:
        """Update document status."""
        document = self.get_by_id(document_id)
        if document:
            document.status = status
            document.processed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(document)
        return document
    
    def delete(self, document_id: UUID) -> bool:
        """Delete document."""
        document = self.get_by_id(document_id)
        if document:
            self.db.delete(document)
            self.db.commit()
            return True
        return False


class RuleRepository:
    """Repository for rule operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, rule: Rule) -> Rule:
        """Create a new rule."""
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule
    
    def get_by_id(self, rule_id: UUID) -> Optional[Rule]:
        """Get rule by ID."""
        return self.db.query(Rule).filter(Rule.id == rule_id).first()
    
    def get_by_type(self, rule_type: RuleType) -> List[Rule]:
        """Get rules by type."""
        return self.db.query(Rule).filter(Rule.rule_type == rule_type).all()
    
    def get_active_rules(self) -> List[Rule]:
        """Get all active rules."""
        return self.db.query(Rule).filter(Rule.status == "active").all()
    
    def update(self, rule_id: UUID, **kwargs) -> Optional[Rule]:
        """Update rule."""
        rule = self.get_by_id(rule_id)
        if rule:
            for key, value in kwargs.items():
                setattr(rule, key, value)
            rule.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(rule)
        return rule
    
    def delete(self, rule_id: UUID) -> bool:
        """Delete rule."""
        rule = self.get_by_id(rule_id)
        if rule:
            self.db.delete(rule)
            self.db.commit()
            return True
        return False


class ValidationReportRepository:
    """Repository for validation report operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, report: ValidationReport) -> ValidationReport:
        """Create a new validation report."""
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report
    
    def get_by_id(self, report_id: UUID) -> Optional[ValidationReport]:
        """Get report by ID."""
        return self.db.query(ValidationReport).filter(ValidationReport.id == report_id).first()
    
    def get_by_job_id(self, job_id: UUID) -> Optional[ValidationReport]:
        """Get report by job ID."""
        return self.db.query(ValidationReport).filter(ValidationReport.job_id == job_id).first()
    
    def get_by_document_id(self, document_id: UUID) -> List[ValidationReport]:
        """Get reports by document ID."""
        return self.db.query(ValidationReport).filter(ValidationReport.document_id == document_id).all()
    
    def get_by_status(self, status: ValidationStatus) -> List[ValidationReport]:
        """Get reports by status."""
        return self.db.query(ValidationReport).filter(ValidationReport.overall_status == status).all()
    
    def delete(self, report_id: UUID) -> bool:
        """Delete report."""
        report = self.get_by_id(report_id)
        if report:
            self.db.delete(report)
            self.db.commit()
            return True
        return False 