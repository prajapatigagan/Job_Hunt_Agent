import sqlite3
from datetime import datetime, timezone

from app.config import DB_PATH
from app.schemas import MatchResult


def init_match_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS matches ("
        "job_id TEXT PRIMARY KEY, data TEXT NOT NULL, created_at TEXT NOT NULL)"
    )
    conn.commit()
    conn.close()


def save_matches(results):
    # naya match chalane par purane results badal jate hain
    init_match_table()
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now(timezone.utc).isoformat()

    for r in results:
        conn.execute(
            "INSERT OR REPLACE INTO matches (job_id, data, created_at) VALUES (?, ?, ?)",
            (r.job_id, r.model_dump_json(), now),
        )

    conn.commit()
    conn.close()


def load_matches():
    init_match_table()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT data FROM matches").fetchall()
    conn.close()

    results = [MatchResult.model_validate_json(row[0]) for row in rows]
    results.sort(key=lambda r: r.final_score, reverse=True)
    return results


def clear_matches():
    init_match_table()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM matches")
    conn.commit()
    conn.close()