# 🧠 Intelligent Document Compliance Checker – Multi-Workflow Overview

This project provides **three scalable and intelligent workflows** for automating document compliance across business documents such as invoices, purchase orders (POs), and goods receipt notes (GRNs). Each workflow offers a different architectural approach — from a lightweight rule-based validator to a scalable backend API and a multi-agent CrewAI orchestrated setup.

👉 **Please explore each workflow in its dedicated branch for implementation details and instructions.**

---

## 🔁 Available Workflows

---

### 1️⃣ **Rule-Based Workflow**

> Branch: `rule-based`

A lightweight, modular system designed for streamlined document validation using structured JSON rules and optional LLM assistance for interpreting natural language rules or explaining failures.

#### 🧩 Key Highlights:

* Upload documents (PDF/TXT/images) via a Streamlit UI
* Use plain English rules → converted to structured logic (via LLM)
* Validate conditions across related documents (e.g., invoice total ≤ PO total)
* Get structured Markdown/JSON reports
* No backend server or external orchestration required

#### 🔧 Technologies:

Streamlit • Tesseract OCR • pdfplumber • OpenAI (optional) • Custom Rule Engine

👉 **Check out the `rule-based` branch for setup and usage instructions.**

---

### 2️⃣ **CrewAI-Orchestrated Workflow**

> Branch: `crewAIAgentBasedWorkflow `

This version introduces **multi-agent coordination** using **CrewAI**, where tasks like rule parsing, document extraction, and validation are independently managed by LLM-backed agents. Designed for enhanced explainability and agent-driven reasoning.

#### 🧩 Key Highlights:

* Multi-step agent workflow (Parse → Extract → Validate → Explain)
* Orchestrated using **CrewAI**
* Modular and extensible via LangChain tools
* Uses GPT-4 for both logic parsing and failure explanation
* Frontend via Streamlit for input/output interaction

#### 🔧 Technologies:

CrewAI • LangChain • Streamlit • Tesseract OCR • pdfplumber • OpenAI GPT

👉 **Check out the `crewai-workflow` branch for implementation details.**

---

### 3️⃣ **Scalable API-Based Workflow**

> Branch: `scalable-api`

Built with scalability in mind, this architecture uses **FastAPI** to expose REST endpoints for document processing, rule evaluation, and reporting — ideal for integration with enterprise systems, microservices, and cloud-native deployments.

#### 🧩 Key Highlights:

* Stateless API endpoints for document ingestion and rule validation
* Document ↔ Rule ↔ Result flow fully decoupled
* Compatible with batch or real-time validation pipelines
* Ready for Docker/Kubernetes/Cloud deployment
* LLM support for rule parsing and explanation

#### 🔧 Technologies:

FastAPI • LangChain • SQLAlchemy • Tesseract OCR • OpenAI (optional) • pdfplumber

👉 **Check out the `scalable-api` branch for deployment instructions and API specs.**

---

## 🛡️ Security & Privacy Across Workflows

* All workflows support **local-first processing**
* No data is stored permanently by default
* Temporary files are cleaned up after processing
* LLM integration (e.g., OpenAI) is optional and configurable via `.env`

---

## 📦 Repository Structure

| Branch            | Purpose                                 |
| ----------------- | --------------------------------------- |
| `rule-based`      | Streamlit + JSON rules + optional LLM   |
| `crewai-workflow` | CrewAI agent-based multi-step reasoning |
| `scalable-api`    | FastAPI backend with REST endpoints     |


---