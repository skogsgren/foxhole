import json
import os
import sqlite3
import struct
import sys
import tempfile
from urllib.parse import urlparse

import pypdfium2 as pdfium
import requests

from .config import DATADIR, DOCPATH, IGNORE_LIST


def is_ignored(url):
    parsed = urlparse(url)
    netloc = parsed.netloc
    for domain in IGNORE_LIST:
        if netloc == domain:
            return True
        if netloc.endswith("." + domain):
            return True

        parts = parsed.path.split("/")[1:]
        for i in range(len(parts) + 1):
            if domain == netloc + "/" + "/".join(parts[:i]):
                return True

    return False


def parse_pdf_link(msg: dict):
    msg["title"] = msg["url"]

    with requests.get(msg["url"], timeout=30) as r:
        r.raise_for_status()

        with tempfile.NamedTemporaryFile(prefix="foxhole-", suffix=".pdf") as f:
            f.write(r.content)
            f.flush()

            pdf = pdfium.PdfDocument(f.name)
            page_texts = []
            for page in pdf:
                textpage = page.get_textpage()
                page_texts.append(textpage.get_text_range())

            text = " ".join(page_texts)
            text = text.translate(str.maketrans("\r\t\n\ufffe", " " * 4))

    msg["text"] = text
    return msg


def read_message():
    raw = sys.stdin.buffer.read(4)
    if not raw:
        return None
    length = struct.unpack("@I", raw)[0]
    payload = sys.stdin.buffer.read(length)
    msg = json.loads(payload.decode("utf-8"))
    if msg.get("kind") == "pdf":
        return parse_pdf_link(msg)
    return msg


def write_response(msg):
    encoded = json.dumps(msg).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("@I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def main():
    try:
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

        conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
            title, text, content='pages', content_rowid='id'
        )
        """)

        msg = read_message()

        if (
            msg
            and "title" in msg
            and "text" in msg
            and "url" in msg
            and not is_ignored(msg["url"])
        ):
            conn.execute(
                "INSERT OR IGNORE INTO pages (title, text, url) VALUES (?, ?, ?)",
                (msg["title"], msg["text"], msg["url"]),
            )
            conn.commit()

            conn.execute("INSERT INTO pages_fts(pages_fts) VALUES('rebuild')")
            conn.commit()

            write_response({"status": "ok"})
        else:
            write_response({"status": "error", "msg": "invalid or ignored message"})

        conn.close()

    except Exception as e:
        write_response({"status": "error", "msg": str(e)})


if __name__ == "__main__":
    main()
