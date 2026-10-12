"""Airflow 3 reference DAG. Install creditflow on workers; use shared persistent storage."""
import os
from datetime import datetime, timezone
from pathlib import Path
from airflow.sdk import DAG, task
from creditflow.pipeline import run, export

with DAG("creditflow_daily", start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
         schedule="@daily", catchup=False, max_active_runs=1,
         default_args={"retries": 2}) as dag:
    @task
    def ingest():
        root = Path(os.environ["CREDITFLOW_DATA_DIR"])
        # Input is supplied externally. Replays are safe; no regenerated input.
        return run(root / "applications.jsonl", root / "creditflow.db",
                   os.environ["CREDITFLOW_TOKEN_KEY"])
    @task
    def publish(metrics):
        root = Path(os.environ["CREDITFLOW_DATA_DIR"])
        export(root / "creditflow.db", root / "products")
        return {"run_id": metrics["run_id"], "published": True}
    publish(ingest())
