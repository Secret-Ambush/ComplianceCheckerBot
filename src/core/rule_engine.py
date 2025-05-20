import ast
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

from src.models.document import Document
from src.models.rule import (
    Rule,
    RuleCondition,
    RuleExecutionResult,
    RuleOperator,
    RuleSet,
    RuleType,
)
from src.models.validation import ValidationIssue, ValidationResult, ValidationSeverity, ValidationStatus

logger = logging.getLogger(__name__)


class RuleEngine:
    def __init__(self, openai_api_key: str):
        """Initialize the rule engine.
        
        Args:
            openai_api_key: OpenAI API key for rule interpretation
        """
        self.llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-4",
            openai_api_key=openai_api_key
        )
        
        # Initialize rule templates
        self.rule_templates = {
            RuleType.DOCUMENT_MATCH: self._create_document_match_rule,
            RuleType.QUANTITY_CHECK: self._create_quantity_check_rule,
            RuleType.PRICE_CHECK: self._create_price_check_rule,
            RuleType.DATE_CHECK: self._create_date_check_rule,
            RuleType.VENDOR_CHECK: self._create_vendor_check_rule,
            RuleType.CUSTOM: self._create_custom_rule
        }
    
    def interpret_rule(self, natural_language_instruction: str) -> Rule:
        """Interpret a natural language instruction into a rule.
        
        Args:
            natural_language_instruction: Natural language instruction
            
        Returns:
            Interpreted rule
        """
        # Create prompt for rule interpretation
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a rule interpretation system that converts natural language instructions into structured rules.
            Analyze the instruction and determine:
            1. The type of rule
            2. The source and target document types
            3. The conditions to check
            4. The error message template
            
            Return the rule in a structured format."""),
            HumanMessage(content=natural_language_instruction)
        ])
        
        # Get interpretation from LLM
        response = self.llm(prompt.format_messages())
        
        # Parse response into rule structure
        # TODO: Implement proper parsing of LLM response
        rule = Rule(
            name="Interpreted Rule",
            description=natural_language_instruction,
            rule_type=RuleType.CUSTOM,  # Default to custom
            source_document_type="invoice",  # Default values
            target_document_types=["purchase_order"],
            conditions=[],
            natural_language_instruction=natural_language_instruction,
            error_message_template="Rule validation failed"
        )
        
        return rule
    
    def execute_rule(self, rule: Rule, document: Document, related_documents: List[Document]) -> RuleExecutionResult:
        """Execute a rule against a document and its related documents.
        
        Args:
            rule: Rule to execute
            document: Source document
            related_documents: Related documents to check against
            
        Returns:
            Rule execution result
        """
        start_time = time.time()
        
        try:
            # Get rule template
            rule_template = self.rule_templates.get(rule.rule_type)
            if not rule_template:
                raise ValueError(f"Unknown rule type: {rule.rule_type}")
            
            # Execute rule
            status, message, details = rule_template(rule, document, related_documents)
            
            # Create execution result
            result = RuleExecutionResult(
                rule_id=rule.id,
                document_id=document.id,
                status=status,
                message=message,
                details=details,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error executing rule {rule.id}: {str(e)}")
            result = RuleExecutionResult(
                rule_id=rule.id,
                document_id=document.id,
                status=False,
                message=f"Error executing rule: {str(e)}",
                details={"error": str(e)},
                execution_time=time.time() - start_time
            )
        
        return result
    
    def execute_rule_set(self, rule_set: RuleSet, document: Document, related_documents: List[Document]) -> ValidationResult:
        """Execute a set of rules against a document.
        
        Args:
            rule_set: Set of rules to execute
            document: Source document
            related_documents: Related documents to check against
            
        Returns:
            Validation result
        """
        issues = []
        overall_status = ValidationStatus.PASS
        
        for rule in rule_set.rules:
            # Execute rule
            result = self.execute_rule(rule, document, related_documents)
            
            # Create validation issue if rule failed
            if not result.status:
                issue = ValidationIssue(
                    rule_id=rule.id,
                    document_id=document.id,
                    status=ValidationStatus.FAIL,
                    severity=ValidationSeverity.HIGH,  # Default to high severity
                    message=result.message,
                    details=result.details
                )
                issues.append(issue)
                overall_status = ValidationStatus.FAIL
        
        # Create validation result
        validation_result = ValidationResult(
            document_id=document.id,
            status=overall_status,
            issues=issues,
            execution_time=sum(issue.execution_time for issue in issues)
        )
        
        return validation_result
    
    def _create_document_match_rule(self, rule: Rule, document: Document, related_documents: List[Document]) -> tuple[bool, str, Dict]:
        """Create and execute a document matching rule."""
        # TODO: Implement document matching logic
        return True, "Documents matched successfully", {}
    
    def _create_quantity_check_rule(self, rule: Rule, document: Document, related_documents: List[Document]) -> tuple[bool, str, Dict]:
        """Create and execute a quantity check rule."""
        # TODO: Implement quantity check logic
        return True, "Quantity check passed", {}
    
    def _create_price_check_rule(self, rule: Rule, document: Document, related_documents: List[Document]) -> tuple[bool, str, Dict]:
        """Create and execute a price check rule."""
        # TODO: Implement price check logic
        return True, "Price check passed", {}
    
    def _create_date_check_rule(self, rule: Rule, document: Document, related_documents: List[Document]) -> tuple[bool, str, Dict]:
        """Create and execute a date check rule."""
        # TODO: Implement date check logic
        return True, "Date check passed", {}
    
    def _create_vendor_check_rule(self, rule: Rule, document: Document, related_documents: List[Document]) -> tuple[bool, str, Dict]:
        """Create and execute a vendor check rule."""
        # TODO: Implement vendor check logic
        return True, "Vendor check passed", {}
    
    def _create_custom_rule(self, rule: Rule, document: Document, related_documents: List[Document]) -> tuple[bool, str, Dict]:
        """Create and execute a custom rule."""
        if not rule.validation_logic:
            return True, "No validation logic provided", {}
        
        try:
            # Parse and execute validation logic
            # Note: This is a simple implementation. In production, you'd want to use a proper rule engine
            validation_func = ast.literal_eval(rule.validation_logic)
            result = validation_func(document, related_documents)
            
            if isinstance(result, tuple) and len(result) == 3:
                return result
            else:
                return bool(result), "Custom validation completed", {"result": result}
                
        except Exception as e:
            logger.error(f"Error executing custom rule: {str(e)}")
            return False, f"Error executing custom rule: {str(e)}", {"error": str(e)} 