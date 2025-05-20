from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from document_reader import process_document
from compliance_agent import evaluate_all_rules
from llm_agent import llm_explain_failure
from pathlib import Path
import json
from functools import lru_cache
from typing import Dict, List, Any

# --- CrewAI-Compatible Tool Classes ---
class ExtractAndParseDocumentTool(BaseTool):
    name: str = "extract_and_parse_document"
    description: str = "Extracts fields and tables from a business document and returns structured JSON."

    def _run(self, file_path: str) -> str:
        return json.dumps(process_document(Path(file_path)))

class MatchDocumentsTool(BaseTool):
    name: str = "match_documents"
    description: str = "Matches related documents based on key identifiers and returns matched pairs."

    def _run(self, documents_json: str) -> str:
        documents = json.loads(documents_json)
        # Implement document matching logic here
        # For now, return a simple structure
        return json.dumps({
            "matches": [
                {
                    "primary": "invoice",
                    "related": ["po", "grn"],
                    "key": "po_number"
                }
            ]
        })

class EvaluateComplianceRulesTool(BaseTool):
    name: str = "evaluate_compliance_rules"
    description: str = "Evaluates parsed documents against structured rules and returns results as JSON."

    def _run(self, documents_json: str, rules_json: str) -> str:
        try:
            documents = json.loads(documents_json)
            rules = json.loads(rules_json)
            results = evaluate_all_rules(rules, documents)
            # Ensure the result is valid JSON
            return json.dumps(results)
        except Exception as e:
            # Return a valid JSON error response
            return json.dumps({
                "error": str(e),
                "result": "error",
                "details": {
                    "message": "Failed to evaluate rules",
                    "exception": str(e)
                }
            })

class ExplainComplianceFailureTool(BaseTool):
    name: str = "explain_compliance_failure"
    description: str = "Uses an LLM to explain why a compliance rule failed."

    def _run(self, rule_json: str, values_json: str, docs_json: str) -> str:
        return llm_explain_failure(
            json.loads(rule_json),
            json.loads(values_json),
            json.loads(docs_json)
        )

# Cache the tools
@lru_cache(maxsize=1)
def get_tools():
    return {
        'extract': ExtractAndParseDocumentTool(),
        'match': MatchDocumentsTool(),
        'evaluate': EvaluateComplianceRulesTool(),
        'explain': ExplainComplianceFailureTool()
    }

# Cache the agents
@lru_cache(maxsize=1)
def get_agents():
    tools = get_tools()
    return {
        'parser': Agent(
            role="Document Parser",
            goal="Extract structured data from business documents.",
            backstory="Expert in OCR and field extraction.",
            tools=[tools['extract']],
            verbose=True
        ),
        'matcher': Agent(
            role="Document Matcher",
            goal="Match related documents based on key identifiers.",
            backstory="Expert in document relationship analysis.",
            tools=[tools['match']],
            verbose=True
        ),
        'checker': Agent(
            role="Compliance Rule Evaluator",
            goal="Validate parsed document fields using structured rules.",
            backstory="Compliance officer trained in document consistency checking.",
            tools=[tools['evaluate']],
            verbose=True
        ),
        'explainer': Agent(
            role="LLM Failure Explainer",
            goal="Explain why rules failed in simple, clear language.",
            backstory="Assistant who makes audit results understandable using LLM insights.",
            tools=[tools['explain']],
            verbose=True
        )
    }

# Cache the tasks
@lru_cache(maxsize=1)
def get_tasks():
    agents = get_agents()
    return {
        'parse': Task(
            description="Parse all documents and return structured fields and tables.",
            agent=agents['parser'],
            expected_output="A JSON string containing extracted fields and table data from all documents."
        ),
        'match': Task(
            description="Match related documents based on key identifiers.",
            agent=agents['matcher'],
            expected_output="A JSON string containing matched document pairs and their relationships."
        ),
        'evaluate': Task(
            description="Evaluate the parsed and matched documents using rules from {{rules_json}}.",
            agent=agents['checker'],
            expected_output="A JSON string representing the results of rule evaluations."
        ),
        'explain': Task(
            description="Explain why the rule {{failed_rule}} failed based on the values {{rule_values}} and documents {{docs_json}}.",
            agent=agents['explainer'],
            expected_output="A human-readable string explaining the logic behind the rule failure."
        )
    }

