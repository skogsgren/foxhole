import sqlite3

from foxhole.config import DOCPATH, TEST_QUERIES
from foxhole.search import TFIDFSearchEngine
from sklearn.metrics.pairwise import cosine_similarity


def test_tf_idf():
    engine = TFIDFSearchEngine()
    engine.load_db(DOCPATH)

    conn = sqlite3.connect(DOCPATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    for query in TEST_QUERIES:
        print(f"= QUERY={query}")
        results = engine.search_db(query, top_k=50)
        query_vector = engine.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, engine.tfidf_matrix).flatten()
        print("\nTop results:")
        for rank, idx in enumerate(results, 1):
            cur.execute("SELECT * FROM pages WHERE id = ?", (str(idx + 1),))
            row = cur.fetchone()
            score = similarities[idx]
            print(f"{rank}. {row['url']} — score: {score:.3f}")
        print()
