import argparse
import shutil
import sqlite3
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from langchain_chroma import Chroma
from .config import DATADIR, DOCPATH, IGNORE_LIST, VECPATH


def is_ignored(url):
    netloc = urlparse(url).netloc
    return any(
        netloc == domain or netloc.endswith("." + domain) for domain in IGNORE_LIST
    )


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


def prune_sqlite_by_ignore(db: Path) -> list[int]:
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT rowid, url FROM pages")
    rows = cur.fetchall()
    del_idx = [rowid for rowid, url in rows if is_ignored(url)]
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


def prune_sqlite_by_age(db: Path, older_than_days: int):
    raise NotImplementedError


def prune_sqlite_by_count(db: Path, keep_latest: int):
    raise NotImplementedError


def prune_vec_db(db: Path, **kwargs):
    if kwargs.get("ignore_list"):
        del_rows = prune_vector_by_ignore(db)
    elif n := kwargs.get("older_than_days"):
        del_rows = prune_vector_by_age(db, n)
    elif n := kwargs.get("keep_latest"):
        del_rows = prune_vector_by_count(db, n)
    else:
        raise ValueError(
            "either ignore_list, older_than_days or keep_latest must be specified"
        )
    return del_rows


def prune_vector_by_ignore(db: Path):
    vec_db = Chroma(persist_directory=str(db))
    urls = {
        doc["url"]
        for doc in vec_db.get(include=["metadatas"])["metadatas"]
        if is_ignored(doc["url"])
    }
    if not urls:
        return []
    del_indices = []
    for url in urls:
        del_indices += vec_db.get(where={"url": url}, include=["metadatas"])["ids"]
    if not del_indices:
        return []
    vec_db.delete(ids=del_indices)
    return del_indices


def prune_vector_by_age(db_path: str, older_than_days: int):
    raise NotImplementedError


def prune_vector_by_count(db_path: str, keep_latest: int):
    raise NotImplementedError


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
        "--vec_path",
        required=False,
        default=VECPATH,
        help=f"Path to the document database, otherwise Foxhole default ({VECPATH})",
    )
    parser.add_argument(
        "--skip_backup",
        required=False,
        action="store_true",
        help="by default foxhole-prune creates backups before pruning. If this is not needed, this flag disables it.",
    )
    args = parser.parse_args()

    print("starting foxhole pruning...")
    if not args.skip_backup:
        backup_doc = tempfile.NamedTemporaryFile(
            prefix="foxhole_doc_backup_",
            suffix=".db",
            delete=False,
        ).name
        shutil.copyfile(args.doc_path, backup_doc)
        print(f"created document database backup at {backup_doc}")

        backup_vec = tempfile.mkdtemp(prefix="foxhole_vec_backup_")
        shutil.copytree(args.vec_path, backup_vec, dirs_exist_ok=True)
        print(f"created vector database backup at {backup_vec}")

    del_idx_doc = prune_doc_db(
        args.doc_path,
        older_than_days=args.older_than_days,
        keep_latest=args.keep_latest,
        ignore_list=args.ignore_list,
    )
    print(f"DOCUMENTS > deleted {len(del_idx_doc)} rows from table")
    print(f"DOCUMENTS > deleted row indices: {del_idx_doc}")

    del_idx_vec = prune_vec_db(
        args.vec_path,
        older_than_days=args.older_than_days,
        keep_latest=args.keep_latest,
        ignore_list=args.ignore_list,
    )
    print(f"VECTOR_DB > deleted {len(del_idx_vec)} chunks")
    print(f"VECTOR_DB > deleted chunk indices: {del_idx_vec}")
