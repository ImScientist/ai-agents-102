"""
tools.py
All tools available to the email agent.
The LLM decides which tools to call and in what order — not our code.
"""

import json
import requests
from agents import function_tool

from gmail_client import fetch_recent_emails as _fetch_emails
from slack_notifier import post_urgent_alert as _post_urgent
from slack_notifier import post_github_message as _post_github
from models import EmailRef, UrgentClassification, GithubClassification


# ---------------------------------------------------------------------------
# Email fetching
# ---------------------------------------------------------------------------

@function_tool
def fetch_recent_emails(count: int = 20) -> str:
    """
    Fetch the most recent emails from the user's Gmail inbox.

    Args:
        count: How many emails to retrieve (default 20).

    Returns a JSON array of email objects, each with:
        id, subject, sender, date, snippet, body
    """
    emails = _fetch_emails(count)
    return json.dumps([e.model_dump() for e in emails], ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# GitHub enrichment
# ---------------------------------------------------------------------------

@function_tool
def get_github_repo_info(repo: str) -> str:
    """
    Fetch live public metadata for a GitHub repository.
    Use this before posting a GitHub notification to enrich the message.

    Args:
        repo: Repository in "owner/name" format, e.g. "acme-corp/backend".

    Returns a JSON object with description, language, stars, open issues, etc.
    """
    try:
        print(f"  Get info about {repo} Github repository")

        resp = requests.get(
            f"https://api.github.com/repos/{repo}",
            timeout=5,
            headers={"Accept": "application/vnd.github+json"},
        )
        if resp.status_code == 200:
            data = resp.json()
            return json.dumps(
                {
                    "full_name": data.get("full_name"),
                    "description": data.get("description"),
                    "language": data.get("language"),
                    "stars": data.get("stargazers_count"),
                    "forks": data.get("forks_count"),
                    "open_issues": data.get("open_issues_count"),
                    "default_branch": data.get("default_branch"),
                    "html_url": data.get("html_url"),
                },
                indent=2,
            )
        return json.dumps({"error": f"GitHub API returned HTTP {resp.status_code}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Slack actions
# ---------------------------------------------------------------------------

@function_tool
def post_urgent_alert(sender: str, subject: str, date: str, summary: str) -> str:
    """
    Post an immediate alert to the #alerts Slack channel.
    Use this for emails that require urgent human attention (incidents,
    security issues, time-sensitive requests, etc.).

    Args:
        sender:  The "From" field of the email.
        subject: The email subject line.
        date:    The email date string.
        summary: A 1-2 sentence description of why this is urgent.
    """
    _post_urgent(
        email=EmailRef(sender=sender, subject=subject, date=date),
        classification=UrgentClassification(summary=summary),
    )
    return f"✅ Urgent alert posted for: {subject!r}"


@function_tool
def post_github_message(
        sender: str,
        subject: str,
        date: str,
        repo: str,
        subcategory: str,
        summary: str,
) -> str:
    """
    Post a GitHub-related notification to the #github Slack channel.

    Args:
        sender:      The "From" field of the email.
        subject:     The email subject line.
        date:        The email date string.
        repo:        Repository in "owner/name" format (use "unknown" if not determinable).
        subcategory: One of: "new_pull_request", "comment", "ci_message".
        summary:     A 1-2 sentence description of the event, enriched with repo info if available.
    """
    _post_github(
        email=EmailRef(sender=sender, subject=subject, date=date),
        classification=GithubClassification(
            subcategory=subcategory, repo=repo, summary=summary),
    )
    return f"✅ GitHub message posted for: {subject!r} [{subcategory}]"


@function_tool
def skip_email(subject: str, reason: str) -> str:
    """
    Skip an email without taking any action.
    Use this for newsletters, marketing emails, spam, and other non-actionable messages.

    Args:
        subject: The email subject line.
        reason:  Brief reason for skipping (e.g. "newsletter", "spam", "automated promo").
    """
    print(f"  ⏭️  Skipping: {subject!r} — {reason}")
    return f"Skipped: {subject!r}"
