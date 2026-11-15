import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data/career_companion.db")


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                preferred_role TEXT,
                preferred_location TEXT,
                resume_filename TEXT,
                resume_filepath TEXT,
                raw_resume_text TEXT,
                structured_profile_json TEXT,
                created_at TEXT
            )
        """)
        conn.commit()


def save_student_profile(
    full_name: str,
    email: str,
    preferred_role: str,
    preferred_location: str,
    resume_filename: str,
    resume_filepath: str,
    raw_text: str,
    structured_profile: dict,
) -> dict:
    init_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO students (
                full_name, email, preferred_role, preferred_location,
                resume_filename, resume_filepath, raw_resume_text,
                structured_profile_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                full_name=excluded.full_name,
                preferred_role=excluded.preferred_role,
                preferred_location=excluded.preferred_location,
                resume_filename=excluded.resume_filename,
                resume_filepath=excluded.resume_filepath,
                raw_resume_text=excluded.raw_resume_text,
                structured_profile_json=excluded.structured_profile_json,
                created_at=excluded.created_at
            """,
            (
                full_name,
                email,
                preferred_role,
                preferred_location,
                resume_filename,
                resume_filepath,
                raw_text,
                json.dumps(structured_profile),
                now_iso,
            ),
        )
        conn.commit()

    return {
        "full_name": full_name,
        "email": email,
        "preferred_role": preferred_role,
        "preferred_location": preferred_location,
        "resume_filename": resume_filename,
        "structured_profile": structured_profile,
        "created_at": now_iso,
    }


def get_all_students() -> list[dict]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM students ORDER BY created_at DESC").fetchall()
        results = []
        for row in rows:
            item = dict(row)
            item["structured_profile"] = json.loads(item.pop("structured_profile_json") or "{}")
            results.append(item)
        return results