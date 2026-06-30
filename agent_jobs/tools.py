"""
tools.py
All tools available to the Jobs Agent.
The LLM decides which tools to call and in what order — not our code.
"""

import json
import logging

from agents import function_tool

from serpapi_client import search_jobs as _search_jobs

logger = logging.getLogger(__name__)

_DEFAULT_LOCATION = "Berlin"


# ---------------------------------------------------------------------------
# Tool: search jobs
# ---------------------------------------------------------------------------

@function_tool
def search_jobs(query: str, start: int = 0) -> str:
    """
    Search for job openings in Berlin using the Google Jobs engine (via SerpApi).

    The city "Berlin" is automatically appended to your query. You only need
    to provide the role/skill part, e.g. "machine learning engineer" or
    "data scientist Python".

    Args:
        query: Free-text job role/skills query WITHOUT the city name.
               E.g. "machine learning engineer", "data scientist Python",
               "MLOps engineer", "AI researcher".
        start: Pagination offset. Use 0 for the first page, 10 for the second,
               20 for the third, etc. Google Jobs returns 10 results per page.

    Returns a JSON object with:
        query        – the full search query sent (role + "Berlin")
        location     – the location appended ("Berlin")
        jobs         – array of job objects, each with:
            job_id       – unique identifier
            title        – job title
            company_name – hiring company
            location     – job location string
            via          – source platform (e.g. "via LinkedIn")
            description  – full job description snippet
            extensions:
                posted_at     – relative post date (e.g. "3 days ago")
                schedule_type – e.g. "Full-time"
                salary        – salary range if listed
                work_from_home – true/false
            apply_link   – direct application URL (may be null)
    """
    result = _search_jobs(query=query, location=_DEFAULT_LOCATION, start=start)
    return json.dumps(result.model_dump(), ensure_ascii=False, indent=2)

