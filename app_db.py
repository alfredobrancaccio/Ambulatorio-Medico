import os
from pathlib import Path
import sqlite3

BASE_DIR    = Path(__file__).resolve().parent
RUNTIME_DIR = BASE_DIR / "runtime"
DB_PATH     = RUNTIME_DIR / "ambulatorio.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"
SEED_PATH   = BASE_DIR / "seed.sql"

INTEGRITY_ERRORS = (sqlite3.IntegrityError,)


def init_db(reset=False):
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
    if DB_PATH.exists():
        return
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.executescript(SEED_PATH.read_text(encoding="utf-8"))
        conn.commit()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def query(sql, params=()):
    with get_db() as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def query_one(sql, params=()):
    with get_db() as conn:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row is not None else None


def execute(sql, params=()):
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
