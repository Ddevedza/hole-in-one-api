"""
user_stats.py
-------------
GET /user-stats endpoint.
Returns player statistics ordered by total playtime.
Filterable by country and device OS.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.database import get_connection

# Router for API
router = APIRouter()

# On user-stats visit
@router.get("/user-stats")
def get_user_stats(countries: str = None, os: str = None):
    try:
        # DB conecting
        conn = get_connection()
        cursor = conn.cursor()

        # Query creation - commented out for more clarity
        query = """
                SELECT 
                    -- Player's username
                    u.username,
                    -- Country code eg. SRB, GBR
                    u.country,
                    -- Date they registered eg. 2026-04-03
                    u.registration_date,
                    
                    -- Total seconds spent playing
                    -- COALESCE returns 0 if no sessions found
                    COALESCE((
                        SELECT SUM(s.ended_at - s.started_at) 
                        FROM sessions s WHERE s.user_id = u.user_id
                    ), 0) as total_playtime,
                    
                    -- Win ratio between 0 and 1
                    -- NULLIF prevents division by zero
                    -- COALESCE returns 0 if no matches found
                    COALESCE(ROUND((
                        SELECT SUM(mr.outcome) * 1.0 / NULLIF(COUNT(mr.outcome), 0) 
                        FROM match_results mr WHERE mr.user_id = u.user_id
                    ), 2), 0) as total_win_ratio,
                    
                    -- Average matches played per session
                    -- total matches divided by total sessions
                    ROUND(COALESCE((
                        SELECT COUNT(*) FROM match_results mr WHERE mr.user_id = u.user_id
                    ), 0) * 1.0 / NULLIF((
                        SELECT COUNT(*) FROM sessions s WHERE s.user_id = u.user_id
                    ), 0), 2) as avg_matches_per_session,
                    
                    -- Map where user has highest win ratio
                    -- Joins match_results to matches to maps
                    -- Groups by map, orders by win ratio descending, takes top 1
                    (
                        SELECT m.map_name
                        FROM match_results mr2
                        JOIN matches ma ON mr2.match_id = ma.match_id
                        JOIN maps m ON ma.map_id = m.map_id
                        WHERE mr2.user_id = u.user_id
                        GROUP BY ma.map_id
                        ORDER BY SUM(mr2.outcome) * 1.0 / COUNT(mr2.outcome) DESC
                        LIMIT 1
                    ) as fav_map,
                    
                    -- Win ratio on the favorite map
                    -- Same logic as fav_map but returns the ratio instead of name
                    (
                        SELECT ROUND(SUM(mr2.outcome) * 1.0 / COUNT(mr2.outcome), 2)
                        FROM match_results mr2
                        JOIN matches ma ON mr2.match_id = ma.match_id
                        WHERE mr2.user_id = u.user_id
                        GROUP BY ma.map_id
                        ORDER BY SUM(mr2.outcome) * 1.0 / COUNT(mr2.outcome) DESC
                        LIMIT 1
                    ) as fav_map_win_ratio,
                    
                    -- Comma separated list of OS user has played on
                    -- eg. "iOS" or "iOS,Android"
                    (
                        SELECT GROUP_CONCAT(DISTINCT s.device_os)
                        FROM sessions s
                        WHERE s.user_id = u.user_id
                    ) as device_os
                    
                -- Main table is users, every other stat joins back to it
                FROM users u
                -- Sort by most active player first
                ORDER BY total_playtime DESC
            """

        results = [dict(row) for row in cursor.execute(query).fetchall()]
        conn.close()

        # Country filter per need
        if countries:
            country_list = [c.strip() for c in countries.split(",")]
            results = [r for r in results if r["country"] in country_list]

        # OS filter per need
        if os:
            os_list = [o.strip() for o in os.split(",")]
            filtered = []
            for r in results:
                # OS cleanes in such cases but (or "") is put just in case
                user_os = r.get("device_os") or ""
                #splits "iOS","Android" into ["iOS", "Android"]
                user_os_list = user_os.split(",")
                if any(o in user_os_list for o in os_list): # check for matches
                    filtered.append(r)
            results = filtered

        return results

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Something went wrong: {str(e)}"}
        )
