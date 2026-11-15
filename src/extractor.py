import os
from google import genai
from google.genai import types
from .schemas import CandidateProfile


def parse_resume_with_llm(raw_resume_text: str) -> CandidateProfile:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY is missing in .env")

    client = genai.Client(api_key=api_key)

    prompt = (
        "Extract accurate, structured candidate details from the resume below. "
        "Only use facts explicitly present in the resume.\n\n"
        f"RESUME TEXT:\n{raw_resume_text}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CandidateProfile,
            temperature=0.1,
        ),
    )

    return CandidateProfile.model_validate_json(response.text)
