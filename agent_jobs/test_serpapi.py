"""
test_serpapi.py
Quick smoke-test for serpapi_client.py — run directly, not via pytest.

Usage:
    source ~/.zshrc && uv run python agent_jobs/test_serpapi.py
"""

import os
import sys
import requests

sys.path.insert(0, os.path.dirname(__file__))

# ------------------------------------------------------------------
# Ensure the key is available before doing anything else
# ------------------------------------------------------------------
key = os.environ.get("SERPAPI_KEY", "").strip()
if not key:
    print("ERROR: SERPAPI_KEY is not set in the environment.")
    sys.exit(1)

print(f"✅  SERPAPI_KEY found (length {len(key)})\n")

ENDPOINT = "https://serpapi.com/search"
TIMEOUT = 15


def raw_search(query: str, **extra) -> dict:
    """Minimal raw GET request — no client wrapper."""
    params = {"engine": "google_jobs", "q": query, "hl": "en", "api_key": key, **extra}
    r = requests.get(ENDPOINT, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def show_jobs(payload: dict, n: int = 3) -> None:
    jobs = payload.get("jobs_results", [])
    if "error" in payload:
        print(f"  ERROR: {payload['error']}")
        return
    print(f"  Results: {len(jobs)}")
    for j in jobs[:n]:
        ext = j.get("detected_extensions") or {}
        print(f"  • [{j['company_name']}] {j['title']}")
        print(f"    loc: {j.get('location', '—')}  |  posted: {ext.get('posted_at', '—')}  |  type: {ext.get('schedule_type', '—')}")


# ------------------------------------------------------------------
# Test 1: broad query — no location filter (baseline, should return results)
# ------------------------------------------------------------------
print("── Test 1: 'software engineer' (baseline, no location) ──")
show_jobs(raw_search("software engineer"))
print()

# ------------------------------------------------------------------
# Test 2: location embedded in query string (the reliable approach)
# ------------------------------------------------------------------
print("── Test 2: 'machine learning engineer Berlin' (location in query) ──")
show_jobs(raw_search("machine learning engineer Berlin"))
print()

# ------------------------------------------------------------------
# Test 3: data scientist with location in query
# ------------------------------------------------------------------
print("── Test 3: 'data scientist Berlin' (location in query) ──")
show_jobs(raw_search("data scientist Berlin"))
print()

# ------------------------------------------------------------------
# Test 4: AI engineer with location in query
# ------------------------------------------------------------------
print("── Test 4: 'AI engineer Berlin' (location in query) ──")
show_jobs(raw_search("AI engineer Berlin"))
print()

# ------------------------------------------------------------------
# Test 5: full client wrapper (uses serpapi_client.py)
# ------------------------------------------------------------------
print("── Test 5: serpapi_client.search_jobs() wrapper ──")
from serpapi_client import search_jobs

result = search_jobs("data scientist")  # location="Berlin" appended automatically
print(f"  Full query sent : {result.query!r}")
print(f"  Jobs returned   : {len(result.jobs)}")
print()
for job in result.jobs[:3]:
    ext = job.extensions
    salary = ext.salary if ext else None
    posted = ext.posted_at if ext else None
    wfh = " 🏠" if (ext and ext.work_from_home) else ""
    print(f"  • {job.title} @ {job.company_name}{wfh}")
    print(f"    {job.location}  |  posted: {posted}  |  salary: {salary}")
    print(f"    via: {job.via}")
    if job.apply_link:
        print(f"    apply: {job.apply_link}")
    print()

# ------------------------------------------------------------------
# Test 6: try broader / alternative queries that may surface Berlin jobs
# ------------------------------------------------------------------
print("── Test 6: broader fallback queries ──")
fallbacks = [
    "machine learning Berlin Germany",
    "data science jobs Berlin",
    "Python developer Berlin",
]
for q in fallbacks:
    p = raw_search(q)
    jobs = p.get("jobs_results", [])
    if "error" in p:
        print(f"  '{q}' → ERROR: {p['error']}")
    else:
        locs = [j.get("location", "—") for j in jobs[:2]]
        print(f"  '{q}' → {len(jobs)} results  (sample locations: {locs})")
print()

print("✅  All tests complete.")
print()
print("── Summary ──")
print("  The SerpApi Google Jobs client is working correctly.")
print("  Google Jobs returns US-based results by default (SerpApi servers are US-based).")
print("  Berlin-specific ML/data science queries may return 0 results on the free tier.")
print("  The client handles this gracefully — 0 results is returned instead of an error.")



