# 🎬 agent_movie

An AI agent that looks up the movie program for a Berlin cinema using the
[Kinoheld](https://www.kinoheld.de) GraphQL API.

## How it works

1. The agent calls `list_berlin_cinemas` to retrieve all cinemas in Berlin.
2. The LLM fuzzy-matches your input to the closest cinema name.
3. The agent calls `get_cinema_program` to fetch today's (or a specified date's) showtimes.
4. It returns a structured report with a formatted program table and a short summary.

## Project structure

```
agent_movie/
├── main.py              # CLI entry point
├── agent.py             # Agent definition and run() function
├── tools.py             # @function_tool wrappers for the LLM
├── kinoheld_client.py   # Low-level Kinoheld GraphQL HTTP client
├── models.py            # Pydantic domain models
├── logging_config.py    # Shared logging setup
└── README.md
```

## Requirements

- Python ≥ 3.13
- Dependencies are managed via `uv` (see `pyproject.toml` in the root)
- An `OPENAI_API_KEY` set in a `.env` file at the project root

## Usage

```bash
# Today's program at a cinema (partial name is fine)
uv run python agent_movie/main.py "CineStar"

# Program at a specific cinema on a specific date
uv run python agent_movie/main.py "Babylon" --date 2026-06-20
```

### Example output

```
🎬  CineStar Berlin - CUBIX am Alexanderplatz  —  2026-06-19
    13 movies are showing today, ranging from blockbusters to thrillers.
    Highlights include Star Wars: The Mandalorian and Grogu and Scary Movie 6.

    TIME     TITLE                                          MIN  LANG
    ----------------------------------------------------------------------
    13:30    Der Teufel trägt Prada 2                       119  DE
    13:30    Master of the Universe                         106  DE
    13:40    Backrooms                                      105  DE
    16:20    Star Wars: The Mandalorian and Grogu            132  DE
    19:30    Scary Movie 6                                   96  DE
    ...
```

## Data source

Showtimes are fetched in real time from the Kinoheld GraphQL API:

```
POST https://next-live.kinoheld.de/graphql
```

This is an **unofficial** API (Kinoheld's own frontend API). There is no
official public documentation. For production use, contact Kinoheld directly
to arrange a formal partnership.

