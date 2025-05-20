
# Technical Architecture

## Overview

The Compliance Checker Bot automates validation of structured business documents (e.g., invoices, POs, GRNs) against configurable compliance rules. It integrates OCR, NLP, and validation pipelines to extract, evaluate, and explain document data.

---

## System Architecture

### 1. Core Modules

#### 📄 Document Pipeline

* `DocumentProcessor`: OCR, classification, and field extraction
* `DocumentMatcher`: Cross-document correlation (e.g., PO ↔ Invoice)
* `ValidationEngine`: Core rule evaluation engine
* `RuleEngine`: Parses and executes structured/natural language rules
* `ReportGenerator`: Produces JSON and human-readable compliance reports

#### 🌐 API Layer

* Framework: **FastAPI**
* Features:

  * Async REST endpoints
  * Auto-generated OpenAPI docs
  * Pydantic-based input/output validation

#### 🗃 Data Models

* `Document`: Metadata, layout, and field container
* `LineItem`: Structured tabular data per document
* `Rule`: Typed rule definition (equality, lookup, tolerance, expression, etc.)

---

## Feature Set

### 🧾 Document Handling

* Input: PDF, PNG, JPEG, TIFF
* OCR: Tesseract via PyTesseract
* Classification: Regex + fuzzy logic
* Parsing: Layout-preserving field extraction
* Format Support: Structured (text/PDF forms) + scanned (image-based)

### 🧠 Rule & Validation Engine

* Declarative and natural language rule support
* Rule Types:

  * Equality / Inequality
  * Tolerance-based numeric comparison
  * Date range checks
  * Lookup validations
  * Aggregated expressions
* Optional LLM-based explanation of validation outcomes

---

## Technology Stack

### Backend

| Component         | Tech       | Notes                                   |
| ----------------- | ---------- | --------------------------------------- |
| Web Framework     | FastAPI    | Async REST APIs with OpenAPI schema     |
| ORM               | SQLAlchemy | DB abstraction with Alembic migrations  |
| Schema Validation | Pydantic   | Typed validation for API + internal use |
| Migrations        | Alembic    | Version-controlled DB migrations        |

### Document Processing

| Tool        | Role                           |
| ----------- | ------------------------------ |
| PyTesseract | OCR engine for text extraction |
| PDF2Image   | PDF to image conversion        |
| PyPDF2      | Text and metadata extraction   |

### AI/NLP

| Tool                     | Use Case                            |
| ------------------------ | ----------------------------------- |
| LangChain                | Agent orchestration & chaining      |
| OpenAI API               | LLM-based parsing, explanation      |
| HuggingFace Transformers | Embedding, classification           |
| Sentence-Transformers    | Semantic similarity + vector search |

### Testing

| Tool           | Usage                    |
| -------------- | ------------------------ |
| Pytest         | Unit + integration tests |
| Pytest-asyncio | Async test support       |
| Pytest-cov     | Coverage reporting       |

### DevOps & Quality

| Tool   | Role                 |
| ------ | -------------------- |
| Black  | Code formatting      |
| isort  | Import sorting       |
| flake8 | Linting              |
| mypy   | Static type checking |

---

## Project Structure

```bash
src/
├── api/          # FastAPI routes and dependencies
├── core/         # Business logic (matcher, rules, validation)
├── database/     # Models, migrations (SQLAlchemy + Alembic)
├── models/       # Pydantic schemas
├── main.py       # Entrypoint
tests/
├── test_files/   # Sample documents
└── conftest.py   # Fixtures and setup
```

---

## Testing Strategy

* **Unit Tests**: Rule parsing, field extraction, core logic
* **Integration Tests**: API + document pipelines
* **Async Support**: Handled via `pytest-asyncio`
* **Fixtures**: Preloaded sample documents for regression
* **Coverage**: Enforced using `pytest-cov`

---

## Development Best Practices

* Modular, layered design with strict separation of concerns
* Type safety enforced with `mypy` and Pydantic
* Comprehensive test coverage with CI hooks
* Consistent style (Black, isort, flake8)
* Explicit error handling and fallback strategies

---

## Future Enhancements

* Advanced semantic document matching (e.g., Graph-based)
* Real-time rule evaluation via WebSockets or event-driven backends
* Dynamic rule builder UI for non-technical users
* Visual analytics and audit dashboards (Power BI / Streamlit)
* Support for multi-lingual and multi-region document layouts

---

