"""
main.py
-------
Entry point for the application.
Creates database, cleans data, loads into SQLite,
and starts the FastAPI server.
"""

import sys
sys.path.append("app")

from database import create_tables
from cleaner import load_events, load_maps, run_cleaning
from loader import insert_maps, insert_users, insert_sessions, insert_matches, insert_match_results
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
def startup():
    create_tables()
    
    events = load_events("data/events.jsonl")
    maps = load_maps("data/maps.jsonl")
    
    events = run_cleaning(events, maps)
    
    insert_maps(maps)
    insert_users(events)
    insert_sessions(events)
    insert_matches(events)
    insert_match_results(events)
    
    print("Data loaded successfully!")