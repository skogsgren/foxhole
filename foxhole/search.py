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
    def __init__(self):
        import chromadb
        #pip install git+https://github.com/brandonstarxel/chunking_evaluation.git
        #this repo served also as source for the _chunker_to_collection() function
        self.my_embedding_function = chromadb.utils.embedding_functions.SentenceTransformersEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
                )
        #my_embedding_function = chromadb.utils.embedding_functions.OpenAIEmbeddingFunction(
        #        api_key="OPENAI_API_KEY",
        #        model_name="text-embedding-3-large"
        #        )
        self.collection_name = "my_webpages"
        #cc = chromadb.Client()
        #self.collection = cc.get_or_create_collection(name=self.collection_name)
        from chunking_evaluation import ClusterSemanticChunker
        self.my_chunker = ClusterSemanticChunker(self.my_embedding_function, max_chunk_size = 200)

    def _chunker_to_collection(self, chunker, embedding_function, chroma_db_path:str = None, collection_name:str = None):
        collection = None

        if chroma_db_path is not None:
            try:
                chunk_client = chromadb.PersistentClient(path=chroma_db_path)
                collection = chunk_client.create_collection(collection_name, embedding_function=embedding_function, metadata={"hnsw:search_ef":50})
                print("Created collection: ", collection_name)
            except Exception as e:
                print("Failed to create collection: ", e)
                pass
                # This shouldn't throw but for whatever reason, if it does we will default to below.

        collection_name = "auto_chunk"
        if collection is None:
            try:
                self.chroma_client.delete_collection(collection_name)
            except ValueError as e:
                pass
            collection = self.chroma_client.create_collection(collection_name, embedding_function=embedding_function, metadata={"hnsw:search_ef":50})

        docs, metas = self._get_chunks_and_metadata(chunker)

        BATCH_SIZE = 500
        for i in range(0, len(docs), BATCH_SIZE):
            batch_docs = docs[i:i+BATCH_SIZE]
            batch_metas = metas[i:i+BATCH_SIZE]
            batch_ids = [str(i) for i in range(i, i+len(batch_docs))]
            collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )

            # print("Documents: ", batch_docs)
            # print("Metadatas: ", batch_metas)

        return collection

    def load_db(self, db_path:Path):
        # read database
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        res = cursor.execute("SELECT url, text FROM pages")
        if res.fetchone() is None:
            raise ValueError("No documents for ChromaSemanticSearch found.")
        urls, docs = zip(*res.fetchall())
        connection.close()

        # add database documents to the collection
        #self.collection.upsert(docs, urls) # or add
        try:
            cc = chromadb.PersistentClient(path=db_path)
            self.collection = cc.get_collection(name=self.collection_name, embedding_function=self.my_embedding_function)
        except:
            self.collection = self._chunker_to_collection(self.my_chunker, self.my_embedding_function, chroma_db_path=db_path, collection_name=self.collection_name)
        if self.collection is None:
            self.collection = self._chunker_to_collection(self.my_chunker, self.my_embedding_function)


    def search_db(self, query:str, top_k:int=5):
        # throw a warning for empty collections?
        results = self.collection.query(query_texts=[query], n_results=top_k)

        return results
