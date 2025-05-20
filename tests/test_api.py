import json
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(test_client):
    """Test root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "RuleCheckerAgent API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "running"


def test_health_check(test_client):
    """Test health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_upload_document(test_client, test_files_dir):
    """Test document upload endpoint."""
    # Create test file
    test_file = test_files_dir / "test_invoice.pdf"
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text("Test invoice content")
    
    try:
        # Upload file
        with open(test_file, "rb") as f:
            response = test_client.post(
                "/api/v1/documents/upload",
                files={"file": ("test_invoice.pdf", f, "application/pdf")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test_invoice.pdf"
        assert data["document_type"] == "invoice"
        assert data["status"] == "processed"
        
    finally:
        # Clean up
        test_file.unlink()


def test_get_document(test_client):
    """Test get document endpoint."""
    # TODO: Implement when document storage is added
    response = test_client.get(f"/api/v1/documents/{uuid4()}")
    assert response.status_code == 501


def test_create_rule(test_client):
    """Test create rule endpoint."""
    # Create rule
    rule_data = {
        "name": "Test Rule",
        "description": "Test rule description",
        "natural_language_instruction": "Check if total amount is greater than 1000",
        "source_document_type": "invoice",
        "target_document_types": ["purchase_order"],
        "error_message_template": "Total amount must be greater than 1000"
    }
    
    response = test_client.post(
        "/api/v1/rules",
        json=rule_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == rule_data["name"]
    assert data["description"] == rule_data["description"]
    assert data["rule_type"] == "custom"
    assert data["source_document_type"] == rule_data["source_document_type"]
    assert data["target_document_types"] == rule_data["target_document_types"]


def test_list_rules(test_client):
    """Test list rules endpoint."""
    # TODO: Implement when rule storage is added
    response = test_client.get("/api/v1/rules")
    assert response.status_code == 501


def test_validate_documents(test_client):
    """Test validate documents endpoint."""
    # Create validation request
    request_data = {
        "document_ids": [str(uuid4())],
        "rule_ids": [str(uuid4())]
    }
    
    response = test_client.post(
        "/api/v1/validate",
        json=request_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "completed"
    assert "report_path" in data


def test_get_report(test_client):
    """Test get report endpoint."""
    # TODO: Implement when report storage is added
    response = test_client.get(f"/api/v1/reports/{uuid4()}")
    assert response.status_code == 501


def test_download_report(test_client):
    """Test download report endpoint."""
    # TODO: Implement when report storage is added
    response = test_client.get(f"/api/v1/reports/{uuid4()}/download")
    assert response.status_code == 501 