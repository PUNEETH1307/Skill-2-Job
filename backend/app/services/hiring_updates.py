"""Live hiring and preparation resources for saved Dream Jobs."""

import json
import logging
import re
import threading
import time
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)
_CACHE: dict[str, tuple[float, list[dict]]] = {}
_CACHE_LOCK = threading.Lock()
_CACHE_TTL_SECONDS = 900


def get_hiring_updates(company_name: str, role_title: str) -> dict:
    """Return live apply links, preparation resources, and a safe fallback."""
    key = f"{company_name.strip().lower()}|{role_title.strip().lower()}"
    now = time.monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get(key)
        if cached and now - cached[0] < _CACHE_TTL_SECONDS:
            live_jobs = cached[1]
        else:
            live_jobs = _fetch_live_jobs(company_name, role_title)
            _CACHE[key] = (now, live_jobs)

    encoded_query = quote_plus(f"{company_name} {role_title}")
    if not live_jobs:
        live_jobs = [{
            "title": f"Apply for {role_title} openings at {company_name}",
            "company_name": company_name,
            "apply_url": f"https://www.linkedin.com/jobs/search/?keywords={encoded_query}",
            "source": "LinkedIn Jobs",
            "posted_at": None,
            "location": None,
        }]

    role_query = quote_plus(role_title)
    company_query = quote_plus(company_name)
    company_slug = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
    resources = [
        {
            "title": f"Previous-year {role_title} interview questions",
            "provider": "GeeksforGeeks",
            "url": f"https://www.geeksforgeeks.org/search/?q={company_query}%20{role_query}%20interview%20questions",
        },
        {
            "title": f"{role_title} aptitude and reasoning questions",
            "provider": "IndiaBIX",
            "url": "https://www.indiabix.com/aptitude/questions-and-answers/",
        },
        {
            "title": f"{role_title} coding practice questions",
            "provider": "LeetCode",
            "url": f"https://leetcode.com/problemset/?search={role_query}",
        },
        {
            "title": f"{company_name} interview experiences",
            "provider": "AmbitionBox",
            "url": f"https://www.ambitionbox.com/interviews/{company_slug}-interview-questions",
        },
    ]
    return {
        "live_jobs": live_jobs,
        "preparation_resources": resources,
        "last_checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _fetch_live_jobs(company_name: str, role_title: str) -> list[dict]:
    """Fetch current public listings; failures degrade to the search fallback."""
    try:
        request = Request(
            "https://www.arbeitnow.com/api/job-board-api",
            headers={"User-Agent": "Skill2Job/1.0"},
        )
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        company_key = company_name.lower()
        role_words = [word for word in role_title.lower().split() if len(word) > 2]
        matches = []
        for job in payload.get("data", []):
            title = str(job.get("title") or "")
            listed_company = str(job.get("company_name") or "")
            haystack = f"{title} {listed_company}".lower()
            company_match = company_key in listed_company.lower() or listed_company.lower() in company_key
            role_match = not role_words or sum(word in haystack for word in role_words) >= max(1, len(role_words) // 2)
            if company_match and role_match and job.get("url"):
                matches.append({
                    "title": title,
                    "company_name": listed_company or company_name,
                    "apply_url": job["url"],
                    "source": "Arbeitnow",
                    "posted_at": job.get("created_at"),
                    "location": job.get("location"),
                })
            if len(matches) >= 10:
                break
        return matches
    except Exception as exc:
        logger.warning("Live hiring lookup failed for %s/%s: %s", company_name, role_title, exc)
        return []
