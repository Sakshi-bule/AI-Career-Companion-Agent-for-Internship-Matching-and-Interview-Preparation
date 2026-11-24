import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from src.schemas import CandidateProfile

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "career_companion.db"

JSON_FIELDS = (
    "skills",
    "soft_skills",
    "education",
    "experience",
    "projects",
    "certifications",
)


def get_db_connection() -> sqlite3.Connection:
    """Open a connection to the SQLite database with dict-like rows."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the students table if it does not exist."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT,
                email TEXT UNIQUE,
                phone TEXT,
                location TEXT,
                preferred_role TEXT,
                preferred_location TEXT,
                summary TEXT,
                skills TEXT,
                soft_skills TEXT,
                education TEXT,
                experience TEXT,
                projects TEXT,
                certifications TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def save_student_profile(profile: CandidateProfile) -> int:
    """Insert a profile, or update it if the email already exists.

    Returns the row id of the saved record.
    """
    data = profile.model_dump()
    values = {
        "full_name": data.get("full_name"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "location": data.get("location"),
        "preferred_role": data.get("preferred_role"),
        "preferred_location": data.get("preferred_location"),
        "summary": data.get("summary"),
    }
    for field in JSON_FIELDS:
        values[field] = json.dumps(data.get(field) or [])

    conn = get_db_connection()
    try:
        existing = None
        if values["email"]:
            existing = conn.execute(
                "SELECT id FROM students WHERE email = ?", (values["email"],)
            ).fetchone()

        if existing:
            assignments = ", ".join(f"{col} = :{col}" for col in values)
            conn.execute(
                f"UPDATE students SET {assignments}, "
                "updated_at = CURRENT_TIMESTAMP WHERE id = :id",
                {**values, "id": existing["id"]},
            )
            row_id = existing["id"]
        else:
            cols = ", ".join(values)
            placeholders = ", ".join(f":{col}" for col in values)
            cursor = conn.execute(
                f"INSERT INTO students ({cols}) VALUES ({placeholders})", values
            )
            row_id = cursor.lastrowid
        conn.commit()
        return row_id
    finally:
        conn.close()


def get_all_profiles() -> List[Dict[str, Any]]:
    """Return every saved profile, decoding JSON columns back to lists."""
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    finally:
        conn.close()

    profiles: List[Dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        for field in JSON_FIELDS:
            try:
                item[field] = json.loads(item[field]) if item[field] else []
            except (TypeError, json.JSONDecodeError):
                item[field] = []
        profiles.append(item)
    return profiles
