from pathlib import Path

from foxhole.eval.metrics import Evaluator
from ir_measures import MAP, nDCG

ANNOTATION_DB_PATH = Path("annotations.db")
ANNOTATION_POOL_PATH = Path("annotation_pool.json")
XRELS_PATH = Path("xrels.json")

if __name__ == "__main__":
    # Load the qrels and annotation pool
    evaluator = Evaluator(XRELS_PATH, ANNOTATION_POOL_PATH)
    results = evaluator.evaluate([nDCG @ 10, MAP])
    # Print the results
    for system, metrics in results.items():
        print(f"System: {system}")
        for metric, value in metrics.items():
            print(f"  {metric}: {value:.4f}")
