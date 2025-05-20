# Crew AI Orchestrated Workflow

The system leverages LangChain for LLM integration and task routing, while CrewAI orchestrates multi-agent workflows, enabling modular, explainable, and extensible compliance checks driven by structured tasks and collaborative reasoning.
---

## 🌟 Key Capabilities

### 🧠 Natural Language Rule Interpretation

* Define rules in plain English without programming
* Automatically converts input to structured logic
* Supports multi-document references and expressions (e.g. tolerances, lookups)

### 📄 Document Processing

* Ingests PDFs, scanned images, and text files
* Uses OCR (Tesseract) and layout-aware parsing (pdfplumber)
* Maintains relationships (e.g., Invoice → PO → GRN) via primary keys

### ✅ Compliance Validation

* Cross-document matching and logical checks
* Verifies quantities, dates, prices, and vendor info
* Supports conditional and comparative rule logic

### 📊 Human-Friendly Reporting

* Pass/fail indicators per rule
* LLM-generated explanations for failed validations
* Structured report output with rule outcomes and context

---

## 🧱 System Architecture

### 📂 Core Layers

#### 1. **Document Processing**

* `document_reader.py`: Handles OCR and structured field extraction
* Supports multi-format ingestion and layout preservation

#### 2. **Rule Processing**

* `nl_rule_parser.py`: Converts plain-language rules to structured logic
* `compliance_agent.py`: Evaluates rules against parsed document data

#### 3. **Intelligence Layer**

* `llm_agent.py`: Uses LLMs (e.g., GPT-4) for natural explanations of validation failures
* `crew_runner.py`: Coordinates multi-step AI workflows using CrewAI

#### 4. **User Interface**

* `compliance_checker_app.py`: Streamlit-based frontend
* Allows rule input, document uploads, and real-time result visualisation

---

## 🚀 Quick Start

1. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run Application**

   ```bash
   streamlit run compliance_checker_app.py
   ```

3. **Use the Web Interface**

   * Upload documents (e.g., Invoice, PO, GRN)
   * Input natural language rules
   * View structured compliance outcomes

---

## 🛠️ Tech Stack

| Component       | Technology                   |
| --------------- | ---------------------------- |
| Frontend        | Streamlit                    |
| OCR + Parsing   | Tesseract, pdfplumber        |
| Rule Evaluation | Custom logic engine          |
| LLM Integration | OpenAI GPT-4 (via LangChain) |
| Orchestration   | CrewAI                       |

---

## 🔒 Security & Privacy

* Local-first processing (no file storage)
* No persistent database
* Temporary file cleanup per session
