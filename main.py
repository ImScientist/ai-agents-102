"""
main.py
Entry point for the Gmail AI Agent.

Pipeline:
  1. Fetch the last 20 emails from Gmail
  2. Classify each email with GPT-4o
  3. Route to the appropriate Slack action (or skip)
"""

from dotenv import load_dotenv

load_dotenv()  # load .env before importing modules that read env vars

from gmail_client import fetch_recent_emails
from categorizer import categorize_email
from slack_notifier import post_urgent_alert, post_github_message

N_EMAILS = 20

CATEGORY_LABELS = {
    "urgent":           "🚨 Urgent",
    "github":           "🐙 GitHub",
    "newsletter_spam":  "🗑️  Newsletter / Spam",
}


def process_email(email: dict) -> None:
    print(f"\n📧  [{email['date']}] {email['subject'][:80]}")
    print(f"     From: {email['sender']}")

    classification = categorize_email(email)
    category = classification["category"]
    label = CATEGORY_LABELS.get(category, category)
    print(f"     Category: {label}", end="")

    if category == "github":
        sub = classification.get("github_subcategory", "—")
        repo = classification.get("repo", "—")
        print(f"  |  Subcategory: {sub}  |  Repo: {repo}")
        post_github_message(email, classification)

    elif category == "urgent":
        print()
        post_urgent_alert(email, classification)

    elif category == "newsletter_spam":
        print("  →  Skipping.")

    else:
        print(f"  →  Unknown category '{category}', skipping.")


def main() -> None:
    print(f"🤖  Gmail Agent starting — fetching last {N_EMAILS} emails …\n")
    emails = fetch_recent_emails(N_EMAILS)
    print(f"✉️   Retrieved {len(emails)} emails. Classifying …")

    for email in emails:
        process_email(email)

    print("\n✅  Done.")


if __name__ == "__main__":
    main()

