"""
models.py
Shared domain models used across the project.
"""

from typing import Literal
from pydantic import BaseModel


class Email(BaseModel):
    """A parsed email from the Gmail inbox."""
    id: str
    subject: str
    sender: str
    date: str
    snippet: str
    body: str


class EmailRef(BaseModel):
    """Minimal email reference passed to Slack notifiers.
    Contains only what is needed to compose a notification message.
    """
    subject: str
    sender: str
    date: str


class UrgentClassification(BaseModel):
    """Classification data for an urgent email."""
    summary: str


class GithubClassification(BaseModel):
    """Classification data for a GitHub-related email."""
    subcategory: Literal["new_pull_request", "comment", "ci_message"]
    repo: str
    summary: str


