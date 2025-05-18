import json
from typing import Dict, Any, List, Union
from llm_agent import llm_explain_failure

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

def evaluate_rule(rule: Dict[str, Any], documents: Dict[str, Dict[str, Any]], enable_llm: bool = False) -> Dict[str, Any]:
    check_type = rule["check_type"]
    fields = rule["fields"]
    values = {}

    if check_type == "expression":
        total_path = list(fields.keys())[0]
        values[total_path] = get_nested_value(documents, total_path)
        result = compare_values(values[total_path], None, check_type, {
            "quantity": fields[total_path][0],
            "unit_price": fields[total_path][1]
        })
    else:
        a_path, b_path = list(fields.items())[0]
        a_value = get_nested_value(documents, a_path)

        if isinstance(b_path, (int, float)):
            b_value = b_path
        elif isinstance(b_path, str):
            if "[*]" in b_path:
                list_path, field = b_path.split("[*].")
                list_data = get_nested_value(documents, list_path)
                b_value = aggregate_values(list_data, field, "sum")
            elif "." in b_path and not b_path.startswith("reference."):
                b_value = get_nested_value(documents, b_path)
            elif b_path.startswith("reference."):
                b_value = documents.get("reference", {}).get(b_path.split('.')[-1], [])
            else:
                b_value = b_path  # literal
        else:
            b_value = None

        values[a_path] = a_value
        values[str(b_path)] = b_value
        result = compare_values(a_value, b_value, check_type, rule.get("parameters", {}))

    result_obj = {
        "rule_id": rule["rule_id"],
        "result": "pass" if result else "fail",
        "reason": None if result else rule["on_fail"],
        "details": values
    }

    if not result and enable_llm:
        try:
            # result_obj["llm_commentary"] = llm_explain_failure(rule, values, documents)
            pass
        except Exception as e:
            result_obj["llm_commentary"] = f"LLM explanation unavailable: {e}"

    return result_obj

def evaluate_all_rules(rules: List[Dict[str, Any]], documents: Dict[str, Dict[str, Any]], enable_llm: bool = False) -> List[Dict[str, Any]]:
    return [evaluate_rule(rule, documents, enable_llm) for rule in rules]

def filter_rules_for_docs(rules: List[Dict[str, Any]], docs: Dict[str, Any]) -> List[Dict[str, Any]]:
    available = set(docs.keys())
    return [r for r in rules if set(r["applies_to"]).issubset(available)]
