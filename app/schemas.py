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


class LLMScore(BaseModel):
    score: int
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    reason: str = ""


class MatchResult(BaseModel):
    job_id: str
    semantic_score: float
    llm_score: Optional[float] = None
    preference_score: float = 0.0
    final_score: float
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    reason: str = ""
    verdict: str = "skip"


class TailoredBullet(BaseModel):
    text: str
    source: str = ""        # profile ka kaun sa project/company se aaya


class TailorOutput(BaseModel):
    summary: str = ""
    skills_to_highlight: List[str] = Field(default_factory=list)
    bullets: List[TailoredBullet] = Field(default_factory=list)
    cover_letter: str = ""


class CriticReport(BaseModel):
    passed: bool
    violations: List[str] = Field(default_factory=list)


class TailoredDoc(BaseModel):
    job_id: str
    summary: str = ""
    skills_to_highlight: List[str] = Field(default_factory=list)
    bullets: List[TailoredBullet] = Field(default_factory=list)
    cover_letter: str = ""
    attempts: int = 1
    passed: bool = False
    issues: List[str] = Field(default_factory=list)