import json
from foxhole.config import DOCPATH, VECPATH
from foxhole.search import TFIDFSearchEngine, ChromaSemanticSearchEngine
from foxhole.eval.annotate import build_annotation_pool

TEST_QUERIES = [
    "machine learning",
    "python type checker",
]


def save_annotation_pool_json() -> None:
    """Save the annotation pool to a JSON file."""
    engines = [
        TFIDFSearchEngine(DOCPATH, VECPATH),
        ChromaSemanticSearchEngine(DOCPATH, VECPATH),
    ]
    for engine in engines:
        engine.load_db()

    output = build_annotation_pool(DOCPATH, engines, TEST_QUERIES)

    with open("annotation_pool.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(output)} annotation pairs to annotation_pool.json")


if __name__ == "__main__":
    save_annotation_pool_json()
