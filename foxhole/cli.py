import argparse
import sqlite3
import sys
from pathlib import Path

from .config import DOCPATH


def list_documents(db: Path = DOCPATH):
    conn = sqlite3.connect(db)
    conn.execute(f"PRAGMA mmap_size = {db.stat().st_size}")
    cursor = conn.cursor()
    cursor.execute("SELECT id, url, title, text FROM pages;")
    for row in cursor.fetchall():
        clean_text = row[3].replace("\n", "")
        sys.stdout.buffer.write(
            f"{row[0]}\t{row[1]}\t{row[2]}\t{clean_text}\n".encode("utf-8")
        )
    conn.close()


def view_document(page_id: str | None = None, db: Path = DOCPATH):
    """list id,url,timestamp for all document in database"""
    if not page_id:
        if len(sys.argv) != 2:
            print("Usage: foxhole-show <id>", file=sys.stderr)
            sys.exit(1)
        page_id = sys.argv[1]
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pages WHERE id=?", (page_id,))
    for row in cursor:  # NOTE: should only happen once, but whatever
        print(row)
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="CLI interface for foxhole")
    parser.add_argument("-k", default=10, type=int, help="number of results;default 10")
    parser.add_argument("query", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    query = " ".join(f'"{t}"' if " " in t else t for t in args.query)
    if not query:
        raise ValueError("ERR: query can't be empty")

    with (conn := sqlite3.connect(DOCPATH)):
        cursor = conn.cursor()
        res = cursor.execute(
            """
            SELECT pages.id, pages.url, pages.title
            FROM pages_fts
            JOIN pages ON pages_fts.rowid = pages.id
            WHERE pages_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """,
            (query, args.k),
        )
        for row in res:
            print(f"{row[0]}\t{row[1]}\t{row[2]}")


if __name__ == "__main__":
    main()
