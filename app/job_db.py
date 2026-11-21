import sqlite3
from datetime import datetime, timezone

from app.config import DB_PATH
from app.schemas import Job


def init_job_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS jobs ("
        "id TEXT PRIMARY KEY, data TEXT NOT NULL, found_at TEXT NOT NULL)"
    )
    conn.commit()
    conn.close()


def save_jobs(jobs):
    # sirf naye jobs save hote hain, purane (same id) ignore ho jate hain
    init_job_table()
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now(timezone.utc).isoformat()

    new_count = 0
    for job in jobs:
        cur = conn.execute(
            "INSERT OR IGNORE INTO jobs (id, data, found_at) VALUES (?, ?, ?)",
            (job.id, job.model_dump_json(), now),
        )
        new_count += cur.rowcount

    conn.commit()
    conn.close()
    return new_count


def load_jobs():
    init_job_table()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT data FROM jobs ORDER BY found_at DESC, rowid DESC").fetchall()
    conn.close()
    return [Job.model_validate_json(row[0]) for row in rows]


def clear_jobs():
    init_job_table()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM jobs")
    conn.commit()
    conn.close()