import json
from typing import Dict, Any, List, Union
from llm_agent import llm_explain_failure
import re

def get_nested_value(documents: Dict[str, Any], path: str) -> Any:
    parts = path.split('.')
    current = documents
    for i, part in enumerate(parts):
        if isinstance(current, dict):
            if part in current:
                current = current[part]
            elif "fields" in current and part in current["fields"]:
                current = current["fields"][part]
            else:
                return None
        elif isinstance(current, list):
            if part == '*':
                return current  # wildcard for aggregation
            try:
                idx = int(part)
                current = current[idx]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current

def aggregate_values(data: List[Dict[str, Any]], field: str, agg_type="sum") -> Union[float, None]:
    try:
        values = [float(row.get(field, 0)) for row in data if field in row]
        if agg_type == "sum":
            return sum(values)
        elif agg_type == "max":
            return max(values)
        elif agg_type == "min":
            return min(values)
    except Exception:
        return None

def compare_values(a: Any, b: Any, check_type: str, parameters: Dict[str, Any] = None) -> bool:
    try:
        if check_type == "equality":
            return a == b
        elif check_type == "less_than_or_equal":
            return float(a) <= float(b)
        elif check_type == "tolerance":
            tolerance = parameters.get("tolerance_percent", 0)
            return abs(float(a) - float(b)) <= (tolerance / 100.0) * float(b)
        elif check_type == "lookup":
            return a in b
        elif check_type == "date_after":
            from dateutil.parser import parse
            return parse(a) > parse(b)
        elif check_type == "date_before":
            from dateutil.parser import parse
            return parse(a) < parse(b)
    except Exception:
        return False
    return False

