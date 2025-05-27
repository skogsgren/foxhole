import sqlite3
import time
from pathlib import Path

import openai


ANNOTATE_FUNC = {
    "type": "function",
    "function": {
        "name": "annotate_relevance",
        "description": "Assign a relevance score and explanation for a query-document pair.",
        "parameters": {
            "type": "object",
            "properties": {
                "score": {
                    "type": "integer",
                    "enum": [0, 1, 2],
                    "description": "The relevance score: 0 = not relevant, 1 = somewhat relevant, 2 = highly relevant."
                },
                "explanation": {
                    "type": "string",
                    "description": "A short explanation of why this score was chosen."
                }
            },
            "required": ["score", "explanation"]
        }
    }
}

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
            label INTEGER,
            explanation TEXT 
        )
    """) #Added explanation field to store LLM's reasoning - for manual update of schema: ALTER TABLE annotations ADD COLUMN explanation TEXT;
    conn.commit()
    return conn


def call_llm(query: str, document: str, model: str, with_explanation: bool = False) -> tuple[int, str]:
    """Send a query + document to the LLM and return a relevance score (and explanation if requested)
    using a function call to get structured .json output."""
    prompt = f"Query: {query}\n\nDocument:\n{document[:10000]}"

    if with_explanation:
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            tools=[ANNOTATE_FUNC],
            tool_choice="auto",
        )
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            args = tool_calls[0].function.arguments
            import json
            parsed = json.loads(args)
            return int(parsed["score"]), parsed["explanation"]
        return -1, "No tool call returned"

    # Simple scalar response mode (score only)
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    reply = response.choices[0].message.content.strip()
    try:
        return int(reply[0]), None
    except:
        print(f"Unexpected reply: {reply}")
        return -1, reply

def annotate_pool(
    pool_items: list[dict],
    annotation_conn: sqlite3.Connection,
    model: str,
    system_msg: str,
    with_explanation: bool = False,
    sleep_seconds: float = 1.0,
) -> None:
    """Annotate (query, document) pairs using an LLM and store in SQLite."""
    cursor = annotation_conn.cursor()

    for i, item in enumerate(pool_items):
        query = item["query"]
        document = item["document"]
        doc_id = item["id"]

        score, explanation = call_llm(query, document, model, with_explanation)

        if score not in [0, 1, 2]:
            print(f"Invalid score for item {i}: {score}")
            continue

        if with_explanation:
            cursor.execute(
                "INSERT INTO annotations (query, id, label, explanation) VALUES (?, ?, ?, ?)",
                (query, doc_id, score, explanation)
            )
        else:
            cursor.execute(
                "INSERT INTO annotations (query, id, label) VALUES (?, ?, ?)",
                (query, doc_id, score)
            )

        annotation_conn.commit()
        print(f"Annotated [{i + 1}/{len(pool_items)}] — score: {score}")
        time.sleep(sleep_seconds)
