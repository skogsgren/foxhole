#!/usr/bin/env python3
import sys
import struct
import json
import sqlite3
import os

from config import DATADIR, DOCPATH


def read_message():
    raw = sys.stdin.buffer.read(4)
    if not raw:
        return None
    length = struct.unpack("=I", raw)[0]
    return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))


def write_response(msg):
    encoded = json.dumps(msg).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("=I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def main():
    os.makedirs(DATADIR, exist_ok=True)
    conn = sqlite3.connect(DOCPATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY,
        title TEXT,
        text TEXT,
        url TEXT UNIQUE,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    msg = read_message()
    if msg and "title" in msg and "text" in msg and "url" in msg:
        conn.execute(
            "INSERT OR IGNORE INTO pages (title, text, url) VALUES (?, ?, ?)",
            (msg["title"], msg["text"], msg["url"]),
        )
        conn.commit()
        write_response({"status": "ok"})
    else:
        write_response({"status": "error"})
    conn.close()


if __name__ == "__main__":
    main()
