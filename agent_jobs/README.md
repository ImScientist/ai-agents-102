# agent_jobs — Berlin Tech Jobs Agent

An AI agent that searches for **machine learning, data science, and AI engineering** job openings in Berlin using the [SerpApi Google Jobs](https://serpapi.com/google-jobs-api) endpoint and OpenAI's GPT-4o.

---

## How it works

```
User query
   │
   ▼
jobs_agent (GPT-4o)
   │
   ├─► search_jobs("machine learning engineer Berlin")
   ├─► search_jobs("data scientist Berlin")
   ├─► search_jobs("AI engineer Berlin")
   └─► (optional extra pages via start=10)
         │
         ▼
   SerpApi Google Jobs (raw HTTP GET)
         │
         ▼
   JobSearchReport  ──►  formatted table in stdout
```

The LLM drives the search loop — it decides how many queries to run,
deduplicates results, and writes a plain-English summary.

---

## Setup

### 1. Install dependencies

The project uses `uv` and the dependencies are declared in `pyproject.toml` at the repo root.

```bash
uv sync
```

### 2. Configure API keys

Create a `.env` file in the **repo root** (next to `pyproject.toml`):

```dotenv
OPENAI_API_KEY=sk-...
SERPAPI_KEY=your_serpapi_key_here
```

Get a free SerpApi key (100 searches/month) at <https://serpapi.com>.

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
    Searched : machine learning engineer Berlin, data scientist Berlin, AI engineer Berlin
    Found    : 27 unique listings

    27 job openings found across 3 searches. Top hiring companies include Zalando,
    HelloFresh, and various Series B startups. Salaries range from €55k to €110k/year.
    Most roles require Python and PyTorch/TensorFlow; several offer remote-friendly
    arrangements.

    TITLE                                         COMPANY                        POSTED          TYPE            SALARY
    -----------------------------------------------------------------------------------------------------------------------
    Senior Machine Learning Engineer             Zalando SE                     1 day ago       Full-time       €80,000–€110,000 a year
    ↳ Apply: https://jobs.zalando.com/...
    Data Scientist – NLP                          HelloFresh                     3 days ago      Full-time       —
    ...
```

---

## File structure

| File                 | Purpose                                              |
|----------------------|------------------------------------------------------|
| `models.py`          | Pydantic models: `JobListing`, `JobSearchResult`     |
| `serpapi_client.py`  | Raw HTTP client for the SerpApi Google Jobs endpoint |
| `tools.py`           | `@function_tool` wrappers exposed to the LLM         |
| `agent.py`           | Agent definition, output schema, `run()` function    |
| `logging_config.py`  | Centralised logging setup                            |
| `main.py`            | CLI entry point                                      |

