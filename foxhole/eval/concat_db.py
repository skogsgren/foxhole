#!/usr/bin/env/python
__doc__ = """concatenate sqlite files"""

import argparse
import sqlite3
from pathlib import Path


def insert_pages_from_db(src_conn, dest_conn):
    cursor = src_conn.execute("SELECT title, text, url, timestamp FROM pages")
    for row in cursor:
        try:
            dest_conn.execute(
                "INSERT OR IGNORE INTO pages (title, text, url, timestamp) VALUES (?, ?, ?, ?)",
                row,
            )
        except sqlite3.IntegrityError:
            print(f"IntegrityError on {row}")


def main(db_files: list[Path], concat_out: Path):
    if len(db_files) <= 1:
        raise ValueError("At least two database files are required for concatenation.")

    conn = sqlite3.connect(concat_out)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY,
            title TEXT,
            text TEXT,
            url TEXT UNIQUE,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()

    for db_path in db_files:
        with sqlite3.connect(db_path) as src_conn:
            insert_pages_from_db(src_conn, conn)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("input_files", nargs="+")
    args = parser.parse_args()

    main(args.input_files, args.output)
