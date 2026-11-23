import sqlite3
from datetime import datetime, timezone

from app.config import DB_PATH
from app.schemas import TailoredDoc


def init_tailored_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tailored ("
        "job_id TEXT PRIMARY KEY, data TEXT NOT NULL, created_at TEXT NOT NULL)"
    )
    conn.commit()
    conn.close()


def save_tailored(doc):
    # ek job ka naya draft purane ko badal deta hai
    init_tailored_table()
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO tailored (job_id, data, created_at) VALUES (?, ?, ?)",
        (doc.job_id, doc.model_dump_json(), now),
    )
    conn.commit()
    conn.close()


def load_tailored(job_id):
    init_tailored_table()
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT data FROM tailored WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return TailoredDoc.model_validate_json(row[0])