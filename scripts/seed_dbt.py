"""Create a dbt seed from the validated local silver product."""
import csv
import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from creditflow.generator import generate
from creditflow.pipeline import run

ROOT = Path(__file__).resolve().parents[1]
(ROOT / "data").mkdir(exist_ok=True)
destination = ROOT / "analytics/seeds/applications.csv"
destination.parent.mkdir(parents=True, exist_ok=True)
with TemporaryDirectory() as temp:
    source, database = Path(temp) / "raw.jsonl", Path(temp) / "lake.db"
    generate(source, 1000)
    run(source, database, "synthetic-dbt-demo-key")
    with closing(sqlite3.connect(database)) as con, destination.open("w", newline="") as handle:
        cursor = con.execute("SELECT application_id, application_date, amount_eur, income_eur, term_months, status, channel FROM silver")
        writer = csv.writer(handle)
        writer.writerow([c[0] for c in cursor.description])
        writer.writerows(cursor)
