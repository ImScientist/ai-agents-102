"""
serpapi_client.py
Low-level HTTP client for the SerpApi Google Jobs endpoint.

Endpoint: https://serpapi.com/search
Authentication: API key passed as the `api_key` query parameter.
Docs: https://serpapi.com/google-jobs-api

All calls are unauthenticated GET requests — the API key is injected at
call time from the environment variable SERPAPI_KEY.
"""

import logging
import os

import requests

from models import DetectedExtensions, JobListing, JobSearchResult

logger = logging.getLogger(__name__)

_ENDPOINT = "https://serpapi.com/search"
_TIMEOUT = 15  # seconds


def _get_api_key() -> str:
    """Read the SerpApi key from the environment, raising clearly if missing."""
    key = os.environ.get("SERPAPI_KEY", "").strip()
    if not key:
        raise EnvironmentError(
            "SERPAPI_KEY environment variable is not set. "
            "Sign up at https://serpapi.com to get a free API key and add it to your .env file."
        )
    return key


def _get(params: dict) -> dict:
    """
    Perform a GET request to the SerpApi endpoint and return parsed JSON.

    Raises requests.HTTPError on non-2xx responses.
    Returns an empty payload (with an empty jobs_results list) when Google
    reports no results for the query, rather than raising an exception —
    zero results is a valid outcome for niche or location-restricted searches.
    """
    response = requests.get(_ENDPOINT, params=params, timeout=_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        error_msg = payload["error"]
        if "hasn't returned any results" in error_msg or "No results" in error_msg:
            logger.warning("SerpApi returned no results for query (empty result set).")
            return {"jobs_results": []}
        raise RuntimeError(f"SerpApi error: {error_msg}")
    return payload


def _parse_job(raw: dict) -> JobListing:
    """Convert a raw SerpApi jobs_results entry into a JobListing."""
    ext_raw = raw.get("detected_extensions") or {}
    extensions = DetectedExtensions(
        posted_at=ext_raw.get("posted_at"),
        schedule_type=ext_raw.get("schedule_type"),
        salary=ext_raw.get("salary"),
        work_from_home=ext_raw.get("work_from_home"),
    )

    # Pick the first apply link if available
    apply_links = raw.get("apply_options") or []
    apply_link = apply_links[0].get("link") if apply_links else None

    return JobListing(
        job_id=raw.get("job_id", ""),
        title=raw.get("title", "Unknown"),
        company_name=raw.get("company_name", "Unknown"),
        location=raw.get("location", ""),
        via=raw.get("via"),
        description=raw.get("description"),
        extensions=extensions if any(v is not None for v in ext_raw.values()) else None,
        apply_link=apply_link,
    )


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def search_jobs(
    query: str,
    location: str = "Berlin",
    language: str = "en",
    start: int = 0,
) -> JobSearchResult:
    """
    Search for jobs using the SerpApi Google Jobs engine.

    The location is embedded directly into the query string (e.g. "machine
    learning engineer Berlin") because the Google Jobs engine ignores the
    separate `location` parameter for location-specific job searches.

    Args:
        query:    Free-text job search query, e.g. "machine learning engineer".
                  Do NOT include the city — it is appended automatically.
        location: City/region to append to the query (default "Berlin").
                  Pass an empty string to search globally.
        language: Interface language code (default "en").
        start:    Pagination offset — 0, 10, 20 … (Google returns 10 results per page).

    Returns a JobSearchResult with the matched listings (may be empty).
    """
    api_key = _get_api_key()

    # Embed location in the query — the only reliable way for Google Jobs
    full_query = f"{query} {location}".strip() if location else query

    params = {
        "engine": "google_jobs",
        "q": full_query,
        "hl": language,
        "start": start,
        "api_key": api_key,
    }

    logger.info("Searching SerpApi Google Jobs: q=%r, start=%d", full_query, start)
    payload = _get(params)

    raw_jobs = payload.get("jobs_results") or []
    jobs = [_parse_job(j) for j in raw_jobs]
    logger.info("Received %d job listings", len(jobs))

    return JobSearchResult(
        query=full_query,
        location=location,
        total_results_approx=None,  # Google Jobs does not expose a total count
        jobs=jobs,
    )