# Cache the crew
@lru_cache(maxsize=1)
def get_crew():
    agents = get_agents()
    tasks = get_tasks()
    return Crew(
        agents=[agents['parser'], agents['matcher'], agents['checker']],
        tasks=[tasks['parse'], tasks['match'], tasks['evaluate']],
        verbose=False
    )

def run_crew_pipeline(
    file_paths: Dict[str, str],
    rules_json: str,
    log_fn=None
) -> tuple[str, List[Dict[str, Any]]]:
    """
    Run the compliance check pipeline on multiple documents.
    
    Args:
        file_paths: Dictionary mapping document types to their file paths
        rules_json: JSON string containing the rules to evaluate
        log_fn: Optional logging function
    
    Returns:
        tuple: (parsed_documents_json, rule_results)
    """
    if log_fn: log_fn("🚀 Starting compliance check pipeline...")
    
    # Get the cached components
    agents = get_agents()
    tasks = get_tasks()
    
    # Create the main crew for parsing and matching
    main_crew = Crew(
        agents=[agents['parser'], agents['matcher']],
        tasks=[tasks['parse'], tasks['match']],
        verbose=False
    )
    
    # Run the main pipeline
    if log_fn: log_fn("✅ Processing documents...")
    main_result = main_crew.kickoff(inputs={
        "file_paths": json.dumps(file_paths)
    })
    
    # Unpack TaskOutput objects
    parse_out, match_out = main_result.tasks_output
    # Grab your JSON strings (or use .raw_output if that's what your version exposes)
    parsed_documents = parse_out.raw
    matched_documents  = match_out.raw  # Second task: match
    
    # Create evaluation crew
    eval_crew = Crew(
        agents=[agents['checker']],
        tasks=[tasks['evaluate']],
        verbose=False
    )
    
    # Run evaluation
    if log_fn: log_fn("🔍 Evaluating rules...")
    eval_result = eval_crew.kickoff(inputs={
        "documents_json": parsed_documents,
        "rules_json": rules_json
    })
    
    # Unpack the single TaskOutput from the evaluation crew
    eval_out = eval_result.tasks_output[0]
    
    # Add debugging and error handling for JSON parsing
    try:
        if log_fn: log_fn(f"Raw evaluation output: {eval_out.raw}")
        rule_outcomes = json.loads(eval_out.raw)
    except json.JSONDecodeError as e:
        if log_fn: log_fn(f"Error parsing JSON: {str(e)}")
        if log_fn: log_fn(f"Invalid JSON content: {eval_out.raw}")
        # Return empty results instead of failing
        return parsed_documents, []
    
    # Handle failed rules
    failed_rules = [r for r in rule_outcomes if r["result"] == "fail"]
    if failed_rules:
        if log_fn: log_fn("❌ Processing failed rules...")
        explanation_crew = Crew(
            agents=[agents['explainer']],
            tasks=[tasks['explain']],
            verbose=False
        )
        
        for r in failed_rules:
            if log_fn: log_fn(f"💬 Generating explanation for rule `{r['rule_id']}`...")
            explanation_result = explanation_crew.kickoff(inputs={
                "failed_rule": json.dumps({"rule_id": r["rule_id"], "on_fail": r["reason"]}),
                "rule_values": json.dumps(r["details"]),
                "docs_json": parsed_documents
            })
            
            # Correctly access the task output from the CrewOutput object
            explain_out = explanation_result.tasks_output[0]
            r["llm_commentary"] = explain_out.raw
    
    return parsed_documents, rule_outcomes
