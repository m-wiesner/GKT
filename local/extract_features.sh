#!/bin/bash

. ./conf/aud.conf

if [ $# -eq 0 ]; then
  echo "Usage: ./extract_features.sh data/dataset1 data/dataset2 ..."
  exit 1
fi

# Get input arguments
data_dirs=( "$@" )

# Default
if [ ${#data_dirs[@]} -lt 1 ]; then
  data_dirs=( data/train data/lorelei )
fi

# Get training features (Add deltas, apply cmvn
for dir in ${data_dirs[@]}
do 
  apply-cmvn --utt2spk=ark:${dir}/utt2spk scp:${dir}/cmvn.scp scp:${dir}/feats.scp ark:- \
    | add-deltas ark:- ark:- \
    | copy-feats-to-htk --output-dir=${fea_dir} --output-ext=${fea_ext} ark:-
done

