import streamlit as st
import tempfile
import os
import json
from pathlib import Path
from document_reader import process_document
from nl_rule_parser import parse_natural_rule
from compliance_agent import evaluate_rule
from compliance_report_generator import generate_compliance_report

st.set_page_config(page_title="Compliance Checker Agent", page_icon="📄", layout="centered")

with st.sidebar:
    st.title("🧠 AI Compliance Agent")
    st.markdown("""
    Upload related documents (Invoice, PO, GRN).

    Enter one or more compliance rules like:
    - Ensure invoice and PO have the same PO number.
    - Check invoice date is on or after GRN date.
    - Check vendor is approved.

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

if "rule_results" not in st.session_state:
    st.session_state.rule_results = []

if st.button("▶️ Run Compliance Check") and uploaded_files:
    st.header("🧾 Step 1: Document Parsing")
    documents = {}
    for file in uploaded_files:
        suffix = Path(file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(file.read())
            tmp_path = tmp_file.name

        try:
            doc = process_document(Path(tmp_path))
            doc_type = doc["doc_type"]
            documents[doc_type] = doc

            with st.expander(f"✅ `{doc_type}` → `{file.name}`: View Extracted Fields"):
                st.subheader("📋 Fields")
                st.json(doc["fields"])
                if "tables_structured" in doc:
                    st.subheader("📦 Line Items")
                    st.table(doc["tables_structured"])
        except Exception as e:
            st.warning(f"⚠️ Could not process `{file.name}`: {e}")

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

    for idx, rule in enumerate(rules):
        st.markdown(f"### 🔍 Rule {idx+1}: `{rule.get('description', rule.get('rule_id', 'Rule'))}`")
        try:
            required_docs = set(rule["applies_to"])
            missing_docs = required_docs - set(documents.keys())
            if missing_docs:
                st.warning(f"🚫 Skipped (Missing docs): {', '.join(missing_docs)}")
                error_count += 1
                continue

            result = evaluate_rule(rule, documents, enable_llm=True)
            results.append(result)

            if result["result"] == "fail":
                st.error(f"❌ FAILED – {result['reason']}")
                fail_count += 1
                if "llm_commentary" in result:
                    st.info(f"🧠 LLM Insight: {result['llm_commentary']}")
            else:
                st.success("✅ PASSED")
                pass_count += 1

            with st.expander("📌 Evaluation Details"):
                st.json(result["details"])

            with st.expander("🧩 Full Rule JSON"):
                st.json(rule)

        except Exception as e:
            st.error(f"⚠️ Rule could not be evaluated: {e}")
            error_count += 1

    st.session_state.rule_results = results
    st.session_state.documents_snapshot = documents
    st.info(f"📊 Summary: ✅ Passed: {pass_count} | ❌ Failed: {fail_count} | ⚠️ Errors/Skipped: {error_count}")

if st.session_state.get("rule_results"):
    st.header("📄 Final Compliance Report")
    report = generate_compliance_report(
        st.session_state.documents_snapshot, st.session_state.rule_results
    )
    st.markdown(report)
    st.download_button("⬇️ Download Report", report, file_name="compliance_report.md")
