"""
main.py
Entry point for the Gmail AI Agent.
"""

import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()  # must happen before importing agent (which imports openai)

from logging_config import setup_logging
from agent import run, InboxReport

logger = logging.getLogger(__name__)


def _format_report(report: InboxReport) -> str:
    lines = [
        "📋  Inbox report:",
        f"    Processed : {report.total_processed}",
        f"    Urgent    : {report.urgent_count}",
        f"    GitHub    : {report.github_count}",
        f"    Skipped   : {report.skipped_count}",
        "    Actions:",
    ]
    for action in report.actions:
        sub = f" [{action.github_subcategory}]" if action.github_subcategory else ""
        lines.append(
            f"      • [{action.category}{sub}] {action.subject!r} — {action.action_taken}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    setup_logging()
    report: InboxReport = asyncio.run(run())
    logger.info("\n%s", _format_report(report))
