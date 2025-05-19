import time
import json
from foxhole.annotate import call_llm

SYSTEM_PROMPT = "You are an expert annotator trained in TREC-style relevance evaluation." # Or whateever

def annotate_using_llm() -> None:
    """Annotate using LLM and save to JSON."""
    # Load annotation pool
    with open("annotation_pool.json") as f:
        examples = json.load(f)

    annotated = []

    for i, ex in enumerate(examples):
        score = call_llm(ex["query"], ex["document"], SYSTEM_PROMPT)
        annotated.append({**ex, "llm_score": score})

        # Save progress occasionally
        if i % 10 == 0:
            with open("llm_annotated.json", "w") as f_out:
                json.dump(annotated, f_out, indent=2)
            time.sleep(1)  # let the api breathe

if __name__ == "__main__":
    annotate_using_llm()