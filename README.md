# 📄 Intelligent Document Compliance Agent

An AI-powered compliance automation system that transforms how organizations handle document validation and compliance checks. This system combines the power of Large Language Models (LLMs) with structured rule processing to create an intelligent, human-like compliance officer.

## 🌟 Key Benefits

### 1. Natural Language Rule Processing
- Define compliance rules in plain English
- No need for complex programming or rule engines
- Rules are automatically converted into structured logic
- Supports complex multi-document relationships

### 2. Intelligent Document Processing
- Handles multiple document types (PDF, images, text)
- Extracts structured data using OCR and text analysis
- Maintains document relationships (Invoice → PO → GRN)
- Preserves original document context

### 3. Advanced Compliance Checking
- Cross-document validation
- Complex logical conditions
- Reference data lookups
- Automated data consistency checks

### 4. Human-Friendly Reporting
- Clear pass/fail indicators
- LLM-generated explanations for failures
- Contextual insights into rule violations
- Downloadable compliance reports

## 🏗️ System Architecture

### Core Components

1. **Document Processing Layer**
   - `document_reader.py`: Handles OCR and field extraction
   - Supports multiple document formats
   - Extracts structured data and tables

2. **Rule Processing Layer**
   - `nl_rule_parser.py`: Converts natural language to structured rules
   - `compliance_agent.py`: Evaluates rules against documents
   - Supports complex logical conditions

3. **Intelligence Layer**
   - `llm_agent.py`: Provides human-like explanations
   - `crew_runner.py`: Orchestrates AI agents
   - Uses CrewAI for task coordination

4. **User Interface**
   - `compliance_checker_app.py`: Streamlit-based web interface
   - Real-time processing feedback
   - Interactive rule input
   - Visual compliance reports

## 🚀 Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   streamlit run compliance_checker_app.py
   ```

3. Upload documents and define rules through the web interface

## 📝 Example Use Case

### Input Documents
- Invoice (INV1001.pdf)
- Purchase Order (PO505.pdf)
- Goods Receipt Note (GRN802.pdf)

### Sample Rules
```
- Match Invoice to PO and GRN using PO number
- Ensure invoice line items don't exceed PO quantities
- Verify unit prices match PO values
- Check total invoice amount is within 2% of PO total
- Validate invoice date is on or after GRN date
- Confirm vendor is in approved list
```

### Output
- ✅ Structured compliance report
- ❌ Clear failure explanations
- 💡 LLM-generated insights
- 📊 Summary statistics

## 🛠️ Technical Stack

- **Frontend**: Streamlit
- **Document Processing**: Tesseract OCR, pdfplumber
- **AI/ML**: LangChain, CrewAI
- **Rule Engine**: Custom implementation
- **LLM Integration**: GPT-4

## 🔒 Security & Privacy

- Local document processing
- No data persistence
- Secure file handling
- Temporary file cleanup

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Made with ❤️ for the Al Shirawi Intelligent Compliance Agent Challenge.