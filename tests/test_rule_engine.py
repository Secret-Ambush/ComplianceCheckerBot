import pytest
from src.models.document import Document, DocumentType
from src.models.rule import Rule, RuleCondition, RuleOperator, RuleType
from src.models.validation import ValidationStatus


def test_rule_engine_initialization(rule_engine):
    """Test rule engine initialization."""
    assert rule_engine is not None


def test_rule_interpretation(rule_engine):
    """Test rule interpretation."""
    # Test natural language rule
    rule_text = "Check if invoice total amount is greater than 1000"
    rule = rule_engine.interpret_rule(rule_text)
    
    assert rule.name == "Interpreted Rule"
    assert rule.description == rule_text
    assert rule.rule_type == RuleType.CUSTOM
    assert rule.source_document_type == "invoice"
    assert len(rule.target_document_types) > 0


def test_rule_execution(rule_engine, sample_document, sample_rule):
    """Test rule execution."""
    # Execute rule
    result = rule_engine.execute_rule(sample_rule, sample_document, [])
    
    # Check result
    assert result.rule_id == sample_rule.id
    assert result.document_id == sample_document.id
    assert result.status is True
    assert result.execution_time > 0


def test_rule_set_execution(rule_engine, sample_document, sample_rule):
    """Test rule set execution."""
    # Create rule set
    rule_set = RuleSet(
        name="Test Rule Set",
        description="Test rule set description",
        rules=[sample_rule]
    )
    
    # Execute rule set
    result = rule_engine.execute_rule_set(rule_set, sample_document, [])
    
    # Check result
    assert result.document_id == sample_document.id
    assert result.status == ValidationStatus.PASS
    assert len(result.issues) == 0
    assert result.execution_time > 0


def test_rule_execution_error(rule_engine, sample_document):
    """Test rule execution error handling."""
    # Create invalid rule
    invalid_rule = Rule(
        id=sample_document.id,  # Using document ID as rule ID for testing
        name="Invalid Rule",
        description="Invalid rule description",
        rule_type=RuleType.CUSTOM,
        source_document_type="invoice",
        target_document_types=["purchase_order"],
        conditions=[],
        natural_language_instruction="Invalid rule",
        error_message_template="Invalid rule"
    )
    
    # Execute rule
    result = rule_engine.execute_rule(invalid_rule, sample_document, [])
    
    # Check error handling
    assert result.status is False
    assert "Error" in result.message


def test_rule_operators(rule_engine, sample_document):
    """Test different rule operators."""
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
    
    result = rule_engine.execute_rule(equals_rule, sample_document, [])
    assert result.status is True
    
    # Test greater than operator
    greater_rule = Rule(
        id=sample_document.id,
        name="Greater Than Rule",
        description="Test greater than operator",
        rule_type=RuleType.CUSTOM,
        source_document_type="invoice",
        target_document_types=["purchase_order"],
        conditions=[
            RuleCondition(
                field="total_amount",
                operator=RuleOperator.GREATER_THAN,
                value=500.00
            )
        ],
        natural_language_instruction="Check if total amount is greater than 500",
        error_message_template="Total amount must be greater than 500"
    )
    
    result = rule_engine.execute_rule(greater_rule, sample_document, [])
    assert result.status is True 