import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen
from pathlib import Path
from tempfile import TemporaryDirectory
from creditflow.api import make_server
from creditflow.generator import generate
from creditflow.pipeline import run

class APITests(unittest.TestCase):
    def test_read_only_endpoints(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source, db = root / "events.jsonl", root / "lake.db"
            generate(source, 20)
            run(source, db, "synthetic-api-test-key")
            server = make_server(db, port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with urlopen(base + "/health") as response:
                    self.assertEqual(json.load(response)["status"], "ok")
                with urlopen(base + "/v1/daily") as response:
                    rows = json.load(response)
                    self.assertEqual(sum(r["applications"] for r in rows), 20)
                    self.assertNotIn("customer_token", json.dumps(rows))
                with urlopen(base + "/") as response:
                    self.assertIn("CreditFlow", response.read().decode())
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + "/v1/silver")
                self.assertEqual(error.exception.code, 404)
            finally:
                server.shutdown()
                thread.join()
                server.server_close()
