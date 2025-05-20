# Compliance Checker Bot

A sophisticated document compliance checking system that combines rule-based validation with LLM-powered analysis to ensure document accuracy and compliance.

## 🌟 Key Features

### 1. Intelligent Document Processing
- **Multi-format Support**: Handles PDF, TXT, and image-based documents
- **Smart Field Extraction**: Uses a combination of template matching, regex, and LLM-based extraction
- **Vendor Detection**: Automatically identifies document sources
- **Type Classification**: Intelligent document categorization based on content and filename

### 2. Flexible Rule Engine
- **Natural Language Rule Input**: Convert plain English rules into structured JSON format
- **Nested Validation**: Support for complex hierarchical document structures
- **Multiple Comparison Types**:
  - Equality checks
  - Numeric comparisons with tolerance
  - Date validations
  - Lookup operations
  - Custom expressions

### 3. Advanced Analysis Capabilities
- **LLM-Powered Explanations**: Get detailed explanations for failed compliance checks
- **Aggregation Support**: Perform calculations across document sections
- **Reference Data Integration**: Compare against external reference data
- **Detailed Reporting**: Generate comprehensive compliance reports

## 🛠 Technical Architecture

### Core Components
- `document_reader.py`: Document ingestion and field extraction
- `compliance_agent.py`: Rule evaluation engine
- `llm_agent.py`: LLM-powered failure analysis
- `nl_rule_parser.py`: Natural language to JSON rule conversion
- `compliance_report_generator.py`: Report generation

### Workflow
1. Document ingestion and field extraction
2. Rule parsing and validation
3. Compliance checking
4. LLM-powered analysis (optional)
5. Report generation

## 💪 Strengths

1. **Flexibility**
   - Supports multiple document formats
   - Extensible rule system
   - Customizable validation logic

2. **Intelligence**
   - LLM-powered explanations
   - Smart field extraction
   - Context-aware validation

3. **Robustness**
   - Error handling
   - Fallback mechanisms
   - Detailed logging

4. **Scalability**
   - Modular architecture
   - Batch processing support
   - Extensible design

## 🚀 Benefits

1. **Efficiency**
   - Automated compliance checking
   - Reduced manual review time
   - Batch processing capabilities

2. **Accuracy**
   - Consistent rule application
   - Multiple validation layers
   - Detailed error reporting

3. **Transparency**
   - Clear compliance reports
   - LLM-powered explanations
   - Detailed audit trails

4. **Maintainability**
   - Clear code structure
   - Modular design
   - Well-documented components

## 🔜 Future Enhancements

- Table parsing capabilities
- Enhanced document classification
- Cloud OCR integration
- Line item comparison
- Document grouping by PO number
- Conversational interface

## 🛠 Setup and Usage

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the compliance checker:
```bash
python compliance_checker_app.py
```

## 📝 License

MIT License - See LICENSE file for details

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