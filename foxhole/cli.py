import sys
import sqlite3
from pathlib import Path

from .config import DOCPATH, VECPATH
from . import search


def update_chroma_db():
    """updates chroma db in foxhole default location with new documents"""
    se = search.ChromaSemanticSearchEngine(DOCPATH, VECPATH)
    se.load_db()


def list_documents(db: Path = DOCPATH):
    """list id,url,timestamp for all document in database"""
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT id, url, timestamp FROM pages;")
    for row in cursor:
        print(row[0], "\t", row[1], "\t", row[2])
    conn.close()


def view_document(page_id: str | None = None, db: Path = DOCPATH):
    """list id,url,timestamp for all document in database"""
    if not page_id:
        if len(sys.argv) != 2:
            print("Usage: foxhole-show <id>", file=sys.stderr)
            sys.exit(1)
        page_id = sys.argv[1]
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pages WHERE id=?", (page_id,))
    for row in cursor:  # should only happen once, but whatever
        print(row)
    conn.close()


def check_method(search_method: str, search_methods: list):
    if search_method.isdigit():
        search_method = search_methods[int(search_method) - 1]
    method_provided = True
    if search_method not in search_methods:
        raise TypeError("ERROR: Search method must be out of", search_methods)
    return search_method


def select_model(i: int, doc_path, vec_path):
    if i == 1:
        se = search.TFIDFSearchEngine(doc_path, vec_path)
    if i == 2:
        se = search.BM25SearchEngine(doc_path, vec_path)
    if i == 3:
        se = search.ChromaSemanticSearchEngine(doc_path, vec_path)
    return se


def main():
    # get db file name from command line
    try:
        db_path = Path(sys.argv[1])
    except:
        raise TypeError("ERROR: No path provided at all!")

    if not db_path.exists() or db_path.is_dir():
        raise TypeError("ERROR: No valid path to a .db file provided!")
    print("Database file", db_path, "selected.")

    # get vec file name from command line
    try:
        vec_path = Path(sys.argv[2])
        if not vec_path.exists() or vec_path.is_dir():
            raise TypeError("Warning: No valid path to a vec file provided!")
        v = True
    except:
        print("Warning: No 2nd path (to vec) provided!")
        vec_path = None
        v = False  # vector file provided?
    print("Vector file", vec_path, "selected.")

    # try getting optional top_k
    k = False  # top_k provided?
    try:
        if sys.argv[2 + int(v)][:3] == "top":
            top_k = int(sys.argv[2 + int(v)][3:])
            k = True
            print("top_k =", top_k)
    except:
        print("top_k not specified, using default")

    interactive = False

    # select search method to be used
    search_methods = ("TFIDF", "BM25", "ChromaSemantic")
    try:
        search_method = check_method(sys.argv[2 + int(k) + int(v)], search_methods)
        method_provided = True
        print("Search method", search_method, "selected.")
    except:
        # raise TypeError("ERROR: No search method provided!")
        method_provided = False
        interactive = True
        print("No search method selected.")

    if method_provided:
        se = select_model(search_methods.index(search_method) + 1, db_path, vec_path)
        se.load_db()

    # try getting query from command line or start interactive mode
    try:
        _ = sys.argv[3 + int(k) + int(v)]
        query = " ".join(sys.argv[4 + int(k) + int(v) :])
    except:
        interactive = True

    # conduct the search and print the results
    if not interactive:
        print("Searching with method", search_method, "the following query:", query)
        if k:
            result = se.search_db(query, top_k)
        else:
            result = se.search_db(query)
        print("result:\n", result)
    else:  # interactive input loop
        while True:
            if not method_provided:
                user_input = input("Select search method or enter 'q' to quit:\n")
                if user_input == "q":
                    break
                try:
                    search_method = check_method(user_input, search_methods)
                except Exception as e:
                    print(e)
                    continue
                print("Search method", search_method, "selected.")
                se = select_model(
                    search_methods.index(search_method) + 1, db_path, vec_path
                )
                se.load_db()

            user_input = input("Type whatever query or enter 'q' to quit:\n")
            if user_input == "q":
                break
            query = user_input
            print("Searching with method", search_method, "the following query:", query)
            if k:
                result = se.search_db(query, top_k)
            else:
                result = se.search_db(query)
            print("result:\n", result)


if __name__ == "__main__":
    main()
