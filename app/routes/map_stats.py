"""
map_stats.py
------------
GET /map-stats/{map_name} endpoint.
Returns daily statistics for a specific golf map.
Filterable by date range.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.database import get_connection

# Router for API
router = APIRouter()

@router.get("/map-stats/{map_name}") # map parameter - eg. when someone visits /map-stats/Lake
def get_map_stats(map_name: str, date_from: str = None, date_to: str = None):  
    try:
        # DB conecting
        conn = get_connection()
        cursor = conn.cursor()

        # First check if map exists - "type in" error "catch"
        map_row = cursor.execute(
            "SELECT map_id FROM maps WHERE map_name = ?", (map_name,)
        ).fetchone()

        if not map_row:
            return JSONResponse(
                status_code=404,
                content={"error": f"Map '{map_name}' not found"}
            )

        map_id = map_row["map_id"]

        query = """
                SELECT 
                    -- Convert Unix timestamp to readable date eg. "2026-04-03"
                    DATE(ma.ended_at, 'unixepoch') as date,
                    
                    -- Count unique matches that ended on this date
                    COUNT(DISTINCT ma.match_id) as match_count,
                    
                    -- Average match duration in seconds
                    ROUND(AVG(ma.ended_at - ma.started_at), 0) as average_playtime,
                    
                    -- Find player with highest summed win ratio up to this date
                    -- Runs once per date row in the outer query
                    (
                        SELECT u.username
                        FROM match_results mr2
                        JOIN matches ma2 ON mr2.match_id = ma2.match_id
                        JOIN users u ON mr2.user_id = u.user_id
                        WHERE ma2.map_id = ?
                        -- all matches up to and including this date
                        AND DATE(ma2.ended_at, 'unixepoch') <= DATE(ma.ended_at, 'unixepoch')
                        GROUP BY mr2.user_id
                        -- Sort by win ratio highest first
                        ORDER BY SUM(mr2.outcome) * 1.0 / COUNT(mr2.outcome) DESC
                        -- Take only the best player
                        LIMIT 1
                    ) as best_player_username
                    
                FROM matches ma
                -- Filter by this specific map
                WHERE ma.map_id = ?
                -- Only include finished matches
                AND ma.ended_at IS NOT NULL
                -- One row per date
                GROUP BY DATE(ma.ended_at, 'unixepoch')
                -- Newest first
                ORDER BY date DESC
            """


        results = [dict(row) for row in cursor.execute(query, (map_id, map_id)).fetchall()]
        conn.close()

        # Apply date filters (in case the user filters out by date)
        if date_from:
            results = [r for r in results if r["date"] >= date_from]
        if date_to:
            results = [r for r in results if r["date"] <= date_to]

        return results

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Something went wrong: {str(e)}"}
        )

    