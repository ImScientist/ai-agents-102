"""
agent.py
Defines the Jobs Agent and its run function.

Architecture
------------
The agent is given a search tool and a goal. It:
  1. Calls search_jobs one or more times for the requested role categories
     (machine learning, data science, AI engineering).
  2. Aggregates and deduplicates the results.
  3. Returns a structured JobSearchReport with a human-friendly summary.

The LLM drives the flow — it decides how many searches to run and how
to present the results.
"""

import logging
from pydantic import BaseModel
from agents import Agent, Runner, RunHooks, RunContextWrapper
from agents.tool import FunctionTool

from tools import search_jobs_adzuna, search_jobs_serpapi

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured output schema
# ---------------------------------------------------------------------------

class JobSummary(BaseModel):
    title: str
    company_name: str
    location: str
    contract_time: str | None       # "full_time" | "part_time" | None
    contract_type: str | None       # "permanent" | "contract" | None
    salary_min: float | None        # Minimum salary in EUR
    salary_max: float | None        # Maximum salary in EUR
    salary_is_predicted: bool       # True if salary was estimated by Adzuna
    posted_at: str | None           # Posting date, e.g. "2026-06-28"
    category: str | None            # Job category label, e.g. "IT Jobs"
    apply_link: str | None          # Direct URL to the full listing
    description_snippet: str | None # First ~200 chars of the description


class JobSearchReport(BaseModel):
    location: str                   # e.g. "Berlin, Germany"
    categories_searched: list[str]  # e.g. ["machine learning", "data science", "AI engineering"]
    total_jobs_found: int
    jobs: list[JobSummary]
    summary: str                    # 3-5 sentence human-friendly overview


# ---------------------------------------------------------------------------
# Agent instructions
# ---------------------------------------------------------------------------

INSTRUCTIONS = """
You are a helpful job-search assistant specialising in tech roles in Berlin, Germany.
Your task is to find current job openings in machine learning, data science, and AI
engineering in Berlin, and present them in a clear, structured way.

## Tools available
- `search_jobs_adzuna`  — PRIMARY tool. Searches the Adzuna German job index with real
  Berlin listings including salary data. Supports pagination via the `page` parameter.
- `search_jobs_serpapi` — FALLBACK tool. Uses Google Jobs via SerpApi. Use only if Adzuna
  returns no results for a specific query.

## Step 1 — Run targeted searches with Adzuna
Call `search_jobs_adzuna` multiple times to cover the three main categories. Good queries:
  - "machine learning engineer"
  - "data scientist"
  - "AI engineer"
  - "MLOps engineer"
  - "deep learning engineer"
  - "LLM engineer"

Use `page=2` for any query to fetch a second page if you want more breadth.

## Step 2 — Deduplicate
Some jobs may appear in multiple searches. Deduplicate by `id` or by identical
(title, company_name) pairs. Keep the richer of the two records.

## Step 3 — Build the report
Produce a JobSearchReport:
- `location`: "Berlin, Germany"
- `categories_searched`: the list of query strings you actually used.
- `total_jobs_found`: count of unique jobs after deduplication.
- `jobs`: one JobSummary per unique job, ordered by date (most recent first;
  put jobs with no date at the end). For each job:
    - `title`: job title
    - `company_name`: hiring company
    - `location`: location_display string from the listing
    - `contract_time`: "full_time" | "part_time" | null
    - `contract_type`: "permanent" | "contract" | null
    - `salary_min`: minimum salary in EUR (null if missing)
    - `salary_max`: maximum salary in EUR (null if missing)
    - `salary_is_predicted`: true if Adzuna estimated the salary
    - `posted_at`: the `created` date from the listing (null if missing)
    - `category`: category label from the listing (null if missing)
    - `apply_link`: the `redirect_url` from the listing (null if missing)
    - `description_snippet`: first ~200 characters of the description (null if missing)
- `summary`: a 3–5 sentence overview — highlight the number of openings found,
  the most active hiring companies, salary ranges observed (distinguishing real
  vs. predicted salaries), and the most common seniority levels or required skills.

## Rules
- Always try Adzuna first for each query.
- If a search returns no results, note it but continue with the other queries.
- Keep the summary factual, friendly, and useful for a job seeker.
"""


# ---------------------------------------------------------------------------
# Logging hooks
# ---------------------------------------------------------------------------

class LoggingHooks(RunHooks):
    async def on_tool_start(
        self, context: RunContextWrapper, agent: Agent, tool: FunctionTool,
    ) -> None:
        logger.info("🔧  Tool call → %s", tool.name)

    async def on_tool_end(
        self, context: RunContextWrapper, agent: Agent, tool: FunctionTool, result: object,
    ) -> None:
        first_line = str(result).splitlines()[0] if result else ""
        logger.info("    ↳ %s", first_line)


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

jobs_agent = Agent(
    name="Berlin Jobs Agent",
    model="gpt-4o",
    instructions=INSTRUCTIONS,
    output_type=JobSearchReport,
    tools=[search_jobs_adzuna, search_jobs_serpapi],
)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def run(categories: list[str] | None = None) -> JobSearchReport:
    """
    Run the agent to find ML / data science / AI engineering jobs in Berlin.

    Args:
        categories: Optional list of role categories to focus on.
                    Defaults to ["machine learning", "data science", "AI engineering"].

    Returns a structured JobSearchReport.
    """
    if not categories:
        categories = ["machine learning", "data science", "AI engineering"]

    cats_str = ", ".join(categories)
    user_message = (
        f"Find current job openings in Berlin for the following categories: {cats_str}. "
        "Search for each category, deduplicate the results, and give me a full report."
    )

    logger.info("💼  Jobs agent starting for categories: %s", cats_str)
    result = await Runner.run(
        jobs_agent,
        input=user_message,
        hooks=LoggingHooks(),
        max_turns=15,
    )
    return result.final_output

