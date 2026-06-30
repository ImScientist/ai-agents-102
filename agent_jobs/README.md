# agent_jobs — Berlin Tech Jobs Agent

An AI agent that searches for **machine learning, data science, and AI engineering** job openings in Berlin using the [Adzuna Jobs API](https://developer.adzuna.com) as its primary source and [SerpApi Google Jobs](https://serpapi.com/google-jobs-api) as a fallback, powered by OpenAI's GPT-4o.

---

## How it works

```
User query
   │
   ▼
jobs_agent (GPT-4o)
   │
   ├─► search_jobs_adzuna("machine learning engineer")   ← primary (real Berlin listings)
   ├─► search_jobs_adzuna("data scientist")
   ├─► search_jobs_adzuna("AI engineer")
   ├─► search_jobs_adzuna(..., page=2)                   ← optional second page
   └─► search_jobs_serpapi(...)                          ← fallback if Adzuna returns nothing
         │
         ▼
   AdzunaJobSearchResult / JobSearchResult
         │
         ▼
   JobSearchReport  ──►  formatted table in stdout
```

The LLM drives the search loop — it decides how many queries to run,
deduplicates results across searches, and writes a plain-English summary.

### Why Adzuna as the primary source?

| | Adzuna | SerpApi (Google Jobs) |
|---|---|---|
| Berlin listings | ✅ Real German index | ⚠️ US-based index by default (free tier) |
| Salary data | ✅ Numeric EUR min/max | ⚠️ Text only, rarely present |
| Pagination | Page numbers (1, 2, 3…) | Offset (0, 10, 20…) |
| Free tier | 250 calls/month | 100 calls/month |
| Auth | `app_id` + `app_key` | Single `api_key` |

---

## Setup

### 1. Install dependencies

The project uses `uv` and dependencies are declared in `pyproject.toml` at the repo root.

```bash
uv sync
```

### 2. Configure API keys

Export the following environment variables (or add them to a `.env` file in the repo root):

```dotenv
OPENAI_API_KEY=sk-...

# Adzuna — primary job source
# Sign up at https://developer.adzuna.com to get both values.
ADZUNA_APP_ID=your_app_id_here        # short alphanumeric ID (~8 chars)
ADZUNA_API_KEY=your_app_key_here      # 32-character hex key

# SerpApi — fallback job source (optional)
# 100 free searches/month at https://serpapi.com
SERPAPI_KEY=your_serpapi_key_here
```

> **Note:** The agent works without `SERPAPI_KEY` as long as Adzuna returns results.
> `SERPAPI_KEY` is only needed if you want the fallback tool to be available.

---

## Usage

```bash
# Search default categories: ML, data science, AI engineering
uv run python agent_jobs/main.py

# Search specific categories
uv run python agent_jobs/main.py --categories "machine learning" "MLOps" "LLM engineer"
```

### Example output

```
💼  Berlin Jobs Report
    Location : Berlin, Germany
    Searched : machine learning engineer, data scientist, AI engineer, MLOps engineer
    Found    : 34 unique listings

    34 job openings found across 4 searches. Top hiring companies include SumUp,
    Reply Deutschland SE, and Almedia. Salary data is available for roughly a third
    of listings, ranging from EUR 60,000 to EUR 210,000; some figures are Adzuna
    estimates (marked ~). Most roles require Python and cloud experience (AWS/GCP);
    several senior positions also ask for PyTorch or LLM fine-tuning experience.

    TITLE                                         COMPANY                        DATE         TYPE         SALARY (EUR)
    ------------------------------------------------------------------------------------------------------------------------
    Senior Machine Learning Engineer II          SumUp                          2026-06-24   full time    —
        ↳ https://www.adzuna.de/details/5775406717...
    Machine Learning Engineer                    Almedia                        2026-06-20   full time    80,000–210,000
        ↳ https://www.adzuna.de/details/5538325030...
    Data Scientist                               adsquare                       2026-06-18   full time    —
    ...
```

---

## File structure

| File                  | Purpose                                                                     |
|-----------------------|-----------------------------------------------------------------------------|
| `models.py`           | Pydantic models for both APIs: `AdzunaJobListing`, `AdzunaJobSearchResult`, `JobListing`, `JobSearchResult` |
| `adzuna_client.py`    | Raw HTTP client for the Adzuna Jobs API (`app_id` + `app_key` auth)         |
| `serpapi_client.py`   | Raw HTTP client for the SerpApi Google Jobs endpoint                        |
| `tools.py`            | `@function_tool` wrappers: `search_jobs_adzuna` (primary), `search_jobs_serpapi` (fallback) |
| `agent.py`            | Agent definition, `JobSearchReport` output schema, `run()` entry point      |
| `logging_config.py`   | Centralised logging setup                                                   |
| `main.py`             | CLI entry point with formatted report output                                |
| `test_serpapi.py`     | Smoke tests for the SerpApi client (run directly, not via pytest)           |
