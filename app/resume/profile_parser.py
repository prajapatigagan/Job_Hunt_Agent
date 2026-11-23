import sys

from app.config import MAX_RESUME_CHARS
from app.llm import generate_structured
from app.resume.pdf_reader import read_pdf_text
from app.schemas import UserProfile

SYSTEM_PROMPT = """You are a precise resume parser.
Extract the candidate's details from the resume text into the given JSON schema.

Rules:
- Use ONLY information present in the resume. Never invent or guess anything.
- If a field is missing, use null (or an empty list for lists).
- skills: a flat list of individual skills/technologies (no sentences).
- Keep bullet points close to the original wording.
- Dates: keep as written in the resume (e.g. "Jun 2024", "2023", "Present").
- projects and experience are different: internships/jobs go to experience, personal/academic work goes to projects.
"""


def parse_resume_text(text: str) -> UserProfile:
    text = text[:MAX_RESUME_CHARS]
    return generate_structured(SYSTEM_PROMPT, f"RESUME TEXT:\n\n{text}", UserProfile)


def parse_resume_pdf(path: str) -> UserProfile:
    return parse_resume_text(read_pdf_text(path))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.resume.profile_parser <resume.pdf>")
        sys.exit(1)
    print(parse_resume_pdf(sys.argv[1]).model_dump_json(indent=2))
