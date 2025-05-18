"""search.py"""

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

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"


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
        self.tfidf_matrix = self.vectorizer.fit_transform(x.lower() for x in self.docs)

    def search_db(self, query: str, top_k: int = 5) -> tuple[list[int], list[float]]:
        """Search the index for the query, return list of URLs or IDs"""
        if self.tfidf_matrix is None:
            raise ValueError("TF-IDF matrix not initialized. Did you call load_db()?")
        query_vector = self.vectorizer.transform([query.lower()])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        top_indices = similarities.argsort()[::-1][:top_k]
        # we have to add one since sqlite indexes from 1
        return [i + 1 for i in top_indices], similarities[top_indices]

    def __repr__(self) -> str:
        return f"<TFIDFSearchEngine: {len(self.docs)} documents indexed>"
    
class BM25SearchEngine(SearchEngine):
    """BM25 Search Engine"""
    def __init__(self):
        #pip install rank_bm25
        from rank_bm25 import BM25Plus #BM25 BM250kapi BM25L BM25Plus
        self.urls = []

    def load_db(self, db_path: Path):
        # read database
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        res = cursor.execute("SELECT url, text FROM pages")
        if res.fetchone() is None:
            raise ValueError("No documents for ChromaSemanticSearch found.")
        self.urls, docs = zip(*res.fetchall())
        connection.close()

        tokenized_docs = [re.findall(r"[\w']+", doc.strip()) for doc in docs]
        self.bm25 = BM25Plus(tokenized_docs)

    def search_db(self, query:str, top_k:int=5):
        if self.urls == []:
            raise ValueError("No corpus documents found. Did you call load_db()?")
        # tokenize the query and return top urls
        tokenized_query = re.findall(r"[\w']+", query.strip())
        results = self.bm25.get_top_n(tokenized_query, self.urls, n=top_k)
        return results

    def __repr__(self) -> str:
        return f"<BM25SearchEngine: {len(self.urls)} documents indexed>"

class ChromaSemanticSearchEngine(SearchEngine):
    """Chroma Semantic Search Engine"""

    def __init__(self):
        import chromadb

        cc = chromadb.Client()
        self.collection = cc.get_or_create_collection(name="my_webpages")

    def load_db(self, db_path: Path):
        # read database
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        res = cursor.execute("SELECT url, text FROM pages")
        if res.fetchone() is None:
            raise ValueError("No documents for ChromaSemanticSearch found.")
        urls, docs = zip(*res.fetchall())
        connection.close()

        # add database documents to the collection
        self.collection.upsert(docs, urls)  # or add

    def search_db(self, query: str, top_k: int = 5):
        # throw a warning for empty collections?
        results = self.collection.query(query_texts=[query], n_results=top_k)

        return results
    
    def __repr__(self) -> str:
        return f"<ChromaSemanticSearchEngine: {self.collection.count()} documents indexed>"