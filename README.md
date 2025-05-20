# Rule Based Workflow

An AI-augmented document compliance system that automates validation across business documents using structured rule logic, intelligent field extraction, and optional LLM assistance for rule interpretation and failure explanation.

---

## 🌟 Key Features

### 📑 Document Processing

* **Multi-format Input**: Supports PDF (native/scanned), text, and images
* **Smart Field Extraction**: Uses Tesseract, `pdfplumber`, regex, and layout-based logic
* **Document Classification**: Identifies and tags documents by type and source
* **Vendor Detection**: Infers origin from filename patterns or metadata

### 🧾 Rule Engine

* **Plain English → JSON Rule Conversion**: Uses an LLM to convert natural language into structured rule logic
* **Validation Types Supported**:

  * Equality and inequality checks
  * Numeric comparisons with tolerances
  * Date comparisons
  * Reference lookups
  * Expression-based conditions
* **Nested Field Support**: Traverse deep or grouped document structures
* **Cross-document Checks**: Match values across PO, Invoice, and GRN documents

### 🧠 LLM Integration (Optional)

* **Rule Translation**: Converts plain language into rule JSON
* **Failure Explanation**: Generates natural language reasoning for non-compliance cases

### 📊 Structured Reporting

* Pass/fail summaries for each rule
* LLM-backed explanations for failed checks
* Markdown/JSON report generation
* Streamlit frontend with real-time results

---

## 🧱 Architecture Overview

```text
Natural Language Rules
        ↓ (Optional LLM)
Structured JSON Rules
        ↓
+-----------------------+
|  DocumentProcessor    | ← OCR & parsing (Tesseract/pdfplumber)
+-----------------------+
        ↓
+-----------------------+
|   RuleEvaluator       | ← Applies rules to extracted fields
+-----------------------+
        ↓
+-----------------------+
|   ReportGenerator     | ← Summarises results, formats output
+-----------------------+
```

### 🧩 Core Files

| File                             | Purpose                               |
| -------------------------------- | ------------------------------------- |
| `document_reader.py`             | Parses fields/tables from documents   |
| `nl_rule_parser.py`              | Converts plain-language rules to JSON |
| `compliance_agent.py`            | Evaluates rules on structured data    |
| `llm_agent.py` (optional)        | Explains failed rules via GPT-4       |
| `compliance_report_generator.py` | Creates structured reports            |
| `compliance_checker_app.py`      | Streamlit-based frontend              |

---

## 🚀 Usage

### 🛠 Setup

```bash
pip install -r requirements.txt
```
Maintain a .env with an OpenAI key

### ▶️ Run the App

```bash
streamlit run compliance_checker_app.py
```

---

## 🧰 Tech Stack

| Layer          | Tools                   |
| -------------- | ----------------------- |
| Frontend       | Streamlit               |
| OCR            | Tesseract               |
| PDF Parsing    | pdfplumber              |
| Rule Engine    | Custom JSON-based logic |
| LLM (Optional) | OpenAI GPT (via API)    |

---

## 🔒 Security & Privacy

* No persistent data storage
* Temporary files are deleted post-processing
* All document parsing happens locally by default

---
