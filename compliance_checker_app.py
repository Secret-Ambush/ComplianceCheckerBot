import streamlit as st
import tempfile
import os
import json
from pathlib import Path
from typing import Dict, List, Any

st.set_page_config(page_title="Compliance Checker Agent", page_icon="📄", layout="centered")

# Initialize session state variables
if "rule_results" not in st.session_state:
    st.session_state.rule_results = []
if "documents_snapshot" not in st.session_state:
    st.session_state.documents_snapshot = {}
if "report" not in st.session_state:
    st.session_state.report = None
if "matched_documents" not in st.session_state:
    st.session_state.matched_documents = {}

# Lazy load expensive imports
@st.cache_resource
def load_dependencies():
    from nl_rule_parser import parse_natural_rule
    from crew_runner import run_crew_pipeline
    from compliance_report_generator import generate_compliance_report
    return parse_natural_rule, run_crew_pipeline, generate_compliance_report

# Load dependencies only when needed
parse_natural_rule, run_crew_pipeline, generate_compliance_report = load_dependencies()

with st.sidebar:
    st.title("🧠 AI Compliance Agent")
    st.markdown("""
    Upload related documents (Invoice, PO, GRN).

    Enter one or more compliance rules like:
    - Match Invoice to PO and GRN using PO number
    - Ensure each line item on the invoice doesn't exceed ordered quantities
    - Unit prices should match PO values
    - Total invoice amount must be within 2% of PO total
    - Invoice date should be on or after GRN date
    - Vendor must appear in the approved vendor list

    Each line will be treated as a separate rule.
    """)
    st.info("Uses GPT-4 + Rule Engine", icon="📎")

    use_file_rules = st.checkbox("📄 Use predefined JSON rules", value=False)

    if not use_file_rules:
        user_instruction = st.text_area("💬 Enter one or more natural language rules (one per line):", height=150)
    else:
        st.markdown("✅ Using `compliance_rules.json` from disk.")
        with open("compliance_rules.json") as f:
            predefined_rules = json.load(f)

st.title("📄 Compliance Checker Agent")

uploaded_files = st.file_uploader("📁 Upload one or more documents", accept_multiple_files=True)

if st.button("▶️ Run Compliance Check") and uploaded_files:
    st.header("🧾 Step 1: Document Parsing")
    documents = {}
    file_paths = {}
    
    for file in uploaded_files:
        suffix = Path(file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(file.read())
            tmp_path = tmp_file.name

        try:
            doc_type = Path(file.name).stem.lower()
            file_paths[doc_type] = tmp_path
            with st.expander(f"📄 `{doc_type}` uploaded"):
                st.info(f"📎 Will be parsed via CrewAI pipeline.")
        except Exception as e:
            st.warning(f"⚠️ Could not process `{file.name}`: {e}")

    # Add reference data
    documents["reference"] = {
        "approved_vendors": ["generic", "TechSupply Inc."],
        "allowed_currencies": ["AED", "USD"]
    }

    st.header("🧠 Step 2: Multi-Rule Evaluation")
    results = []
    pass_count = fail_count = error_count = 0

    if use_file_rules:
        rules = predefined_rules
    else:
        lines = [line.strip() for line in user_instruction.strip().split("\n") if line.strip()]
        rules = [parse_natural_rule(line) for line in lines]

    # Run the pipeline with all documents
    parsed_documents, rule_results = run_crew_pipeline(
        file_paths,
        json.dumps(rules),
        lambda msg: st.markdown(f"> {msg}")
    )

    # Display results
    for idx, result in enumerate(rule_results):
        st.markdown(f"### 🔍 Rule {idx+1}: `{result.get('rule_id', 'Unknown')}`")
        if result["result"] == "fail":
            st.error(f"❌ FAILED – {result['reason']}")
            st.info(f"🧠 LLM Insight: {result.get('llm_commentary')}")
        else:
            st.success("✅ PASSED")

        with st.expander("📌 Evaluation Details"):
            st.json(result["details"])

    # Update session state
    st.session_state.rule_results = rule_results
    st.session_state.documents_snapshot = documents
    st.session_state.parsed_documents = json.loads(parsed_documents)
    
    # Generate and store report
    st.session_state.report = generate_compliance_report(
        st.session_state.documents_snapshot,
        st.session_state.rule_results,
        st.session_state.parsed_documents
    )

    st.info(f"📊 Summary: ✅ Passed: {pass_count} | ❌ Failed: {fail_count} | ⚠️ Errors/Skipped: {error_count}")

# Display report and download button if we have results
if st.session_state.rule_results:
    st.header("📄 Final Compliance Report")
    st.markdown(st.session_state.report)
    
    # Create a container for the download button
    download_container = st.container()
    with download_container:
        st.download_button(
            "⬇️ Download Report",
            st.session_state.report,
            file_name="compliance_report.md",
            mime="text/markdown"
        )
