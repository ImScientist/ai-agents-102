"""
main.py
Entry point for the Berlin Movie Agent.

Usage:
    # Today's program at a cinema (default)
    uv run python main.py "CineStar"

    # Program for a specific date
    uv run python main.py "Babylon" --date 2026-06-20
"""

import argparse
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()  # must happen before importing agent (which imports openai)

from logging_config import setup_logging
from agent import run, CinemaProgramReport

logger = logging.getLogger(__name__)


def _format_report(report: CinemaProgramReport) -> str:
    lines = [
        f"🎬  {report.cinema_name}  —  {report.date}",
        f"    {report.summary}",
        "",
        f"    {'TIME':<8} {'TITLE':<45} {'MIN':>4}  LANG",
        "    " + "-" * 70,
    ]
    for show in report.shows:
        duration = str(show.duration_minutes) if show.duration_minutes else "  —"
        lang = show.language_note or ""
        title = show.title[:43] + "…" if len(show.title) > 44 else show.title
        lines.append(f"    {show.time:<8} {title:<45} {duration:>4}  {lang}")
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Look up the movie program for a Berlin cinema."
    )
    parser.add_argument(
        "cinema",
        help='Cinema name or partial name, e.g. "CineStar" or "Babylon".',
    )
    parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        default=None,
        help="Date to look up (defaults to today).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    setup_logging()
    args = _parse_args()

    report: CinemaProgramReport = asyncio.run(run(args.cinema, args.date))
    logger.info("\n%s", _format_report(report))
