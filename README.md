# hole-in-one-api

A data pipeline and REST API for golf game event analytics.

---

## What It Does

1. Reads raw game event data from events.jsonl
2. Cleans the data using 13 validation rules
3. Loads clean data into a SQLite database
4. Exposes two REST API endpoints for querying statistics

---

## Requirements

- Python 3.10 or higher
- pip

---

## Installation

1. Clone the repository
2. Create a virtual environment: python -m venv .venv
3. Activate it: .venv\Scripts\activate (Windows)
4. Install dependencies: pip install -r requirements.txt
5. Place events.jsonl and maps.jsonl inside the data/ folder

---

## Running The App

uvicorn app.main:app --reload

The server starts at http://localhost:8000
On first run it automatically cleans and loads all data.

---

## API Endpoints

GET /user-stats
- Optional: ?countries=SRB,MNE
- Optional: ?os=iOS

GET /map-stats/{map_name}
- Optional: ?date_from=2026-01-01&date_to=2026-04-01

Interactive docs available at: http://localhost:8000/docs

---

## Author

Dušan Devedžić
LinkedIn: YOUR LINKEDIN
