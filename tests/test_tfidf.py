import sqlite3

from foxhole.config import DOCPATH, TEST_QUERIES
from foxhole.search import TFIDFSearchEngine


def test_tf_idf():
    engine = TFIDFSearchEngine()
    engine.load_db(DOCPATH)

    conn = sqlite3.connect(DOCPATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    for query in TEST_QUERIES:
        print(f"= QUERY={query}")
        indices, scores = engine.search_db(query, top_k=50)
        assert indices, scores
        for rank in range(len(indices)):
            idx, score = indices[rank], scores[rank]
            cur.execute("SELECT * FROM pages WHERE id = ?", (str(idx),))
            print(f"{rank + 1}. {cur.fetchone()['url']} — score: {score:.3f}")
        print()
