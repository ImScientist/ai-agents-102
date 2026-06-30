"""
main.py
Entry point for the Berlin Jobs Agent.

Usage:
    # Search default categories (ML, data science, AI engineering)
    uv run python main.py

    # Search specific categories
    uv run python main.py --categories "machine learning" "MLOps" "LLM engineer"
"""

import argparse
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()  # must happen before importing agent (which imports openai)

from logging_config import setup_logging
from agent import run, JobSearchReport

logger = logging.getLogger(__name__)


def _format_report(report: JobSearchReport) -> str:
    lines = [
        f"💼  Berlin Jobs Report",
        f"    Location : {report.location}",
        f"    Searched : {', '.join(report.categories_searched)}",
        f"    Found    : {report.total_jobs_found} unique listings",
        "",
        f"    {report.summary}",
        "",
        f"    {'TITLE':<45} {'COMPANY':<30} {'POSTED':<15} {'TYPE':<15} SALARY",
        "    " + "-" * 115,
    ]
    for job in report.jobs:
        title = job.title[:43] + "…" if len(job.title) > 44 else job.title
        company = job.company_name[:28] + "…" if len(job.company_name) > 29 else job.company_name
        posted = job.posted_at or "—"
        schedule = job.schedule_type or "—"
        salary = job.salary or "—"
        wfh = " 🏠" if job.work_from_home else ""
        lines.append(f"    {title:<45} {company:<30} {posted:<15} {schedule:<15} {salary}{wfh}")
        if job.apply_link:
            lines.append(f"    {'':>10}↳ Apply: {job.apply_link}")
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find ML / data science / AI engineering jobs in Berlin."
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        metavar="CATEGORY",
        default=None,
        help=(
            'One or more job categories to search for, e.g. '
            '"machine learning" "data scientist" "AI engineer". '
            'Defaults to ML, data science and AI engineering.'
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    setup_logging()
    args = _parse_args()

    report: JobSearchReport = asyncio.run(run(args.categories))
    logger.info("\n%s", _format_report(report))

