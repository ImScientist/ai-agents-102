"""
models.py
Shared domain models for the Jobs Agent.
"""

from pydantic import BaseModel


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

