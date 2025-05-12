#!/bin/bash
# MINIMAL BASH SCRIPT FOR TESTING
set -e
DATA=./00_data_dataset.db
ANN=./00_data_ann.db
TRECDIR=./00_data_trec.json

rm -f "$DATA"
rm -f "$ANN"
rm -rf "$TRECDIR"

python3 ./create_eval_dataset.py --query_file ./queries.txt --output_file "$DATA" -k 10
python3 ./annotate.py -i "$DATA" -o "$ANN"
python3 ./create_trec_dataset.py -i "$ANN" -o "$TRECDIR"
