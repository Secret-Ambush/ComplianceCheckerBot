import os
from pathlib import Path
from typing import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.core.document_matcher import DocumentMatcher
from src.core.document_processor import DocumentProcessor
from src.core.report_generator import ReportGenerator
from src.core.rule_engine import RuleEngine
from src.core.validation_engine import ValidationEngine
from src.models.document import Document, DocumentType, LineItem
from src.models.rule import Rule, RuleCondition, RuleOperator, RuleType


@pytest.fixture
def test_client() -> Generator:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def document_processor() -> DocumentProcessor:
    """Create a document processor instance."""
    return DocumentProcessor()


@pytest.fixture
def rule_engine() -> RuleEngine:
    """Create a rule engine instance."""
    return RuleEngine(openai_api_key=os.getenv("OPENAI_API_KEY", "test-key"))


@pytest.fixture
def document_matcher() -> DocumentMatcher:
    """Create a document matcher instance."""
    return DocumentMatcher()


@pytest.fixture
def validation_engine() -> ValidationEngine:
    """Create a validation engine instance."""
    return ValidationEngine()


@pytest.fixture
def report_generator() -> ReportGenerator:
    """Create a report generator instance."""
    return ReportGenerator(output_dir="test_reports")


@pytest.fixture
def sample_document() -> Document:
    """Create a sample document for testing."""
    return Document(
        id=uuid4(),
        filename="test_invoice.pdf",
        document_type=DocumentType.INVOICE,
        document_number="INV-001",
        vendor_name="Test Vendor",
        vendor_id="V001",
        total_amount=1000.00,
        line_items=[
            LineItem(
                item_id="ITEM-001",
                description="Test Item",
                quantity=2,
                unit_price=500.00,
                total_price=1000.00
            )
        ]
    )


@pytest.fixture
def sample_rule() -> Rule:
    """Create a sample rule for testing."""
    return Rule(
        id=uuid4(),
        name="Test Rule",
        description="Test rule description",
        rule_type=RuleType.QUANTITY_CHECK,
        source_document_type="invoice",
        target_document_types=["purchase_order"],
        conditions=[
            RuleCondition(
                field="quantity",
                operator=RuleOperator.GREATER_THAN,
                value=0
            )
        ],
        natural_language_instruction="Check if quantity is greater than 0",
        error_message_template="Quantity must be greater than 0"
    )


@pytest.fixture
def test_files_dir() -> Path:
    """Get the test files directory."""
    return Path(__file__).parent / "test_files"


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment."""
    # Create test directories
    os.makedirs("test_reports", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    yield
    
    # Clean up test directories
    # TODO: Implement cleanup 