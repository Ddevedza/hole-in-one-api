# Hole In One API

A data engineering pipeline and REST API for golf game event analytics, built for the Nordeus Job Fair 2026 Data Engineering Challenge.

---

## What It Does

This project takes raw golf game event data and makes it queryable through a clean REST API:

1. **Cleans** raw game event data using 13 validation rules
2. **Stores** clean data in a SQLite database  
3. **Serves** statistics through three REST API endpoints

The input files are processed **once at startup**. After that, all queries are answered from the database — never from the raw files again. This keeps the API fast and efficient.

---

## Architecture & Design Decisions

```
events.jsonl ──┐
               ├──► cleaner.py ──► golf.db ──► FastAPI ──► User
maps.jsonl   ──┘
```

The project is split into four files — each with one clear responsibility:

| File | Responsibility |
|---|---|
| `cleaner.py` | Reads raw files, applies 13 cleaning rules, returns clean events |
| `database.py` | Creates SQLite tables, provides database connection |
| `loader.py` | Takes clean events and inserts them into the database |
| `main.py` | Starts FastAPI, runs pipeline on startup, registers routes |

**Why SQLite?** It is built into Python, requires no installation, and stores everything in a single file. The right tool for this use case — one application, moderate data, no concurrent users.

**Why FastAPI?** Modern, fast to build with, and automatically generates interactive documentation at `/docs`. No extra work needed.

**Why separate files?** Separation of concerns — each file does one job. Makes the code easier to read, test, and maintain.

---

## Project Structure

```
hole-in-one-api/
  app/
    main.py             ← entry point, starts the server
    cleaner.py          ← 13 data cleaning rules
    database.py         ← SQLite schema and connection
    loader.py           ← loads clean data into database
    routes/
      user_stats.py     ← GET /user-stats
      map_stats.py      ← GET /map-stats/{map_name}
      chart.py          ← GET /chart
  data/
    events.jsonl        ← place raw data here
    maps.jsonl          ← place raw data here
  README.md
  requirements.txt
```

---

## Requirements

- Python 3.10 or higher
- pip

---

## Installation

**1. Clone the repository:**
```bash
git clone https://github.com/Ddevedza/hole-in-one-api.git
cd hole-in-one-api
```

**2. Create and activate a virtual environment:**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Add the data files:**

Place `events.jsonl` and `maps.jsonl` inside the `data/` folder.

---

## Running The App

```bash
uvicorn app.main:app --reload
```

On first run the app automatically:
1. Creates the SQLite database with 5 tables
2. Reads and cleans all event data
3. Prints a cleaning summary showing what was removed and why
4. Loads clean data into the database
5. Starts the API server at `http://localhost:8000`

---

## API Endpoints

### GET /user-stats

Returns player statistics ordered by total playtime descending.

**Optional query parameters:**
- `countries` — comma separated country codes eg. `SRB,GBR`
- `os` — operating system filter eg. `iOS` or `Android`

Note: The OS filter uses session data, not registration data. A user appears in iOS results if they played any session on iOS, regardless of registration OS.

**Examples:**
```
GET /user-stats
GET /user-stats?countries=SRB
GET /user-stats?countries=SRB,GBR
GET /user-stats?os=iOS
GET /user-stats?countries=SRB&os=iOS
```

**Response fields:**

| Field | Description |
|---|---|
| username | Player's in-game nickname |
| country | Country code eg. SRB, GBR |
| registration_date | Date of registration (YYYY-MM-DD) |
| total_playtime | Total seconds with the app open |
| total_win_ratio | Win ratio between 0 and 1 |
| avg_matches_per_session | Average matches played per session |
| fav_map | Map with the highest win ratio |
| fav_map_win_ratio | Win ratio on the favorite map |

---

### GET /map-stats/{map_name}

Returns daily statistics for a specific golf map, ordered by date descending.

**Available maps:** Lake, Inferno, Cobblestone, Desert, Forest

**Optional query parameters:**
- `date_from` — start date (YYYY-MM-DD)
- `date_to` — end date (YYYY-MM-DD)

**Examples:**
```
GET /map-stats/Lake
GET /map-stats/Inferno?date_from=2026-04-05
GET /map-stats/Lake?date_from=2026-04-03&date_to=2026-04-06
```

**Response fields:**

| Field | Description |
|---|---|
| date | Date in YYYY-MM-DD format |
| match_cnt | Number of matches on that date |
| avg_playtime | Average match duration in seconds |
| best_player_username | Player with highest cumulative win ratio up to that date |

---

### GET /chart

Returns an HTML page with a line chart showing match counts per map over time.

Default behaviour: shows last 7 days of available data. Each map is represented as a separate colored line.

**Optional query parameters:**
- `date_from` — custom start date (YYYY-MM-DD)
- `date_to` — custom end date (YYYY-MM-DD)

**Examples:**
```
GET /chart
GET /chart?date_from=2026-04-03&date_to=2026-04-07
```

---

## Interactive API Docs

FastAPI automatically generates interactive documentation. Once the server is running visit:

```
http://localhost:8000/docs
```

You can test all endpoints directly from your browser without writing any code.

---

## Data Cleaning

The pipeline applies 13 cleaning rules before loading data:

| Rule | Reason |
|---|---|
| Remove duplicate events | Network retries cause the same event to be sent twice — keep the earliest |
| Remove missing top-level fields | Events missing id, timestamp, user_id etc. are unusable |
| Remove missing event_data fields | Each event type has required fields — discard if missing |
| Remove invalid outcome values | match_finish outcome must be 0, 0.5, or 1 |
| Remove self-matches | A player cannot match against themselves |
| Remove unregistered users | Events from users with no registration are unusable |
| Remove incomplete matches | A match needs at least one match_start AND one match_finish |
| Remove invalid device_os | device_os must be iOS or Android |
| Remove invalid session states | state must be started, in_progress, or ended |
| Remove future timestamps | Events timestamped in the future are impossible |
| Remove invalid map_id | Match events must reference a map that exists in maps.jsonl |
| Remove zero or negative timestamps | Timestamps of 0 or below are meaningless |
| Remove duplicate registrations | Same user registered twice — keep the earliest |
| Remove events before registration | Events that predate a user's registration are impossible |

**Cleaning results on the provided dataset:**
```
Total events loaded:    5000
Events after cleaning:  4299
Events discarded:        701 (14%)
```

---

## Database Design

Five SQLite tables were designed to support efficient querying:

- **maps** — golf course names and IDs from maps.jsonl
- **users** — registered players with username, country, and registration date
- **sessions** — gameplay sessions with start and end timestamps
- **matches** — one row per match with map and timestamps
- **match_results** — one row per player per match with outcome

**Session tracking without state column (bonus point):** Sessions are reconstructed purely from session_ping timestamps. If more than 120 seconds pass between two pings, they belong to different sessions. The `state` column is intentionally ignored.

---

## Assumptions

- A match is considered to have happened on the date it **ended** (match_finish timestamp)
- Win ratio is expressed as a decimal between 0 and 1
- Total playtime includes all time with the app open, not just time in matches
- The OS filter uses session OS — a user may register on one OS and play on another

---

## Author

Dušan Devedžić
LinkedIn: https://www.linkedin.com/in/dusan-devedzic-3812031b2/
