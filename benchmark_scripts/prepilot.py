#!/usr/bin/env python

# PRE-PILOT STUDY EVALUATION SCRIPT
# IF YOU ARE CONFUSED, READ IT LIKE A BASH SCRIPT, YA GIT?

import argparse
import json
from pathlib import Path

from ir_measures import nDCG, MAP
from foxhole.eval import llm, metrics
from foxhole.eval.metrics import Evaluator
from foxhole.eval.annotate import annotate_sqlite, build_annotation_pool
from foxhole.search import (
    # BM25SearchEngine,
    ChromaSemanticSearchEngine,
    TFIDFSearchEngine,
)

# define constants
DATA = Path("./00-data")
QUERIESPATH = DATA / "queries_pilot_dev.tsv"
DOCPATH = DATA / "doc.db"
VECPATH = DATA / "vec.chroma"
TOPK = 10

LLM_MODEL = "gpt-4.1-nano"
PROMPT = (DATA / "prompt.txt").read_text()
SLEEP_SECONDS = 1

(OUT := Path("./01_prepilot_out")).mkdir(exist_ok=True)
POOL_OUT = OUT / "00_pool.json"
LLM_OUT = OUT / "01_llm.db"
MAN_OUT = OUT / "01_man.db"
LLM_XRELS = OUT / "02_llm_xrels.json"
MAN_XRELS = OUT / "02_man_xrels.json"

# define reset argparse
parser = argparse.ArgumentParser()
parser.add_argument(
    "-r",
    "--reset",
    action="store_true",
    help=f"deletes LLM ANNOTATIONS/POOL (in {OUT.absolute()}) before run",
)
args = parser.parse_args()
if args.reset:
    LLM_OUT.unlink(missing_ok=True)
    POOL_OUT.unlink(missing_ok=True)

# load queries for prepilot study
with open(QUERIESPATH) as f:
    queries = [line.split("\t")[0].strip() for line in f][1:4]
    print(f"{queries=}")

if not POOL_OUT.exists():
    # NOTE: BM-25 currently non-functional
    # print("loading BM-25 system")
    # bm_engine = BM25SearchEngine(DOCPATH, VECPATH)
    # bm_engine.load_db()

    print("loading ChromaSemantic system")
    ch_engine = ChromaSemanticSearchEngine(DOCPATH, VECPATH)
    ch_engine.load_db()

    print("loading TFIDF system")
    tf_engine = TFIDFSearchEngine(DOCPATH, VECPATH)
    tf_engine.load_db()

    engines = [
        # bm_engine,
        ch_engine,
        tf_engine,
    ]

    # go from queries to dataset for annotation
    dataset = build_annotation_pool(DOCPATH, engines, queries, top_k=TOPK)
    with open(POOL_OUT, "w") as f:
        json.dump(dataset, f)
        print(f"saved {len(dataset)} annotation pairs to {POOL_OUT}")
else:
    print("loading cached pool dataset")
    with open(POOL_OUT) as f:
        dataset = json.load(f)


# get llm annotations for dataset
if not LLM_OUT.exists():
    conn = llm.init_annotation_db(LLM_OUT)
    llm.annotate_pool(
        pool_items=dataset,
        text_to_id=llm.load_text_to_id_map(DOCPATH),
        annotation_conn=conn,
        model=LLM_MODEL,
        system_msg=PROMPT,
        sleep_seconds=SLEEP_SECONDS,
    )
    conn.close()

# manual annotation for dataset
print("manual annotation step")
annotate_sqlite(inp=POOL_OUT, out=MAN_OUT)

# interannotator agreement
ia = metrics.interannotator_agreement(MAN_OUT, LLM_OUT)
print(ia)

# calculate metrics (because why not?)
metrics.export_xrels(MAN_OUT, MAN_XRELS)
metrics.export_xrels(LLM_OUT, LLM_XRELS)

for xrel in [MAN_XRELS, LLM_XRELS]:
    print(f"= EVALUATING FOR {xrel.name}")
    evaluator = Evaluator(xrel, POOL_OUT)
    results = evaluator.evaluate([nDCG @ TOPK, MAP])
    for s, m in results.items():
        print(f"System: {s}")
        for mt, value in m.items():
            print(f"  {mt}: {value:.4f}")
