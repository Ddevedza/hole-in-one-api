import json
import time

# Event file load
def load_events(filepath): # load events
    events = []

    # In case the filepath is not well defined
    try:
        with open(filepath,"r") as file:
            for line in file:
                event=json.loads(line)
                events.append(event)

        return events

    except FileNotFoundError:
        print(f"Error: {filepath} not found!")
        raise

# Map file load
def load_maps(filepath):
    maps = {}

    # In case the filepath is not well defined
    try:
        with open(filepath, "r") as file:
            for line in file:
                m = json.loads(line)
                maps[m["id"]] = m["name"]
        return maps
    except FileNotFoundError:
        print(f"Error: {filepath} not found!")
        raise

'''
Duplicate remove
Logic: If we haven't seen the id before, we add it.
       If we have seen it:
            If the new one is earlier, swap it in
            If the new one is NOT earlier, do nothing, existing one is already correct
'''

def remove_events(events): # duplicate remove function
    seen = {}

    for event in events:
        event_id = event["id"]

        if event_id not in seen:
            seen[event_id] = event # creates event id dict if it doesn't exist
        else:
            existing_event=seen[event_id]
            if event["timestamp"] < existing_event["timestamp"]: # compares timestamps in case there are duplicates
                seen[event_id] = event # The new one is earlier, so replace the existing one

    unique_events = list(seen.values())
    removed_events = len(events) - len(unique_events)
    print(f"Duplicate events removed: {removed_events}")

    return unique_events

''' 
Here we define required fields and check if we match the needed fields in our events:
        "country" in event_data    → True
        "device_os" in event_data  → True
        "username" in event_data   → False  ← missing!
'''

def remove_invalid_events(events):
    required_top_level = ["id", "timestamp", "event_type", "user_id", "event_data"] # Top level fields

    required_fields = {
        "registration": ["country", "device_os", "username"],
        "session_ping": ["state", "device_os"],
        "match_start": ["map_id", "opponent_id"],
        "match_finish": ["map_id", "opponent_id", "outcome"]
    }  # defines required fields per event type

    valid_events = []
    removed = 0 # counter for removed fields

    for event in events:
        # first check top level fields
        if not all(field in event for field in required_top_level):
            removed += 1
            continue

        event_type = event["event_type"]
        event_data = event.get("event_data",{})

        fields = required_fields.get(event_type, []) # cathes which fields are required for this specific eventy type per event

        all_present = all(field in event_data for field in fields) #checks if fields matches the required field for that event

        if all_present: # In case all fields all present (True)
            valid_events.append(event)
        else:
            removed += 1

    print(f"Events removed due to missing fields: {removed}")
    return valid_events

'''
Outcome values can only be 0,0.5 or 1. 
Thus in this check we will remove the 
values which go beyond this limit
'''

def remove_invalid_outcomes(events):
    valid_events = []
    removed = 0  # counter for removed fields

    for event in events:
        event_type = event["event_type"]
        event_data = event.get("event_data", {})

        if event_type == "match_finish":
            outcome = event_data["outcome"]
            if outcome not in [0, 0.5, 1]:
                removed += 1
                continue  # skip this event

        valid_events.append(event)  # keep everything that wasn't skipped

    print(f"Events removed due to invalid outcomes: {removed}")
    return valid_events

'''
- User cannot play against himself. 
In this check we will check if 
User ids match and discard
such invalid events
'''
def remove_matching_oponents(events):
    valid_events = []
    removed = 0  # counter for removed fields

    for event in events:
        event_type = event["event_type"]
        event_data = event.get("event_data", {})

        if event_type in ["match_start", "match_finish"]:
            user = event["user_id"]
            opponent = event_data["opponent_id"]
            if user == opponent:
                print(user,opponent)
                removed += 1
                continue  # skip this event

        valid_events.append(event)  # keep everything that wasn't skipped

    print(f"Events removed due to self-matches: {removed}")
    return valid_events

'''
- User's that is not registered cannot play.
In this check we will spot
any unregistered users and remove
their events.
'''

def remove_unregistered_users(events):
    registered_users=set()


    for event in events:
        if event["event_type"] == "registration":
            registered_users.add(event["user_id"])

    valid_events = []
    removed = 0  # counter for removed fields

    for event in events:
        if event["user_id"] in registered_users:
            valid_events.append(event)  # keep everything that wasn't skipped
        else:
            removed += 1


    print(f"Events removed due to unregistered users: {removed}")
    return valid_events

'''
-Players whose matches are not finished, are removed.
In this check we will go trough each event
add the match_start and match_finish, along with
players who were in this event and later on
compare if said pairs have both match_start and
match_finish. After which valid ones are held on
and others are discarded.
'''

def remove_incomplete_matches(events):
    match_events = {} # This will serve to catch each event pair

    # What event type exists per match pair
    for event in events:
        if event["event_type"] in ["match_start", "match_finish"]:
            user = event["user_id"]
            opponent = event["event_data"]["opponent_id"]
            players = tuple(sorted([user, opponent])) # We are sorting as match_start and match_finish event happen from
            # both perspectives

            if players not in match_events:
                match_events[players] = set() # create empty slot if first time seeing this pair
            match_events[players].add(event["event_type"]) # add this event type to that slot

    valid_pairs = set() # defines valid player pairs
    for players, types in match_events.items():
        if "match_start" in types and "match_finish" in types:
            valid_pairs.add(players) # players are added for played out matches

    valid_events = []
    removed = 0

    for event in events:
        if event["event_type"] in ["match_start", "match_finish"]:
            user = event["user_id"]
            opponent = event["event_data"]["opponent_id"]
            players = tuple(sorted([user, opponent]))
            if players not in valid_pairs:
                removed += 1
                continue
        valid_events.append(event)

    print(f"Events removed due to incomplete matches: {removed}")
    return valid_events

