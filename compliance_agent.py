import json
from typing import Dict, Any, List, Union


def get_nested_value(documents: Dict[str, Any], path: str) -> Any:
    parts = path.split('.')
    current = documents
    for i, part in enumerate(parts):
        if part in current:
            current = current[part]
        elif i == 1 and "fields" in current:
            current = current["fields"]
            if part in current:
                current = current[part]
            else:
                return None
        else:
            return None
    return current


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
        elif check_type == "expression":
            q = float(get_nested_value(documents, parameters["quantity"]))
            p = float(get_nested_value(documents, parameters["unit_price"]))
            return float(a) == q * p
    except Exception:
        return False
    return False


def evaluate_rule(rule: Dict[str, Any], documents: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
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

        # Interpret b_path either as a field path or as a literal value
        if isinstance(b_path, str) and b_path.replace('.', '', 1).isdigit():
            b_value = float(b_path)
        elif "reference" not in b_path:
            b_value = get_nested_value(documents, b_path)
        else:
            b_value = documents.get("reference", {}).get(b_path.split('.')[-1], [])

        values[a_path] = a_value
        values[b_path] = b_value
        result = compare_values(a_value, b_value, check_type, rule.get("parameters", {}))

    return {
        "rule_id": rule["rule_id"],
        "result": "pass" if result else "fail",
        "reason": None if result else rule["on_fail"],
        "details": values
    }


def evaluate_all_rules(rules: List[Dict[str, Any]], documents: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [evaluate_rule(rule, documents) for rule in rules]


def filter_rules_for_docs(rules: List[Dict[str, Any]], docs: Dict[str, Any]) -> List[Dict[str, Any]]:
    available = set(docs.keys())
    return [r for r in rules if set(r["applies_to"]).issubset(available)]

# Example usage (not included in final module):
rules = json.load(open("compliance_rules.json"))
documents = {
    "invoice": {
        "filename": "invoice (1).PDF",
        "doc_type": "invoice",
        "vendor": "generic",
        "fields": {
            "po_number": "1002475",
            "invoice_number": "626867-ADS1-1",
            "invoice_date": "12-Aug-2023",
            "currency": "AED",
            "total_amount": "168.70"
        }
    },
    "reference": {"approved_vendors": ['generic'], "allowed_currencies": ['AED']}
}
relevant_rules = filter_rules_for_docs(rules, documents)
results = evaluate_all_rules(relevant_rules, documents)
print(results)
