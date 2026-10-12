"""Deterministic synthetic events; never uses real customer information."""
import json
import random
from datetime import date, timedelta
from pathlib import Path


def generate(path: Path, count: int = 1000, seed: int = 42) -> None:
    if count < 1:
        raise ValueError("count must be positive")
    rng = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for i in range(count):
            day = date(2026, 1, 1) + timedelta(days=i % 90)
            row = {
                "application_id": f"APP-{i:08d}", "customer_id": f"SYNTH-{i % 300:05d}",
                "updated_at": f"{day}T12:00:00+00:00", "application_date": str(day),
                "amount_eur": rng.randrange(1000, 50001, 100),
                "income_eur": rng.randrange(1500, 10001, 100),
                "term_months": rng.choice([12, 24, 36, 48, 60, 72]),
                "status": rng.choice(["approved", "approved", "rejected", "pending"]),
                "channel": rng.choice(["broker", "direct", "partner"]),
            }
            handle.write(json.dumps(row) + "\n")
