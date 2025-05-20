import pytest
from src.models.document import Document, DocumentType
from src.models.rule import Rule, RuleCondition, RuleOperator, RuleType
from src.models.validation import ValidationStatus, ValidationSeverity


def test_validation_engine_initialization(validation_engine):
    """Test validation engine initialization."""
    assert validation_engine is not None


def test_document_validation(validation_engine, sample_document, sample_rule):
    """Test document validation."""
    # Validate document
    report = validation_engine.validate_document(
        sample_document,
        [],  # No related documents
        [sample_rule]
    )
    
    # Check report
    assert report.document_id == sample_document.id
    assert report.overall_status == ValidationStatus.PASS
    assert len(report.validation_results) == 1
    assert len(report.summary) > 0


def test_validation_with_related_documents(validation_engine, sample_document):
    """Test validation with related documents."""
    # Create related document
    related_doc = Document(
        id=sample_document.id,  # Using same ID for testing
        filename="related_po.pdf",
        document_type=DocumentType.PURCHASE_ORDER,
        document_number="PO-001",
        vendor_name="Test Vendor",
        vendor_id="V001",
        total_amount=1000.00
    )
    
    # Create rule for related documents
    rule = Rule(
        id=sample_document.id,
        name="Related Document Rule",
        description="Test related document validation",
        rule_type=RuleType.DOCUMENT_MATCH,
        source_document_type="invoice",
        target_document_types=["purchase_order"],
        conditions=[
            RuleCondition(
                field="total_amount",
                operator=RuleOperator.EQUALS,
                value=1000.00
            )
        ],
        natural_language_instruction="Check if invoice and PO amounts match",
        error_message_template="Amounts do not match"
    )
    
    # Validate document
    report = validation_engine.validate_document(
        sample_document,
        [related_doc],
        [rule]
    )
    
    # Check report
    assert report.overall_status == ValidationStatus.PASS
    assert len(report.validation_results) == 1


def test_validation_failure(validation_engine, sample_document):
    """Test validation failure."""
    # Create failing rule
    failing_rule = Rule(
        id=sample_document.id,
        name="Failing Rule",
        description="Test validation failure",
        rule_type=RuleType.CUSTOM,
        source_document_type="invoice",
        target_document_types=["purchase_order"],
        conditions=[
            RuleCondition(
                field="total_amount",
                operator=RuleOperator.GREATER_THAN,
                value=2000.00  # Will fail for sample document
            )
        ],
        natural_language_instruction="Check if total amount is greater than 2000",
        error_message_template="Total amount must be greater than 2000"
    )
    
    # Validate document
    report = validation_engine.validate_document(
        sample_document,
        [],
        [failing_rule]
    )
    
    # Check report
    assert report.overall_status == ValidationStatus.FAIL
    assert len(report.validation_results) == 1
    assert len(report.validation_results[0].issues) == 1
    
    # Check issue
    issue = report.validation_results[0].issues[0]
    assert issue.status == ValidationStatus.FAIL
    assert issue.severity == ValidationSeverity.HIGH
    assert "greater than 2000" in issue.message


def test_validation_operators(validation_engine, sample_document):
    """Test different validation operators."""
    # Test equals operator
    equals_rule = Rule(
        id=sample_document.id,
        name="Equals Rule",
        description="Test equals operator",
        rule_type=RuleType.CUSTOM,
        source_document_type="invoice",
        target_document_types=["purchase_order"],
        conditions=[
            RuleCondition(
                field="total_amount",
                operator=RuleOperator.EQUALS,
                value=1000.00
            )
        ],
        natural_language_instruction="Check if total amount equals 1000",
        error_message_template="Total amount must equal 1000"
    )
    
    report = validation_engine.validate_document(
        sample_document,
        [],
        [equals_rule]
    )
    assert report.overall_status == ValidationStatus.PASS
    
    # Test not equals operator
    not_equals_rule = Rule(
        id=sample_document.id,
        name="Not Equals Rule",
        description="Test not equals operator",
        rule_type=RuleType.CUSTOM,
        source_document_type="invoice",
        target_document_types=["purchase_order"],
        conditions=[
            RuleCondition(
                field="total_amount",
                operator=RuleOperator.NOT_EQUALS,
                value=2000.00
            )
        ],
        natural_language_instruction="Check if total amount is not 2000",
        error_message_template="Total amount must not be 2000"
    )
    
    report = validation_engine.validate_document(
        sample_document,
        [],
        [not_equals_rule]
    )
    assert report.overall_status == ValidationStatus.PASS 