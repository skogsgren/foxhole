import sqlite3
import time
from pathlib import Path

import openai


def load_text_to_id_map(content_db_path: Path) -> dict[str, int]:
    """Load document text → ID mapping from the Foxhole content DB."""
    conn = sqlite3.connect(content_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, text FROM pages")
    mapping = {row[1]: row[0] for row in cursor.fetchall()}
    conn.close()
    return mapping


def init_annotation_db(annotation_db_path: Path) -> sqlite3.Connection:
    """Create and return a connection to the annotations DB."""
    conn = sqlite3.connect(annotation_db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS annotations (
            query TEXT,
            id INTEGER,
            label INTEGER
        )
    """)
    conn.commit()
    return conn


def call_llm(query: str, document: str, model: str, system_msg: str) -> int:
    """Send a query + document to the LLM and return a relevance score."""
    prompt = f"Query: {query}\n\nDocument:\n{' '.join(document.split()[:100000])}\n\nRelevance score (0–2)?"

    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        # temperature=0,
    )

    reply = response.choices[0].message.content
    assert reply
    reply = reply.strip()
    try:
        return int(reply[0])
    except Exception:
        print(f"Unexpected reply: {reply}")
        return -1


def annotate_pool(
    pool_items: list[dict],
    text_to_id: dict[str, int],
    annotation_conn: sqlite3.Connection,
    model: str,
    system_msg: str,
    sleep_seconds: float = 1.0,
) -> None:
    """Annotate the (query, document) pairs using an LLM and store in SQLite."""
    cursor = annotation_conn.cursor()

    for i, item in enumerate(pool_items):
        query = item["query"]
        document = item["document"]
        doc_id = text_to_id.get(document)

        if doc_id is None:
            print(f"Missing doc ID for item {i}")
            continue

        score = call_llm(query, document, model, system_msg)
        if score not in [0, 1, 2]:
            print(f"Invalid score for item {i}: {score}")
            continue

        cursor.execute(
            "INSERT INTO annotations (query, id, label) VALUES (?, ?, ?)",
            (query, doc_id, score),
        )
        annotation_conn.commit()

        print(f"Annotated [{i + 1}/{len(pool_items)}] — score: {score}")
        time.sleep(sleep_seconds)
