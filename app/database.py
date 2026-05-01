import sqlite3

DATABASE = "golf.db"

# Creating a connector for the database
def get_connection():
    # In case there are issues with the database
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        raise


# Table creation
def create_tables():

    # Calling on the connector
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS maps (
            map_id   TEXT PRIMARY KEY,
            map_name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id           TEXT PRIMARY KEY,
            username          TEXT NOT NULL,
            country           TEXT NOT NULL,
            registration_date TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    TEXT NOT NULL,
            device_os  TEXT NOT NULL,
            started_at INTEGER NOT NULL,
            ended_at   INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS matches (
            match_id   TEXT PRIMARY KEY,
            map_id     TEXT NOT NULL,
            started_at INTEGER,
            ended_at   INTEGER
        );

        CREATE TABLE IF NOT EXISTS match_results (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id TEXT NOT NULL,
            user_id  TEXT NOT NULL,
            outcome  REAL NOT NULL
        );
    """)

    conn.commit()
    conn.close()
    print("Tables created successfully!")

if __name__ == "__main__":
    create_tables()
