from pathlib import Path
from foxhole.evaluation import Evaluation
from foxhole.config import DOCPATH
from ir_measures import nDCG, MAP, Precision, Recall

ANNOTATION_DB_PATH = Path("annotations.db")
ANNOTATION_POOL_PATH = Path("annotation_pool.json")
XRELS_PATH = Path("xrels.json")

if __name__ == "__main__":
    # from ir_measures import nDCG, MAP
    # from ir_measures import evaluate

    # eval = Evaluator(Path("xrels.json"))

    # tfidf_run = {
    #     "machine learning": [(42, 0.9), (105, 0.75)],
    #     "list comprehension": [(200, 0.8), (88, 0.5)],
    # }

    # eval.add_run("tfidf", tfidf_run)

    # results = evaluate(eval.qrels, eval.runs["tfidf"], [nDCG@10, MAP])
    # print(results)



    evaluator = Evaluation(Path(XRELS_PATH), Path(ANNOTATION_POOL_PATH))
    results = evaluator.evaluate([nDCG@10, MAP])

    for system, metrics in results.items():
        print(f"System: {system}")
        for metric, value in metrics.items():
            print(f"  {metric}: {value:.4f}")
