"""
chart.py
--------
GET /chart endpoint.
Returns an HTML page with a Chart.js line chart showing
match counts per map over a date range.

Default behaviour: shows last 7 days of AVAILABLE data
Optional: use ?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD to reach specific date
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from app.database import get_connection
from datetime import datetime, timedelta
import json

router = APIRouter()

@router.get("/chart", response_class=HTMLResponse)
def get_chart(date_from: str = None, date_to: str = None):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # If no dates provided, find last 7 days of AVAILABLE data
        # This is smarter than using todays date since our dataset
        # may not have recent data
        if not date_from and not date_to:
            latest = cursor.execute("""
                SELECT DATE(MAX(ended_at), 'unixepoch') as max_date
                FROM matches WHERE ended_at IS NOT NULL
            """).fetchone()["max_date"]

            # Calculate 7 days before the latest available date
            latest_date = datetime.strptime(latest, "%Y-%m-%d")
            date_from = (latest_date - timedelta(days=7)).strftime("%Y-%m-%d")
            date_to = latest

        # Query match counts per map per day within date range
        query = """
            SELECT 
                m.map_name,
                -- Convert Unix timestamp to readable date e.g. "2026-04-03"
                DATE(ma.ended_at, 'unixepoch') as date,
                -- Count matches per map per day
                COUNT(*) as match_count
            FROM matches ma
            JOIN maps m ON ma.map_id = m.map_id
            -- Only include finished matches
            WHERE ma.ended_at IS NOT NULL
            -- Apply date range filter
            AND DATE(ma.ended_at, 'unixepoch') >= ?
            AND DATE(ma.ended_at, 'unixepoch') <= ?
            -- One row per map per day
            GROUP BY ma.map_id, DATE(ma.ended_at, 'unixepoch')
            -- Oldest first for chart to read left to right
            ORDER BY date ASC
        """

        rows = [dict(r) for r in cursor.execute(query, (date_from, date_to)).fetchall()]
        conn.close()

        # Get all unique dates across all maps — these become x-axis labels
        dates = sorted(set(r["date"] for r in rows))

        # Organize data into a dict: map_name {date: count}
        # This makes it easy to look up a map count for any date
        maps = {}
        for row in rows:
            name = row["map_name"]
            if name not in maps:
                maps[name] = {}
            maps[name][row["date"]] = row["match_count"]

        # Define a color per map for the chart lines
        colors = {
            "Lake": "rgb(54, 162, 235)",
            "Inferno": "rgb(255, 99, 132)",
            "Cobblestone": "rgb(255, 159, 64)",
            "Desert": "rgb(255, 205, 86)",
            "Forest": "rgb(75, 192, 192)"
        }

        # data.get(d, 0) returns 0 if map had no matches that day
        datasets = []
        for map_name, data in maps.items():
            values = [data.get(d, 0) for d in dates]
            color = colors.get(map_name, "rgb(100,100,100)")
            datasets.append({
                "label": map_name,
                "data": values,
                "borderColor": color,
                "backgroundColor": color,
                "tension": 0.3  # slight curve on lines
            })

        # Build the HTML page with Chart.js
        # Double curly braces {{ }} are needed in "f" strings
        # to output literal { } characters in JavaScript
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Match Count Chart</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 40px;
                    background: #f5f5f5;
                }}
                h1 {{ color: #333; }}
                h3 {{ color: #666; font-weight: normal; }}
                .chart-container {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    max-width: 900px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
            </style>
        </head>
        <body>
            <h1>Match Count per Map</h1>
            <h3>{date_from} to {date_to}</h3>
            <div class="chart-container">
                <canvas id="myChart"></canvas>
            </div>
            <script>
                const ctx = document.getElementById('myChart');
                new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: {json.dumps(dates)},
                        datasets: {json.dumps(datasets)}
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            legend: {{ position: 'top' }},
                            title: {{
                                display: true,
                                text: 'Match Count by Map Over (Default Last 7 Days)'
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                title: {{
                                    display: true,
                                    text: 'Match Count'
                                }}
                            }},
                            x: {{
                                title: {{
                                    display: true,
                                    text: 'Date'
                                }}
                            }}
                        }}
                    }}
                }});
            </script>
        </body>
        </html>
        """

        return HTMLResponse(content=html)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Something went wrong: {str(e)}"}
        )