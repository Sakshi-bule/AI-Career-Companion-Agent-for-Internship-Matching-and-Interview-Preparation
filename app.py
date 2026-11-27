from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.matching_agent import JobResumeMatcher
from src.rag_pipeline import InternshipRAG

app = FastAPI(title="AI Career Companion Agent")
templates = Jinja2Templates(directory="templates")

rag = InternshipRAG()
jobs = rag.load_jobs("data/internships.json")
rag.index_jobs(jobs)
matcher = JobResumeMatcher(rag)

DEFAULT_PROFILE = {
    "name": "Sakshi Bule",
    "preferred_role": "Data Science / ML Intern",
    "preferred_location": "Remote",
    "education": "B.E. Computer Engineering",
    "skills": [
        "Python",
        "Pandas",
        "Scikit-learn",
        "TensorFlow",
        "Keras",
        "OpenCV",
        "SQL",
    ],
    "projects": [
        "Home Loan Default Prediction",
        "Rice Leaf Disease Classification",
        "Dog Breed Classifier",
    ],
}


def _parse_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "profile": DEFAULT_PROFILE,
            "skills_text": ", ".join(DEFAULT_PROFILE["skills"]),
            "projects_text": ", ".join(DEFAULT_PROFILE["projects"]),
            "matches": [],
            "submitted": False,
        },
    )


@app.post("/match", response_class=HTMLResponse)
async def match_internships(
    request: Request,
    name: str = Form("Sakshi Bule"),
    preferred_role: str = Form("Data Science / ML Intern"),
    preferred_location: str = Form("Remote"),
    education: str = Form("B.E. Computer Engineering"),
    skills: str = Form(""),
    projects: str = Form(""),
    top_k: int = Form(5),
):
    profile = {
        "name": name.strip() or "Sakshi Bule",
        "preferred_role": preferred_role.strip(),
        "preferred_location": preferred_location.strip(),
        "education": education.strip(),
        "skills": _parse_csv(skills),
        "projects": _parse_csv(projects),
    }
    ranked_matches = matcher.match(profile, top_k=max(1, min(top_k, 10)))

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "profile": profile,
            "skills_text": skills,
            "projects_text": projects,
            "matches": ranked_matches,
            "submitted": True,
        },
    )
