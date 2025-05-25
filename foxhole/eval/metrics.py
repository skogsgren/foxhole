import json
import sqlite3
from collections import defaultdict
from pathlib import Path

from ir_measures import calc_aggregate
from sklearn.metrics import cohen_kappa_score


def interannotator_agreement(
    man: Path,
    llm: Path,
    debug_delta: Path | None = None,
) -> float:
    def load_labels(sqlite_path):
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, label FROM annotations")
        data = sorted([(row[0], row[1]) for row in cursor.fetchall()])
        conn.close()
        return [x[1] for x in data], [x[0] for x in data]

    man_labels, man_ids = load_labels(man)
    llm_labels, llm_ids = load_labels(llm)
    assert len(llm_labels) == len(man_labels)
    for i, j in zip(man_ids, llm_ids):
        if i not in llm_ids:
            print(f"{i} in man not llm ({i}, {j})")
        if j not in man_ids:
            print(f"{j} in llm not man ({i}, {j})")

    if debug_delta:
        delta = {
            i: (man_labels[n], llm_labels[n])
            for n, i in enumerate(man_ids)
            if man_labels[n] != llm_labels[n]
        }
        conn = sqlite3.connect(debug_delta)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, url FROM pages;")
        for i, title, url in cursor:
            if i not in delta:
                continue
            print(
                {
                    "id": i,
                    "man_label": delta[i][0],
                    "llm_label": delta[i][1],
                    "title": title,
                    "url": url,
                }
            )

    return cohen_kappa_score(man_labels, llm_labels)


def export_xrels(annotations: Path, out: Path):
    conn = sqlite3.connect(annotations)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    qrels = defaultdict(dict)
    cur.execute("SELECT * FROM annotations;")
    for ann in cur.fetchall():
        qrels[ann["query"]][ann["id"]] = ann["label"]
    with open(out, "w") as f:
        json.dump(qrels, f)
    conn.close()


class Evaluator:
    """A class to evaluate the performance of a retrieval system using various IR metrics."""

    def __init__(self, qrels_path: Path, annotation_pool_path: Path):
        """Initializes the Evaluation class with the paths to the qrels and annotation pool files."""
        self.qrels = self._load_qrels(qrels_path)
        self.runs = self._extract_runs(annotation_pool_path)

    def _load_qrels(self, path: Path) -> dict:
        """Loads the qrels from a JSON file."""
        with open(path, "r") as f:
            return json.load(f)

    def _extract_runs(self, path: Path) -> defaultdict:
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
