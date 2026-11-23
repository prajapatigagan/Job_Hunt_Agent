import sqlite3
from datetime import datetime, timezone

from app.config import DB_PATH
from app.schemas import Preferences, UserProfile


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS profile "
        "(id INTEGER PRIMARY KEY, data TEXT, updated_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS preferences "
        "(id INTEGER PRIMARY KEY, data TEXT, updated_at TEXT)"
    )
    conn.commit()
    conn.close()


def save_profile(profile: UserProfile):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO profile (id, data, updated_at) VALUES (1, ?, ?)",
        (profile.model_dump_json(), datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def load_profile():
    conn = get_conn()
    row = conn.execute("SELECT data FROM profile WHERE id = 1").fetchone()
    conn.close()
    if row is None:
        return None
    return UserProfile.model_validate_json(row[0])


def save_preferences(prefs: Preferences):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO preferences (id, data, updated_at) VALUES (1, ?, ?)",
        (prefs.model_dump_json(), datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def load_preferences():
    conn = get_conn()
    row = conn.execute("SELECT data FROM preferences WHERE id = 1").fetchone()
    conn.close()
    if row is None:
        return None
    return Preferences.model_validate_json(row[0])