# Scalable Workflow

An AI-driven system for validating document compliance against business rules using natural language processing and intelligent document parsing.

---

## 🚀 Overview

This project automates compliance validation by transforming human-readable rules into executable logic and evaluating them against extracted document data. It integrates NLP, OCR, and document linking to enable robust rule-based verification workflows.

---

## ✨ Features

### 🧠 Natural Language Rule Parsing

* Parses and interprets human-written compliance rules
* Supports logical expressions, tolerances, date checks, and lookups
* No coding required to define rules

### 📄 Smart Document Processing

* Supports PDF, scanned images, and plain text
* Uses OCR with layout awareness for scanned documents
* Detects and links related documents (e.g., invoice ↔ PO ↔ GRN)

### ✅ Validation Engine

* Rule execution with context-aware logic
* Generates structured results and explanations
* Confidence scores for compliance decisions

### ⚙️ Modern Tech Stack

* **FastAPI**: RESTful service endpoints
* **LangChain**: AI workflow orchestration
* **SQLAlchemy**: Persistent data modelling
* **Tesseract**: OCR for image-based PDFs

---

## 🛠 Architecture

```
User Input → Document Processor → Rule Engine → Validation Engine → Report
```

**Modules:**

* `DocumentProcessor`: Extracts fields and tables from documents
* `RuleEngine`: Parses and executes compliance rules
* `ValidationEngine`: Evaluates rule outcomes with optional LLM feedback
* `ReportGenerator`: Summarises compliance outcomes

---

## 📦 Requirements

* Python 3.8+
* `requirements.txt` dependencies
* OpenAI API Key (for LLM explanation module)
* Tesseract OCR (for scanned PDFs)

---

## 🧭 Roadmap

**Phase 1** *(In Progress)*

* Core rule engine and document parser
* Basic validation and reporting

**Phase 2**

* LLM-enhanced context interpretation
* Inter-document validation (cross-checking GRN, PO, invoices)
* Enhanced failure explanation via LLMs

**Phase 3**

* Role-based access and audit logging
* Integration with DMS and ERP systems
* Distributed processing for scale

---

## 📌 Status

Core functionality is implemented and usable. Additional features (e.g., auto-rule suggestion, enterprise security, advanced reporting) are planned for future iterations.

---
