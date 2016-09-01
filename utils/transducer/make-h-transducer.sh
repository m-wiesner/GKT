#!/bin/bash

# This script has the basic structure for creating the Openfst transducer
# from AUDs to graphemes.

if [ $# -ne 2 ]; then
  echo "./make-h-transducer.sh <fst_dir> <lang_dir>"
  exit 1
fi

FST_DIR=$1 
LANG_DIR=$2

# Create fsts for each grapheme
#./local/transducer/transducer-to-pdfArc-fst.py ${FST_DIR}/model.bin \
#  ${FST_DIR}

./local/transducer/transducer-to-fst.py ${FST_DIR}/model.bin \
  ${FST_DIR}

# Create fsts for disambiguation symbols
for disambig in `cut -d' ' -f1 ${LANG_DIR}/phones/disambig.txt`; do
  text="0 1 $disambig $disambig 0 \n1"
  printf "$text" > ${FST_DIR}/disambig_${disambig}.fst
done

# Add disambiguation symbols to pdf_ids.txt input symbols
#cat ${FST_DIR}/pdf_ids.txt ${LANG_DIR}/phones/disambig.txt \
#  | awk '{ print $1 " " NR-1 }' > ${FST_DIR}/isyms.txt

cat ${FST_DIR}/ems.txt ${LANG_DIR}/phones/disambig.txt \
  | awk '{ print $1 " " NR-1 }' > ${FST_DIR}/isyms.txt

# Compile the fsts
fsts=( `find $FST_DIR -name "*.fst"` )
for f in ${fsts[@]}; do
  fstcompile --isymbols=${FST_DIR}/isyms.txt \
    --osymbols=${LANG_DIR}/phones.txt $f ${f}.bin
done
# Union of fsts
cp ${fsts[0]}.bin ${FST_DIR}/union.bin

for f in ${fsts[@]:1}; do
  fstunion ${FST_DIR}/union.bin ${f}.bin ${FST_DIR}/tmp.bin
  mv ${FST_DIR}/tmp.bin ${FST_DIR}/union.bin
done

# Apply closure and remove epsilon arcs
fstclosure ${FST_DIR}/union.bin | fstrmepsilon > ${FST_DIR}/T.fst

# Sort and Compose with LG.fst
#fstarcsort ${LANG_DIR}/LG.fst ${FST_DIR}/LG_sort.fst
#fstcompose ${FST_DIR}/T.fst ${FST_DIR}/LG_sort.fst #\
#  | fstrmsymbols ${LANG_DIR}/phones/disambig.int \
#  | fstrmepslocal | fstminimizeencoded > ${FST_DIR}/TLG.fst

fstarcsort ${LANG_DIR}/LG.fst ${FST_DIR}/LG_sort.fst
fstcompose ${FST_DIR}/T.fst ${FST_DIR}/LG_sort.fst > TLG.fst



# Compose with L.fst
#fstarcsort ${LANG_DIR}/L.fst ${FST_DIR}/L_sort.fst
#fstcompose ${FST_DIR}/T.fst ${LANG_DIR}/L_sort.fst #\
# | fstrmsymbols phones/disambig.int | fstrmepslocal \
# | fstminimizeencoded > ${FST_DIR}/L_prime.fst

fstarcsort ${LANG_DIR}/L.fst ${FST_DIR}/L_sort.fst
fstcompose ${FST_DIR}/T.fst ${FST_DIR}/L_sort.fst > L_prime.fst




