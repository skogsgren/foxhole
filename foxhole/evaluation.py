import json
from pathlib import Path
from ir_measures import Measure, Run, nDCG, MAP, Precision, Recall



class Evaluation:
    """A class to evaluate the performance of a retrieval system using various IR metrics.
    """

    def __init__(self, qrels_path: Path):
        self.qrels = self._load_qrels(qrels_path)

    def _load_qrels(self, qrels_path: Path) -> dict[str, dict[str, int]]:
        """Load the qrels from a JSON file."""
        with open(qrels_path, 'r') as f:
            qrels = json.load(f)
        return {k: {str(k): v for k, v in v.items()} for k, v in qrels.items()}


    def add_run(self, system_name: str, run_dict: dict[str, list[tuple[int, float]]]): #a tuple of doc_id and score(int or float?) 
        """Convert IR system output to ir_measures.Run format."""
        runs = []
        for query, ranked_docs in run_dict.items():
            for rank, (doc_id, score) in enumerate(ranked_docs, start=1):
                runs.append(Run(query_id=query, doc_id=str(doc_id), rank=rank, score=score))
        self.runs[system_name] = runs

    def evaluate(self, metrics: list[Measure]) -> dict[str, dict[str, float]]:
        """Evaluate the run data using the specified metrics and return the results."""
        pass

