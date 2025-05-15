from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
import os

# Load your OpenAI API key from environment or set directly
os.environ["OPENAI_API_KEY"] = "your-api-key-here"  # Replace or load securely

llm = ChatOpenAI(temperature=0, model="gpt-4")

def llm_explain_failure(rule, values, documents) -> str:
    rule_text = rule.get("description", rule["rule_id"])
    prompt = f"""
    A compliance rule failed during automated checking.

    Rule: {rule_text}
    Reason: {rule.get('on_fail', 'No specific failure reason provided.')}

    Extracted Values:
    {values}

    Provide a human-readable explanation of why this rule failed.
    Suggest what might be missing or incorrect and how it could be fixed in the documents.
    """
    response = llm([HumanMessage(content=prompt)])
    return response.content

# Example usage:
# result = {
#     "rule_id": "LOOKUP_001",
#     "result": "fail",
#     "reason": "Vendor is not on the approved vendor list",
#     "details": {"invoice.vendor_id": None, "reference.approved_vendors": ["generic"]}
# }
# explanation = llm_explain_failure(rule, result["details"], documents)
# print(explanation)
