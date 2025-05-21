import argparse
from collections import defaultdict
import json
import sqlite3
from pathlib import Path

def create_xrels(annotations: Path, out: Path):
    conn = sqlite3.connect(annotations)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    qrels = defaultdict(dict)
    cur.execute("SELECT * FROM annotations;")
    for ann in cur.fetchall():
        qrels[ann["query"]][ann["id"]] = ann["label"]
    with open(out, "w") as f:
        json.dump(qrels, f)
    conn.close()
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        type=Path,
        help="Path to annotations file",
        required=True,
    )
    parser.add_argument(
        "-o",
        type=Path,
        help="Path to output xrel file",
        required=True,
    )
    args = parser.parse_args()
    create_xrels(args.i, args.o)