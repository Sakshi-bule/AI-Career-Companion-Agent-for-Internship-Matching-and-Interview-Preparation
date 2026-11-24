import json
import os
import time
import urllib.error
import urllib.request
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from .rag_pipeline import InternshipRAG

load_dotenv()

BROAD_TAGS = {
    "computer science",
    "mathematics",
    "math",
    "physics",
    "research",
    "engineering",
    "science",
    "analytics",
    "data analysis",
    "data analytics",
}


class RankedMatch(BaseModel):
    rank: int
    job_id: str
    job_title: str
    company: str
    location: str
    match_score: float = Field(ge=0.0, le=100.0)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    reasoning: str


def build_profile_query(profile: dict) -> str:
    skills = ", ".join(profile.get("skills", []))
    role = profile.get("preferred_role", "")
    location = profile.get("preferred_location", "")
    education = profile.get("education", "")
    projects = ", ".join(
        p.get("title", str(p)) if isinstance(p, dict) else str(p)
        for p in profile.get("projects", [])
    )
    return (
        f"Role: {role}. Location: {location}. Education: {education}. "
        f"Skills: {skills}. Projects: {projects}."
    ).strip()


class JobResumeMatcher:
    def __init__(
        self,
        rag: InternshipRAG,
        model_name: str | None = None,
        base_url: str | None = None,
    ):
        self.rag = rag
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model_name = (
            model_name
            or os.getenv("LLM_MODEL")
            or os.getenv("GROQ_MODEL")
            or "openai/gpt-oss-20b"
        ).strip()
        resolved_base = (
            base_url
            or os.getenv("LLM_BASE_URL")
            or "https://api.groq.com/openai/v1"
        ).strip().rstrip("/")
        self.chat_url = f"{resolved_base}/chat/completions"

    def _score_job(
        self, profile: dict, job: dict, similarity: float
    ) -> tuple[float, list[str], list[str]]:
        student_skills = {
            s.strip().lower() for s in profile.get("skills", []) if s and s.strip()
        }
        req_skills = [
            s.strip() for s in job.get("required_skills", []) if s and s.strip()
        ]

        matched: list[str] = []
        missing: list[str] = []

        for skill in req_skills:
            s_low = skill.lower()
            if s_low in student_skills or any(
                s_low in st or st in s_low for st in student_skills if len(st) > 3
            ):
                matched.append(skill)
            elif s_low not in BROAD_TAGS:
                missing.append(skill)

        skill_ratio = (len(matched) / len(req_skills)) if req_skills else 0.5

        pref_role = (profile.get("preferred_role") or "").lower()
        title_text = (job.get("job_title") or "").lower()
        role_match = (
            1.0
            if (
                pref_role
                and any(w in title_text for w in pref_role.split() if len(w) > 2)
            )
            else 0.4
        )

        pref_loc = (profile.get("preferred_location") or "").lower()
        job_loc = (job.get("location") or "").lower()
        loc_match = (
            1.0
            if (
                not pref_loc
                or pref_loc in job_loc
                or "remote" in job_loc
                or "anywhere" in job_loc
            )
            else 0.3
        )

        score = (
            50.0 * skill_ratio
            + 25.0 * max(0.0, min(1.0, similarity))
            + 15.0 * role_match
            + 10.0 * loc_match
        )
        return round(min(100.0, score), 1), matched, missing

    def _call_llm(self, prompt: str, retries: int = 4) -> str | None:
        if not self.api_key:
            return None

        payload = {
            "model": self.model_name,
            "temperature": 0.2,
            "max_tokens": 350,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a concise career matching assistant. Explain fit factually in 2 complete sentences using only provided details. Never cut off mid-sentence.",
                },
                {"role": "user", "content": prompt},
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        }

        for attempt in range(1, retries + 1):
            try:
                req = urllib.request.Request(
                    self.chat_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=25) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    content = data["choices"][0]["message"]["content"]
                    if content and content.strip():
                        return content.strip()
            except urllib.error.HTTPError as err:
                err_body = err.read().decode("utf-8", errors="ignore")
                if err.code == 429 and attempt < retries:
                    time.sleep(2.5 * attempt)
                    continue
                print(f"[INFO] LLM API HTTP {err.code}: {err_body[:200]}")
                return None
            except Exception as err:
                if attempt < retries:
                    time.sleep(1.0 * attempt)
                    continue
                print(f"[INFO] LLM API call skipped/failed: {err}")
                return None

        return None

    def _explain_match(
        self,
        profile: dict,
        job: dict,
        score: float,
        matched: list[str],
        missing: list[str],
    ) -> str:
        fallback = (
            f"{job.get('job_title')} at {job.get('company')} ({job.get('location')}) scored {score}/100. "
            f"Matched skills: {', '.join(matched) if matched else 'none listed'}. "
            f"Additional skills to build: {', '.join(missing) if missing else 'none listed'}."
        )

        prompt = (
            f"Student target role: {profile.get('preferred_role')}, skills: {profile.get('skills')}, "
            f"projects: {profile.get('projects')}.\n"
            f"Internship: {job.get('job_title')} at {job.get('company')} in {job.get('location')}, "
            f"experience: {job.get('experience_requirements')}, required skills: {job.get('required_skills')}.\n"
            f"Match score: {score}/100. Matched skills: {matched}. Missing technical skills: {missing}."
        )
        llm_reason = self._call_llm(prompt)
        return llm_reason if llm_reason else fallback

    def match(
        self, profile: dict, top_k: int = 5, pool_size: int = 12
    ) -> list[RankedMatch]:
        query = build_profile_query(profile)
        retrieved = self.rag.search(query=query, top_k=pool_size)

        scored_items: list[tuple[float, list[str], list[str], dict]] = []
        for item in retrieved:
            job = item["job"]
            sim = item["similarity"]
            score, matched, missing = self._score_job(profile, job, sim)
            scored_items.append((score, matched, missing, job))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        top_items = scored_items[:top_k]

        results: list[RankedMatch] = []
        for idx, (score, matched, missing, job) in enumerate(top_items, start=1):
            reason = self._explain_match(profile, job, score, matched, missing)
            results.append(
                RankedMatch(
                    rank=idx,
                    job_id=job.get("job_id", ""),
                    job_title=job.get("job_title", ""),
                    company=job.get("company", ""),
                    location=job.get("location", ""),
                    match_score=score,
                    matched_skills=matched,
                    missing_skills=missing,
                    reasoning=reason,
                )
            )
            time.sleep(0.5)

        return results


if __name__ == "__main__":
    rag = InternshipRAG()
    jobs = rag.load_jobs("data/internships.json")
    rag.index_jobs(jobs)

    matcher = JobResumeMatcher(rag)
    sample_profile = {
        "name": "Sample ML Student",
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

    ranked = matcher.match(sample_profile, top_k=5)
    for m in ranked:
        print(f"#{m.rank} | {m.job_title} @ {m.company} | Score: {m.match_score}")
        print(f"   Matched: {m.matched_skills} | Missing: {m.missing_skills}")
        print(f"   Why: {m.reasoning}\n")