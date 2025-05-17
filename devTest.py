
import json
from nl_rule_parser import parse_natural_rule
from compliance_agent import evaluate_rule
from document_reader import process_document

# Load a preprocessed sample document
documents = {
    "invoice": process_document("invoice (1).PDF"),
    "reference": {
        "approved_vendors": ["generic"],
        "allowed_currencies": ["AED"]
    }
}

print("📄 Document types loaded:", list(documents.keys()))

while True:
    instruction = input("\nEnter a compliance rule (or type 'exit'): ").strip()
    if instruction.lower() == "exit":
        break

    try:
        rule = parse_natural_rule(instruction)
        result = evaluate_rule(rule, documents, enable_llm=True)

        print(f"\n✅ Rule Result: {result['result'].upper()}")
        print(f"🔎 Rule ID: {result['rule_id']}")
        if result["result"] == "fail":
            print(f"❌ Reason: {result['reason']}")
            if "llm_commentary" in result:
                print(f"🧠 LLM Insight: {result['llm_commentary']}")
        else:
            print("✅ All checks passed.")
    except Exception as e:
        print(f"⚠️ Error: {e}")
