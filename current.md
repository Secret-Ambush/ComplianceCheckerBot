| Requirement                      | ✅ Your Workflow Now                                                                                          |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **AI model**                     | ✅ `ChatOpenAI` (GPT-4 via LangChain) for rule explanation, document classification                           |
| **OCR/document parsing**         | ✅ `Tesseract` for scanned images and image-PDF fallback<br>✅ `pdfplumber` for embedded text                  |
| **Agent / workflow engine**      | ✅ Custom agent (`evaluate_rule`) with support for expressions, lookup, tolerance<br>✅ Rule JSON-based engine |
| **Knowledge integration / RAG**  | ➖ Not yet implemented, but could be used to ground checks against external policies, contracts               |
| **Code generation / AI writing** | ✅ LLM generates insights; rules are natural language → parsed to structured logic                            |


CrewAI workflow - 📌 Candidate CrewAI Agents  

| Agent Name                   | Role                                              | Code Source                              | Output                    |
| ---------------------------- | ------------------------------------------------- | ---------------------------------------- | ------------------------- |
| `DocumentParserAgent`        | Extracts text, fields, and tables from a document | `process_document()`                     | Parsed document dict      |
| `ClassifierAgent` (Optional) | Decides type/vendor (already inside parser)       | `classify_document()`, `detect_vendor()` | Doc type                  |
| `ComplianceAgent`            | Evaluates structured rules                        | `evaluate_rule()`                        | List of rule results      |
| `ExplainerAgent`             | Explains failures using LLM                       | `llm_explain_failure()`                  | Justifications (optional) |

file → process_document()
           ↳ extract_text()
           ↳ classify_document()
           ↳ extract_fields_regex()
           ↳ extract_tables()

document → evaluate_rule()
           ↳ compare_values()
           ↳ get_nested_value()

result → llm_explain_failure()
