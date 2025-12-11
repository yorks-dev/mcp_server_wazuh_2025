import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "assets.db")

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_name TEXT,
        owner TEXT,
        group_name TEXT,
        criticality TEXT,
        ip_address TEXT UNIQUE
    );
    """)
    conn.commit()
    conn.close()
# Call this when the MCP server loads this tool
init_database()
