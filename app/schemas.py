from typing import List, Optional

from pydantic import BaseModel, Field


class Experience(BaseModel):
    company: str
    role: str
    start: Optional[str] = None
    end: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)


class Project(BaseModel):
    name: str
    tech: List[str] = Field(default_factory=list)
    bullets: List[str] = Field(default_factory=list)


class Education(BaseModel):
    institute: str
    degree: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    score: Optional[str] = None


class UserProfile(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    links: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)


class Preferences(BaseModel):
    target_roles: List[str] = Field(default_factory=list)
    cities: List[str] = Field(default_factory=list)
    remote_ok: bool = True
    min_salary_lpa: Optional[float] = None
    experience_level: str = "fresher"
    must_have_skills: List[str] = Field(default_factory=list)
    blacklist_companies: List[str] = Field(default_factory=list)

class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str = ""
    description: str = ""
    url: str = ""
    source: str = "adzuna"
    posted_at: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None