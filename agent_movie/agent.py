"""
agent.py
Defines the Movie Agent and its run function.

Architecture
------------
The agent is given two tools and a goal. It:
  1. Calls list_berlin_cinemas to find the cinema the user asked for.
  2. Calls get_cinema_program to retrieve today's (or a specific day's) shows.
  3. Returns a structured CinemaProgramReport with a human-friendly summary.

The LLM drives the flow — it performs fuzzy matching of the cinema name
and decides how to present the results.
"""

import logging
from pydantic import BaseModel
from agents import Agent, Runner, RunHooks, RunContextWrapper
from agents.tool import FunctionTool

from tools import list_berlin_cinemas, get_cinema_program

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured output schema
# ---------------------------------------------------------------------------

class ShowSummary(BaseModel):
    time: str                       # "HH:MM" local time, e.g. "19:30"
    title: str
    duration_minutes: int | None
    language_note: str | None       # e.g. "OV", "OmU", "DE"
    ticket_url: str | None


class CinemaProgramReport(BaseModel):
    cinema_name: str
    date: str                       # YYYY-MM-DD
    shows: list[ShowSummary]
    summary: str                    # 2-3 sentence human-friendly overview


# ---------------------------------------------------------------------------
# Agent instructions
# ---------------------------------------------------------------------------

INSTRUCTIONS = """
You are a helpful cinema assistant for Berlin. Your job is to look up what
is playing at a particular cinema today (or on a requested date) and present
the program in a clear, friendly way.

## Step 1 — Discover cinemas
Call `list_berlin_cinemas` to get all cinemas in Berlin with their IDs and names.
Find the cinema that best matches the user's request (use fuzzy/partial matching
if needed — e.g. "CineStar" should match "CineStar Berlin – CUBIX am Alexanderplatz").

## Step 2 — Fetch the program
Call `get_cinema_program` with the correct cinema_id, cinema_name, and optionally
a date_iso (YYYY-MM-DD). If the user did not specify a date, omit date_iso so it
defaults to today.

## Step 3 — Build the report
From the raw show data, produce a CinemaProgramReport:
- `cinema_name`: the exact name from the API.
- `date`: the date of the program (YYYY-MM-DD).
- `shows`: one ShowSummary per show, ordered by start time, where:
    - `time` is the local start time formatted as "HH:MM".
    - `title` is the movie title.
    - `duration_minutes` is the runtime in minutes (null if unknown).
    - `language_note` is derived from audioLanguage / subtitleLanguage:
        • "OmU"  if subtitle is German/Deutsch
        • "OV"   if audio is non-German and there are no German subtitles
        • "DE"   if audio is German (or language info is missing)
        • null   if no language information is available at all
    - `ticket_url` is the deeplink (null if none).
- `summary`: a 2-3 sentence human-friendly overview of the program
  (number of unique movies, genres or highlights, any notable screenings).

## Rules
- If no cinema matches the user's request, set `shows` to [] and explain in `summary`.
- If the cinema exists but has no shows on the requested date, say so in `summary`.
- Keep the summary friendly and concise.
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

movie_agent = Agent(
    name="Berlin Movie Agent",
    model="gpt-4o",
    instructions=INSTRUCTIONS,
    output_type=CinemaProgramReport,
    tools=[list_berlin_cinemas, get_cinema_program],
)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def run(cinema_query: str, date_iso: str | None = None) -> CinemaProgramReport:
    """
    Run the agent for a given cinema name query and optional date.

    Args:
        cinema_query: Free-text cinema name, e.g. "CineStar" or "Babylon".
        date_iso:     Date in YYYY-MM-DD format, or None for today.

    Returns a structured CinemaProgramReport.
    """
    user_message = f"What is playing at {cinema_query!r} today?"
    if date_iso:
        user_message = f"What is playing at {cinema_query!r} on {date_iso}?"

    logger.info("🎬  Movie agent starting for query: %r", cinema_query)
    result = await Runner.run(
        movie_agent,
        input=user_message,
        hooks=LoggingHooks(),
        max_turns=10,
    )
    return result.final_output
