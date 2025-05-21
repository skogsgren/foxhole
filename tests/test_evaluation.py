from foxhole.evaluation import Evaluator
from pathlib import Path
from ir_measures import nDCG, MAP, Precision, Recall

if __name__ == "__main__":
    from ir_measures import nDCG, MAP
    from ir_measures import evaluate

    eval = Evaluator(Path("xrels.json"))

    tfidf_run = {
        "machine learning": [(42, 0.9), (105, 0.75)],
        "list comprehension": [(200, 0.8), (88, 0.5)],
    }

    eval.add_run("tfidf", tfidf_run)

    results = evaluate(eval.qrels, eval.runs["tfidf"], [nDCG@10, MAP])
    print(results)
