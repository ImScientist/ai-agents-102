"""
tools.py
All tools available to the Jobs Agent.
The LLM decides which tools to call and in what order — not our code.
"""

import json
import logging

from agents import function_tool

from adzuna_client import search_jobs as _adzuna_search
from serpapi_client import search_jobs as _serpapi_search

logger = logging.getLogger(__name__)

_DEFAULT_LOCATION = "Berlin"
_DEFAULT_COUNTRY  = "de"


# ---------------------------------------------------------------------------
# Tool: search_jobs_adzuna  (primary — real Berlin results)
# ---------------------------------------------------------------------------

@function_tool
def search_jobs_adzuna(query: str, page: int = 1) -> str:
    """
    Search for job openings in Berlin, Germany using the Adzuna Jobs API.

    This is the primary job search tool. It returns real, up-to-date listings
    from the German job market, including salary ranges where available.

    Args:
        query: Free-text job role/skills query, e.g. "machine learning engineer",
               "data scientist Python", "MLOps engineer", "AI researcher",
               "LLM engineer". Do NOT include the city — Berlin is used automatically.
        page:  1-based page number (default 1). Each page returns 10 jobs.
               Use page=2, page=3, etc. to fetch additional results.

    Returns a JSON object with:
        query          – the search query sent
        location       – "Berlin"
        country        – "de"
        page           – current page number
        total_results  – total matching jobs available across all pages
        jobs           – array of up to 10 job objects, each with:
            id               – unique Adzuna job ID
            title            – job title
            company_name     – hiring company
            location_display – location string, e.g. "Mitte, Berlin"
            location_area    – list of area hierarchy, e.g. ["Deutschland", "Berlin", "Mitte"]
            description      – job description snippet
            redirect_url     – link to the full listing on adzuna.de
            contract_time    – "full_time" | "part_time" | null
            contract_type    – "permanent" | "contract" | null
            salary_min       – minimum salary in EUR (null if not listed)
            salary_max       – maximum salary in EUR (null if not listed)
            salary_is_predicted – true if Adzuna estimated the salary
            category:
                tag          – category tag, e.g. "it-jobs"
                label        – human label, e.g. "IT Jobs"
            created          – posting date, e.g. "2026-06-28"
    """
    result = _adzuna_search(
        query=query,
        location=_DEFAULT_LOCATION,
        country=_DEFAULT_COUNTRY,
        page=page,
        results_per_page=10,
        sort_by="date",
    )
    return json.dumps(result.model_dump(), ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool: search_jobs_serpapi  (fallback — Google Jobs engine)
# ---------------------------------------------------------------------------

@function_tool
def search_jobs_serpapi(query: str, start: int = 0) -> str:
    """
    Search for job openings using the Google Jobs engine via SerpApi.

    Use this as a fallback if Adzuna returns no results for a specific query,
    or to cross-check listings. Note: on the free SerpApi tier, results are
    US-based and may not reflect the Berlin market.

    Args:
        query: Free-text job role/skills query WITHOUT the city name,
               e.g. "machine learning engineer", "data scientist Python".
               The city "Berlin" is appended automatically.
        start: Pagination offset — 0 (first page), 10 (second), 20 (third), etc.

    Returns a JSON object with:
        query        – the full search query sent (role + "Berlin")
        location     – "Berlin"
        jobs         – array of job objects, each with:
            job_id, title, company_name, location, via, description,
            extensions (posted_at, schedule_type, salary, work_from_home),
            apply_link
    """
    result = _serpapi_search(query=query, location=_DEFAULT_LOCATION, start=start)
    return json.dumps(result.model_dump(), ensure_ascii=False, indent=2)

