"""
categorizer.py
Uses GPT-4o to classify each email and extract a short summary.

Returns a structured result:
{
    "category": "urgent" | "github" | "newsletter_spam",
    "github_subcategory": "new_pull_request" | "comment" | "ci_message" | None,
    "summary": "<one or two sentence summary>",
    "repo": "<owner/repo or None>",   # best effort extraction for GitHub emails
}
"""

import json
from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from environment

SYSTEM_PROMPT = """
You are an email classification assistant. Given an email (subject, sender, body snippet),
you must classify it into exactly one top-level category and return a JSON object.

Top-level categories:
- "urgent"          – The email requires immediate attention (production incident, security alert,
                      time-sensitive request from a human, etc.)
- "github"          – The email originates from GitHub or a GitHub-integrated CI service
                      (CircleCI, GitHub Actions, Dependabot, etc.)
- "newsletter_spam" – Marketing, newsletters, automated promotional emails, or spam

For "github" emails, also fill in "github_subcategory" with one of:
- "new_pull_request"
- "comment"
- "ci_message"        (CircleCI, GitHub Actions workflow runs, Dependabot, etc.)

For "github" emails, extract the repository name as "repo" (format: "owner/repo").
If you cannot determine the repo, use null.

Always include a "summary" field: 1–2 concise sentences describing the email content.

Return ONLY valid JSON, no prose. Example:
{
  "category": "github",
  "github_subcategory": "new_pull_request",
  "repo": "acme-corp/backend",
  "summary": "Alice opened PR #42 'Add rate limiting middleware' targeting the main branch."
}
""".strip()


def categorize_email(email: dict) -> dict:
    """
    Classify a single email dict (keys: subject, sender, date, snippet, body).
    Returns a classification dict.
    """
    user_content = (
        f"From: {email['sender']}\n"
        f"Date: {email['date']}\n"
        f"Subject: {email['subject']}\n\n"
        f"{email['body'] or email['snippet']}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )

    raw = response.choices[0].message.content
    result = json.loads(raw)

    # Normalise to expected keys with safe defaults
    return {
        "category": result.get("category", "newsletter_spam"),
        "github_subcategory": result.get("github_subcategory"),
        "repo": result.get("repo"),
        "summary": result.get("summary", ""),
    }
