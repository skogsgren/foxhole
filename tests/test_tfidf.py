from sklearn.metrics.pairwise import cosine_similarity

from foxhole.search import TFIDFSearchEngine
from foxhole.config import DOCPATH, TEST_QUERIES


def test_tf_idf():
    engine = TFIDFSearchEngine()
    engine.load_db(DOCPATH)

    for query in TEST_QUERIES:
        results = engine.search_db(query)
        query_vector = engine.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, engine.tfidf_matrix).flatten()
        print("\nTop results:")
        for i, url in enumerate(results, 1):
            index = engine.urls.index(url)
            score = similarities[index]
            print(f"{i}. {url} — score: {score:.3f}")
        print()
