import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from src.models.document import Document, DocumentType
from src.models.rule import Rule, RuleCondition, RuleOperator
from src.models.validation import (
    ComplianceReport,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    ValidationStatus,
)

logger = logging.getLogger(__name__)


class ValidationEngine:
    def __init__(self):
        """Initialize the validation engine."""
        # Initialize validation operators
        self.operators = {
            RuleOperator.EQUALS: self._validate_equals,
            RuleOperator.NOT_EQUALS: self._validate_not_equals,
            RuleOperator.GREATER_THAN: self._validate_greater_than,
            RuleOperator.LESS_THAN: self._validate_less_than,
            RuleOperator.GREATER_THAN_EQUALS: self._validate_greater_than_equals,
            RuleOperator.LESS_THAN_EQUALS: self._validate_less_than_equals,
            RuleOperator.CONTAINS: self._validate_contains,
            RuleOperator.NOT_CONTAINS: self._validate_not_contains,
            RuleOperator.BETWEEN: self._validate_between,
            RuleOperator.NOT_BETWEEN: self._validate_not_between,
            RuleOperator.MATCHES: self._validate_matches,
            RuleOperator.NOT_MATCHES: self._validate_not_matches,
        }
    
    def validate_document(
        self, document: Document, related_documents: List[Document], rules: List[Rule]
    ) -> ComplianceReport:
        """Validate a document against a set of rules.
        
        Args:
            document: Document to validate
            related_documents: Related documents to check against
            rules: List of rules to validate against
            
        Returns:
            Compliance report
        """
        validation_results = []
        issues = []
        overall_status = ValidationStatus.PASS
        
        for rule in rules:
            # Skip if rule is not active
            if rule.status != "active":
                continue
            
            # Validate rule
            result = self._validate_rule(rule, document, related_documents)
            validation_results.append(result)
            
            # Update overall status
            if result.status == ValidationStatus.FAIL:
                overall_status = ValidationStatus.FAIL
                issues.extend(result.issues)
        
        # Create summary
        summary = self._create_summary(validation_results)
        
        # Create compliance report
        report = ComplianceReport(
            job_id=document.id,  # Using document ID as job ID for simplicity
            document_id=document.id,
            overall_status=overall_status,
            validation_results=validation_results,
            summary=summary
        )
        
        return report
    
    def _validate_rule(
        self, rule: Rule, document: Document, related_documents: List[Document]
    ) -> ValidationResult:
        """Validate a single rule against a document.
        
        Args:
            rule: Rule to validate
            document: Document to validate
            related_documents: Related documents to check against
            
        Returns:
            Validation result
        """
        issues = []
        start_time = datetime.utcnow()
        
        try:
            # Validate each condition
            for condition in rule.conditions:
                # Get validation operator
                operator = self.operators.get(condition.operator)
                if not operator:
                    raise ValueError(f"Unknown operator: {condition.operator}")
                
                # Validate condition
                is_valid, message, details = operator(
                    document, related_documents, condition
                )
                
                # Create issue if validation failed
                if not is_valid:
                    issue = ValidationIssue(
                        rule_id=rule.id,
                        document_id=document.id,
                        status=ValidationStatus.FAIL,
                        severity=self._determine_severity(rule, condition),
                        message=message,
                        details=details
                    )
                    issues.append(issue)
        
        except Exception as e:
            logger.error(f"Error validating rule {rule.id}: {str(e)}")
            issue = ValidationIssue(
                rule_id=rule.id,
                document_id=document.id,
                status=ValidationStatus.ERROR,
                severity=ValidationSeverity.HIGH,
                message=f"Error validating rule: {str(e)}",
                details={"error": str(e)}
            )
            issues.append(issue)
        
        # Create validation result
        result = ValidationResult(
            document_id=document.id,
            status=ValidationStatus.PASS if not issues else ValidationStatus.FAIL,
            issues=issues,
            execution_time=(datetime.utcnow() - start_time).total_seconds()
        )
        
        return result
    
    def _validate_equals(
        self, document: Document, related_documents: List[Document], condition: RuleCondition
    ) -> Tuple[bool, str, Dict]:
        """Validate equals condition."""
        value = self._get_field_value(document, condition.field)
        if value is None:
            return False, f"Field {condition.field} not found", {}
        
        is_valid = value == condition.value
        message = (
            f"Field {condition.field} equals {condition.value}"
            if is_valid
            else f"Field {condition.field} ({value}) does not equal {condition.value}"
        )
        
        return is_valid, message, {"actual": value, "expected": condition.value}
    
    def _validate_not_equals(
        self, document: Document, related_documents: List[Document], condition: RuleCondition
    ) -> Tuple[bool, str, Dict]:
        """Validate not equals condition."""
        value = self._get_field_value(document, condition.field)
        if value is None:
            return False, f"Field {condition.field} not found", {}
        
        is_valid = value != condition.value
        message = (
            f"Field {condition.field} does not equal {condition.value}"
            if is_valid
            else f"Field {condition.field} ({value}) equals {condition.value}"
        )
        
        return is_valid, message, {"actual": value, "expected": condition.value}
    
    def _validate_greater_than(
        self, document: Document, related_documents: List[Document], condition: RuleCondition
    ) -> Tuple[bool, str, Dict]:
        """Validate greater than condition."""
        value = self._get_field_value(document, condition.field)
        if value is None:
            return False, f"Field {condition.field} not found", {}
        
        is_valid = value > condition.value
        message = (
            f"Field {condition.field} is greater than {condition.value}"
            if is_valid
            else f"Field {condition.field} ({value}) is not greater than {condition.value}"
        )
        
        return is_valid, message, {"actual": value, "expected": condition.value}
    
    def _validate_less_than(
        self, document: Document, related_documents: List[Document], condition: RuleCondition
    ) -> Tuple[bool, str, Dict]:
        """Validate less than condition."""
        value = self._get_field_value(document, condition.field)
        if value is None:
            return False, f"Field {condition.field} not found", {}
        
        is_valid = value < condition.value
        message = (
            f"Field {condition.field} is less than {condition.value}"
            if is_valid
            else f"Field {condition.field} ({value}) is not less than {condition.value}"
        )
        
        return is_valid, message, {"actual": value, "expected": condition.value}
    
    def _validate_greater_than_equals(
        self, document: Document, related_documents: List[Document], condition: RuleCondition
    ) -> Tuple[bool, str, Dict]:
        """Validate greater than or equals condition."""
        value = self._get_field_value(document, condition.field)
        if value is None:
            return False, f"Field {condition.field} not found", {}
        
        is_valid = value >= condition.value
        message = (
            f"Field {condition.field} is greater than or equal to {condition.value}"
            if is_valid
            else f"Field {condition.field} ({value}) is not greater than or equal to {condition.value}"
        )
        
        return is_valid, message, {"actual": value, "expected": condition.value}
    
    def _validate_less_than_equals(
        self, document: Document, related_documents: List[Document], condition: RuleCondition
    ) -> Tuple[bool, str, Dict]:
        """Validate less than or equals condition."""
        value = self._get_field_value(document, condition.field)
        if value is None:
            return False, f"Field {condition.field} not found", {}
        
        is_valid = value <= condition.value
        message = (
            f"Field {condition.field} is less than or equal to {condition.value}"
            if is_valid
            else f"Field {condition.field} ({value}) is not less than or equal to {condition.value}"
        )
        
        return is_valid, message, {"actual": value, "expected": condition.value}
    
    def _validate_contains(
        self, document: Document, related_documents: List[Document], condition: RuleCondition
    ) -> Tuple[bool, str, Dict]:
        """Validate contains condition."""
        value = self._get_field_value(document, condition.field)
        if value is None:
            return False, f"Field {condition.field} not found", {}
        
        is_valid = condition.value in value
        message = (
            f"Field {condition.field} contains {condition.value}"
            if is_valid
            else f"Field {condition.field} ({value}) does not contain {condition.value}"
        )
        
        return is_valid, message, {"actual": value, "expected": condition.value}
    
    def _validate_not_contains(
        self, document: Document, related_documents: List[Document], condition: RuleCondition
    ) -> Tuple[bool, str, Dict]:
        """Validate not contains condition."""
        value = self._get_field_value(document, condition.field)
        if value is None:
            return False, f"Field {condition.field} not found", {}
        
        is_valid = condition.value not in value
        message = (
            f"Field {condition.field} does not contain {condition.value}"
            if is_valid
            else f"Field {condition.field} ({value}) contains {condition.value}"
        )
        
        return is_valid, message, {"actual": value, "expected": condition.value}
    
    def _validate_between(
        self, document: Document, related_documents: List[Document], condition: RuleCondition
    ) -> Tuple[bool, str, Dict]:
        """Validate between condition."""
        value = self._get_field_value(document, condition.field)
        if value is None:
            return False, f"Field {condition.field} not found", {}
        
        min_value, max_value = condition.value
        is_valid = min_value <= value <= max_value
        message = (
            f"Field {condition.field} is between {min_value} and {max_value}"
            if is_valid
            else f"Field {condition.field} ({value}) is not between {min_value} and {max_value}"
        )
        
        return is_valid, message, {
            "actual": value,
            "min": min_value,
            "max": max_value
        }
    
    def _validate_not_between(
        self, document: Document, related_documents: List[Document], condition: RuleCondition
    ) -> Tuple[bool, str, Dict]:
        """Validate not between condition."""
        value = self._get_field_value(document, condition.field)
        if value is None:
            return False, f"Field {condition.field} not found", {}
        
        min_value, max_value = condition.value
        is_valid = not (min_value <= value <= max_value)
        message = (
            f"Field {condition.field} is not between {min_value} and {max_value}"
            if is_valid
            else f"Field {condition.field} ({value}) is between {min_value} and {max_value}"
        )
        
        return is_valid, message, {
            "actual": value,
            "min": min_value,
            "max": max_value
        }
    
    def _validate_matches(
        self, document: Document, related_documents: List[Document], condition: RuleCondition
    ) -> Tuple[bool, str, Dict]:
        """Validate matches condition."""
        value = self._get_field_value(document, condition.field)
        if value is None:
            return False, f"Field {condition.field} not found", {}
        
        # TODO: Implement pattern matching
        return False, "Pattern matching not implemented", {}
    
    def _validate_not_matches(
        self, document: Document, related_documents: List[Document], condition: RuleCondition
    ) -> Tuple[bool, str, Dict]:
        """Validate not matches condition."""
        value = self._get_field_value(document, condition.field)
        if value is None:
            return False, f"Field {condition.field} not found", {}
        
        # TODO: Implement pattern matching
        return False, "Pattern matching not implemented", {}
    
    def _get_field_value(self, document: Document, field: str) -> Any:
        """Get value of a field from a document.
        
        Args:
            document: Document to get field from
            field: Field name
            
        Returns:
            Field value
        """
        # Try to get value from document attributes
        if hasattr(document, field):
            return getattr(document, field)
        
        # Try to get value from extracted data
        if field in document.extracted_data:
            return document.extracted_data[field]
        
        return None
    
    def _determine_severity(self, rule: Rule, condition: RuleCondition) -> ValidationSeverity:
        """Determine severity of a validation issue.
        
        Args:
            rule: Rule that failed
            condition: Condition that failed
            
        Returns:
            Validation severity
        """
        # TODO: Implement more sophisticated severity determination
        return ValidationSeverity.HIGH
    
    def _create_summary(self, validation_results: List[ValidationResult]) -> Dict:
        """Create summary of validation results.
        
        Args:
            validation_results: List of validation results
            
        Returns:
            Summary dictionary
        """
        total_rules = len(validation_results)
        passed_rules = sum(1 for r in validation_results if r.status == ValidationStatus.PASS)
        failed_rules = sum(1 for r in validation_results if r.status == ValidationStatus.FAIL)
        error_rules = sum(1 for r in validation_results if r.status == ValidationStatus.ERROR)
        
        total_issues = sum(len(r.issues) for r in validation_results)
        
        return {
            "total_rules": total_rules,
            "passed_rules": passed_rules,
            "failed_rules": failed_rules,
            "error_rules": error_rules,
            "total_issues": total_issues,
            "pass_rate": (passed_rules / total_rules) * 100 if total_rules > 0 else 0
        } 