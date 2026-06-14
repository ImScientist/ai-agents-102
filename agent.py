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
from agents import Agent, Runner, RunHooks, RunContextWrapper, RunItem

from tools import (
    fetch_recent_emails,
    get_github_repo_info,
    post_urgent_alert,
    post_github_message,
    skip_email,
)

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
- When you have finished all emails, output a brief plain-text summary of what you did.
"""


# ---------------------------------------------------------------------------
# Optional: logging hooks so the terminal shows the agent's reasoning
# ---------------------------------------------------------------------------

class LoggingHooks(RunHooks):
    async def on_tool_start(
            self,
            context: RunContextWrapper,
            tool_name: str,
            **kwargs,
    ) -> None:
        print(f"\n🔧  Tool call → {tool_name}")

    async def on_tool_end(
            self,
            context: RunContextWrapper,
            tool_name: str,
            output: str,
            **kwargs,
    ) -> None:
        # Only print first line of output to keep console readable
        first_line = output.splitlines()[0] if output else ""
        print(f"    ↳ {first_line}")


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

email_agent = Agent(
    name="Email Processing Agent",
    model="gpt-4o",
    instructions=INSTRUCTIONS,
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

async def run() -> str:
    """Run the agent and return its final summary."""
    print("🤖  Email agent starting…\n")
    result = await Runner.run(
        email_agent,
        input="Please process my inbox now.",
        # hooks=LoggingHooks(),
        max_turns=60,  # up to 60 LLM turns to handle 20 emails with enrichment
    )
    return result.final_output


if __name__ == "__main__":
    summary = asyncio.run(run())
    print(f"\n📋  Agent summary:\n{summary}")
