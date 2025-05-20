from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RuleType(str, Enum):
    DOCUMENT_MATCH = "document_match"
    QUANTITY_CHECK = "quantity_check"
    PRICE_CHECK = "price_check"
    DATE_CHECK = "date_check"
    VENDOR_CHECK = "vendor_check"
    CUSTOM = "custom"


class RuleOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_EQUALS = "greater_than_equals"
    LESS_THAN_EQUALS = "less_than_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    BETWEEN = "between"
    NOT_BETWEEN = "not_between"
    MATCHES = "matches"
    NOT_MATCHES = "not_matches"


class RuleStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


class RuleCondition(BaseModel):
    field: str
    operator: RuleOperator
    value: Any
    tolerance: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Rule(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    rule_type: RuleType
    status: RuleStatus = RuleStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Rule configuration
    source_document_type: str
    target_document_types: List[str]
    conditions: List[RuleCondition]
    priority: int = 0
    
    # Rule execution
    natural_language_instruction: str
    validation_logic: Optional[str] = None  # Python code or function reference
    error_message_template: str
    
    # Rule metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class RuleExecutionResult(BaseModel):
    rule_id: UUID
    document_id: UUID
    status: bool
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class RuleSet(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    rules: List[Rule]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        } 