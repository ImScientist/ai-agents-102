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

## Project structure

```
.
├── main.py              # Entry point — orchestrates the full pipeline
├── gmail_client.py      # Fetches and parses emails via Gmail API
├── categorizer.py       # Uses GPT-4o to categorize each email
├── slack_notifier.py    # Sends formatted messages to Slack
├── pyproject.toml       # Project metadata & dependencies (uv)
├── uv.lock              # Locked dependency tree (commit this)
├── credentials.json     # Gmail OAuth client secrets (you provide this)
├── token.json           # Gmail OAuth token (auto-generated on first run)
├── .env                 # Your secrets (never commit this)
└── .env.example         # Template for .env
```

