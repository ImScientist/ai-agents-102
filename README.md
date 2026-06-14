# Gmail AI Agent

An AI-powered agent that reads your last 20 Gmail emails, categorizes them using GPT-4o, and routes actions to Slack.

## Categories & Actions

| Category | Action |
|---|---|
| **Urgent** | Posts an immediate alert to `#alerts` Slack channel |
| **GitHub related** | Posts a message to `#github` with repo info + subcategory (New PR / Comment / CI message) |
| **Newsletter / Spam** | Skipped entirely |

---

## Setup

### 1. Gmail API credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Gmail API**: _APIs & Services → Enable APIs → search "Gmail API"_
4. Go to _APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID_
5. Choose **Desktop app**, download the JSON file, and save it as `credentials.json` in the project root
6. On the first run, a browser window will open asking you to authorize access — after that, a `token.json` file is created and reused automatically

### 2. Slack Bot token

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App → From scratch**
2. Under _OAuth & Permissions_, add these **Bot Token Scopes**:
   - `chat:write`
   - `channels:read`
3. Click **Install App to Workspace** and copy the **Bot OAuth Token** (`xoxb-...`)
4. Invite the bot to `#alerts` and `#github` channels: `/invite @your-bot-name`

### 3. OpenAI API key

Get your key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

### 4. Environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

### 5 — Install dependencies & run the agent

```bash
# Sync the virtual environment (creates .venv and installs all packages)
uv sync

# Run the agent
uv run main.py
```

---

## Architecture

This is a genuine **agentic** system built on the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python).
The LLM drives the entire flow by calling tools — there is no hard-coded routing logic.

```
┌─────────────────────────────────────────────────────────┐
│                    Email Agent (GPT-4o)                 │
│                                                         │
│  1. Calls fetch_recent_emails()                         │
│  2. For each email, decides autonomously:               │
│     - Is this urgent?     → post_urgent_alert()         │
│     - Is this GitHub?     → get_github_repo_info()      │
│                             post_github_message()       │
│     - Is this spam?       → skip_email()                │
│     - Both urgent+GitHub? → calls both Slack tools      │
└─────────────────────────────────────────────────────────┘
```

The agent can also **enrich** GitHub notifications with live repository metadata
(stars, language, description, open issues) by calling the GitHub REST API before
composing the Slack message — something a static pipeline cannot do.

## Project structure

```
.
├── main.py              # Async entry point
├── agent.py             # Agent definition, instructions, logging hooks
├── tools.py             # All @function_tool definitions (the agent's "hands")
├── gmail_client.py      # Gmail API utility — fetches and parses emails
├── slack_notifier.py    # Slack SDK utility — formats and sends messages
├── pyproject.toml       # Project metadata & dependencies (uv)
├── uv.lock              # Locked dependency tree
├── client_secret.json   # Gmail OAuth client secrets (you provide this)
├── token.json           # Gmail OAuth token (auto-generated on first run)
├── .env                 # Your secrets (never commit this)
└── .env.example         # Template for .env
```
