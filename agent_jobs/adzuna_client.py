"""
adzuna_client.py
Low-level HTTP client for the Adzuna Jobs API.

Endpoint: https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
Auth    : app_id + app_key as query parameters.
Docs    : https://developer.adzuna.com/activedocs

Environment variables required:
    ADZUNA_APP_ID   – short alphanumeric application ID (8 chars)
    ADZUNA_API_KEY  – 32-character hex application key
"""

import logging
import os
from datetime import datetime

import requests

from models import AdzunaJobListing, AdzunaCategory, AdzunaJobSearchResult

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.adzuna.com/v1/api/jobs"
_TIMEOUT = 15  # seconds


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------

def _get_credentials() -> tuple[str, str]:
    """Read app_id and app_key from the environment, raising clearly if missing."""
    app_id = os.environ.get("ADZUNA_APP_ID", "").strip()
    app_key = os.environ.get("ADZUNA_API_KEY", "").strip()
    if not app_id:
        raise EnvironmentError(
            "ADZUNA_APP_ID environment variable is not set. "
            "Find it at https://developer.adzuna.com under your application."
        )
    if not app_key:
        raise EnvironmentError(
            "ADZUNA_API_KEY environment variable is not set. "
            "Find it at https://developer.adzuna.com under your application."
        )
    return app_id, app_key


# ---------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------

def _get(country: str, page: int, params: dict) -> dict:
    """
    Perform a GET request to the Adzuna search endpoint and return parsed JSON.

    Raises:
        requests.HTTPError  on non-2xx HTTP responses.
        RuntimeError        on Adzuna API-level errors (exception field in JSON).
    """
    url = f"{_BASE_URL}/{country}/search/{page}"
    response = requests.get(url, params=params, timeout=_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    if "exception" in payload:
        raise RuntimeError(
            f"Adzuna API error [{payload['exception']}]: {payload.get('display', '')}"
        )
    return payload


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_job(raw: dict) -> AdzunaJobListing:
    """Convert a raw Adzuna result entry into an AdzunaJobListing."""
    raw_loc = raw.get("location") or {}
    raw_cat = raw.get("category") or {}

    category = AdzunaCategory(
        tag=raw_cat.get("tag"),
        label=raw_cat.get("label"),
    ) if raw_cat else None

    # Parse ISO-8601 created date to a readable string
    created_raw = raw.get("created")
    created_str: str | None = None
    if created_raw:
        try:
            dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
            created_str = dt.strftime("%Y-%m-%d")
        except ValueError:
            created_str = created_raw

    return AdzunaJobListing(
        id=str(raw.get("id", "")),
        title=raw.get("title", "Unknown"),
        company_name=raw.get("company", {}).get("display_name", "Unknown"),
        location_display=raw_loc.get("display_name", ""),
        location_area=raw_loc.get("area", []),
        description=raw.get("description"),
        redirect_url=raw.get("redirect_url"),
        contract_time=raw.get("contract_time"),    # "full_time" | "part_time" | None
        contract_type=raw.get("contract_type"),    # "permanent" | "contract" | None
        salary_min=raw.get("salary_min"),
        salary_max=raw.get("salary_max"),
        salary_is_predicted=raw.get("salary_is_predicted") == 1,
        category=category,
        created=created_str,
        latitude=raw.get("latitude"),
        longitude=raw.get("longitude"),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def search_jobs(
    query: str,
    location: str = "Berlin",
    country: str = "de",
    page: int = 1,
    results_per_page: int = 10,
    sort_by: str = "date",
) -> AdzunaJobSearchResult:
    """
    Search for jobs via the Adzuna API.

    Args:
        query            : Free-text job role / skills query, e.g. "machine learning engineer".
        location         : City or region filter, e.g. "Berlin". Pass empty string for all Germany.
        country          : ISO 3166-1 alpha-2 country code (default "de" = Germany).
        page             : 1-based page number (default 1). Each page returns `results_per_page` jobs.
        results_per_page : Number of results per page (default 10, max 50).
        sort_by          : "date" (most recent first) or "salary" (highest first).

    Returns:
        AdzunaJobSearchResult with the matched listings plus total count.
    """
    app_id, app_key = _get_credentials()

    params: dict = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": results_per_page,
        "what": query,
        "sort_by": sort_by,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location

    logger.info(
        "Adzuna search: country=%s query=%r location=%r page=%d", country, query, location, page
    )
    payload = _get(country=country, page=page, params=params)

    raw_jobs = payload.get("results") or []
    jobs = [_parse_job(j) for j in raw_jobs]
    total = payload.get("count", 0)

    logger.info("Adzuna returned %d jobs (total available: %d)", len(jobs), total)

    return AdzunaJobSearchResult(
        query=query,
        location=location,
        country=country,
        page=page,
        total_results=total,
        jobs=jobs,
    )

