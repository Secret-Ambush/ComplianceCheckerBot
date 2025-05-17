import json
from typing import Dict, Any, List, Union
from llm_agent import llm_explain_failure

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

def is_literal(value: str) -> bool:
    try:
        float(value.replace(',', ''))
        return True
    except (ValueError, AttributeError):
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

        # Handle literals and reference lookups
        if isinstance(b_path, (int, float)):
            b_value = b_path
        elif isinstance(b_path, str) and is_literal(b_path):
            b_value = float(b_path.replace(',', ''))
        elif isinstance(b_path, str) and "reference" in b_path:
            b_value = documents.get("reference", {}).get(b_path.split('.')[-1], [])
        else:
            b_value = get_nested_value(documents, b_path)

        values[a_path] = a_value
        values[b_path] = b_value
        result = compare_values(a_value, b_value, check_type, rule.get("parameters", {}))

    result_obj = {
        "rule_id": rule["rule_id"],
        "result": "pass" if result else "fail",
        "reason": None if result else rule["on_fail"],
        "details": values
    }

    if not result and enable_llm:
        try:
            result_obj["llm_commentary"] = llm_explain_failure(rule, values, documents)
        except Exception as e:
            result_obj["llm_commentary"] = f"LLM explanation unavailable: {e}"

    return result_obj

def evaluate_all_rules(rules: List[Dict[str, Any]], documents: Dict[str, Dict[str, Any]], enable_llm: bool = False) -> List[Dict[str, Any]]:
    return [evaluate_rule(rule, documents, enable_llm) for rule in rules]

def filter_rules_for_docs(rules: List[Dict[str, Any]], docs: Dict[str, Any]) -> List[Dict[str, Any]]:
    available = set(docs.keys())
    return [r for r in rules if set(r["applies_to"]).issubset(available)]

# Example Test:
# if __name__ == "__main__":
#     rules = json.load(open("compliance_rules.json"))
#     documents = {
#         "invoice": {
#             "filename": "invoice (1).PDF",
#             "doc_type": "invoice",
#             "vendor": "generic",
#             "fields": {
#                 "po_number": "1002475",
#                 "invoice_number": "626867-ADS1-1",
#                 "invoice_date": "12-Aug-2023",
#                 "currency": "AED",
#                 "total_amount": "168.70"
#             }
#         },
#         "reference": {
#             "approved_vendors": ['generic'],
#             "allowed_currencies": ['AED']
#         }
#     }
#     relevant_rules = filter_rules_for_docs(rules, documents)
#     results = evaluate_all_rules(relevant_rules, documents, enable_llm=True)
#     print(json.dumps(results, indent=2))
