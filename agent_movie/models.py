"""
models.py
Shared domain models for the Movie Agent.
"""

from pydantic import BaseModel


class Cinema(BaseModel):
    """A cinema returned by the Kinoheld API."""
    id: str
    name: str
    url_slug: str


class Movie(BaseModel):
    """A movie playing at a cinema."""
    id: str
    title: str
    duration_minutes: int | None = None
    short_description: str | None = None


class Show(BaseModel):
    """A single screening (show) of a movie."""
    id: str
    beginning: str          # ISO-8601 datetime, e.g. "2026-06-18T19:30:00+02:00"
    deeplink: str | None    # Direct ticket-booking URL
    audio_language: str | None = None
    subtitle_language: str | None = None
    movie: Movie


class CinemaProgram(BaseModel):
    """Full program for one cinema on a given date."""
    cinema_id: str
    cinema_name: str
    date: str
    shows: list[Show]

