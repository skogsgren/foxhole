import sys
from pathlib import Path

import pytest
from utils import _create_dummy_pages_table

from foxhole.cli import view_document


def test_view_document_with_id(tmp_path, capsys):
    db = tmp_path / "test.db"
    _create_dummy_pages_table(db, [("42", "http://a", "Title", "Content")])
    view_document("42", db)
    out = capsys.readouterr().out
    assert "42" in out and "http://a" in out


def test_view_document_sys_argv(monkeypatch, tmp_path, capsys):
    db = tmp_path / "test.db"
    _create_dummy_pages_table(db, [("99", "http://z", "TitleZ", "Zcontent")])
    monkeypatch.setattr(sys, "argv", ["script", "99"])
    view_document(None, db)
    out = capsys.readouterr().out
    assert "99" in out


def test_view_document_argv_missing(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["script"])
    with pytest.raises(SystemExit):
        view_document(None, Path("/dev/null"))
