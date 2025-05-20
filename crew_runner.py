from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from document_reader import process_document
from compliance_agent import evaluate_all_rules
from llm_agent import llm_explain_failure
from pathlib import Path
import json
from functools import lru_cache
from typing import Dict, List, Any
import tempfile
import os

# --- CrewAI-Compatible Tool Classes ---
class ExtractAndParseDocumentTool(BaseTool):
    name: str = "extract_and_parse_document"
    description: str = "Extracts fields and tables from a business document and returns structured JSON."

    def _run(self, file_paths: str) -> str:
        if not file_paths or not isinstance(file_paths, str):
            return json.dumps({
                "error": "Invalid input: file_paths must be a non-empty string",
                "input": file_paths
            })
        try:
            paths = json.loads(file_paths)
            if not paths:
                return json.dumps({"error": "No file paths provided"})
            
            # Process each document
            results = {}
            for doc_type, file_path in paths.items():
                try:
                    # Verify file exists
                    path = Path(file_path)
                    if not path.exists():
                        results[doc_type] = {
                            "error": f"File not found: {file_path}",
                            "fields": {},
                            "tables": []
                        }
                        continue
                    
                    # Process the document
                    doc_result = process_document(path)
                    if not doc_result:
                        results[doc_type] = {
                            "error": f"Failed to process document: {file_path}",
                            "fields": {},
                            "tables": []
                        }
                        continue
                        
                    results[doc_type] = doc_result
                    
                except Exception as e:
                    results[doc_type] = {
                        "error": f"Error processing {doc_type}: {str(e)}",
                        "fields": {},
                        "tables": []
                    }
            
            # Ensure we have at least one successfully processed document
            if not any("error" not in result for result in results.values()):
                return json.dumps(results)
            
            return json.dumps({
                "error": "No documents were successfully processed",
                "details": results
            })
            
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": f"Invalid JSON input: {str(e)}",
                "input": file_paths
            })
        except Exception as e:
            return json.dumps({
                "error": f"Unexpected error: {str(e)}",
                "input": file_paths
            })

class MatchDocumentsTool(BaseTool):
    name: str = "match_documents"
    description: str = "Matches related documents based on key identifiers and returns matched pairs."

    def _run(self, documents_json: str) -> str:
        documents = json.loads(documents_json)
        matches = []
        
        # Extract key fields for matching
        key_fields = {
            'po_number': ['po_number', 'purchase_order_number', 'po'],
            'invoice_number': ['invoice_number', 'invoice_no', 'inv_number'],
            'delivery_ref': ['delivery_ref', 'grn_number', 'delivery_reference']
        }
        
        # Find matching documents
        for doc_type, doc in documents.items():
            if doc_type == 'reference':
                continue
                
            # Extract fields from the document
            fields = doc.get('fields', {})
            
            # Try to match with other documents
            for other_type, other_doc in documents.items():
                if other_type == doc_type or other_type == 'reference':
                    continue
                    
                other_fields = other_doc.get('fields', {})
                
                # Check for matching PO numbers
                for po_field in key_fields['po_number']:
                    if po_field in fields and po_field in other_fields:
                        if fields[po_field] == other_fields[po_field]:
                            matches.append({
                                'primary': doc_type,
                                'related': other_type,
                                'key': 'po_number',
                                'value': fields[po_field]
                            })
                
                # Check for matching invoice numbers
                for inv_field in key_fields['invoice_number']:
                    if inv_field in fields and inv_field in other_fields:
                        if fields[inv_field] == other_fields[inv_field]:
                            matches.append({
                                'primary': doc_type,
                                'related': other_type,
                                'key': 'invoice_number',
                                'value': fields[inv_field]
                            })
                
                # Check for matching delivery references
                for ref_field in key_fields['delivery_ref']:
                    if ref_field in fields and ref_field in other_fields:
                        if fields[ref_field] == other_fields[ref_field]:
                            matches.append({
                                'primary': doc_type,
                                'related': other_type,
                                'key': 'delivery_ref',
                                'value': fields[ref_field]
                            })
        
        return json.dumps({
            'matches': matches,
            'document_types': list(documents.keys())
        })

