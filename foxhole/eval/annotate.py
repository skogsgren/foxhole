import json
import sqlite3
import sys
import tkinter as tk
from collections import defaultdict
from pathlib import Path

from ..search import SearchEngine


def annotate_sqlite(inp: Path | dict, out: Path):
    """simple tkinter interface for manual annotation"""
    rows = json.loads(inp.read_text()) if isinstance(inp, Path) else inp
    if not out.exists():
        out_conn = sqlite3.connect(out)
        out_conn.execute("""
            CREATE TABLE annotations (
                query TEXT,
                id INTEGER,
                label INTEGER,
                annotation_id INTEGER PRIMARY KEY AUTOINCREMENT
        )""")
        out_conn.commit()
        out_conn.close()
    output_conn = sqlite3.connect(out)
    output_conn.row_factory = sqlite3.Row
    output_cur = output_conn.cursor()
    output_cur.execute("SELECT query, id FROM annotations")

    existing_keys = set((r["query"], r["id"]) for r in output_cur.fetchall())
    filtered_rows = [r for r in rows if (r["query"], r["id"]) not in existing_keys]
    filtered_rows = sorted(filtered_rows, key=lambda x: x["query"])
    if not filtered_rows:
        print("no rows left to annotate!")
        return

    current = {"index": 0}

    def next_entry(label):
        row = dict(filtered_rows[current["index"]])
        output_cur.execute(
            """
            INSERT INTO annotations (query, id, label)
            VALUES (?, ?, ?)
            """,
            (row["query"], int(row["id"]), int(label)),
        )
        output_conn.commit()
        current["index"] += 1
        if current["index"] >= len(filtered_rows):
            root.destroy()
            return
        update_display()

    def update_display():
        idx = current["index"]
        id_label.config(text=f"ID: {filtered_rows[idx]['id']}")
        query_label.config(text=f"Query: {filtered_rows[idx]['query']}")
        title_label.config(text=f"Title: {filtered_rows[idx]['title']}")
        text_box.delete(1.0, tk.END)
        text_box.insert(tk.END, filtered_rows[idx]["document"])
        progress_label.config(text=f"{idx} / {len(filtered_rows)}")

    def on_key_press(event):
        if event.char == "0":
            next_entry(0)
        elif event.char == "1":
            next_entry(1)
        elif event.char == "2":
            next_entry(2)

    root = tk.Tk()
    root.title("SQLite Annotator")

    header_frame = tk.Frame(root)
    header_frame.pack(fill="x")

    id_label = tk.Label(header_frame, text="", anchor="w")
    id_label.pack(fill="x")

    query_label = tk.Label(header_frame, text="", anchor="w")
    query_label.pack(fill="x")

    title_label = tk.Label(header_frame, text="", anchor="w")
    title_label.pack(fill="x")

    text_frame = tk.Frame(root)
    text_frame.pack(fill="both", expand=True)

    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")

    text_box = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set)
    text_box.pack(fill="both", expand=True)
    scrollbar.config(command=text_box.yview)

    button_frame = tk.Frame(root)
    button_frame.pack()

    tk.Button(
        button_frame, text="(0) Not relevant", command=lambda: next_entry(0)
    ).pack(side="left")
    tk.Button(button_frame, text="(1) Relevant", command=lambda: next_entry(1)).pack(
        side="left"
    )
    tk.Button(
        button_frame, text="(2) Highly relevant", command=lambda: next_entry(2)
    ).pack(side="left")

    progress_label = tk.Label(root, text="")
    progress_label.pack()

    root.bind("<KeyPress>", on_key_press)

    update_display()

    def on_close():
        root.destroy()
        sys.exit("Annotation prematurely aborted by user.")

    root.protocol("WM_DELETE_WINDOW", on_close)
    try:
        root.mainloop()
    except RuntimeError:
        output_conn.close()
        raise


def build_annotation_pool(
    db_path: Path,
    engines: list[SearchEngine],
    queries: list[str],
    top_k: int = 5,
    engine_names: list[str] | None = None,
) -> list[dict]:
    """Builds a deduplicated list of (query, document, sources) for annotation.
    Args:
        db_path: Path to the SQLite database.
        engines: List of search engines to use for querying.
        queries: List of queries to search for.
        top_k: Number of top results to return from each engine.
        engine_names: Optional list of names for the engines.

    Returns:
        List of dicts with: query, document, url, sources
    """
    if engine_names is None:
        engine_names = [e.__class__.__name__ for e in engines]

    # 1:Load id → (text, url)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, text, url, title FROM pages")
    doc_info = {
        row[0]: {"text": row[1], "url": row[2], "title": row[3]}
        for row in cursor.fetchall()
    }
    conn.close()

    # Step 2: Build mapping of (query, text) → set of sources
    pair_to_metadata = defaultdict(lambda: {"sources": {}})

    for engine, name in zip(engines, engine_names):
        for query in queries:
            try:
                doc_ids, scores = engine.search_db(query, top_k=top_k)
                for rank, (doc_id, score) in enumerate(zip(doc_ids, scores), start=1):
                    info = doc_info[doc_id]
                    key = (query, info["text"])
                    pair_to_metadata[key]["sources"][name] = {
                        "rank": rank,
                        "score": float(score),
                    }  # 1-based
                    pair_to_metadata[key]["url"] = info["url"]
                    pair_to_metadata[key]["title"] = info["title"]
                    pair_to_metadata[key]["id"] = doc_id
            except Exception as e:
                print(f"Error in engine {name} for query '{query}': {e}")

    # 3: Return output
    output = []
    for (query, text), meta in pair_to_metadata.items():
        output.append(
            {
                "query": query,
                "document": text,
                "url": meta["url"],
                "id": meta["id"],
                "title": meta["title"],
                "sources": meta["sources"],
            }
        )

    return output
