from typing import List, Optional

from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    """Structured candidate data extracted from a resume."""

    model_config = {"extra": "allow"}

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    preferred_role: Optional[str] = None
    preferred_location: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    education: List[dict] = Field(default_factory=list)
    experience: List[dict] = Field(default_factory=list)
    projects: List[dict] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
