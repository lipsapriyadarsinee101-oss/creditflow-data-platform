import argparse
import json
import os
from pathlib import Path
from .generator import generate
from .pipeline import run, export
from .api import serve


def main():
    parser = argparse.ArgumentParser(description="CreditFlow synthetic lending platform")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate")
    gen.add_argument("--output", type=Path, default=Path("data/applications.jsonl"))
    gen.add_argument("--rows", type=int, default=1000)
    ingest = sub.add_parser("run")
    ingest.add_argument("--input", type=Path, default=Path("data/applications.jsonl"))
    ingest.add_argument("--database", type=Path, default=Path("data/creditflow.db"))
    ingest.add_argument("--max-reject-ratio", type=float, default=0.05)
    out = sub.add_parser("export")
    out.add_argument("--database", type=Path, default=Path("data/creditflow.db"))
    out.add_argument("--output", type=Path, default=Path("data/products"))
    api = sub.add_parser("serve")
    api.add_argument("--database", type=Path, default=Path("data/creditflow.db"))
    api.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.command == "generate":
        generate(args.output, args.rows)
    elif args.command == "run":
        print(json.dumps(run(args.input, args.database, os.environ.get("CREDITFLOW_TOKEN_KEY", ""), args.max_reject_ratio)))
    elif args.command == "export":
        export(args.database, args.output)
    else:
        serve(args.database, port=args.port)


if __name__ == "__main__":
    main()
