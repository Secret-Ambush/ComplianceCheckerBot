import pytest
from pathlib import Path

from src.core.document_processor import DocumentProcessor
from src.models.document import DocumentStatus, DocumentType


def test_document_processor_initialization(document_processor):
    """Test document processor initialization."""
    assert document_processor is not None


def test_document_type_detection(document_processor, test_files_dir):
    """Test document type detection."""
    # Test invoice detection
    doc_type = document_processor._detect_document_type(Path("invoice_001.pdf"))
    assert doc_type == DocumentType.INVOICE
    
    # Test purchase order detection
    doc_type = document_processor._detect_document_type(Path("po_001.pdf"))
    assert doc_type == DocumentType.PURCHASE_ORDER
    
    # Test unknown type
    doc_type = document_processor._detect_document_type(Path("unknown.pdf"))
    assert doc_type == DocumentType.UNKNOWN


def test_document_processing(document_processor, test_files_dir):
    """Test document processing."""
    # Create a test PDF file
    test_file = test_files_dir / "test_invoice.pdf"
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text("Test invoice content")
    
    try:
        # Process document
        doc = document_processor.process_document(test_file)
        
        # Check document properties
        assert doc.filename == "test_invoice.pdf"
        assert doc.document_type == DocumentType.INVOICE
        assert doc.status == DocumentStatus.PROCESSED
        assert doc.processed_at is not None
        
    finally:
        # Clean up
        test_file.unlink()


def test_document_processing_error(document_processor):
    """Test document processing error handling."""
    # Try to process non-existent file
    with pytest.raises(FileNotFoundError):
        document_processor.process_document(Path("non_existent.pdf"))


def test_extract_structured_data(document_processor):
    """Test structured data extraction."""
    # Test data
    text = """
    Invoice Number: INV-001
    Vendor: Test Vendor
    Vendor ID: V001
    Issue Date: 2024-03-20
    Due Date: 2024-04-20
    Total Amount: 1000.00 USD
    
    Items:
    1. Test Item - 2 x 500.00 = 1000.00
    """
    
    layout = []  # Empty layout for now
    
    # Extract data
    data = document_processor._extract_structured_data(text, layout)
    
    # Check extracted data
    assert data["document_number"] == "INV-001"
    assert data["vendor_name"] == "Test Vendor"
    assert data["vendor_id"] == "V001"
    assert data["total_amount"] == 1000.00
    
    # Check line items
    assert len(data["line_items"]) == 1
    item = data["line_items"][0]
    assert item["description"] == "Test Item"
    assert item["quantity"] == 2
    assert item["unit_price"] == 500.00
    assert item["total_price"] == 1000.00 