"""
agent.py
Defines the email-processing agent and its run function.

Architecture
------------
The agent is given five tools and a goal. It decides:
  - which tool to call for each email
  - whether to enrich a GitHub notification with live repo data first
  - whether an email is urgent AND GitHub-related (post to both channels)
  - what to skip

This is a genuine reasoning loop — the LLM drives the flow,
not hard-coded if/elif branches.
"""

import asyncio
import os
from typing import Literal, Optional
from pydantic import BaseModel
from openai import AsyncOpenAI
from agents import Agent, Runner, RunHooks, RunContextWrapper, set_default_openai_client, set_default_openai_api
from agents.tool import FunctionTool

from tools import (
    fetch_recent_emails,
    get_github_repo_info,
    post_urgent_alert,
    post_github_message,
    skip_email,
)

# ---------------------------------------------------------------------------
# LLM client — uses GitHub Models if GITHUB_TOKEN is set, otherwise OpenAI
# ---------------------------------------------------------------------------

def _configure_client() -> str:
    """
    Point the Agents SDK at GitHub Models when a GITHUB_TOKEN is present,
    or fall back to the standard OpenAI API (requires OPENAI_API_KEY).
    Returns the model name to use.
    """
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        client = AsyncOpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=github_token,
        )
        set_default_openai_client(client)
        # GitHub Models exposes the Chat Completions API, not the newer
        # Responses API that the Agents SDK uses by default.
        set_default_openai_api("chat_completions")
        return "gpt-4o"  # available on GitHub Models
    return "gpt-4o"  # default OpenAI model


_MODEL = _configure_client()


# ---------------------------------------------------------------------------
# Structured output schema
# ---------------------------------------------------------------------------

class EmailAction(BaseModel):
    subject: str
    sender: str
    category: Literal["urgent", "github", "newsletter_spam"]
    github_subcategory: Optional[Literal["new_pull_request", "comment", "ci_message"]] = None
    action_taken: str  # human-readable description of what the agent did


class InboxReport(BaseModel):
    total_processed: int
    urgent_count: int
    github_count: int
    skipped_count: int
    actions: list[EmailAction]


# ---------------------------------------------------------------------------
# Agent instructions
# ---------------------------------------------------------------------------

INSTRUCTIONS = """
You are an email-processing agent. Your goal is to triage the user's inbox
and take the right action for every email.

## Step 1 — Fetch emails
Call `fetch_recent_emails` to retrieve the last 5 emails.

## Step 2 — Process each email
For every email decide which category it belongs to and call the matching tool:

### URGENT
Emails that need immediate human attention:
  - Production incidents or outages
  - Security alerts
  - Time-sensitive requests from real people
  - Any email that could cause harm if ignored for a few hours
→ Call `post_urgent_alert` with a clear, actionable summary.

### GITHUB
Emails that originate from GitHub or a GitHub-integrated CI/CD service
(CircleCI, GitHub Actions, Dependabot, Renovate, CodeCov, etc.):
→ First call `get_github_repo_info` to fetch live repository metadata
  (stars, description, language, open issues).
→ Then call `post_github_message` with:
    - subcategory: "new_pull_request" | "comment" | "ci_message"
    - summary enriched with the live repo info you just fetched

### NEWSLETTER / SPAM
Marketing emails, newsletters, automated promotions, cold outreach, spam:
→ Call `skip_email` with a short reason.

## Important rules
- Process **every** email — do not silently drop any.
- An email can belong to more than one category (e.g. urgent *and* GitHub-related).
  In that case call both `post_urgent_alert` and `post_github_message`.
- Keep summaries concise: 1-2 sentences.
- When you have finished all emails, produce the final structured InboxReport.
"""



# ---------------------------------------------------------------------------
# Optional: logging hooks so the terminal shows the agent's reasoning
# ---------------------------------------------------------------------------

class LoggingHooks(RunHooks):
    async def on_tool_start(
        self,
        context: RunContextWrapper,
        agent: Agent,
        tool: FunctionTool,
    ) -> None:
        print(f"\n🔧  Tool call → {tool.name}")

    async def on_tool_end(
        self,
        context: RunContextWrapper,
        agent: Agent,
        tool: FunctionTool,
        result: object,
    ) -> None:
        first_line = str(result).splitlines()[0] if result else ""
        print(f"    ↳ {first_line}")


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

email_agent = Agent(
    name="Email Processing Agent",
    model=_MODEL,
    instructions=INSTRUCTIONS,
    output_type=InboxReport,
    tools=[
        fetch_recent_emails,
        get_github_repo_info,
        post_urgent_alert,
        post_github_message,
        skip_email,
    ],
)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def run() -> InboxReport:
    """Run the agent and return a structured InboxReport."""
    print("🤖  Email agent starting…\n")
    result = await Runner.run(
        email_agent,
        input="Please process my inbox now.",
        hooks=LoggingHooks(),
        max_turns=60,
    )
    return result.final_output


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
