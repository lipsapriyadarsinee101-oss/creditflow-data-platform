"""Reproducible local throughput measurement; outputs actual measured timings."""
import argparse
import json
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from creditflow.generator import generate
from creditflow.pipeline import run

parser = argparse.ArgumentParser()
parser.add_argument("--rows", type=int, default=100000)
args = parser.parse_args()
with TemporaryDirectory() as folder:
    source, database = Path(folder) / "events.jsonl", Path(folder) / "lake.db"
    generate(source, args.rows)
    timings = {}
    for label in ("initial", "replay"):
        start = time.perf_counter()
        stats = run(source, database, "synthetic-benchmark-key")
        elapsed = time.perf_counter() - start
        timings[label] = {"seconds": round(elapsed, 3), "rows_per_second": round(args.rows / elapsed), "changed": stats["changed"]}
    print(json.dumps({"rows": args.rows, "timings": timings}, indent=2))
