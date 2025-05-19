import json
import sqlite3
from foxhole.config import DOCPATH#, TEST_QUERIES #Added my own queries below
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
        
        engine.load_db(DOCPATH)
        print(engine)

    # Generate annotation pool
    pairs = build_annotation_pool(DOCPATH, engines, TEST_QUERIES, top_k=5)

    assert pairs, "No (query, text) pairs were generated."

    #Print results
    print(f"\nGenerated {len(pairs)} unique (query, text) pairs for annotation.\n")
    for i, (query, text) in enumerate(pairs[:5]):
        print(f"{i+1}. QUERY: {query}\n   TEXT: {text[:150]}...\n")
    
def save_annotation_pool_json(output_path="annotation_pool.json"):
    engines = [TFIDFSearchEngine(), ChromaSemanticSearchEngine()]

    for engine in engines:
        engine.load_db(DOCPATH)

    # Build deduplicated (query, text) pairs
    pairs = build_annotation_pool(DOCPATH, engines, TEST_QUERIES, top_k=5)

    # Retrieve URLs for each doc ID from the DB
    import sqlite3
    conn = sqlite3.connect(DOCPATH)
    cursor = conn.cursor()

    output = []
    for query, doc_text in pairs:
        cursor.execute("SELECT url FROM pages WHERE text = ? LIMIT 1", (doc_text,))
        row = cursor.fetchone()
        url = row[0] if row else "UNKNOWN"
        output.append({
            "query": query,
            "document": doc_text,
            "url": url
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(output)} annotation pairs to {output_path}")
    
if __name__ == "__main__":
    #test_build_annotation_pool()
    save_annotation_pool_json()