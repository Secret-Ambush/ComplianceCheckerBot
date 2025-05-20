import logging
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.document_matcher import DocumentMatcher
from src.core.document_processor import DocumentProcessor
from src.core.report_generator import ReportGenerator
from src.core.rule_engine import RuleEngine
from src.core.validation_engine import ValidationEngine
from src.database.config import get_db
from src.database.models import Document as DocumentModel
from src.database.models import Rule as RuleModel
from src.database.models import ValidationReport as ValidationReportModel
from src.database.repository import DocumentRepository, RuleRepository, ValidationReportRepository
from src.models.document import Document, DocumentType
from src.models.rule import Rule, RuleSet
from src.models.validation import ComplianceReport

logger = logging.getLogger(__name__)

router = APIRouter()


class RuleCreate(BaseModel):
    name: str
    description: str
    natural_language_instruction: str
    source_document_type: str
    target_document_types: List[str]
    error_message_template: str


class RuleResponse(BaseModel):
    id: UUID
    name: str
    description: str
    rule_type: str
    status: str
    source_document_type: str
    target_document_types: List[str]


class ValidationRequest(BaseModel):
    document_ids: List[UUID]
    rule_ids: Optional[List[UUID]] = None


class ValidationResponse(BaseModel):
    job_id: UUID
    status: str
    report_path: Optional[str] = None


# Dependency injection
def get_document_processor():
    return DocumentProcessor()


def get_rule_engine():
    return RuleEngine(openai_api_key="your-api-key")  # TODO: Get from config


def get_document_matcher():
    return DocumentMatcher()


def get_validation_engine():
    return ValidationEngine()


def get_report_generator():
    return ReportGenerator(output_dir="reports")


@router.post("/documents/upload", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    document_processor: DocumentProcessor = Depends(get_document_processor),
    db: Session = Depends(get_db)
):
    """Upload and process a document."""
    try:
        # Save uploaded file
        file_path = Path("uploads") / file.filename
        file_path.parent.mkdir(exist_ok=True)
        
        with file_path.open("wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process document
        document = document_processor.process_document(file_path)
        
        # Save to database
        doc_repo = DocumentRepository(db)
        db_document = DocumentModel(
            filename=document.filename,
            document_type=document.document_type,
            document_number=document.document_number,
            vendor_name=document.vendor_name,
            vendor_id=document.vendor_id,
            total_amount=document.total_amount,
            status=document.status,
            processed_at=document.processed_at
        )
        saved_document = doc_repo.create(db_document)
        
        return Document.from_orm(saved_document)
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}", response_model=Document)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """Get document details."""
    doc_repo = DocumentRepository(db)
    document = doc_repo.get_by_id(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return Document.from_orm(document)


@router.post("/rules", response_model=RuleResponse)
async def create_rule(
    rule: RuleCreate,
    rule_engine: RuleEngine = Depends(get_rule_engine),
    db: Session = Depends(get_db)
):
    """Create a new rule."""
    try:
        # Interpret rule
        interpreted_rule = rule_engine.interpret_rule(rule.natural_language_instruction)
        
        # Save to database
        rule_repo = RuleRepository(db)
        db_rule = RuleModel(
            name=interpreted_rule.name,
            description=interpreted_rule.description,
            rule_type=interpreted_rule.rule_type,
            source_document_type=interpreted_rule.source_document_type,
            target_document_types=interpreted_rule.target_document_types,
            conditions=interpreted_rule.conditions,
            natural_language_instruction=rule.natural_language_instruction,
            error_message_template=rule.error_message_template
        )
        saved_rule = rule_repo.create(db_rule)
        
        return RuleResponse(
            id=saved_rule.id,
            name=saved_rule.name,
            description=saved_rule.description,
            rule_type=saved_rule.rule_type,
            status=saved_rule.status,
            source_document_type=saved_rule.source_document_type,
            target_document_types=saved_rule.target_document_types
        )
        
    except Exception as e:
        logger.error(f"Error creating rule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules", response_model=List[RuleResponse])
async def list_rules(
    db: Session = Depends(get_db)
):
    """List all rules."""
    rule_repo = RuleRepository(db)
    rules = rule_repo.get_active_rules()
    
    return [
        RuleResponse(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            rule_type=rule.rule_type,
            status=rule.status,
            source_document_type=rule.source_document_type,
            target_document_types=rule.target_document_types
        )
        for rule in rules
    ]


@router.post("/validate", response_model=ValidationResponse)
async def validate_documents(
    request: ValidationRequest,
    background_tasks: BackgroundTasks,
    document_processor: DocumentProcessor = Depends(get_document_processor),
    rule_engine: RuleEngine = Depends(get_rule_engine),
    document_matcher: DocumentMatcher = Depends(get_document_matcher),
    validation_engine: ValidationEngine = Depends(get_validation_engine),
    report_generator: ReportGenerator = Depends(get_report_generator),
    db: Session = Depends(get_db)
):
    """Validate documents against rules."""
    try:
        # Get documents from database
        doc_repo = DocumentRepository(db)
        documents = [doc_repo.get_by_id(doc_id) for doc_id in request.document_ids]
        documents = [doc for doc in documents if doc is not None]
        
        if not documents:
            raise HTTPException(status_code=404, detail="No documents found")
        
        # Get rules from database
        rule_repo = RuleRepository(db)
        rules = rule_repo.get_active_rules()
        
        if not rules:
            raise HTTPException(status_code=404, detail="No rules found")
        
        # Process documents
        for document in documents:
            # Find related documents
            related_docs = []
            for target_doc in documents:
                if target_doc.id != document.id:
                    matches = document_matcher.find_matches(
                        document,
                        [target_doc],
                        {
                            "source_type": document.document_type,
                            "target_type": target_doc.document_type,
                            "min_confidence": 0.7
                        }
                    )
                    if matches:
                        related_docs.append(target_doc)
            
            # Validate document
            report = validation_engine.validate_document(
                document,
                related_docs,
                rules
            )
            
            # Generate report
            report_path = report_generator.generate_report(
                report,
                document,
                related_docs,
                format="markdown"
            )
            
            # Save report to database
            report_repo = ValidationReportRepository(db)
            db_report = ValidationReportModel(
                job_id=report.job_id,
                document_id=document.id,
                overall_status=report.overall_status,
                validation_results=report.validation_results,
                summary=report.summary,
                report_path=str(report_path)
            )
            saved_report = report_repo.create(db_report)
            
            return ValidationResponse(
                job_id=saved_report.job_id,
                status="completed",
                report_path=saved_report.report_path
            )
            
    except Exception as e:
        logger.error(f"Error validating documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{job_id}", response_model=ComplianceReport)
async def get_report(
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """Get validation report."""
    report_repo = ValidationReportRepository(db)
    report = report_repo.get_by_job_id(job_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return ComplianceReport.from_orm(report)


@router.get("/reports/{job_id}/download")
async def download_report(
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """Download validation report."""
    report_repo = ValidationReportRepository(db)
    report = report_repo.get_by_job_id(job_id)
    
    if not report or not report.report_path:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        report.report_path,
        media_type="application/octet-stream",
        filename=f"report_{job_id}.md"
    ) 