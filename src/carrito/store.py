"""SQLite preparado: el alumnado no tiene que escribir un ORM."""

import json
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DATE = date(2026, 9, 20)


def create_store(path: str = ":memory:") -> sqlite3.Connection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY, name TEXT, category TEXT,
            price_cents INTEGER, description TEXT, returnable INTEGER);
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY, user_id TEXT, product_id TEXT,
            status TEXT, delivered_at TEXT);
        CREATE TABLE IF NOT EXISTS return_requests (
            request_id INTEGER PRIMARY KEY, order_id TEXT UNIQUE,
            user_id TEXT, reason TEXT, requested_at TEXT);
    """)
    for table in ("products", "orders"):
        rows = json.loads((ROOT / "data" / f"{table}.json").read_text())
        for row in rows:
            columns = ",".join(row)
            placeholders = ",".join("?" for _ in row)
            db.execute(
                f"INSERT OR IGNORE INTO {table} ({columns}) VALUES ({placeholders})",
                list(row.values()),
            )
    db.commit()
    return db
