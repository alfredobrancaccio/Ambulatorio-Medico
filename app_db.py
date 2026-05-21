import os
import sqlite3

try:
    import psycopg
    from psycopg.rows import dict_row as _pg_dict_row
except ImportError:
    psycopg = None

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime")
DB_PATH     = os.path.join(RUNTIME_DIR, "ambulatorio.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")
SEED_PATH   = os.path.join(BASE_DIR, "seed.sql")

INTEGRITY_ERRORS = (sqlite3.IntegrityError,)
if psycopg is not None:
    INTEGRITY_ERRORS = INTEGRITY_ERRORS + (psycopg.errors.IntegrityError,)


def _adatta_sql(sql):
    if os.environ.get("DATABASE_URL"):
        return sql.replace("?", "%s")
    return sql


class AmbulatorioDatabase:
    def __init__(self):
        self._conn = None

    def connect(self):
        db_url = os.environ.get("DATABASE_URL")
        if db_url:
            if psycopg is None:
                raise RuntimeError("DATABASE_URL è impostato ma psycopg non è installato.")
            self._conn = psycopg.connect(db_url, row_factory=_pg_dict_row)
        else:
            os.makedirs(RUNTIME_DIR, exist_ok=True)
            self._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self

    def initialize(self, reset=False):
        self.connect()
        db_url = os.environ.get("DATABASE_URL")
        if db_url:
            if reset:
                self._conn.execute(
                    "DROP TABLE IF EXISTS prescrizioni, referti, visite,"
                    " esami, medici, reparti, pazienti CASCADE"
                )
                self._conn.commit()
            with open(SCHEMA_PATH, encoding="utf-8") as f:
                schema = f.read()
            with open(SEED_PATH, encoding="utf-8") as f:
                seed = f.read()
            for stmt in (schema + "\n" + seed).split(";"):
                stmt = stmt.strip()
                if stmt:
                    self._conn.execute(stmt)
            self._conn.commit()
        else:
            if reset:
                self._conn.execute("PRAGMA foreign_keys = OFF")
                for tbl in ("prescrizioni", "referti", "visite",
                            "esami", "medici", "reparti", "pazienti"):
                    self._conn.execute(f"DROP TABLE IF EXISTS {tbl}")
                self._conn.execute("PRAGMA foreign_keys = ON")
                self._conn.commit()
            with open(SCHEMA_PATH, encoding="utf-8") as f:
                schema = f.read()
            with open(SEED_PATH, encoding="utf-8") as f:
                seed = f.read()
            schema = schema.replace("SERIAL", "INTEGER")
            seed_lines = [
                line for line in seed.splitlines()
                if not line.strip().upper().startswith("SELECT SETVAL")
            ]
            self._conn.executescript(schema + "\n" + "\n".join(seed_lines))
        return self

    def query(self, sql, params=()):
        sql = _adatta_sql(sql)
        return [dict(row) for row in self._conn.execute(sql, params).fetchall()]

    def query_one(self, sql, params=()):
        sql = _adatta_sql(sql)
        row = self._conn.execute(sql, params).fetchone()
        return dict(row) if row is not None else None

    def execute(self, sql, params=()):
        sql = _adatta_sql(sql)
        cur = self._conn.execute(sql, params)
        last_id = None
        if "RETURNING" in sql.upper():
            row = cur.fetchone()
            if row is not None:
                last_id = dict(row).get("id")
        if last_id is None:
            last_id = getattr(cur, "lastrowid", None)
        self._conn.commit()
        return last_id
