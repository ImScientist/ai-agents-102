"""
models.py
Shared domain models for the Jobs Agent.

Contains models for both:
  - SerpApi Google Jobs (JobListing, JobSearchResult)
  - Adzuna Jobs API   (AdzunaJobListing, AdzunaJobSearchResult)
"""

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# SerpApi / Google Jobs models
# ---------------------------------------------------------------------------

class DetectedExtensions(BaseModel):
    """Structured metadata extracted by Google Jobs from the listing."""
    posted_at: str | None = None          # e.g. "3 days ago"
    schedule_type: str | None = None      # e.g. "Full-time", "Part-time"
    salary: str | None = None             # e.g. "€60,000–€80,000 a year"
    work_from_home: bool | None = None


class JobListing(BaseModel):
    """A single job listing returned by the SerpApi Google Jobs endpoint."""
    job_id: str
    title: str
    company_name: str
    location: str
    via: str | None = None                # Source platform, e.g. "via LinkedIn"
    description: str | None = None
    extensions: DetectedExtensions | None = None
    apply_link: str | None = None         # Direct application URL if available


class JobSearchResult(BaseModel):
    """Result of a single SerpApi Google Jobs query."""
    query: str
    location: str
    total_results_approx: int | None = None
    jobs: list[JobListing]


# ---------------------------------------------------------------------------
# Adzuna API models
# ---------------------------------------------------------------------------

class AdzunaCategory(BaseModel):
    """Job category as returned by the Adzuna API."""
    tag: str | None = None      # e.g. "it-jobs"
    label: str | None = None    # e.g. "IT Jobs"


class AdzunaJobListing(BaseModel):
    """A single job listing returned by the Adzuna Jobs API."""
    id: str
    title: str
    company_name: str
    location_display: str                 # e.g. "Mitte, Berlin"
    location_area: list[str] = []         # e.g. ["Deutschland", "Berlin", "Mitte"]
    description: str | None = None
    redirect_url: str | None = None       # Direct link to the Adzuna listing
    contract_time: str | None = None      # "full_time" | "part_time"
    contract_type: str | None = None      # "permanent" | "contract"
    salary_min: float | None = None
    salary_max: float | None = None
    salary_is_predicted: bool = False     # True when Adzuna estimated the salary
    category: AdzunaCategory | None = None
    created: str | None = None            # ISO date string, e.g. "2026-06-28"
    latitude: float | None = None
    longitude: float | None = None


class AdzunaJobSearchResult(BaseModel):
    """Result of a single Adzuna API query."""
    query: str
    location: str
    country: str                          # ISO 3166-1 alpha-2, e.g. "de"
    page: int
    total_results: int                    # Total matching jobs reported by Adzuna
    jobs: list[AdzunaJobListing]


