#!/usr/bin/env python
# FULL BENCHMARK

import csv
import json
import sqlite3
import tempfile
from collections import defaultdict
from pathlib import Path

from ir_measures import MAP, nDCG

from foxhole.eval import llm, metrics
from foxhole.eval.annotate import build_annotation_pool
from foxhole.eval.metrics import Evaluator
from foxhole.search import (
    BM25SearchEngine,
    ChromaSemanticSearchEngine,
    TFIDFSearchEngine,
)

# define constants
DATA = Path("./00-data")
QUERY_PATHS = [DATA / "queries_pilot_full.tsv", DATA / "queries_full.tsv"]
DOCPATH = DATA / "doc.db"
VECPATH = DATA / "vec.chroma"
TOPK = 10

LLM_MODEL = "o4-mini"
PROMPT = (DATA / "prompt.txt").read_text()
SLEEP_SECONDS = 1

(OUT := Path("./03_benchmark")).mkdir(exist_ok=True)
POOL_OUT = OUT / "00_pool.json"
ANN_OUT = OUT / "01_ann.db"
XRELS_OUT = OUT / "02_xrels.json"
METRICS_OUT = OUT / "03_metrics.json"

# load queries
query_type_pairs = []
for p in QUERY_PATHS:
    with open(p) as f:
        rows = csv.DictReader(f, delimiter="\t")
        query_type_pairs += [x for x in rows]
TYPES = set(x["TYPE"] for x in query_type_pairs)
queries = [x["QUERY"] for x in query_type_pairs]
print(f"{queries=}")

print("loading BM-25 system")
bm_engine = BM25SearchEngine(DOCPATH, VECPATH)
bm_engine.load_db()

print("loading ChromaSemantic system")
ch_engine = ChromaSemanticSearchEngine(DOCPATH, VECPATH)
ch_engine.load_db()

print("loading TFIDF system")
tf_engine = TFIDFSearchEngine(DOCPATH, VECPATH)
tf_engine.load_db()

engines = [
    bm_engine,
    ch_engine,
    tf_engine,
]

if not POOL_OUT.exists():
    dataset = build_annotation_pool(DOCPATH, engines, queries, top_k=TOPK)
    with open(POOL_OUT, "w") as f:
        json.dump(dataset, f)
        print(f"saved {len(dataset)} query/document pairs to {POOL_OUT}")
else:
    print("loading cached pool dataset")
    with open(POOL_OUT) as f:
        dataset = json.load(f)

if not ANN_OUT.exists():
    conn = llm.init_annotation_db(ANN_OUT)
    llm.annotate_pool(
        pool_items=dataset,
        annotation_conn=conn,
        model=LLM_MODEL,
        system_msg=PROMPT,
        sleep_seconds=SLEEP_SECONDS,
    )
    conn.close()

res = defaultdict(dict)

# calculate metrics
metrics.export_xrels(ANN_OUT, XRELS_OUT)
print("= METRICS")
evaluator = Evaluator(XRELS_OUT, POOL_OUT)
results = evaluator.evaluate([nDCG @ TOPK, MAP])
res["all"] = results
for s, m in results.items():
    print(f"System: {s}")
    for mt, value in m.items():
        print(f"  {mt}: {value:.4f}")

# per type metrics
conn = sqlite3.connect(ANN_OUT)
cur = conn.cursor()
for t in TYPES:
    type_queries = [x["QUERY"] for x in query_type_pairs if x["TYPE"] == t]

    print(f"{t=}")
    print(f"{type_queries=}")

    tmp_pool = tempfile.mktemp()
    t_data = build_annotation_pool(DOCPATH, engines, type_queries, top_k=TOPK)

    tmp_ann = tempfile.mktemp()
    print(f"{tmp_ann=}")

    subset_conn = sqlite3.connect(tmp_ann)
    subset_cur = subset_conn.cursor()
    cur.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='annotations'"
    )
    schema = cur.fetchone()[0]
    subset_cur.execute(schema)

    placeholders = ",".join("?" for _ in type_queries)
    cur.execute(
        f"SELECT * FROM annotations WHERE query IN ({placeholders})", type_queries
    )
    rows = cur.fetchall()
    subset_cur.executemany(
        "INSERT INTO annotations VALUES (" + ",".join(["?"] * len(rows[0])) + ")",
        rows,
    )
    subset_conn.commit()
    subset_conn.close()

    tmp_xrels = tempfile.mktemp()
    metrics.export_xrels(tmp_ann, tmp_xrels)

    with open(tmp_pool, "w") as f:
        json.dump(t_data, f)
    evaluator = Evaluator(tmp_xrels, tmp_pool)
    results = evaluator.evaluate([nDCG @ TOPK, MAP])
    print(t, results)

    res[t] = results

conn.close()


with open(METRICS_OUT, "w") as f:
    json.dump(res, f)
