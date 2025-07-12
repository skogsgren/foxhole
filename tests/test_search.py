import sqlite3
import sys

import pytest

from foxhole.cli import main


def test_run_query_outputs_expected(tmp_path, capsys):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE VIRTUAL TABLE pages_fts USING fts5(content)")
    conn.execute("CREATE TABLE pages (id TEXT, url TEXT, title TEXT)")
    conn.execute("INSERT INTO pages_fts (rowid, content) VALUES (?, ?)", (1, "test"))
    conn.execute("INSERT INTO pages VALUES (?, ?, ?)", ("1", "http://a", "T"))
    conn.commit()
    conn.close()

    from foxhole.cli import run_query

    run_query("test", 10, db)

    out = capsys.readouterr().out
    assert "1\thttp://a\tT" in out


def test_main_empty_query(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["script"])
    with pytest.raises(ValueError):
        main()
