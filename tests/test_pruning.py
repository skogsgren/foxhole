import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from foxhole.prune import (
    prune_doc_db,
    prune_sqlite_by_age,
    prune_sqlite_by_count,
    prune_sqlite_by_ignore,
)


@pytest.fixture
def dummy_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = Path(tf.name)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE pages (
            url TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    now = datetime.utcnow()
    test_data = [
        ("http://example.com", now),
        ("http://ignored.com", now - timedelta(days=10)),
        ("http://ignored.com/page", now - timedelta(days=20)),
        ("http://keep.com", now - timedelta(days=1)),
        ("http://delete.com", now - timedelta(days=30)),
    ]
    for url, ts in test_data:
        cur.execute(
            "INSERT INTO pages (url, timestamp) VALUES (?, ?)", (url, ts.isoformat())
        )
    conn.commit()
    conn.close()
    yield db_path
    db_path.unlink()


def test_prune_by_ignore(dummy_db):
    ignore_list = ["ignored.com"]
    deleted = prune_sqlite_by_ignore(dummy_db, ignore_list=ignore_list)
    assert sorted(deleted) == [2, 3]
    conn = sqlite3.connect(dummy_db)
    cur = conn.cursor()
    cur.execute("SELECT url FROM pages")
    urls = [row[0] for row in cur.fetchall()]
    conn.close()
    assert "http://ignored.com" not in urls
    assert "http://ignored.com/page" not in urls


def test_prune_by_age(dummy_db):
    deleted = prune_sqlite_by_age(dummy_db, older_than_days=15)
    assert sorted(deleted) == [3, 5]
    conn = sqlite3.connect(dummy_db)
    cur = conn.cursor()
    cur.execute("SELECT url FROM pages")
    urls = [row[0] for row in cur.fetchall()]
    conn.close()
    assert "http://ignored.com/page" not in urls
    assert "http://delete.com" not in urls


def test_prune_by_count(dummy_db):
    deleted = prune_sqlite_by_count(dummy_db, keep_latest=2)
    assert len(deleted) == 3
    conn = sqlite3.connect(dummy_db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM pages")
    remaining = cur.fetchone()[0]
    conn.close()
    assert remaining == 2


def test_prune_doc_db_invalid(dummy_db):
    with pytest.raises(ValueError):
        prune_doc_db(dummy_db)
