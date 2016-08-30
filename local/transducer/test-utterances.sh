#!/bin/bash

if [ $# -ne 4 ]; then
  echo "Usage: ./test-utterances.py <utt_dir> <train_data> <fst_dir> <lang_dir>" 
  exit 1
fi

utt_dir=$1
train_data=$2
fst_dir=$3
lang_dir=$4

lattice_dir=${fst_dir}/lattices
lbl_dir=${fst_dir}/lbls

mkdir -p {$lattice_dir,$lbl_dir}

utterances=( `find $utt_dir -name "*.fst"` )

# Create isyms
awk '{ print $0 }' RS=' ' $train_data | sort -u | sed '/^$/d' \
  | awk 'BEGIN { print "<eps> 0" } { print $1 " " NR }' > ${fst_dir}/isyms.txt

# Compile utterances
for utt in ${utterances[@]}; do
  fstcompile --isymbols=${fst_dir}/isyms.txt \
    --osymbols=${fst_dir}/pdf_ids.txt $utt $utt
done

# Create lattices
for utt in ${utterances[@]}; do 
  uttname=`basename $utt`
  fstcompose $utt ${fst_dir}/TLG_final.fst ${lattice_dir}/${uttname}.lat   
done

# Get labels
lattices=( `find $lattice_dir -name "*.lat"` )
for lat in ${lattices[@]}; do
  lattname=`basename $lat`
  fstshortestpath $lat ${lbl_dir}/${lattname}.lbl
done

# Print paths
labels=( `find $lbl_dir -name "*.lbl"` )
for lbl in ${labels[@]}; do
  lbl_name=`basename $lbl`
  fstprint --isymbols=${fst_dir}/isyms.txt --osymbols=${lang_dir}/words.txt \
    $lbl ${lbl_dir}/${lbl_name}  
done





