# 📄 Intelligent Document Compliance Agent

This project is an AI-powered agent that automates document compliance workflows. It acts like a human compliance officer by interpreting natural language rules, extracting structured data from business documents, and producing clear compliance reports with pass/fail logic, cross-document checks, and contextual reasoning.

---

## 🧠 Key Features

- ✅ Upload and process scanned or native PDF, image, or text documents (e.g., invoices, POs, GRNs)
- 🧾 Define rules in **natural language** — the agent converts these into structured logic
- 🔎 Evaluate logical conditions, lookups, and cross-document dependencies
- 📊 Generate a **structured compliance report** with pass/fail per rule
- 🧠 Includes **LLM-generated explanations** for failed validations
- 💬 Built with **LangChain**, **Streamlit**, **Tesseract OCR**, and **pdfplumber**

---

## 🧱 System Architecture

**Main Components:**

- `document_reader.py` → Extracts text and fields from uploaded documents
- `nl_rule_parser.py` → Converts natural language rule into structured JSON
- `compliance_agent.py` → Evaluates rule logic across one or more documents
- `llm_agent.py` → Generates LLM commentary for failed rules
- `compliance_report_generator.py` → Creates a structured Markdown compliance report
- `compliance_checker_app.py` → Streamlit UI for uploading documents and entering rules

---

## 📝 Example Use

### Upload:
- `invoice_INV1001.pdf`
- `PO505.pdf`
- `GRN802.pdf`

### Enter Rule:
> "Ensure the invoice date is on or after the GRN date and vendor is approved."

### Output:
- ✅ Invoice Date ≥ GRN Date
- ❌ Vendor not in approved list  
  💡 _LLM: The vendor ID `XYZ Ltd` was not found in the reference list._

---

Made with ❤️ for the Al Shirawi Intelligent Compliance Agent Challenge.

---

![alt text](<Screenshot 2025-05-17 at 11.18.38 pm.png>)