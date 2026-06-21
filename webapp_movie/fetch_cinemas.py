"""
fetch_cinemas.py
Standalone script: fetches all Berlin cinemas from the Kinoheld GraphQL API,
enriches each cinema with the program for today and the following two days,
and writes the result to cinemas.json in the same directory.

Run locally:
    python webapp_movie/fetch_cinemas.py

Run by GitHub Actions to keep cinemas.json up-to-date.
"""

import json
import pathlib
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone

import requests

ENDPOINT = "https://next-live.kinoheld.de/graphql"
OUTPUT_FILE = pathlib.Path(__file__).parent / "cinemas.json"

CINEMAS_QUERY = (
    "query($citySlug: String!) {"
    "  city(urlSlug: $citySlug) {"
    "    cinemas {"
    "      data {"
    "        id name street urlSlug"
    "        postcode { postcode }"
    "        latitude longitude"
    "      }"
    "    }"
    "  }"
    "}"
)

SHOWS_QUERY = (
    "query($cinemaId: ID!, $dates: [Date!]!) {"
    "  shows(cinemaId: $cinemaId, dates: $dates) {"
    "    data {"
    "      beginning"
    "      movie { id title duration shortDescription }"
    "    }"
    "  }"
    "}"
)


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _post(query: str, variables: dict) -> dict:
    response = requests.post(
        ENDPOINT,
        json={"query": query, "variables": variables},
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if "errors" in payload:
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    return payload["data"]


# ---------------------------------------------------------------------------
# Fetch functions
# ---------------------------------------------------------------------------

def fetch_cinemas(city_slug: str = "berlin") -> list[dict]:
    data = _post(CINEMAS_QUERY, {"citySlug": city_slug})
    raw = data.get("city", {}).get("cinemas", {}).get("data", [])

    cinemas = []
    for c in raw:
        lat = c.get("latitude")
        lon = c.get("longitude")
        # Skip cinemas without coordinates — they can't be placed on the map
        if lat is None or lon is None:
            continue
        cinemas.append(
            {
                "id": c["id"],
                "name": c["name"],
                "street": c.get("street", ""),
                "postcode": (c.get("postcode") or {}).get("postcode", ""),
                "url_slug": c.get("urlSlug", ""),
                "latitude": lat,
                "longitude": lon,
                "program": {},  # filled in later: { "YYYY-MM-DD": [movies] }
            }
        )
    return cinemas


def fetch_shows_for_cinema(cinema_id: str, for_date: date) -> list[dict]:
    """
    Return a list of movies playing at *cinema_id* on *for_date*.
    Each entry: { id, title, duration_minutes, short_description, showtimes: [HH:MM, …] }
    Shows are grouped by movie and sorted by first showtime.
    """
    data = _post(SHOWS_QUERY, {"cinemaId": cinema_id, "dates": [for_date.isoformat()]})
    raw_shows = data.get("shows", {}).get("data", [])

    # Group showtimes by movie id
    movies: dict[str, dict] = {}
    showtimes_by_movie: dict[str, list[str]] = defaultdict(list)

    for s in raw_shows:
        raw_movie = s.get("movie") or {}
        movie_id = raw_movie.get("id", "")
        if not movie_id:
            continue

        if movie_id not in movies:
            movies[movie_id] = {
                "id": movie_id,
                "title": raw_movie.get("title", "Unknown"),
                "duration_minutes": raw_movie.get("duration"),
                "short_description": raw_movie.get("shortDescription"),
            }

        # Extract HH:MM from ISO-8601 beginning (e.g. "2026-06-20T19:30:00+02:00")
        beginning = s.get("beginning", "")
        try:
            time_str = datetime.fromisoformat(beginning).strftime("%H:%M")
        except (ValueError, TypeError):
            time_str = beginning
        showtimes_by_movie[movie_id].append(time_str)

    # Build final list sorted by first showtime
    result = []
    for movie_id, movie in movies.items():
        showtimes = sorted(set(showtimes_by_movie[movie_id]))
        result.append({**movie, "showtimes": showtimes})

    result.sort(key=lambda m: m["showtimes"][0] if m["showtimes"] else "")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    today = date.today()
    dates = [today + timedelta(days=i) for i in range(3)]
    date_strs = [d.isoformat() for d in dates]
    print(f"Fetching Berlin cinemas from Kinoheld (dates: {', '.join(date_strs)})…")

    try:
        cinemas = fetch_cinemas()
    except Exception as exc:
        print(f"ERROR fetching cinemas: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(cinemas)} cinemas. Fetching programs in parallel…")

    # Build a lookup: cinema_id → cinema dict
    cinema_by_id = {c["id"]: c for c in cinemas}

    # Submit one task per (cinema, date) combination
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_key = {
            executor.submit(fetch_shows_for_cinema, c["id"], d): (c["id"], d.isoformat())
            for c in cinemas
            for d in dates
        }
        for future in as_completed(future_to_key):
            cinema_id, date_str = future_to_key[future]
            cinema = cinema_by_id[cinema_id]
            try:
                movies = future.result()
                cinema["program"][date_str] = movies
                print(f"  ✓ {cinema['name']} [{date_str}]: {len(movies)} movies")
            except Exception as exc:
                print(f"  ✗ {cinema['name']} [{date_str}]: {exc}", file=sys.stderr)
                cinema["program"][date_str] = []

    # Keep only cinemas that have at least one show across all days
    cinemas = [c for c in cinemas if any(c["program"].values())]

    output = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dates": date_strs,
        "cinemas": cinemas,
    }

    OUTPUT_FILE.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nSaved {len(cinemas)} cinemas → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
