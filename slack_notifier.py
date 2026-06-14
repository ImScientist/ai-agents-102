"""
slack_notifier.py
Sends formatted messages to Slack channels.
"""

import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_ALERTS_CHANNEL = os.environ.get("SLACK_ALERTS_CHANNEL", "#alerts")
SLACK_GITHUB_CHANNEL = os.environ.get("SLACK_GITHUB_CHANNEL", "#github")

_client: WebClient | None = None


def _get_client() -> WebClient:
    global _client
    if _client is None:
        token = SLACK_BOT_TOKEN
        if not token:
            raise EnvironmentError("SLACK_BOT_TOKEN is not set in the environment.")
        _client = WebClient(token=token)
    return _client


def _post(channel: str, text: str, blocks: list | None = None) -> None:
    try:
        kwargs = {"channel": channel, "text": text}
        if blocks:
            kwargs["blocks"] = blocks
        _get_client().chat_postMessage(**kwargs)
        print(f"  ✅  Posted to {channel}")
    except SlackApiError as e:
        print(f"  ❌  Slack error for {channel}: {e.response['error']}")


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def post_urgent_alert(email: dict, classification: dict) -> None:
    """Post an urgent alert to #alerts."""

    channel = SLACK_ALERTS_CHANNEL
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🚨 Urgent Email Alert", "emoji": True},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*From:*\n{email['sender']}"},
                {"type": "mrkdwn", "text": f"*Date:*\n{email['date']}"},
            ],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Subject:* {email['subject']}"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Summary:*\n{classification['summary']}"},
        },
        {"type": "divider"},
    ]
    fallback = f"🚨 Urgent email from {email['sender']}: {email['subject']}"
    _post(channel, fallback, blocks)


_SUBCATEGORY_LABELS = {
    "new_pull_request": "🔀 New Pull Request",
    "comment": "💬 Comment",
    "ci_message": "⚙️ CI / Automation",
}


def post_github_message(email: dict, classification: dict) -> None:
    """Post a GitHub-related message to #github."""

    channel = SLACK_GITHUB_CHANNEL
    subcategory = classification.get("github_subcategory") or "unknown"
    label = _SUBCATEGORY_LABELS.get(subcategory, f"📧 {subcategory}")
    repo = classification.get("repo") or "unknown repository"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"GitHub — {label}", "emoji": True},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Repository:*\n`{repo}`"},
                {"type": "mrkdwn", "text": f"*Type:*\n{label}"},
            ],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Subject:* {email['subject']}"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Summary:*\n{classification['summary']}"},
        },
        {"type": "divider"},
    ]
    fallback = f"GitHub [{label}] {repo} — {email['subject']}"
    _post(channel, fallback, blocks)
