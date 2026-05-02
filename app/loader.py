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
    try:
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
    except Exception as e:
        print(f"Error loading maps: {e}")
        raise

"""
Inserts user data into the users table.
One row per registration event.
"""

def insert_users(events):
    try:
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
    except Exception as e:
        print(f"Error loading users: {e}")
        raise

"""
Inserts session data into the sessions table.
One row per users session.
"""

def insert_sessions(events):
    try:
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
    except Exception as e:
        print(f"Error loading sessions: {e}")
        raise

"""
Inserts match data into the matches table.
One row per full match.
"""

def insert_matches(events):
    try:
        # DB connection
        conn = get_connection()
        cursor = conn.cursor()
        count = 0 # Number of rows added to DB

        match_data = {}

        for event in events:
            if event["event_type"] in ["match_start", "match_finish"]:
                # definitons
                user = event["user_id"]
                opponent = event["event_data"]["opponent_id"]
                map_id = event["event_data"]["map_id"]

                players_sorted = sorted([user,opponent]) # sorting there are no duplicates with the opposite side of the event
                match_id = f"{players_sorted[0]}_{players_sorted[1]}_{map_id}"

                # Creating data per match
                if match_id not in match_data:
                    match_data[match_id]={
                        "map_id" : map_id,
                        "started_at" : None,
                        "ended_at" : None
                    }
                
                # Timestamp insert for start and finish
                if event["event_type"]== "match_start":
                    match_data[match_id]["started_at"] = event["timestamp"]
                if event["event_type"]== "match_finish":
                    match_data[match_id]["ended_at"] = event["timestamp"]

        for match_id, data in match_data.items():
            # inserting to sql per row in case we find a session
            cursor.execute(""" INSERT OR IGNORE INTO matches (match_id, map_id, started_at, ended_at) 
            VALUES (?,?,?,?)""", (match_id, data["map_id"], data["started_at"], data["ended_at"]))
            count +=1 # Row done

        conn.commit()
        conn.close()
        print(f"Matches loaded: {count}")
    except Exception as e:
        print(f"Error loading matches: {e}")
        raise


"""
Inserts match results into the match_result table.
One row per player per outcome.
"""

def insert_match_results(events):
    try:
        # DB connection
        conn = get_connection()
        cursor = conn.cursor()
        count = 0 # Number of rows added to DB

        for event in events:
            if event["event_type"] == "match_finish":
                # definitons
                user = event["user_id"]
                opponent = event["event_data"]["opponent_id"]
                map_id = event["event_data"]["map_id"]
                outcome = event["event_data"]["outcome"]

                players_sorted = sorted([user,opponent]) # sorting there are no duplicates with the opposite side of the event
                match_id = f"{players_sorted[0]}_{players_sorted[1]}_{map_id}"

                cursor.execute("""
                        INSERT OR IGNORE INTO match_results 
                        (match_id, user_id, outcome)
                        VALUES (?, ?, ?)
                    """, (match_id, user, outcome))
                count += 1

        conn.commit()
        conn.close()
        print(f"Match results loaded: {count}")
    except Exception as e:
        print(f"Error loading match_results: {e}")
        raise

        






