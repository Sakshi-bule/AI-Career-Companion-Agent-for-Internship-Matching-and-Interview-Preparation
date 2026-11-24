import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
)

from src.schemas import CandidateProfile

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH, override=True)

# Groq by default (OpenAI-compatible). Override in .env to use OpenAI, OpenRouter, etc.
DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

MODEL_NAME = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
BASE_URL = (os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or DEFAULT_BASE_URL).strip()
REQUEST_TIMEOUT_S = 40
RETRIES = 4
RETRYABLE_CODES = {408, 429, 500, 502, 503, 504}
MAX_RESUME_CHARS = 20_000

logger = logging.getLogger("career_companion")

SYSTEM_PROMPT = """You extract structured data from resumes.
Return ONLY a JSON object with exactly these keys:
- full_name (string or null)
- email (string or null)
- phone (string or null)
- location (string or null)
- preferred_role (string or null)
- preferred_location (string or null)
- summary (string or null): 2-3 sentence professional summary
- skills (array of strings): technical skills
- soft_skills (array of strings)
- education (array of objects with keys: institution, degree, field, start_date, end_date, grade)
- experience (array of objects with keys: company, role, start_date, end_date, location, description)
- projects (array of objects with keys: name, description, technologies, link)
- certifications (array of strings)
Use null or [] when information is missing. Never invent facts that are not in the resume."""


def _clean_json(text: str) -> str:
    """Strip ```json fences some models add around their output."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return text.strip()


def parse_resume_with_llm(raw_resume_text: str) -> CandidateProfile:
    """Send resume text to an OpenAI-compatible API and validate the JSON reply."""
    api_key = (
        os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    ).strip().strip('"').strip("'")
    if not api_key:
        raise RuntimeError(
            f"GROQ_API_KEY is not set. Create a file named .env at {ENV_PATH} "
            "containing the line: GROQ_API_KEY=your_key"
        )

    client = OpenAI(
        api_key=api_key,
        base_url=BASE_URL,
        timeout=REQUEST_TIMEOUT_S,
        max_retries=0,  # we handle retries ourselves below
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Resume text:\n\n" + raw_resume_text[:MAX_RESUME_CHARS],
        },
    ]

    last_error: Exception | None = None
    for attempt in range(RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("The model returned an empty response.")
            return CandidateProfile.model_validate_json(_clean_json(content))

        except APIStatusError as exc:
            code = exc.status_code
            if code == 401:
                raise RuntimeError(
                    "The API key was rejected (401). Check GROQ_API_KEY in .env."
                ) from exc
            if code == 404:
                raise RuntimeError(
                    f"Model '{MODEL_NAME}' was not found for this key (404). "
                    "Change LLM_MODEL in .env (run check_llm.py to list valid names)."
                ) from exc
            if code == 429 and "insufficient_quota" in str(exc):
                raise RuntimeError(
                    "This account has no credits or quota left. Add credits, "
                    "or wait for the free-tier limit to reset."
                ) from exc
            if code not in RETRYABLE_CODES:
                raise
            last_error = exc
            wait = min(2 ** attempt * 2, 15)
            logger.warning(
                "%s returned %s (attempt %d/%d). Retrying in %ds...",
                MODEL_NAME, code, attempt + 1, RETRIES, wait,
            )
            time.sleep(wait)

        except (APITimeoutError, APIConnectionError) as exc:
            last_error = exc
            logger.warning(
                "Timeout or connection problem (attempt %d/%d): %s",
                attempt + 1, RETRIES, exc,
            )
            time.sleep(2)

    raise RuntimeError(
        "The AI service did not respond in time. Please try again in a minute. "
        f"Last error: {last_error}"
    )
