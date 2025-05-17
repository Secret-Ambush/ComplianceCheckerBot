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

## 🚀 How to Run

### 📦 Prerequisites

- Python 3.8+
- Install dependencies:

```bash
pip install -r requirements.txt
```

- Set your OpenAI API key:

```bash
export OPENAI_API_KEY=your-api-key
```

### ▶️ Run the Streamlit App

```bash
streamlit run compliance_checker_app.py
```

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

## 📁 Sample Folder Structure

```
├── compliance_checker_app.py
├── compliance_agent.py
├── document_reader.py
├── llm_agent.py
├── nl_rule_parser.py
├── compliance_report_generator.py
├── compliance_rules.json
├── requirements.txt
└── README.md
```

---

## ⚠️ Known Limitations

- One natural language rule per query (batch input optional)
- No visual parsing of tables (future improvement)
- Document classification is layout- and keyword-based (not ML)

---

## 🛠 Future Improvements

- Add document grouping by `po_number`
- Support table row-wise validation (e.g., line item quantity/price)
- Add LLM-based document classification fallback
- Integrate with cloud OCR APIs (Azure Form Recognizer, etc.)

---

## 📬 Submission

To submit:
1. Push this project to a public GitHub repository
2. Share the link by replying to the challenge email

---

Made with ❤️ for the Al Shirawi Intelligent Compliance Agent Challenge.
