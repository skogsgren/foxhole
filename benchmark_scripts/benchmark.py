#!/usr/bin/env python
# FULL BENCHMARK

import json
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
queries = []
for p in QUERY_PATHS:
    with open(p) as f:
        queries += [line.split("\t")[0].strip() for line in f][1:]
print(f"{queries=}")

if not POOL_OUT.exists():
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
res["metrics"] = results
for s, m in results.items():
    print(f"System: {s}")
    for mt, value in m.items():
        print(f"  {mt}: {value:.4f}")

with open(METRICS_OUT, "w") as f:
    json.dump(res, f)
