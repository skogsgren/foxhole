import sqlite3

from foxhole.config import DOCPATH, VECPATH, TEST_QUERIES
from foxhole.search import ChromaSemanticSearchEngine


def test_chunking():
    ChromaSemanticSearchEngine(DOCPATH, VECPATH).load_db()


def test_chroma_search():
    conn = sqlite3.connect(DOCPATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    se = ChromaSemanticSearchEngine(DOCPATH, VECPATH)
    se.load_db()
    for query in TEST_QUERIES:
        print(f"= QUERY={query}")
        indices, scores = se.search_db(query, top_k=10)
        for rank in range(len(indices)):
            idx, score = indices[rank], scores[rank]
            cur.execute("SELECT * FROM pages WHERE id = ?", (str(idx),))
            print(f"{rank + 1}. {cur.fetchone()['url']} — score: {score:.3f}")
