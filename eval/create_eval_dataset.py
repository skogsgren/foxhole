import argparse
import sqlite3
from pathlib import Path

from foxhole.config import DOCPATH, VECPATH
from foxhole.search import TFIDFSearchEngine


def main(
    query_file: Path, output_file: Path, vec_path: Path, doc_path: Path, k: int = 30
):
    pass
    # read query file
    queries = query_file.read_text().splitlines(keepends=False)
    # read document database
    conn = sqlite3.connect(doc_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # initialize IR-systems
    tfidf = TFIDFSearchEngine()
    tfidf.load_db(doc_path)
    IR = {
        "TFIDF": tfidf,
        # TODO: initialize semantic search system
    }
    # initialize output database
    output_conn = sqlite3.connect(output_file)
    out_cur = output_conn.cursor()
    out_cur.execute("""
        CREATE TABLE IF NOT EXISTS results (
            query TEXT,
            system TEXT,
            id TEXT,
            title TEXT,
            text TEXT,
            url TEXT,
            rank INTEGER,
            label TEXT
        )
    """)
    output_conn.commit()

    # for each IR system get back top k results
    seen_ids = set()
    for system_label, system in IR.items():
        # TODO: make k exact since duplicates will appear
        # add k to each query for redundancy, in the chance that each result in IR system 1 is also in system 2
        # NOTE: is this desired behavior?
        for query in queries:
            top_k = system.search_db(query=query, top_k=k * 2)
            system_rows = []
            for rank, i in enumerate(top_k):
                if len(system_rows) > k:
                    break
                if (query, i) in seen_ids:
                    continue

                cur.execute("SELECT * FROM pages WHERE id = ?", (str(i),))
                row = dict(cur.fetchone())
                seen_ids.add((query, i))
                system_rows.append(
                    (
                        query,
                        system_label,
                        row["id"],
                        row["title"],
                        row["text"],
                        row["url"],
                        rank + 1,
                        "",
                    )
                )
            out_cur.executemany(
                """
                INSERT INTO results (query, system, id, title, text, url, rank, label)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                system_rows,
            )
            output_conn.commit()
    output_conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--query_file",
        type=Path,
        required=True,
        help="Path to file containing queries, one per line",
    )
    parser.add_argument(
        "--output_file",
        type=Path,
        required=True,
        help="Path to output database file (.db)",
    )
    parser.add_argument(
        "--vec_path",
        type=Path,
        default=VECPATH,
        help=f"Path to vector database, else Foxhole default ({str(VECPATH)})",
    )
    parser.add_argument(
        "--doc_path",
        type=Path,
        default=DOCPATH,
        help=f"Path to document database, else Foxhole default ({str(DOCPATH)})",
    )
    parser.add_argument(
        "-k",
        type=int,
        default=30,
        help="how many results to return for each query.",
    )
    args = parser.parse_args()
    main(args.query_file, args.output_file, args.vec_path, args.doc_path, k=args.k)
