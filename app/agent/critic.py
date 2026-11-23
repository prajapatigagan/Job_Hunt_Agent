import re

from app.llm import generate_structured
from app.schemas import CriticReport


def output_to_text(output):
    parts = [output.summary, output.cover_letter]
    for b in output.bullets:
        parts.append(b.text)
    return "\n".join(parts)


def has_word(text, word):
    # poora shabd dhundta hai (C++ ya Java jaise skills ke liye)
    pattern = r"(?<![A-Za-z0-9])" + re.escape(word) + r"(?![A-Za-z0-9])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def rule_check(profile, match, output):
    # layer 1: code ke rules
    problems = []
    text = output_to_text(output)
    profile_json = profile.model_dump_json().lower()

    if not output.bullets:
        problems.append("There are no resume bullets.")

    # 1. numbers jo profile me nahi hain (2+ digits)
    wrong_numbers = set()
    for number in re.findall(r"\d+(?:\.\d+)?", text):
        if len(number) >= 2 and number not in profile_json:
            wrong_numbers.add(number)
    for number in wrong_numbers:
        problems.append(f"The number '{number}' is not in the profile. Remove it.")

    # 2. wo skills jo candidate ke paas nahi hain
    if match is not None:
        for skill in match.missing_skills:
            if has_word(text, skill):
                problems.append(f"It mentions '{skill}', but the candidate does not have this skill.")

    # 3. highlight ki gayi skills profile me honi chahiye
    known = [s.lower() for s in profile.skills]
    for skill in output.skills_to_highlight:
        if skill.lower() not in known:
            problems.append(f"'{skill}' in skills_to_highlight is not in the profile skills.")

    # 4. har bullet ka source asli project/company ka naam ho
    names = [p.name.lower() for p in profile.projects]
    names += [e.company.lower() for e in profile.experience]
    for b in output.bullets:
        if b.source.lower() not in names:
            problems.append(f"Bullet source '{b.source}' is not a project or company name from the profile.")

    return problems


CRITIC_PROMPT = """You are a strict fact checker for resumes and cover letters.
You get the candidate's real profile and a tailored resume/cover letter.

Find every claim that is NOT supported by the profile: skills, tools, companies, numbers, dates, achievements, responsibilities.
- Rephrasing and reordering are allowed.
- Inventing or exaggerating is not allowed.

Return passed=true only if there are no unsupported claims.
Otherwise return passed=false and list each unsupported claim in violations (one short line each, maximum 5).
"""


def llm_check(profile, output):
    # layer 2: LLM fact-checker
    bullets_text = "\n".join(f"- {b.text} (source: {b.source})" for b in output.bullets)
    user_text = (
        "CANDIDATE PROFILE (JSON):\n"
        + profile.model_dump_json(indent=1)
        + "\n\nTAILORED SUMMARY:\n" + output.summary
        + "\n\nTAILORED BULLETS:\n" + bullets_text
        + "\n\nCOVER LETTER:\n" + output.cover_letter
    )
    report = generate_structured(CRITIC_PROMPT, user_text, CriticReport)
    if report.passed:
        return []
    return report.violations or ["The fact checker rejected the draft."]


def check_all(profile, match, output):
    problems = rule_check(profile, match, output)
    problems += llm_check(profile, output)
    return problems