"""
- Events with invalid devices are removed.
If the registration/session_ping device 
is not:
"Android" or "IOS".
We discard it.
"""

def remove_invalid_devices(events):
    valid_events = []
    removed = 0

    for event in events:
        event_type = event["event_type"]
        event_data = event.get("event_data", {})

        if event_type in ["registration","session_ping"]:
            if event_data.get("device_os") not in ["Android", "iOS"]:
                removed += 1
                continue

        valid_events.append(event)

    print(f"Events removed due to invalid devices: {removed}")
    return valid_events


'''
- Events with invalid states are removed.
If the state is not:
"started", "in_progress", "ended".
We discard it.
'''
def remove_invalid_session_state(events):
    valid_events = []
    removed = 0

    for event in events:
        event_type = event["event_type"]
        event_data = event.get("event_data", {})

        if event_type =="session_ping":
            if event_data.get("state") not in ["started", "in_progress", "ended"]:
                removed += 1
                continue

        valid_events.append(event)

    print(f"Events removed due to session state: {removed}")
    return valid_events

"""
Checking for future or negative timestamps.
In case the timestamp goes above our current time
or if they are negative - we are discarding them.
"""

def remove_future_timestamps(events):
    now = int(time.time())
    valid_events = []
    removed = 0

    for event in events:
        if event["timestamp"] > now or event["timestamp"] <= 0:
            removed += 1
            continue
        valid_events.append(event)

    print(f"Events removed due to invalid timestamps: {removed}")
    return valid_events

"""
Events with invalid maps are removed.
"""

def remove_invalid_maps(events, valid_map_ids):
    valid_events = []
    removed = 0

    for event in events:
        event_type = event["event_type"]
        event_data = event.get("event_data", {})

        if event_type in ["match_start", "match_finish"]:
            if event_data.get("map_id") not in valid_map_ids:
                removed += 1
                continue

        valid_events.append(event)

    print(f"Events removed due to invalid map_id: {removed}")
    return valid_events

'''
Remove duplicate registrations.
In case there are duplicate registrations, 
we discard younger one.
'''
def remove_duplicate_registrations(events):
    seen_registrations = {} # dict for already registered users
    non_registration_events = [] # list of normal registrations

    for event in events:
        if event["event_type"] == "registration":
            user_id = event["user_id"]
            if user_id not in seen_registrations:
                seen_registrations[user_id] = event
            else:
                if event["timestamp"] < seen_registrations[user_id]["timestamp"]: # Check which timestamp came first
                    seen_registrations[user_id] = event # accepting older timestamps
        else:
            non_registration_events.append(event)  # keep everything else

    unique_registrations = list(seen_registrations.values()) # list of good registrations
    all_events = unique_registrations + non_registration_events # complete list of all registrations

    removed = len(events) - len(all_events)
    print(f"Duplicate registrations removed: {removed}")
    return all_events

"""
- Remove events before registration.
If events came before the registration,
they are removed.
"""

def remove_events_before_registration(events):
    registration_times = {}

    for event in events:
        if event["event_type"] == "registration":
            registration_times[event["user_id"]] = event["timestamp"]  # user_id → timestamp

    valid_events = []
    removed = 0

    for event in events:
        if event["event_type"] != "registration":
            user_id = event["user_id"]
            reg_time = registration_times.get(user_id)
            if reg_time and event["timestamp"] < reg_time: # if event time is before registration time
                removed += 1 # event is removed
                continue
        valid_events.append(event)

    print(f"Events removed due to pre-registration timestamp: {removed}")
    return valid_events

if __name__ == '__main__':

    events = load_events("data/events.jsonl") # loading events
    print(f"Total events loaded: {len(events)}")

    maps = load_maps("data/maps.jsonl") # loading maps
    valid_map_ids = set(maps.keys()) # We take only map ids (maps are dicts with map id and map name)

    events = remove_events(events)
    print(f"Events after removing duplicates: {len(events)}")

    events = remove_invalid_events(events)
    print(f"Events after removing invalid events: {len(events)}")

    events = remove_invalid_outcomes(events)
    print(f"Events after removing invalid outcomes: {len(events)}")

    events = remove_matching_oponents(events)
    print(f"Events after removing self-matches: {len(events)}")

    events = remove_unregistered_users(events)
    print(f"Events after removing unregistered users: {len(events)}")

    events = remove_incomplete_matches(events)
    print(f"Events after removing incomplete matches: {len(events)}")

    events = remove_invalid_devices(events)
    print(f"Events after removing invalid devices: {len(events)}")

    events = remove_invalid_session_state(events)
    print(f"Events after removing invalid states: {len(events)}")

    events = remove_future_timestamps(events)
    print(f"Events after removing invalid states: {len(events)}")

    events = remove_invalid_maps(events, valid_map_ids)
    print(f"Events after removing invalid maps: {len(events)}")

    events = remove_duplicate_registrations(events)
    print(f"Events after removing duplicate registrations: {len(events)}")

    events = remove_events_before_registration(events)
    print(f"Events after removing pre-registered events: {len(events)}")

    print(f"\n=== Cleaning Complete ===")
    print(f"Started with: 5000 events")
    print(f"Ended with:   {len(events)} events")
    print(f"========================")
