from utils import _create_dummy_pages_table

from foxhole.cli import list_documents


def test_list_documents_outputs_expected_format(tmp_path, capsys):
    db = tmp_path / "test.db"
    _create_dummy_pages_table(db, [("1", "http://x", "Title", "Text\nLine")])
    list_documents(db)
    out = capsys.readouterr().out
    assert "1\thttp://x\tTitle\tTextLine" in out
