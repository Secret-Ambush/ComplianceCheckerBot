from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv

# Load your OpenAI API key from environment or set directly
load_dotenv()
llm = ChatOpenAI(temperature=0, model="gpt-4", openai_api_key=os.getenv("OPENAI_API_KEY"))

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
