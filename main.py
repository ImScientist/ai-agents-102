"""
main.py
Entry point for the Gmail AI Agent.
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()  # must happen before importing agent (which imports openai)

from agent import run, InboxReport

if __name__ == "__main__":
    report: InboxReport = asyncio.run(run())
    print(f"\n📋  Inbox report:")
    print(f"    Processed : {report.total_processed}")
    print(f"    Urgent    : {report.urgent_count}")
    print(f"    GitHub    : {report.github_count}")
    print(f"    Skipped   : {report.skipped_count}")
    print(f"\n    Actions:")
    for action in report.actions:
        sub = f" [{action.github_subcategory}]" if action.github_subcategory else ""
        print(f"      • [{action.category}{sub}] {action.subject!r} — {action.action_taken}")
