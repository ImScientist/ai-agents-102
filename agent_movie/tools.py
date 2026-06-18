"""
tools.py
All tools available to the Movie Agent.
The LLM decides which tools to call and in what order — not our code.
"""

import json
import logging
from datetime import date

from agents import function_tool

from kinoheld_client import fetch_berlin_cinemas, fetch_program
from models import Cinema

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool: list cinemas
# ---------------------------------------------------------------------------

@function_tool
def list_berlin_cinemas() -> str:
    """
    Return a list of all cinemas currently registered in Berlin on Kinoheld.

    Use this first to discover available cinemas and their IDs before
    fetching the program for a specific one.

    Returns a JSON array where each element has:
        id        – Kinoheld cinema ID (needed for get_cinema_program)
        name      – Human-readable cinema name
        url_slug  – URL slug used on kinoheld.de
    """
    cinemas = fetch_berlin_cinemas()
    return json.dumps(
        [c.model_dump() for c in cinemas],
        ensure_ascii=False,
        indent=2,
    )


# ---------------------------------------------------------------------------
# Tool: get program
# ---------------------------------------------------------------------------

@function_tool
def get_cinema_program(cinema_id: str, cinema_name: str, date_iso: str | None = None) -> str:
    """
    Fetch the full movie program for a specific Berlin cinema.

    Args:
        cinema_id:   The Kinoheld cinema ID (obtain from list_berlin_cinemas).
        cinema_name: The human-readable name of the cinema (for logging/display).
        date_iso:    Date in YYYY-MM-DD format. Defaults to today if omitted.

    Returns a JSON object with:
        cinema_id    – the cinema's ID
        cinema_name  – the cinema's name
        date         – the date of the program
        shows        – array of show objects, each with:
            id               – show ID
            beginning        – ISO-8601 datetime of the screening
            deeplink         – direct ticket URL (may be null)
            audio_language   – audio track language (may be null)
            subtitle_language – subtitle language (may be null)
            movie:
                id                – movie ID
                title             – movie title
                duration_minutes  – runtime in minutes (may be null)
                short_description – one-line synopsis (may be null)
    """
    for_date = date.fromisoformat(date_iso) if date_iso else None
    cinema = Cinema(id=cinema_id, name=cinema_name, url_slug="")
    program = fetch_program(cinema, for_date=for_date)
    return json.dumps(program.model_dump(), ensure_ascii=False, indent=2)

