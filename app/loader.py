"""
loader.py
---------
Takes clean event data and loads it
into the SQLite database tables.
"""

from database import get_connection
from datetime import datetime


"""
Inserts map data into map table.
"""
def insert_maps(maps):
    # DB connectors
    conn = get_connection()
    cursor = conn.cursor()

    # Map SQL insert
    for map_id, map_name in maps.items():
        cursor.execute("""
            INSERT OR IGNORE INTO maps (map_id, map_name)
            VALUES (?, ?)
        """, (map_id, map_name))

    conn.commit()
    conn.close()
    print(f"Maps loaded: {len(maps)}")

"""
Inserts user data into the users table.
One row per registration event.
"""

def insert_users(events):

    # DB connection
    conn = get_connection()
    cursor = conn.cursor()
    count = 0 # Number of rows added to DB

    for event in events:
        if event["event_type"] == "registration":
            # definition of objects
            data = event["event_data"]
            user_id = event["user_id"]
            username = data["username"]
            country = data["country"]
            data["username"]
            reg_date = datetime.fromtimestamp(event["timestamp"]).strftime("%Y-%m-%d")

            # inserting to sql per row
            cursor.execute(""" INSERT OR IGNORE INTO users (user_id, username, country, registration_date) 
            VALUES (?,?,?,?)""", (user_id,username, country, reg_date))
            count +=1 # Row done

    conn.commit()
    conn.close()
    print(f"Users loaded: {count}")

"""
Inserts session data into the sessions table.
One row per users session.
"""

def insert_sessions(events):

    # DB connection
    conn = get_connection()
    cursor = conn.cursor()
    count = 0 # number of rows added to DB

    user_pings = {}

    for event in events: 
        if event["event_type"] == "session_ping":
            user_id = event["user_id"]

            # groups events per user
            if user_id not in user_pings:
                user_pings[user_id] = []
            user_pings[user_id].append(event)

    for user_id, pings in user_pings.items():
        pings.sort(key = lambda x: x["timestamp"]) # sorted pings per timestamps

        session_start = pings[0] # first ping

        for i in range (1,len(pings)):
            gap = pings[i]["timestamp"] - pings[i-1]["timestamp"] # difference between timestamps

            if gap>120: # new session
                session_end = pings[i-1]

                # inserting to sql per row in case we find a session
                cursor.execute(""" INSERT OR IGNORE INTO sessions (user_id, device_os, started_at, ended_at) 
                VALUES (?,?,?,?)""", (user_id, pings[0]["event_data"]["device_os"], session_start["timestamp"], session_end["timestamp"]))
                count +=1 # Row done

                # starting the new session
                session_start = pings[i]

        # inserting to sql per row in case we don't
        cursor.execute(""" INSERT OR IGNORE INTO sessions (user_id, device_os, started_at, ended_at) 
        VALUES (?,?,?,?)""", (user_id, pings[0]["event_data"]["device_os"], session_start["timestamp"], pings[-1]["timestamp"]))
        count +=1 # Row done

    conn.commit()
    conn.close()
    print(f"Sessions loaded: {count}")
        