# AI-Career-Companion-Agent-for-Internship-Matching-and-Interview-Preparation
AI Career Companion Agent for Internship Matching and Interview Preparation
# AI Career Companion Agent for Internship Matching and Interview Preparation

An end-to-end multi-agent AI system designed to help students organize their candidate profile from raw resumes, match with relevant internships via RAG, identify skill gaps, tailor application materials, and practice role-specific interviews.

---

## System Architecture

```mermaid
flowchart TD
    UI[Student / User Interface<br/>Streamlit Web App] --> API[Backend / Orchestration Layer<br/>Python Service]
    
    subgraph M1 [Milestone 1: Foundation & Candidate Understanding]
        API --> Upload[Resume Upload & Storage<br/>Local File Store]
        API --> Parser[Resume Parsing Module<br/>PyMuPDF Text Extraction]
        Parser --> LLM[LLM Extraction Engine<br/>Gemini Structured Output]
        LLM --> Profile[Candidate Profile Schema<br/>Pydantic Validated JSON]
        Profile --> DB[(SQLite Database<br/>Metadata + Structured Profile)]
    end

    subgraph M2 [Milestone 2+: RAG & Multi-Agent Layer]
        DB --> Router{AI Agent Layer<br/>Career Assistant Supervisor}
        KB[(Job-Posting Knowledge Base)] --> RAG[RAG Pipeline<br/>ChromaDB Vector Search]
        RAG <--> Router
        
        Router --> A1[Job-Resume Matching Agent]
        Router --> A2[Skill Gap Agent]
        Router --> A3[Resume Agent]
        Router --> A4[Cover Letter Agent]
        Router --> A5[Interview Agent]
        
        A1 & A2 & A3 & A4 & A5 --> Tracker[Application Tracking Module]
        Tracker --> UI
    end
