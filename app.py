import logging
import shutil
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("career_companion")

from src.database import get_all_profiles, init_db, save_student_profile
from src.extractor import parse_resume_with_llm
from src.parser import extract_text_from_pdf

DATA_DIR = BASE_DIR / "data"
TEMPLATE_PATH = BASE_DIR / "templates" / "index.html"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


@asynccontextmanager
async def lifespan(app: FastAPI):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    logger.info("Database initialised.")
    yield


app = FastAPI(title="AI Career Companion Agent", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(TEMPLATE_PATH.read_text(encoding="utf-8"))


@app.get("/api/profiles")
async def list_profiles():
    try:
        return get_all_profiles()
    except Exception as exc:
        logger.exception("Failed to load profiles")
        raise HTTPException(status_code=500, detail=f"Could not load profiles: {exc}")


@app.post("/api/profiles/upload")
def upload_profile(
    full_name: str = Form(...),
    email: str = Form(...),
    preferred_role: str = Form(...),
    preferred_location: str = Form(...),
    resume: UploadFile = File(...),
):
    # Sync endpoint on purpose: PDF parsing and the Gemini call are blocking,
    # so FastAPI runs this in a worker thread instead of stalling the event loop.
    filename = resume.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    saved_path = DATA_DIR / f"{uuid.uuid4().hex}.pdf"

    try:
        with saved_path.open("wb") as out:
            shutil.copyfileobj(resume.file, out)

        if saved_path.stat().st_size > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="PDF is larger than 10 MB.")

        raw_text = extract_text_from_pdf(str(saved_path))
        if not raw_text:
            raise HTTPException(
                status_code=422,
                detail="No text found in this PDF. Scanned resumes are not supported.",
            )

        profile = parse_resume_with_llm(raw_text)

        # Form inputs take priority over what the model extracted.
        profile.full_name = full_name.strip() or profile.full_name
        profile.email = email.strip() or profile.email
        profile.preferred_role = preferred_role.strip() or profile.preferred_role
        profile.preferred_location = (
            preferred_location.strip() or profile.preferred_location
        )

        profile_id = save_student_profile(profile)
        return {
            "status": "success",
            "id": profile_id,
            "profile": profile.model_dump(),
        }

    except HTTPException:
        raise
    except RuntimeError as exc:
        logger.error("Configuration error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.exception("Resume processing failed")
        raise HTTPException(
            status_code=500, detail=f"Failed to process resume: {exc}"
        )
    finally:
        resume.file.close()


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
