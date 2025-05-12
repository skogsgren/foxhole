#!/bin/bash
# MINIMAL BASH SCRIPT FOR TESTING
DATA=./00_data_dataset.db
ANN=./00_data_ann.db
rm "$DATA"
rm "$ANN"

python3 ./create_eval_dataset.py \
    --query_file ./queries.txt \
    --output_file "$DATA" \
    -k 30

python3 ./annotate.py -i "$DATA" -o "$ANN"
sqlite3 "$ANN" "SELECT query,rank,id,url,label FROM annotations;"
