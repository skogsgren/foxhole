"""evaluation.py"""
from collections import defaultdict
import json
from pathlib import Path
from ir_measures import Measure, calc_aggregate, Qrel, nDCG, MAP, Precision, Recall


class Evaluation:
    """A class to evaluate the performance of a retrieval system using various IR metrics.
    """

    def __init__(self, qrels_path: Path, annotation_pool_path: Path):
        """Initializes the Evaluation class with the paths to the qrels and annotation pool files."""
        self.qrels = self._load_qrels(qrels_path)
        self.runs = self._extract_runs(annotation_pool_path)

    def _load_qrels(self, path: Path) -> dict:
        """Loads the qrels from a JSON file."""
        with open(path, "r") as f:
            return json.load(f)

    def _extract_runs(self, path: Path) -> dict[str, dict[str, float]]:
        """Builds run dict per system: system_name -> {query -> {doc_id: score}}"""
        with open(path, "r") as f:
            pool = json.load(f)

        systems = defaultdict(lambda: defaultdict(dict))
        for entry in pool:
            query = entry["query"]
            doc_id = str(entry["id"])
            for system, metadata in entry["sources"].items():
                systems[system][query][doc_id] = float(metadata["score"])
        return systems


    def evaluate(self, metrics: list) -> dict[str, dict[str, float]]:
        """Evaluates the runs using the provided metrics."""
        results = {}
        for system, run in self.runs.items():
            scores = calc_aggregate(metrics, self.qrels, run)
            results[system] = {str(metric): score for metric, score in scores.items()}
        return results


