from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    ERROR = "error"
    PENDING = "pending"


class ValidationSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationIssue(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    rule_id: UUID
    document_id: UUID
    status: ValidationStatus
    severity: ValidationSeverity
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class ValidationResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    status: ValidationStatus
    issues: List[ValidationIssue] = Field(default_factory=list)
    execution_time: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class ComplianceReport(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    job_id: UUID
    document_id: UUID
    overall_status: ValidationStatus
    validation_results: List[ValidationResult]
    summary: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """Convert the compliance report to a markdown format."""
        lines = [
            f"# Compliance Report for Document {self.document_id}",
            f"\nOverall Status: {self.overall_status.upper()}",
            f"\nGenerated at: {self.created_at.isoformat()}",
            "\n## Summary",
        ]
        
        # Add summary statistics
        for key, value in self.summary.items():
            lines.append(f"- {key}: {value}")
        
        # Add detailed results
        lines.append("\n## Detailed Results")
        for result in self.validation_results:
            lines.append(f"\n### {result.document_id}")
            lines.append(f"Status: {result.status}")
            lines.append(f"Execution Time: {result.execution_time:.2f}s")
            
            if result.issues:
                lines.append("\nIssues:")
                for issue in result.issues:
                    lines.append(f"- [{issue.severity.upper()}] {issue.message}")
                    if issue.details:
                        lines.append("  Details:")
                        for key, value in issue.details.items():
                            lines.append(f"  - {key}: {value}")
        
        return "\n".join(lines)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        } 