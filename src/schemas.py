from typing import List, Optional
from pydantic import BaseModel, Field


class EducationItem(BaseModel):
    degree: str
    institution: str
    graduation_year: Optional[str] = None
    cgpa_or_percentage: Optional[str] = None


class ExperienceItem(BaseModel):
    role: str
    organization: str
    duration: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    title: str
    tech_stack: List[str] = Field(default_factory=list)
    description: str


class CandidateProfile(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: str
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    target_roles: List[str] = Field(default_factory=list)