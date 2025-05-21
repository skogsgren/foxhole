from ir_measures import nDCG, MAP, Precision, Recall
from pathlib import Path


class Evaluator:

    def __init__(qrels_path: Path):
        pass

    def add_run(system_name: str, run_data: dict[str, list[tuple[doc_id, score]]]):
        pass
