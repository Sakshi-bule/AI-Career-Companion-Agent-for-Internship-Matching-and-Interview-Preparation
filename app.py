from pathlib import Path
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from src.database import get_all_students, init_db, save_student_profile
from src.extractor import parse_resume_with_llm
from src.parser import extract_text_from_pdf

load_dotenv()
init_db()

UPLOAD_DIR = Path("data/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI Career Companion Agent — Milestone 1")


@app.post("/api/profiles/upload")
async def create_student_profile(
    full_name: str = Form(...),
    email: str = Form(...),
    preferred_role: str = Form(...),
    preferred_location: str = Form(""),
    resume: UploadFile = File(...),
):
    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")

    try:
        pdf_bytes = await resume.read()
        safe_email = email.replace("@", "_").replace(".", "_")
        saved_path = UPLOAD_DIR / f"{safe_email}_{resume.filename}"
        saved_path.write_bytes(pdf_bytes)

        raw_text = extract_text_from_pdf(pdf_bytes)
        structured_profile = parse_resume_with_llm(raw_text)
        profile_dict = structured_profile.model_dump()

        saved_record = save_student_profile(
            full_name=full_name,
            email=email,
            preferred_role=preferred_role,
            preferred_location=preferred_location,
            resume_filename=resume.filename,
            resume_filepath=str(saved_path),
            raw_text=raw_text,
            structured_profile=profile_dict,
        )
        return {"message": "Profile created and resume parsed successfully", "profile": saved_record}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profiles")
def list_profiles():
    return {"profiles": get_all_students()}


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)