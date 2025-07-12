import argparse
import shutil
import sqlite3
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from .config import DATADIR, DOCPATH, IGNORE_LIST


def is_ignored(url, ignore_list=IGNORE_LIST):
    netloc = urlparse(url).netloc
    for domain in ignore_list:
        if netloc == domain:
            return True
        if netloc.endswith("." + domain):
            return True
        parts = urlparse(url).path.split("/")[1:]
        for i in range(len(parts) + 1):
            if domain == netloc + "/" + "/".join(parts[:i]):
                return True
    return False


def prune_doc_db(db: Path, **kwargs) -> list[int]:
    if kwargs.get("ignore_list"):
        del_rows = prune_sqlite_by_ignore(db)
    elif n := kwargs.get("older_than_days"):
        del_rows = prune_sqlite_by_age(db, n)
    elif n := kwargs.get("keep_latest"):
        del_rows = prune_sqlite_by_count(db, n)
    else:
        raise ValueError(
            "either ignore_list, older_than_days or keep_latest must be specified"
        )
    return del_rows


def prune_sqlite_by_ignore(db: Path, ignore_list=IGNORE_LIST) -> list[int]:
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT rowid, url FROM pages")
    rows = cur.fetchall()
    del_idx = [rowid for rowid, url in rows if is_ignored(url, ignore_list)]
    if not del_idx:
        conn.close()
        return []
    cur.executemany(
        "DELETE FROM pages WHERE rowid = ?",
        [(rid,) for rid in del_idx],
    )
    conn.commit()
    conn.close()
    return del_idx


def prune_sqlite_by_age(db: Path, older_than_days: int) -> list[int]:
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT rowid FROM pages
        WHERE timestamp < datetime('now', ?)
    """,
        (f"-{older_than_days} days",),
    )
    rows = cur.fetchall()
    del_idx = [rowid for (rowid,) in rows]
    if not del_idx:
        conn.close()
        return []
    cur.executemany(
        "DELETE FROM pages WHERE rowid = ?",
        [(rid,) for rid in del_idx],
    )
    conn.commit()
    conn.close()
    return del_idx


def prune_sqlite_by_count(db: Path, keep_latest: int) -> list[int]:
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT rowid FROM pages
        ORDER BY timestamp DESC
        LIMIT -1 OFFSET ?
    """,
        (keep_latest,),
    )
    rows = cur.fetchall()
    del_idx = [rowid for (rowid,) in rows]
    if not del_idx:
        conn.close()
        return []
    cur.executemany(
        "DELETE FROM pages WHERE rowid = ?",
        [(rid,) for rid in del_idx],
    )
    conn.commit()
    conn.close()
    return del_idx


def main():
    parser = argparse.ArgumentParser(
        description="This script prunes entries from the foxhole database."
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--older_than_days",
        type=int,
        help="Delete entries older than the specified number of days",
    )
    group.add_argument(
        "--keep_latest",
        type=int,
        help="Keep only the specified number of most recent entries",
    )

    group.add_argument(
        "--ignore_list",
        action="store_true",
        help=f"Use the ignore list ({DATADIR / 'IGNORE'}) to prune entries",
    )

    parser.add_argument(
        "--doc_path",
        required=False,
        default=DOCPATH,
        help=f"Path to the document database, otherwise Foxhole default ({DOCPATH})",
    )
    parser.add_argument(
        "--skip_backup",
        required=False,
        action="store_true",
        help="foxhole-prune backs up before pruning; this flag disables backups.",
    )
    args = parser.parse_args()

    print("starting foxhole pruning...")
    if not args.skip_backup:
        if args.doc_path.exists():
            backup_doc = tempfile.NamedTemporaryFile(
                prefix="foxhole_doc_backup_",
                suffix=".db",
                delete=False,
            ).name
            shutil.copyfile(args.doc_path, backup_doc)
            print(f"created document database backup at {backup_doc}")
    del_idx_doc = prune_doc_db(
        args.doc_path,
        older_than_days=args.older_than_days,
        keep_latest=args.keep_latest,
        ignore_list=args.ignore_list,
    )
    print(f"DOCUMENTS > deleted {len(del_idx_doc)} rows from table")
    print(f"DOCUMENTS > deleted row indices: {del_idx_doc}")
