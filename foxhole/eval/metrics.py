import sqlite3
from pathlib import Path

from sklearn.metrics import cohen_kappa_score


def interannotator_agreement(man: Path, llm: Path) -> float:
    def load_labels(sqlite_path):
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        cursor.execute("SELECT label FROM annotations")
        labels = [row[0] for row in cursor.fetchall()]
        conn.close()
        return labels

    man_labels = load_labels(man)
    llm_labels = load_labels(llm)
    assert len(llm_labels) == len(man_labels)
    return cohen_kappa_score(man_labels, llm_labels)
