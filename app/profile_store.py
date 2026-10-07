"""
Farmer Profile Store — Persistent storage for farmer onboarding details.
Stores data in both SQLite (for structured queries) and JSON (for easy inspection/export).
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "farmer_profiles.db"
JSON_PATH = DATA_DIR / "farmer_profiles.json"


def _init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS farmer_profiles (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                name TEXT,
                age TEXT,
                gender TEXT,
                farmer_type TEXT,
                has_docs INTEGER,
                language TEXT,
                details_json TEXT
            )
        """)
        conn.commit()


def save_farmer_profile(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Saves or updates a farmer profile in both SQLite and JSON format.
    Returns the saved profile record.
    """
    _init_db()
    now_iso = datetime.now().isoformat()
    profile_id = profile_data.get("id") or str(uuid.uuid4())[:8]

    record = {
        "id": profile_id,
        "created_at": profile_data.get("created_at", now_iso),
        "updated_at": now_iso,
        "name": profile_data.get("name", "Unknown"),
        "age": str(profile_data.get("age", "")),
        "gender": profile_data.get("gender", ""),
        "farmer_type": profile_data.get("farmer_type", ""),
        "has_docs": 1 if profile_data.get("has_docs") in [True, 1, "yes", "Yes"] else 0,
        "language": profile_data.get("language", "English"),
        "details_json": json.dumps(profile_data, ensure_ascii=False)
    }

    # 1. Save to SQLite
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO farmer_profiles (
                id, created_at, updated_at, name, age, gender, farmer_type, has_docs, language, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                updated_at=excluded.updated_at,
                name=excluded.name,
                age=excluded.age,
                gender=excluded.gender,
                farmer_type=excluded.farmer_type,
                has_docs=excluded.has_docs,
                language=excluded.language,
                details_json=excluded.details_json
        """, (
            record["id"],
            record["created_at"],
            record["updated_at"],
            record["name"],
            record["age"],
            record["gender"],
            record["farmer_type"],
            record["has_docs"],
            record["language"],
            record["details_json"]
        ))
        conn.commit()

    # 2. Save to JSON file as an array of profiles
    existing_list = []
    if JSON_PATH.exists():
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                existing_list = json.load(f)
        except Exception:
            existing_list = []

    # Update if id matches, otherwise append
    updated = False
    for i, item in enumerate(existing_list):
        if item.get("id") == profile_id:
            existing_list[i] = {**item, **profile_data, "id": profile_id, "updated_at": now_iso}
            updated = True
            break
    if not updated:
        clean_entry = {**profile_data, "id": profile_id, "created_at": record["created_at"], "updated_at": now_iso}
        existing_list.append(clean_entry)

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(existing_list, f, indent=2, ensure_ascii=False)

    return record


def get_all_profiles() -> List[Dict[str, Any]]:
    """Retrieve all stored farmer profiles."""
    if not JSON_PATH.exists():
        return []
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def get_latest_profile() -> Optional[Dict[str, Any]]:
    """Retrieve the most recently registered farmer profile."""
    profiles = get_all_profiles()
    return profiles[-1] if profiles else None
