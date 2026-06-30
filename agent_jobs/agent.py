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

from tools import search_jobs

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured output schema
# ---------------------------------------------------------------------------

class JobSummary(BaseModel):
    title: str
    company_name: str
    location: str
    schedule_type: str | None       # e.g. "Full-time", "Part-time"
    salary: str | None              # e.g. "€60,000–€80,000 a year"
    posted_at: str | None           # e.g. "3 days ago"
    work_from_home: bool | None
    via: str | None                 # e.g. "via LinkedIn"
    apply_link: str | None
    description_snippet: str | None  # First ~200 chars of the description


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
You are a helpful job-search assistant specialising in tech roles in Berlin.
Your task is to find current job openings in machine learning, data science,
and AI engineering in Berlin, and present them in a clear, structured way.

## Step 1 — Run targeted searches
Call `search_jobs` multiple times with specific queries to cover the three
categories. Good example queries:
- "machine learning engineer Berlin"
- "data scientist Berlin"
- "AI engineer Berlin"
- "MLOps engineer Berlin"

You may call `search_jobs` with `start=10` to fetch a second page for any
query if you want more results.

## Step 2 — Deduplicate
Some jobs may appear in multiple searches. Deduplicate by job_id or by
identical (title, company_name) pairs. Keep the richer of the two records.

## Step 3 — Build the report
Produce a JobSearchReport:
- `location`: "Berlin, Germany"
- `categories_searched`: the list of query strings you actually used.
- `total_jobs_found`: count of unique jobs after deduplication.
- `jobs`: one JobSummary per unique job, ordered by recency (most recent first,
  using posted_at; put jobs with no date at the end). For each job:
    - `title`: job title
    - `company_name`: hiring company
    - `location`: location string from the listing
    - `schedule_type`: from extensions (null if missing)
    - `salary`: from extensions (null if missing)
    - `posted_at`: from extensions (null if missing)
    - `work_from_home`: from extensions (null if missing)
    - `via`: the source platform
    - `apply_link`: direct URL to apply (null if missing)
    - `description_snippet`: first ~200 characters of the description (null if missing)
- `summary`: a 3-5 sentence overview — highlight the number of openings found,
  the most active hiring companies, any salary ranges observed, and the most
  common seniority levels or required skills.

## Rules
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
    tools=[search_jobs],
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