class EvaluateComplianceRulesTool(BaseTool):
    name: str = "evaluate_compliance_rules"
    description: str = "Evaluates parsed documents against structured rules and returns results as JSON."

    def _run(self, documents_json: str, rules_json: str) -> str:
        documents = json.loads(documents_json)
        rules = json.loads(rules_json)
        return json.dumps(evaluate_all_rules(rules, documents))

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
            verbose=True,
            max_iterations=3  # Limit parsing attempts
        ),
        'matcher': Agent(
            role="Document Matcher",
            goal="Match related documents based on key identifiers.",
            backstory="Expert in document relationship analysis.",
            tools=[tools['match']],
            verbose=True,
            max_iterations=3  # Limit matching attempts
        ),
        'checker': Agent(
            role="Compliance Rule Evaluator",
            goal="Validate parsed document fields using structured rules.",
            backstory="Compliance officer trained in document consistency checking.",
            tools=[tools['evaluate']],
            verbose=True,
            max_iterations=5  # Allow more iterations for complex rule evaluation
        ),
        'explainer': Agent(
            role="LLM Failure Explainer",
            goal="Explain why rules failed in simple, clear language.",
            backstory="Assistant who makes audit results understandable using LLM insights.",
            tools=[tools['explain']],
            verbose=True,
            max_iterations=2  # Limit explanation attempts
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
        verbose=False,
        max_iterations=10  # Overall limit for the main pipeline
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
    
    # Validate file paths
    if not file_paths:
        raise ValueError("No file paths provided")
        
    # Convert file paths to absolute paths
    abs_file_paths = {
        doc_type: str(Path(file_path).resolve())
        for doc_type, file_path in file_paths.items()
    }
    
    if log_fn: log_fn(f"📁 Processing files: {json.dumps(abs_file_paths, indent=2)}")
    
    # Get the cached components
    agents = get_agents()
    tasks = get_tasks()
    
    # Create the main crew for parsing and matching
    main_crew = Crew(
        agents=[agents['parser'], agents['matcher']],
        tasks=[tasks['parse'], tasks['match']],
        verbose=False,
        max_iterations=6  # Limit for parsing and matching phase
    )
    
    # Run the main pipeline
    if log_fn: log_fn("✅ Processing documents...")
    main_result = main_crew.kickoff(inputs={
        "file_paths": json.dumps(abs_file_paths)  # Use absolute paths
    })
    
    # Unpack TaskOutput objects
    parse_out, match_out = main_result.tasks_output
    parsed_documents = parse_out.raw
    matched_documents = match_out.raw
    
    # Validate parsed documents
    try:
        parsed_docs = json.loads(parsed_documents)
        if "error" in parsed_docs:
            raise ValueError(f"Document processing error: {parsed_docs['error']}")
        if not parsed_docs:
            raise ValueError("No documents were parsed successfully")
    except json.JSONDecodeError as e:
        if log_fn: log_fn(f"❌ Error parsing documents: {str(e)}")
        if log_fn: log_fn(f"Raw output: {parsed_documents}")
        raise ValueError(f"Failed to parse documents: {str(e)}")
    
    # Log document matches
    if log_fn:
        matches = json.loads(matched_documents)
        if matches.get('matches'):
            log_fn("📎 Document matches found:")
            for match in matches['matches']:
                log_fn(f"- {match['primary']} ↔️ {match['related']} (via {match['key']})")
    
    # Create evaluation crew
    eval_crew = Crew(
        agents=[agents['checker']],
        tasks=[tasks['evaluate']],
        verbose=False,
        max_iterations=5  # Limit for evaluation phase
    )
    
    # Run evaluation
    if log_fn: log_fn("🔍 Evaluating rules...")
    eval_result = eval_crew.kickoff(inputs={
        "documents_json": parsed_documents,
        "rules_json": rules_json
    })
    
    # Unpack the single TaskOutput from the evaluation crew
    eval_out = eval_result.tasks_output[0]
    rule_outcomes = json.loads(eval_out.raw)
    
    # Handle failed rules
    failed_rules = [r for r in rule_outcomes if r["result"] == "fail"]
    if failed_rules:
        if log_fn: log_fn("❌ Processing failed rules...")
        explanation_crew = Crew(
            agents=[agents['explainer']],
            tasks=[tasks['explain']],
            verbose=False,
            max_iterations=2  # Limit for explanation phase
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