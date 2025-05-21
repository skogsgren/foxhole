import json
from pathlib import Path
from ir_measures import Measure, nDCG, MAP, Precision, Recall



class Evaluator:
    """A class to evaluate the performance of a retrieval system using various IR metrics.
    """

    def __init__(qrels_path: Path):
        pass

    def add_run(system_name: str, run_data: dict[str, list[tuple[str, int]]]): #a tuple of doc_id and score
        """Add a run to the evaluator."""
        pass

    def evaluate(metrics: list[Measure]) -> dict[str, dict[str, float]]:
        """Evaluate the run data using the specified metrics and return the results."""
        pass
