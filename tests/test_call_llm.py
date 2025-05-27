import json
from pathlib import Path
from foxhole.eval.llm import annotate_pool, load_text_to_id_map, init_annotation_db
from foxhole.config import DOCPATH

# Configurable paths
CONTENT_DB_PATH = Path(DOCPATH)
ANNOTATION_DB_PATH = Path("tests/annotations.db")# Feel free to update paths..
ANNOTATION_POOL_PATH = Path("tests/annotation_pool.json")
LLM_MODEL = "gpt-3.5-turbo"  # We will use some other model later
SYSTEM_PROMPT = (
    "You are an expert assessor following TREC-style relevance guidelines. "
    "Please assess how relevant the following document is to the given query."
)
if __name__ == "__main__":
    # Load data
    #text_to_id = load_text_to_id_map(CONTENT_DB_PATH)
    conn = init_annotation_db(ANNOTATION_DB_PATH)

    with open(ANNOTATION_POOL_PATH) as f:
        items = json.load(f)

    # Annotate
    annotate_pool(
        pool_items=items,
        #text_to_id=text_to_id,
        annotation_conn=conn,
        model=LLM_MODEL,
        system_msg=SYSTEM_PROMPT,
        sleep_seconds=1.0,
    )

    conn.close()
