"""search_engine.py"""

import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SearchEngine(ABC):
    @abstractmethod
    def load_db(self, db_path: Path) -> None:
        """Load and index content from a SQLite database"""
        pass

    @abstractmethod
    def search_db(self, query: str, top_k: int = 5) -> tuple[list[int], list[float]]:
        """Search the index for the query, return a tuple[indices, scores]"""
        pass


class TFIDFSearchEngine(SearchEngine):
    def __init__(self) -> None:
        """Initialize the TF-IDF search engine"""
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = None
        self.docs = []  # full text
        self.urls = []  # for return
        self.db_path = None

    def load_db(self, db_path: Path) -> None:
        """Load and index content from a SQLite database"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT url, text FROM pages")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            raise ValueError("No documents found.")

        self.urls, self.docs = zip(*rows)
        self.tfidf_matrix = self.vectorizer.fit_transform(self.docs)

    def search_db(self, query: str, top_k: int = 5) -> tuple[list[int], list[float]]:
        """Search the index for the query, return list of URLs or IDs"""
        if self.tfidf_matrix is None:
            raise ValueError("TF-IDF matrix not initialized. Did you call load_db()?")
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        top_indices = similarities.argsort()[::-1][:top_k]
        # we have to add one since sqlite indexes from 1
        return [i + 1 for i in top_indices], similarities[top_indices]


class BM25SearchEngine(SearchEngine):
    """BM25 Search Engine"""

    # TODO: Implement


class ChromaSemanticSearchEngine(SearchEngine):
    """Chroma Semantic Search Engine"""

    # TODO: Implement
