"""
gmail_client.py
Fetches and parses the last N emails from Gmail using the Gmail API.
On the first run it will open a browser for OAuth consent and save token.json.
"""

import os
import base64
import email as email_lib
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Read-only access to Gmail is sufficient
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "client_secret.json"
TOKEN_FILE = "token.json"


def _get_service():
    """Authenticate and return a Gmail API service object."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _decode_body(payload: dict) -> str:
    """Recursively extract plain-text body from a message payload."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if mime_type == "text/plain" and body_data:
        return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

    # Multipart: recurse into parts
    for part in payload.get("parts", []):
        text = _decode_body(part)
        if text:
            return text

    return ""


def _parse_headers(headers: list[dict]) -> dict:
    """Return a dict of the headers we care about."""
    wanted = {"Subject", "From", "Date"}
    return {h["name"]: h["value"] for h in headers if h["name"] in wanted}


def fetch_recent_emails(n: int = 5) -> list[dict]:
    """
    Return the last `n` emails as a list of dicts with keys:
        id, subject, sender, date, snippet, body
    """
    service = _get_service()
    results = service.users().messages().list(userId="me", maxResults=n).execute()
    messages = results.get("messages", [])

    emails = []
    for msg_ref in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_ref["id"], format="full")
            .execute()
        )
        headers = _parse_headers(msg.get("payload", {}).get("headers", []))
        body = _decode_body(msg.get("payload", {}))

        emails.append(
            {
                "id": msg_ref["id"],
                "subject": headers.get("Subject", "(no subject)"),
                "sender": headers.get("From", "(unknown)"),
                "date": headers.get("Date", ""),
                "snippet": msg.get("snippet", ""),
                # Trim body to avoid huge prompts; 2 000 chars is plenty for classification
                "body": body[:2000].strip(),
            }
        )

    return emails
