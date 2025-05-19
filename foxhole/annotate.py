from collections import defaultdict
import sqlite3
from pathlib import Path

import openai

from foxhole.config import DOCPATH
from foxhole.search import SearchEngine, TFIDFSearchEngine, ChromaSemanticSearchEngine#, BM25SearchEngine

#openai.api_key = "..."  #


def build_annotation_pool(
    db_path: Path,
    engines: list[SearchEngine],
    queries: list[str],
    top_k: int = 5,
    engine_names: list[str] | None = None
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
    cursor.execute("SELECT id, text, url FROM pages")
    doc_info = {row[0]: {"text": row[1], "url": row[2]} for row in cursor.fetchall()}
    conn.close()

    # Step 2: Build mapping of (query, text) → set of sources
    pair_to_metadata = defaultdict(lambda: {"sources": {}})

    for engine, name in zip(engines, engine_names):
        for query in queries:
            try:
                doc_ids, _ = engine.search_db(query, top_k=top_k)
                for rank, doc_id in enumerate(doc_ids):
                    info = doc_info.get(doc_id)
                    if info:
                        key = (query, info["text"])
                        pair_to_metadata[key]["sources"][name] = rank + 1  # 1-based
                        pair_to_metadata[key]["url"] = info["url"]
            except Exception as e:
                print(f"Error in engine {name} for query '{query}': {e}")

    # 3: Return output
    output = []
    for (query, text), meta in pair_to_metadata.items():
        output.append({
            "query": query,
            "document": text,
            "url": meta["url"],
            "sources": meta["sources"]
        })

    return output

def call_llm(query: str, doc: str, system_prompt: str) -> int:
    """Call the LLM to get a relevance score for the document.
    Args:
        query: The query string.
        doc: The document string.
        system_prompt: The system prompt for the LLM.
    Returns:
        int: Relevance score (0, 1, or 2).
    """
    prompt = f"Query: {query}\n\nDocument:\n{doc}\n\nWhat is the relevance score (0, 1, or 2)?"

    response = openai.ChatCompletion.create(
        model="o4-mini", # Is this the right model?
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    reply = response["choices"][0]["message"]["content"].strip()

    try:
        return int(reply[0])  # crude parsing
    except:
        print(f"Unexpected response: {reply}")
        return -1