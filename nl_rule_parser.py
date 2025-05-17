
import os
import json
from typing import Dict
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(temperature=0, model="gpt-4", openai_api_key=os.getenv("OPENAI_API_KEY"))

def parse_natural_rule(instruction: str) -> Dict:
    RULE_GEN_PROMPT = f"""
    You are an AI assistant that converts compliance instructions into structured JSON rules.
    Each rule must follow this format:

    {{
      "rule_id": "<generated_unique_id>",
      "description": "<copy of the original instruction>",
      "applies_to": ["<document_type_1>", "<document_type_2>"],
      "fields": {{
        "<field_path_1>": "<field_path_2 or reference list>"
      }},
      "check_type": "<equality | less_than_or_equal | lookup | date_after | date_before | expression | tolerance>",
      "on_fail": "<human-readable explanation of what went wrong>"
    }}

    Only return a single valid JSON object. Do not include extra text or explanation.

    Examples:

    ---

    Instruction:
    "Ensure invoice and PO have the same PO number."

    Output:
    {{
      "rule_id": "RULE_INV_PO_001",
      "description": "Ensure invoice and PO have the same PO number.",
      "applies_to": ["invoice", "purchase_order"],
      "fields": {{
        "invoice.fields.po_number": "purchase_order.fields.po_number"
      }},
      "check_type": "equality",
      "on_fail": "PO numbers do not match between invoice and PO"
    }}

    ---

    Instruction:
    "Check that invoice date is on or after GRN date."

    Output:
    {{
      "rule_id": "RULE_INV_GRN_DATE_001",
      "description": "Check that invoice date is on or after GRN date.",
      "applies_to": ["invoice", "grn"],
      "fields": {{
        "invoice.fields.invoice_date": "grn.fields.date"
      }},
      "check_type": "date_after",
      "on_fail": "Invoice date is earlier than GRN date"
    }}

    ---

    Now convert this instruction to a rule (only return JSON):

    Instruction:
    "{instruction}"
    """

    response = llm([HumanMessage(content=RULE_GEN_PROMPT)])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]

    rule = json.loads(raw)

    required_keys = ["rule_id", "description", "applies_to", "fields", "check_type", "on_fail"]
    for key in required_keys:
        if key not in rule:
            raise ValueError(f"Missing required key: {key}")

    return rule
