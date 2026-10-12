"""Transactional bronze/silver/gold pipeline with event replay and quarantine."""
import hashlib
import hmac
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from .contracts import validate

SCHEMA = """
CREATE TABLE IF NOT EXISTS bronze(event_hash TEXT PRIMARY KEY, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS quarantine(event_hash TEXT PRIMARY KEY, reasons TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS silver(
 application_id TEXT PRIMARY KEY, customer_token TEXT NOT NULL,
 updated_at TEXT NOT NULL, application_date TEXT NOT NULL,
 amount_eur REAL NOT NULL, income_eur REAL NOT NULL, term_months INTEGER NOT NULL,
 status TEXT NOT NULL, channel TEXT NOT NULL, event_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, started_at TEXT,
 input_rows INTEGER, accepted INTEGER, rejected INTEGER, changed INTEGER);
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE VIEW IF NOT EXISTS gold_daily AS
 SELECT application_date, channel, COUNT(*) AS applications,
 SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END) AS approved,
 SUM(CASE WHEN status='approved' THEN amount_eur ELSE 0 END) AS approved_volume_eur,
 AVG(amount_eur) AS average_requested_eur,
 1.0 * SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END)/COUNT(*) AS approval_rate
 FROM silver GROUP BY application_date, channel;
CREATE VIEW IF NOT EXISTS gold_features AS
 SELECT application_id, amount_eur/income_eur AS loan_to_monthly_income,
 amount_eur/term_months/income_eur AS principal_payment_to_income,
 term_months, channel FROM silver;
"""


def run(source: Path, database: Path, secret: str, max_reject_ratio: float = 0.05) -> dict:
    if len(secret) < 16:
        raise ValueError("Set a pseudonymization key of at least 16 characters")
    if not 0 <= max_reject_ratio <= 1:
        raise ValueError("max_reject_ratio must be between 0 and 1")
    database.parent.mkdir(parents=True, exist_ok=True)
    stats = {"run_id": str(uuid4()), "input_rows": 0, "accepted": 0, "rejected": 0, "changed": 0}
    started = datetime.now(timezone.utc).isoformat()
    fingerprint = hashlib.sha256(secret.encode()).hexdigest()
    with closing(sqlite3.connect(database)) as con, con:
        con.executescript(SCHEMA)
        existing = con.execute("SELECT value FROM metadata WHERE key='key_fingerprint'").fetchone()
        if existing and existing[0] != fingerprint:
            raise ValueError("Key change requires explicit full rebuild; mixed tokens are forbidden")
        con.execute("INSERT OR IGNORE INTO metadata VALUES ('key_fingerprint', ?)", (fingerprint,))
        with source.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                stats["input_rows"] += 1
                digest = hashlib.sha256(line.strip().encode()).hexdigest()
                con.execute("INSERT OR IGNORE INTO bronze VALUES (?,?)", (digest, line.strip()))
                try:
                    row = json.loads(line)
                    errors = validate(row)
                except json.JSONDecodeError:
                    errors = ["invalid_json"]
                if errors:
                    stats["rejected"] += 1
                    con.execute("INSERT OR IGNORE INTO quarantine VALUES (?,?)", (digest, json.dumps(errors)))
                    continue
                stats["accepted"] += 1
                token = hmac.new(secret.encode(), row["customer_id"].encode(), hashlib.sha256).hexdigest()
                timestamp = datetime.fromisoformat(row["updated_at"]).astimezone(timezone.utc).isoformat()
                cursor = con.execute("""INSERT INTO silver VALUES (?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(application_id) DO UPDATE SET
                    customer_token=excluded.customer_token, updated_at=excluded.updated_at,
                    application_date=excluded.application_date, amount_eur=excluded.amount_eur,
                    income_eur=excluded.income_eur, term_months=excluded.term_months,
                    status=excluded.status, channel=excluded.channel, event_hash=excluded.event_hash
                    WHERE excluded.updated_at > silver.updated_at
                    OR (excluded.updated_at = silver.updated_at AND excluded.event_hash > silver.event_hash)
                    """, (row["application_id"], token, timestamp, row["application_date"],
                          row["amount_eur"], row["income_eur"], row["term_months"],
                          row["status"], row["channel"], digest))
                stats["changed"] += cursor.rowcount
        if not stats["input_rows"]:
            raise ValueError("Empty input: refusing to report a healthy run")
        if stats["rejected"] / stats["input_rows"] > max_reject_ratio:
            raise ValueError("Quality gate failed; batch transaction rolled back")
        con.execute("INSERT INTO runs VALUES (?,?,?,?,?,?)", (stats["run_id"], started, stats["input_rows"], stats["accepted"], stats["rejected"], stats["changed"]))
    return stats


def export(database: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as con, con:
        con.row_factory = sqlite3.Row
        for name in ("gold_daily", "gold_features"):
            rows = con.execute(f"SELECT * FROM {name}").fetchall()
            (destination / f"{name}.json").write_text(json.dumps([dict(r) for r in rows], indent=2), encoding="utf-8")
