#!/bin/bash
set -e

DOCPATH="$HOME/.local/share/foxhole/doc.db"
VECPATH="$HOME/.local/share/foxhole/vec.db"
TMPDOCPATH=$(mktemp --suffix .db)
TMPVECPATH=$(mktemp --suffix .db)

cp -v "$DOCPATH" "$TMPDOCPATH"
cp -v "$VECPATH" "$TMPVECPATH"

foxhole-prune --skip_backup --doc_path "$TMPDOCPATH" --vec_path "$TMPVECPATH" --ignore_list
