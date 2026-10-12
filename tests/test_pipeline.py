import json
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path
from creditflow.generator import generate
from creditflow.pipeline import run, export
from creditflow.contracts import validate

KEY = "synthetic-test-key-do-not-use-in-production"


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source, self.db = self.root / "input.jsonl", self.root / "lake.db"
        generate(self.source, 100)

    def scalar(self, query):
        with closing(sqlite3.connect(self.db)) as con:
            return con.execute(query).fetchone()[0]

    def write(self, rows):
        self.source.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")

    def row(self):
        return json.loads(self.source.read_text().splitlines()[0])

    def test_replay_is_idempotent(self):
        first = run(self.source, self.db, KEY)
        second = run(self.source, self.db, KEY)
        self.assertEqual(first["changed"], 100)
        self.assertEqual(second["changed"], 0)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM bronze"), 100)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM silver"), 100)

    def test_out_of_order_update(self):
        row = self.row()
        newer = dict(row, updated_at="2026-05-01T12:00:00+00:00", status="approved")
        older = dict(row, status="rejected")
        self.write([newer, older])
        run(self.source, self.db, KEY)
        self.assertEqual(self.scalar("SELECT status FROM silver"), "approved")

    def test_equal_time_conflict_is_order_independent(self):
        row = self.row()
        other = dict(row, status="pending")
        self.write([row, other])
        run(self.source, self.db, KEY)
        result = self.scalar("SELECT event_hash FROM silver")
        self.write([other, row])
        run(self.source, self.root / "other.db", KEY)
        with closing(sqlite3.connect(self.root / "other.db")) as con:
            self.assertEqual(result, con.execute("SELECT event_hash FROM silver").fetchone()[0])

    def test_quarantine_and_gate_rollback(self):
        row = self.row()
        self.write([row, dict(row, amount_eur=-1)])
        with self.assertRaisesRegex(ValueError, "Quality gate"):
            run(self.source, self.db, KEY)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM silver"), 0)
        stats = run(self.source, self.db, KEY, 0.5)
        self.assertEqual(stats["rejected"], 1)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM quarantine"), 1)

    def test_pseudonymization_and_key_rotation_guard(self):
        run(self.source, self.db, KEY)
        token = self.scalar("SELECT customer_token FROM silver LIMIT 1")
        self.assertEqual(len(token), 64)
        self.assertNotIn("SYNTH", token)
        with self.assertRaisesRegex(ValueError, "Key change"):
            run(self.source, self.db, KEY + "rotated")

    def test_gold_reconciliation_and_export(self):
        run(self.source, self.db, KEY)
        self.assertEqual(self.scalar("SELECT SUM(applications) FROM gold_daily"), 100)
        self.assertEqual(self.scalar("SELECT SUM(approved) FROM gold_daily"),
                         self.scalar("SELECT COUNT(*) FROM silver WHERE status='approved'"))
        export(self.db, self.root / "products")
        payload = (self.root / "products/gold_daily.json").read_text()
        self.assertNotIn("customer_token", payload)
        self.assertNotIn("customer_id", payload)

    def test_contract_rejects_nan_bool_and_bad_types(self):
        row = self.row()
        for value in (float("nan"), float("inf"), True, "100"):
            self.assertIn("amount_eur_invalid", validate(dict(row, amount_eur=value)))
        self.assertIn("status_invalid", validate(dict(row, status=[])))
        self.assertEqual(validate([]), ["row_not_object"])

    def test_invalid_json_and_empty_input(self):
        self.source.write_text("not json\n")
        stats = run(self.source, self.db, KEY, 1)
        self.assertEqual(stats["rejected"], 1)
        self.source.write_text("")
        with self.assertRaisesRegex(ValueError, "Empty input"):
            run(self.source, self.db, KEY)

    def test_timestamp_normalized_to_utc(self):
        row = self.row()
        self.write([dict(row, updated_at="2026-01-01T14:00:00+02:00")])
        run(self.source, self.db, KEY)
        self.assertEqual(self.scalar("SELECT updated_at FROM silver"), "2026-01-01T12:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
