import streamlit as st
import tempfile
import os
import json
from pathlib import Path
from document_reader import process_document
from nl_rule_parser import parse_natural_rule
from compliance_agent import evaluate_rule
from compliance_report_generator import generate_compliance_report

st.title("📄 Compliance Checker Agent")

uploaded_files = st.file_uploader("Upload one or more documents (PDF, TXT, JPG, PNG)", accept_multiple_files=True)

user_instruction = st.text_input("💬 Enter a natural language compliance rule:")

if st.button("Run Compliance Check") and uploaded_files and user_instruction:
    st.subheader("📂 Processing Uploaded Documents")
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
            st.success(f"✅ Detected `{doc_type}` from `{file.name}` with extracted fields:")
            st.json(doc["fields"])
        except Exception as e:
            st.warning(f"⚠️ Could not process `{file.name}`: {e}")

    # Add dummy reference data
    documents["reference"] = {
        "approved_vendors": ["generic", "TechSupply Inc."],
        "allowed_currencies": ["AED", "USD"]
    }

    try:
        st.subheader("📜 Parsed Rule")
        rule = parse_natural_rule(user_instruction)
        st.json(rule)

        required_docs = set(rule["applies_to"])
        missing_docs = required_docs - set(documents.keys())
        if missing_docs:
            st.warning(f"🚫 Missing required documents: {', '.join(missing_docs)}")
            st.stop()

        st.subheader("🔎 Rule Evaluation")
        result = evaluate_rule(rule, documents, enable_llm=True)

        if result["result"] == "fail":
            st.error(f"❌ Rule Failed: {result['reason']}")
            if "llm_commentary" in result:
                st.info(f"🧠 LLM Insight:\n{result['llm_commentary']}")
        else:
            st.success("✅ Rule Passed")

        st.subheader("📌 Evaluation Details")
        st.json(result["details"])

        report = generate_compliance_report(documents, [result])
        st.subheader("📄 Final Compliance Report")
        st.markdown(report)
        st.download_button("Download Report", report, file_name="compliance_report.md")

    except Exception as e:
        st.error(f"🚨 An error occurred during rule evaluation: {e}")
