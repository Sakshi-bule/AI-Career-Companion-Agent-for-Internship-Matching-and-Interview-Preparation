# AI Career Companion Agent for Internship Matching and Interview Preparation

An end-to-end multi-agent AI system designed to help students build structured candidate profiles from raw resumes, match with relevant internships via RAG, identify skill gaps, tailor application materials, and practice role-specific interviews.

---

## System Architecture

```mermaid
flowchart TD
    UI[Student / User Interface - HTML & Tailwind CSS] -->|Fetch JSON API| API[Backend / API Layer - FastAPI]
    API --> Upload[Resume Upload & Storage]
    API --> Parser[Resume Parsing Module - PyMuPDF]
    Parser --> LLM[LLM Extraction Engine - Gemini]
    LLM --> Profile[Candidate Profile Schema - Pydantic]
    Profile --> DB[(SQLite Database)]
    DB --> Router{AI Agent Layer - Career Assistant}
    KB[(Job-Posting Knowledge Base)] --> RAG[RAG Pipeline - ChromaDB]
    RAG <--> Router
    Router --> A1[Job-Resume Matching Agent]
    Router --> A2[Skill Gap Agent]
    Router --> A3[Resume Agent]
    Router --> A4[Cover Letter Agent]
    Router --> A5[Interview Agent]
    A1 & A2 & A3 & A4 & A5 --> Tracker[Application Tracking Module]
    Tracker -->|JSON Response| UI
```

---

## Data Flow (Milestone 1 Pipeline)
1. **Student Onboarding (Web UI):** Student enters basic details (Name, Email, Preferred Role, Preferred Location) and uploads a PDF resume.
2. **REST API Ingestion (FastAPI):** The browser submits the form and PDF (`multipart/form-data`) to `POST /api/profiles/upload`.
3. **Resume Storage & Text Extraction:** FastAPI saves the uploaded PDF locally and uses `PyMuPDF` to extract plain text across all pages.
4. **LLM Structured Parsing:** Raw resume text is sent to Gemini with a strict Pydantic schema (`CandidateProfile`), extracting structured fields (`technical_skills`, `education`, `experience`, `projects`, `certifications`, `target_roles`).
5. **Database Persistence & UI Display:** SQLite stores the metadata, raw text, and validated JSON profile, returning the structured profile to the UI for clean card-and-badge rendering.

---

## Multi-Agent Responsibilities
* **Career Assistant (Supervisor):** Central coordinator that manages student state and routes requests to specialized worker agents.
* **Job-Resume Matching Agent:** Queries the RAG job knowledge base using the candidate's structured profile and ranks internships by relevance.
* **Skill Gap Agent:** Compares the candidate's current skills against target job requirements and highlights missing competencies.
* **Resume Agent:** Rewrites and tailors resume project descriptions and bullet points for specific internship roles.
* **Cover Letter Agent:** Generates customized cover letters grounded in the candidate's verified projects and target company details.
* **Interview Agent:** Generates role-specific technical and behavioral interview questions based on the candidate's resume and skill gaps.

---

## Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend UI** | HTML5 + Tailwind CSS + JavaScript | Clean web interface for profile creation, PDF upload, and structured profile cards |
| **Backend / API Layer** | FastAPI + Uvicorn | Python web server & REST API connecting the UI, parser, LLM, and database |
| **Schema Validation** | Pydantic | Enforces strict JSON structure on LLM-extracted candidate data |
| **PDF Text Parser** | PyMuPDF (`fitz`) | Extracts clean text from PDF resumes |
| **LLM Engine** | Gemini API (`gemini-2.5-flash`) | Structured extraction of skills, education, projects, and experience |
| **Relational Database** | SQLite | Stores student metadata, resume file paths, raw text, and JSON profiles |
| **Vector DB & RAG** *(M2)* | ChromaDB + Embeddings | Semantic retrieval over internship job descriptions |
| **Agent Orchestration** *(M2)* | LangGraph | Multi-agent state management and routing |

---

## Repository Structure

```text
├── app.py                      # Single-command FastAPI entry point
├── requirements.txt            # Python dependencies
├── README.md                   # System architecture and project overview
├── docs/
│   └── M1_Research_Notes.md    # M1.1 research on workflows, RAG, and agent patterns
├── static/
│   └── index.html              # Modern Tailwind CSS frontend interface
└── src/
    ├── __init__.py
    ├── schemas.py              # M1.2 CandidateProfile Pydantic models
    ├── database.py             # M1.3 SQLite database operations
    ├── parser.py               # M1.4 PDF text extraction module
    └── extractor.py            # M1.4 LLM structured extraction module
```
