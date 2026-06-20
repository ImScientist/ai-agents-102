# Berlin Cinemas Map 🎬

An interactive map of all Berlin cinemas listed on [Kinoheld](https://www.kinoheld.de), automatically updated daily via GitHub Actions and hosted on GitHub Pages.

## How It Works

```
Daily GitHub Action
      ↓
fetch_cinemas.py  →  calls Kinoheld GraphQL API
      ↓
cinemas.json      ←  lat/lon + address for every Berlin cinema
      ↓
GitHub Pages (gh-pages branch)
      ↓
index.html loads cinemas.json → renders Leaflet.js map
```

## Files

| File | Description |
|---|---|
| `index.html` | Interactive map using [Leaflet.js](https://leafletjs.com/) + OpenStreetMap tiles |
| `fetch_cinemas.py` | Standalone Python script — fetches cinema data and writes `cinemas.json` |
| `cinemas.json` | Auto-generated data file (committed by GitHub Actions, **do not edit manually**) |
| `.github/workflows/update_cinema_map.yml` | Workflow that runs daily and deploys to GitHub Pages |

## Running Locally

```bash
# 1. Install the only dependency
pip install requests

# 2. Fetch the latest cinema data
python webapp_movie/fetch_cinemas.py
# → writes webapp_movie/cinemas.json

# 3. Serve the app locally (Python built-in server)
cd webapp_movie
python -m http.server 8080
# → open http://localhost:8080 in your browser
```

## GitHub Pages Setup

1. Push this repository to GitHub.
2. Go to **Settings → Pages** and set the source to the **`gh-pages` branch**, root folder.
3. The first deploy runs automatically on the next scheduled trigger, or you can kick it off manually from the **Actions** tab → *Update Cinema Map* → **Run workflow**.
4. Your map will be live at `https://<your-username>.github.io/<repo-name>/`.

## Data Source

Cinema data is fetched from the Kinoheld internal GraphQL API:
```
https://next-live.kinoheld.de/graphql
```
This is an **unofficial, undocumented API** used by Kinoheld's own frontend. Use it responsibly.

