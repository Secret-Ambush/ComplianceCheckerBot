# Compliance Checker

🔹 1. Document Reader & Field Extractor
📁 Input Folder (PDF/TXT/Images)
   └── 🔍 Document Reader
           ├── Type Classifier (filename + content)
           ├── Vendor Detector
           ├── Text Extractor (PDF/TXT/OCR)
           ├── Field Extractor (Template | Regex | LLM)
           └── ➡️ Normalised JSON Output

🔹 2. Text Extraction Module
💡 Strategy:
PDF (text) → pdfplumber or PyMuPDF to extract text and coordinates.
Scanned PDF/Image → Preprocess with OpenCV → OCR with Tesseract.

Planning
| Phase      | Goal                                     | Output                                      |
| ---------- | ---------------------------------------- | ------------------------------------------- |
| ✅ Phase 1  | Rule-based compliance checker            | `document_reader.py`, `compliance_agent.py` |
| ✅ Phase 2  | LLM failure explainer                    | `llm_agent.py`                              |
| 🔜 Phase 3 | Natural language → JSON rule generator   | `nl_rule_parser.py`                         |
| 🔜 Phase 4 | Line item comparison (nested validation) | Row-wise rule evaluation                    |
| 🔜 Phase 5 | Compliance report generator              | Markdown or JSON report                     |
| 🔜 Phase 6 | LangChain agent orchestration            | Unified toolchain, conversational interface |


### Agent Loop Workflow  
🧾 User types a natural language rule ➝
🧠 LLM converts it to JSON using `parse_natural_rule()` ➝
📑 JSON rule is validated and stored (optional) ➝
📂 Agent runs `evaluate_rule()` on available documents ➝
✅ Returns pass/fail + explanation + (optional) LLM commentary


### Full System Design Summary
| Module                      | Role                                                  |
| --------------------------- | ----------------------------------------------------- |
| `document_reader.py`        | Ingests user documents and extracts structured fields |
| `nl_rule_parser.py`         | Converts natural language rule → JSON rule            |
| `compliance_agent.py`       | Evaluates rule against extracted document data        |
| `llm_agent.py`              | Explains failed rules using OpenAI                    |
| `interactive_agent_loop.py` | Runs the agent loop — but so far uses hardcoded files |



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