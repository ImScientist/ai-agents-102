"""
kinoheld_client.py
Low-level HTTP client for the Kinoheld GraphQL API.

Endpoint: https://next-live.kinoheld.de/graphql
All queries are unauthenticated POST requests with a JSON body.
"""

import logging
from datetime import date

import requests

from models import Cinema, CinemaProgram, Movie, Show

logger = logging.getLogger(__name__)

_ENDPOINT = "https://next-live.kinoheld.de/graphql"
_TIMEOUT = 10  # seconds


def _post(query: str, variables: dict) -> dict:
    """Execute a GraphQL query and return the parsed JSON response."""
    response = requests.post(
        _ENDPOINT,
        json={"query": query, "variables": variables},
        headers={"Content-Type": "application/json"},
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    if "errors" in payload:
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    return payload["data"]


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

_GET_CINEMAS_QUERY = """
query($citySlug: String!) {
  city(urlSlug: $citySlug) {
    id
    name
    cinemas {
      data {
        id
        name
        urlSlug
      }
    }
  }
}
"""

_GET_SHOWS_QUERY = """
query($cinemaId: ID!, $dates: [Date!]!) {
  shows(cinemaId: $cinemaId, dates: $dates) {
    data {
      id
      beginning
      deeplink
      audioLanguage { name }
      subtitleLanguage { name }
      movie {
        id
        title
        duration
        shortDescription
      }
    }
  }
}
"""


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def fetch_berlin_cinemas() -> list[Cinema]:
    """Return all cinemas listed under Berlin on Kinoheld."""
    logger.info("Fetching cinemas in Berlin…")
    data = _post(_GET_CINEMAS_QUERY, {"citySlug": "berlin"})
    raw = data.get("city", {}).get("cinemas", {}).get("data", [])
    cinemas = [
        Cinema(id=c["id"], name=c["name"], url_slug=c["urlSlug"])
        for c in raw
    ]
    logger.info("Found %d cinemas in Berlin", len(cinemas))
    return cinemas


def fetch_program(cinema: Cinema, for_date: date | None = None) -> CinemaProgram:
    """
    Fetch the full program for *cinema* on *for_date* (defaults to today).

    Returns a CinemaProgram with all shows grouped under that cinema.
    """
    if for_date is None:
        for_date = date.today()

    date_str = for_date.isoformat()
    logger.info("Fetching program for '%s' on %s…", cinema.name, date_str)

    data = _post(_GET_SHOWS_QUERY, {"cinemaId": cinema.id, "dates": [date_str]})
    raw_shows = data.get("shows", {}).get("data", [])

    shows: list[Show] = []
    for s in raw_shows:
        raw_movie = s.get("movie") or {}
        shows.append(
            Show(
                id=s["id"],
                beginning=s["beginning"],
                deeplink=s.get("deeplink"),
                audio_language=(s.get("audioLanguage") or {}).get("name"),
                subtitle_language=(s.get("subtitleLanguage") or {}).get("name"),
                movie=Movie(
                    id=raw_movie.get("id", ""),
                    title=raw_movie.get("title", "Unknown"),
                    duration_minutes=raw_movie.get("duration"),
                    short_description=raw_movie.get("shortDescription"),
                ),
            )
        )

    logger.info("Found %d shows for '%s'", len(shows), cinema.name)
    return CinemaProgram(
        cinema_id=cinema.id,
        cinema_name=cinema.name,
        date=date_str,
        shows=shows,
    )

