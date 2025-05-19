import sqlite3

import sqlite3
from foxhole.config import DOCPATH#, TEST_QUERIES #Added my own queries
from foxhole.search import TFIDFSearchEngine, ChromaSemanticSearchEngine#, BM25SearchEngine
from foxhole.annotate import build_annotation_pool 

TEST_QUERIES= ["machine learning", "gryningsräder", "list comprehension", "Python programming"]

def test_build_annotation_pool():
    # Set up and load all engines
    engines = [
        TFIDFSearchEngine(),
        #"bm25": BM25SearchEngine(),
        ChromaSemanticSearchEngine(),
    ]

    for engine in engines:
        print(engine)
        engine.load_db(DOCPATH)

    # Generate annotation pool
    pairs = build_annotation_pool(DOCPATH, engines, TEST_QUERIES, top_k=5)

    assert pairs, "No (query, text) pairs were generated."

    # Optional: inspect results
    print(f"\nGenerated {len(pairs)} unique (query, text) pairs for annotation.\n")
    for i, (query, text) in enumerate(pairs[:5]):
        print(f"{i+1}. QUERY: {query}\n   TEXT: {text[:150]}...\n")

if __name__ == "__main__":
    test_build_annotation_pool()