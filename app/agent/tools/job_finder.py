import re
import requests

from app.config import RAPIDAPI_KEY, JOB_COUNTRY, MAX_QUERIES
from app.schemas import Job


class JobSearchError(Exception):
    pass


def make_queries(prefs):
    # har role ko har city ke saath jodta hai
    roles = prefs.target_roles
    if not roles:
        roles = ["python developer"]

    cities = prefs.cities
    if not cities:
        cities = [""]

    queries = []
    for role in roles:
        for city in cities:
            queries.append((role, city))

    # free plan me sirf 200 requests/month, isliye kam queries
    return queries[:MAX_QUERIES]


def fetch_jobs(what, where):
    url = "https://jsearch.p.rapidapi.com/search-v2"

    # JSearch me role aur city ek hi query string me jaati hai
    query = what
    if where:
        query = f"{what} in {where}"

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }
    params = {
        "query": query,
        "num_pages": 1,
        "country": JOB_COUNTRY,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
    except requests.RequestException as e:
        raise JobSearchError(f"Internet ya JSearch se connect nahi hua: {e}")

    if response.status_code in (401, 403):
        raise JobSearchError("RapidAPI key galat hai ya JSearch subscribe nahi kiya.")
    if response.status_code == 429:
        raise JobSearchError("Request limit khatam ho gayi. Thodi der baad try karo.")
    if response.status_code != 200:
        raise JobSearchError(f"JSearch error {response.status_code}: {response.text[:200]}")

    body = response.json()
    data = body.get("data")

    # naye version me data list ya dict dono ho sakta hai
    jobs = []
    if isinstance(data, list):
        jobs = data
    elif isinstance(data, dict):
        for key in ("jobs", "results", "items"):
            if isinstance(data.get(key), list):
                jobs = data[key]
                break
        if not jobs:
            for value in data.values():
                if isinstance(value, list):
                    jobs = value
                    break

    if not jobs:
        print("DEBUG: jobs nahi mili, response ye tha:", str(body)[:500])

    return jobs


def clean_job(raw):
    title = re.sub(r"<[^>]+>", "", raw.get("job_title") or "").strip()
    description = (raw.get("job_description") or "").strip()

    # city na ho to country dikha do
    location = raw.get("job_city") or raw.get("job_country") or ""

    return Job(
        id=str(raw.get("job_id")),
        title=title,
        company=raw.get("employer_name") or "Unknown",
        location=location,
        description=description,
        url=raw.get("job_apply_link") or "",
        source=raw.get("job_publisher") or "jsearch",
        posted_at=raw.get("job_posted_at_datetime_utc"),
        salary_min=raw.get("job_min_salary"),
        salary_max=raw.get("job_max_salary"),
    )


def remove_duplicates(jobs):
    seen_ids = set()
    seen_pairs = set()
    unique = []

    for job in jobs:
        pair = (job.title.lower(), job.company.lower())
        if job.id in seen_ids or pair in seen_pairs:
            continue
        seen_ids.add(job.id)
        seen_pairs.add(pair)
        unique.append(job)

    return unique


def remove_blacklisted(jobs, blacklist):
    blocked = [name.lower() for name in blacklist]
    result = []
    for job in jobs:
        if job.company.lower() in blocked:
            continue
        result.append(job)
    return result


def find_jobs(prefs):
    if not RAPIDAPI_KEY:
        raise JobSearchError("RAPIDAPI_KEY nahi mili. .env file me daalo.")

    all_jobs = []
    for what, where in make_queries(prefs):
        raw_list = fetch_jobs(what, where)
        for raw in raw_list:
            try:
                all_jobs.append(clean_job(raw))
            except Exception:
                # koi ek kharab job poora search na roke
                continue

    jobs = remove_duplicates(all_jobs)
    jobs = remove_blacklisted(jobs, prefs.blacklist_companies)
    return jobs


if __name__ == "__main__":
    # bina UI ke test:  python -m app.agent.tools.job_finder
    from app.storage import db

    db.init_db()
    prefs = db.load_preferences()
    if prefs is None:
        print("Pehle UI me preferences save karo.")
    else:
        jobs = find_jobs(prefs)
        print(f"{len(jobs)} jobs mili")
        for job in jobs[:10]:
            print("-", job.title, "|", job.company, "|", job.location, "|", job.source)