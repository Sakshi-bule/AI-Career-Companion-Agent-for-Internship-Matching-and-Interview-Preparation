from typing import List, Optional
from pydantic import BaseModel, Field


class EducationItem(BaseModel):
    degree: str = Field(description="Degree name, e.g., B.E. in Computer Engineering")
    institution: str = Field(description="College or university name")
    graduation_year: Optional[str] = Field(default=None, description="Expected or completed year")
    cgpa_or_percentage: Optional[str] = Field(default=None, description="CGPA or percentage if listed")


class ExperienceItem(BaseModel):
    role: str = Field(description="Internship or job title")
    organization: str = Field(description="Company or organization name")
    duration: Optional[str] = Field(default=None, description="Start and end dates")
    responsibilities: List[str] = Field(default_factory=list, description="Key work done or achievements")


class ProjectItem(BaseModel):
    title: str = Field(description="Project title")
    tech_stack: List[str] = Field(default_factory=list, description="Technologies, libraries, or tools used")
    description: str = Field(description="Brief summary of what was built and its outcome")


class CandidateProfile(BaseModel):
    full_name: str = Field(description="Candidate's full name")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: Optional[str] = Field(default=None, description="City and state")
    summary: str = Field(description="2-sentence professional summary based on the resume")
    technical_skills: List[str] = Field(default_factory=list, description="Programming languages, frameworks, ML/AI tools, databases")
    soft_skills: List[str] = Field(default_factory=list, description="Communication, leadership, teamwork, etc.")
    education: List[EducationItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list, description="Relevant certifications or virtual internships")
    target_roles: List[str] = Field(default_factory=list, description="Recommended internship roles matching this profile")