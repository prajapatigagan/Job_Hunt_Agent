import sqlite3
from datetime import datetime, timezone

from app.config import DB_PATH
from app.schemas import Application


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS applications ("
        "job_id TEXT PRIMARY KEY, status TEXT NOT NULL, notes TEXT DEFAULT '', "
        "reason TEXT DEFAULT '', updated_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS status_history ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, "
        "status TEXT NOT NULL, changed_at TEXT NOT NULL)"
    )
    return conn


def set_status(job_id, status, notes=None, reason=None):
    conn = _connect()
    now = datetime.now(timezone.utc).isoformat()

    # purane notes aur reason bacha ke rakho, agar naye nahi diye
    old = conn.execute(
        "SELECT notes, reason FROM applications WHERE job_id = ?", (job_id,)
    ).fetchone()
    if notes is None:
        notes = old[0] if old else ""
    if reason is None:
        reason = old[1] if old else ""

    conn.execute(
        "INSERT OR REPLACE INTO applications (job_id, status, notes, reason, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (job_id, status, notes, reason, now),
    )
    conn.execute(
        "INSERT INTO status_history (job_id, status, changed_at) VALUES (?, ?, ?)",
        (job_id, status, now),
    )
    conn.commit()
    conn.close()


def load_applications():
    conn = _connect()
    rows = conn.execute(
        "SELECT job_id, status, notes, reason, updated_at FROM applications ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append(
            Application(job_id=row[0], status=row[1], notes=row[2], reason=row[3], updated_at=row[4])
        )
    return result


def get_history(job_id):
    conn = _connect()
    rows = conn.execute(
        "SELECT status, changed_at FROM status_history WHERE job_id = ? ORDER BY id", (job_id,)
    ).fetchall()
    conn.close()
    return rows


def decided_job_ids():
    # jin jobs pe tu decision le chuka hai (drafted wali dobara aa sakti hain)
    conn = _connect()
    rows = conn.execute(
        "SELECT job_id FROM applications WHERE status NOT IN ('drafted', 'shortlisted')"
    ).fetchall()
    conn.close()
    return set(row[0] for row in rows)