from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from document_reader import process_document
from compliance_agent import evaluate_all_rules
from llm_agent import llm_explain_failure
from pathlib import Path
import json

# --- CrewAI-Compatible Tool Classes ---
class ExtractAndParseDocumentTool(BaseTool):
    name: str = "extract_and_parse_document"
    description: str = "Extracts fields and tables from a business document and returns structured JSON."

    def _run(self, file_path: str) -> str:
        return json.dumps(process_document(Path(file_path)))


class EvaluateComplianceRulesTool(BaseTool):
    name: str = "evaluate_compliance_rules"
    description: str = "Evaluates parsed document against structured rules and returns results as JSON."

    def _run(self, document_json: str, rules_json: str) -> str:
        document = json.loads(document_json)
        rules = json.loads(rules_json)
        return json.dumps(evaluate_all_rules(rules, {"primary": document}))


class ExplainComplianceFailureTool(BaseTool):
    name: str = "explain_compliance_failure"
    description: str = "Uses an LLM to explain why a compliance rule failed."

    def _run(self, rule_json: str, values_json: str, doc_json: str) -> str:
        return llm_explain_failure(
            json.loads(rule_json),
            json.loads(values_json),
            json.loads(doc_json)
        )

# --- Define Agents ---
document_parser = Agent(
    role="Document Parser",
    goal="Extract structured data from business documents.",
    backstory="Expert in OCR and field extraction.",
    tools=[ExtractAndParseDocumentTool()],
    verbose=True
)

compliance_checker = Agent(
    role="Compliance Rule Evaluator",
    goal="Validate parsed document fields using structured rules.",
    backstory="Compliance officer trained in document consistency checking.",
    tools=[EvaluateComplianceRulesTool()],
    verbose=True
)

explainer = Agent(
    role="LLM Failure Explainer",
    goal="Explain why rules failed in simple, clear language.",
    backstory="Assistant who makes audit results understandable using LLM insights.",
    tools=[ExplainComplianceFailureTool()],
    verbose=True
)

# --- Define Tasks ---
parse_task = Task(
    description="Parse the document at {{file_path}} and return structured fields and tables.",
    agent=document_parser,
    expected_output="A JSON string containing extracted fields and table data from the document."
)

evaluate_task = Task(
    description="Evaluate the parsed document {{parse_task.output}} using rules from {{rules_json}}.",
    agent=compliance_checker,
    expected_output="A JSON string representing the results of rule evaluations, with rule ID, pass/fail status, and any reasons."
)

explain_task = Task(
    description="Explain why the rule {{failed_rule}} failed based on the values {{rule_values}} and document {{parse_task.output}}.",
    agent=explainer,
    expected_output="A human-readable string explaining the logic behind the rule failure using LLM insights."
)

# --- Assemble Crew ---
crew = Crew(
    agents=[document_parser, compliance_checker, explainer],
    tasks=[parse_task, evaluate_task, explain_task],
    verbose=True
)

# --- Run the Crew ---
def run_crew_pipeline(file_path: str, rules_json: str, log_fn=None):
    if log_fn: log_fn("🚀 Running parse + evaluate crew...")
    partial_crew = Crew(
        agents=[document_parser, compliance_checker],
        tasks=[parse_task, evaluate_task],
        verbose=False
    )

    if log_fn: log_fn("✅ Parsed document. Evaluating rules...")
    partial_result = partial_crew.kickoff(inputs={
        "file_path": file_path,
        "rules_json": rules_json
    })

    eval_results = json.loads(partial_result)
    parsed_document = eval_results.get("parse_task", "")
    rule_outcomes = json.loads(eval_results.get("evaluate_task", "[]"))

    for r in rule_outcomes:
        if r["result"] == "fail":
            if log_fn: log_fn(f"❌ Rule `{r['rule_id']}` failed. Generating explanation...")
            explanation_crew = Crew(
                agents=[explainer],
                tasks=[explain_task],
                verbose=False
            )
            if log_fn: log_fn(f"💬 Explanation ready for `{r['rule_id']}`")
            explanation = explanation_crew.kickoff(inputs={
                "failed_rule": json.dumps({"rule_id": r["rule_id"], "on_fail": r["reason"]}),
                "rule_values": json.dumps(r["details"]),
                "parsed_document": parsed_document
            })

            r["llm_commentary"] = explanation

    return parsed_document, rule_outcomes