def evaluate_rule(rule: Dict[str, Any], documents: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a single rule against the documents.
    
    Args:
        rule: The rule to evaluate
        documents: Dictionary of parsed documents
        
    Returns:
        Dict containing evaluation results
    """
    try:
        # Extract rule components
        rule_id = rule.get('rule_id', '')
        condition = rule.get('condition', '')
        on_fail = rule.get('on_fail', '')
        document_type = rule.get('document_type', '')
        
        # Get the target document
        if document_type not in documents:
            return {
                "rule_id": rule_id,
                "result": "error",
                "reason": f"Document type '{document_type}' not found",
                "details": {}
            }
            
        doc = documents[document_type]
        fields = doc.get('fields', {})
        
        # Handle different condition types
        if condition.startswith('field_exists'):
            # Extract field name from condition
            field_name = condition.split('(')[1].split(')')[0].strip()
            result = field_name in fields
            return {
                "rule_id": rule_id,
                "result": "pass" if result else "fail",
                "reason": on_fail if not result else None,
                "details": {
                    "field": field_name,
                    "exists": result
                }
            }
            
        elif condition.startswith('field_equals'):
            # Extract field name and value from condition
            parts = condition.split('(')[1].split(')')[0].split(',')
            field_name = parts[0].strip()
            expected_value = parts[1].strip().strip("'")
            
            if field_name not in fields:
                return {
                    "rule_id": rule_id,
                    "result": "error",
                    "reason": f"Field '{field_name}' not found",
                    "details": {
                        "field": field_name,
                        "expected": expected_value
                    }
                }
                
            actual_value = fields[field_name]
            result = str(actual_value) == expected_value
            
            return {
                "rule_id": rule_id,
                "result": "pass" if result else "fail",
                "reason": on_fail if not result else None,
                "details": {
                    "field": field_name,
                    "expected": expected_value,
                    "actual": actual_value
                }
            }
            
        elif condition.startswith('field_matches'):
            # Extract field name and pattern from condition
            parts = condition.split('(')[1].split(')')[0].split(',')
            field_name = parts[0].strip()
            pattern = parts[1].strip().strip("'")
            
            if field_name not in fields:
                return {
                    "rule_id": rule_id,
                    "result": "error",
                    "reason": f"Field '{field_name}' not found",
                    "details": {
                        "field": field_name,
                        "pattern": pattern
                    }
                }
                
            actual_value = fields[field_name]
            result = bool(re.match(pattern, str(actual_value)))
            
            return {
                "rule_id": rule_id,
                "result": "pass" if result else "fail",
                "reason": on_fail if not result else None,
                "details": {
                    "field": field_name,
                    "pattern": pattern,
                    "actual": actual_value
                }
            }
            
        elif condition.startswith('cross_document_match'):
            # Extract field names from condition
            parts = condition.split('(')[1].split(')')[0].split(',')
            source_field = parts[0].strip()
            target_doc_type = parts[1].strip()
            target_field = parts[2].strip()
            
            if source_field not in fields:
                return {
                    "rule_id": rule_id,
                    "result": "error",
                    "reason": f"Source field '{source_field}' not found",
                    "details": {
                        "source_field": source_field,
                        "target_doc": target_doc_type,
                        "target_field": target_field
                    }
                }
                
            if target_doc_type not in documents:
                return {
                    "rule_id": rule_id,
                    "result": "error",
                    "reason": f"Target document '{target_doc_type}' not found",
                    "details": {
                        "source_field": source_field,
                        "target_doc": target_doc_type,
                        "target_field": target_field
                    }
                }
                
            target_fields = documents[target_doc_type].get('fields', {})
            if target_field not in target_fields:
                return {
                    "rule_id": rule_id,
                    "result": "error",
                    "reason": f"Target field '{target_field}' not found in {target_doc_type}",
                    "details": {
                        "source_field": source_field,
                        "target_doc": target_doc_type,
                        "target_field": target_field
                    }
                }
                
            source_value = fields[source_field]
            target_value = target_fields[target_field]
            result = str(source_value) == str(target_value)
            
            return {
                "rule_id": rule_id,
                "result": "pass" if result else "fail",
                "reason": on_fail if not result else None,
                "details": {
                    "source_field": source_field,
                    "source_value": source_value,
                    "target_doc": target_doc_type,
                    "target_field": target_field,
                    "target_value": target_value
                }
            }
            
        elif condition.startswith('amount_within_tolerance'):
            # Extract field names and tolerance from condition
            parts = condition.split('(')[1].split(')')[0].split(',')
            source_field = parts[0].strip()
            target_doc_type = parts[1].strip()
            target_field = parts[2].strip()
            tolerance = float(parts[3].strip())
            
            if source_field not in fields:
                return {
                    "rule_id": rule_id,
                    "result": "error",
                    "reason": f"Source field '{source_field}' not found",
                    "details": {
                        "source_field": source_field,
                        "target_doc": target_doc_type,
                        "target_field": target_field,
                        "tolerance": tolerance
                    }
                }
                
            if target_doc_type not in documents:
                return {
                    "rule_id": rule_id,
                    "result": "error",
                    "reason": f"Target document '{target_doc_type}' not found",
                    "details": {
                        "source_field": source_field,
                        "target_doc": target_doc_type,
                        "target_field": target_field,
                        "tolerance": tolerance
                    }
                }
                
            target_fields = documents[target_doc_type].get('fields', {})
            if target_field not in target_fields:
                return {
                    "rule_id": rule_id,
                    "result": "error",
                    "reason": f"Target field '{target_field}' not found in {target_doc_type}",
                    "details": {
                        "source_field": source_field,
                        "target_doc": target_doc_type,
                        "target_field": target_field,
                        "tolerance": tolerance
                    }
                }
                
            try:
                source_value = float(str(fields[source_field]).replace('$', '').replace(',', ''))
                target_value = float(str(target_fields[target_field]).replace('$', '').replace(',', ''))
                
                # Calculate percentage difference
                if target_value == 0:
                    return {
                        "rule_id": rule_id,
                        "result": "error",
                        "reason": "Target value cannot be zero for percentage calculation",
                        "details": {
                            "source_field": source_field,
                            "source_value": source_value,
                            "target_doc": target_doc_type,
                            "target_field": target_field,
                            "target_value": target_value,
                            "tolerance": tolerance
                        }
                    }
                    
                percentage_diff = abs((source_value - target_value) / target_value * 100)
                result = percentage_diff <= tolerance
                
                return {
                    "rule_id": rule_id,
                    "result": "pass" if result else "fail",
                    "reason": on_fail if not result else None,
                    "details": {
                        "source_field": source_field,
                        "source_value": source_value,
                        "target_doc": target_doc_type,
                        "target_field": target_field,
                        "target_value": target_value,
                        "tolerance": tolerance,
                        "percentage_diff": percentage_diff
                    }
                }
                
            except (ValueError, TypeError):
                return {
                    "rule_id": rule_id,
                    "result": "error",
                    "reason": "Invalid numeric values for amount comparison",
                    "details": {
                        "source_field": source_field,
                        "source_value": fields[source_field],
                        "target_doc": target_doc_type,
                        "target_field": target_field,
                        "target_value": target_fields[target_field],
                        "tolerance": tolerance
                    }
                }
                
        else:
            return {
                "rule_id": rule_id,
                "result": "error",
                "reason": f"Unknown condition type: {condition}",
                "details": {}
            }
            
    except Exception as e:
        return {
            "rule_id": rule_id,
            "result": "error",
            "reason": f"Error evaluating rule: {str(e)}",
            "details": {}
        }

def evaluate_all_rules(rules: List[Dict[str, Any]], documents: Dict[str, Dict[str, Any]], enable_llm: bool = False) -> List[Dict[str, Any]]:
    return [evaluate_rule(rule, documents) for rule in rules]

def filter_rules_for_docs(rules: List[Dict[str, Any]], docs: Dict[str, Any]) -> List[Dict[str, Any]]:
    available = set(docs.keys())
    return [r for r in rules if set(r["applies_to"]).issubset(available)]
