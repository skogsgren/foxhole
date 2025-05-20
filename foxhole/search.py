"""search.py"""

import re
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
import re

from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_community.document_loaders import SQLDatabaseLoader
from langchain_community.utilities import SQLDatabase
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine
from transformers.models.auto.tokenization_auto import AutoTokenizer

# since 5070-ish is the official limit for chroma, 5000 sounds like a good value
MAX_BATCH = 5000


class SearchEngine(ABC):
    def __init__(self, doc_path: Path, vec_path: Path):
        self.doc_path = doc_path
        self.vec_path = vec_path

    @abstractmethod
    def load_db(self) -> None:
        """Load and index content from a SQLite database"""
        pass

    @abstractmethod
    def search_db(self, query: str, top_k: int = 5) -> tuple[list[int], list[float]]:
        """Search the index for the query, return a tuple[indices, scores]"""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"


class TFIDFSearchEngine(SearchEngine):
    def __init__(self, doc_path: Path, vec_path: Path) -> None:
        super().__init__(doc_path, vec_path)
        """Initialize the TF-IDF search engine"""
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = None
        self.docs = []  # full text
        self.urls = []  # for return
        self.db_path = None

    def load_db(self) -> None:
        """Load and index content from a SQLite database"""
        conn = sqlite3.connect(self.doc_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, url, text FROM pages")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            raise ValueError("No documents found.")

        self.ids, self.urls, self.docs = zip(*rows)
        self.tfidf_matrix = self.vectorizer.fit_transform(x.lower() for x in self.docs)

    def search_db(self, query: str, top_k: int = 5) -> tuple[list[int], list[float]]:
        """Search the index for the query, return list of URLs or IDs"""
        if self.tfidf_matrix is None:
            raise ValueError("TF-IDF matrix not initialized. Did you call load_db()?")
        query_vector = self.vectorizer.transform([query.lower()])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        top_indices = similarities.argsort()[::-1][:top_k]

        return [self.ids[i] for i in top_indices], similarities[top_indices]

    def __repr__(self) -> str:
        return f"<TFIDFSearchEngine: {len(self.docs)} documents indexed>"


class BM25SearchEngine(SearchEngine):
    """BM25 Search Engine"""

    def __init__(self, doc_path: Path, vec_path: Path):
        super().__init__(doc_path, vec_path)

        # #pip install rank_bm25
        # from rank_bm25 import BM25Plus #BM25 BM250kapi BM25L BM25Plus
        self.urls = []
        pass

    def __repr__(self) -> str:
        return f"<BM25SearchEngine: {len(self.urls)} documents indexed>"

    def load_db(self):
        # read database
        connection = sqlite3.connect(self.doc_path)
        cursor = connection.cursor()
        res = cursor.execute("SELECT url, text FROM pages")
        if res.fetchone() is None:
            raise ValueError("No documents for ChromaSemanticSearch found.")
        self.urls, self.docs = zip(*res.fetchall())
        connection.close()

    def search_db(self, query: str, top_k: int = 5):
        if self.urls == []:
            raise ValueError("No corpus documents found. Did you call load_db()?")
        # tokenize the query and return top urls
        tokenized_query = re.findall(r"[\w']+", query.strip())
        results = self.bm25.get_top_n(tokenized_query, self.urls, n=top_k)
        return results


class ChromaSemanticSearchEngine(SearchEngine):
    """Chroma Semantic Search Engine"""

    def __init__(self, doc_path: Path, vec_path: Path):
        super().__init__(doc_path, vec_path)
        self.emb = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            show_progress=False,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    def chunk(self, docs: list[Document]):
        """using RecursiveCharacterTextSplitter splits using model tokenizer"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512
        ).from_huggingface_tokenizer(self.tokenizer)
        return text_splitter.split_documents(docs)

    def _filter_docs(self, docs: list[Document]) -> list[Document]:
        """given documents, returns documents not already in chroma database"""
        db = Chroma(persist_directory=str(self.vec_path), embedding_function=self.emb)
        ids = set([x["id"] for x in db.get()["metadatas"]])
        return [doc for doc in docs if doc.metadata["id"] not in ids]

    def load_db(self):
        """reads document database, creates/updates chroma vector db"""
        docs = SQLDatabaseLoader(
            # TODO: also save timestamp for pruning later
            query="SELECT id,url,text FROM pages;",
            db=SQLDatabase(create_engine(f"sqlite:///{str(self.doc_path)}")),
            page_content_mapper=lambda x: x["text"],
            metadata_mapper=lambda x: {"id": x["id"], "url": x["url"]},
        ).load()
        if self.vec_path.exists():
            docs = self._filter_docs(docs)
        if not docs:
            print("no new documents to add")
            return

        chunks = self.chunk(docs)
        print(f"{len(chunks)} chunks from {len(docs)} documents.")

        start = 0  # dirty trick to deal with batches w/o complex logic
        if self.vec_path.exists():
            db = Chroma(
                persist_directory=str(self.vec_path), embedding_function=self.emb
            )
            print(f"loaded previous vector db with {db._collection.count()}")
        else:
            print("vector db not found. initializing with first batch...")
            db = Chroma.from_documents(
                chunks[:MAX_BATCH], self.emb, persist_directory=str(self.vec_path)
            )
            start += MAX_BATCH

        for i in (steps := list(range(start, len(chunks), MAX_BATCH))):
            # NOTE: progress print is untested, remove if it doesn't work,
            # along with walrus operator above; didn't have time to test
            print(f"{i}/{steps[-1]}")
            db.add_documents(chunks[i : i + MAX_BATCH])

    def search_db(self, query: str, top_k: int = 5) -> tuple[list[int], list[float]]:
        db = Chroma(persist_directory=str(self.vec_path), embedding_function=self.emb)
        # NOTE: we do top_k * 100 to do max_score aggregation for document chunks.
        # TODO: this isn't very good, some kind of pooling would be much better here
        # NOTE: this doesn't guarantee top_k results in the end, should probably be fixed
        chunk_results = db.similarity_search_with_score(query, k=top_k * 100)

        doc_scores = {}
        for chunk, score in chunk_results:
            doc_id = int(chunk.metadata["id"])
            if doc_id not in doc_scores or score < doc_scores[doc_id]:
                doc_scores[doc_id] = score

        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1])[:top_k]

        doc_ids = [doc_id for doc_id, _ in sorted_docs]
        scores = [score for _, score in sorted_docs]

        return doc_ids, scores
