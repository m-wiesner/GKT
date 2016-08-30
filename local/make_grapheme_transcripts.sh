#!/bin/bash

if [ $# -ne 2 ]; then
  echo "Usage: ./make_grapheme_transcripts.sh <path_to_words> <path_to_graphemes_dir>"
  exit 1
fi

word_docs=$1
output_docs=$2

mkdir -p $output_docs

for doc in ${word_docs}/*.txt
do
  ./local_lorelei/words2graphs.py $doc $output_docs/${doc##*/}
done 


