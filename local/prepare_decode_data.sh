#!/bin/bash

#data_sets=( lorelei train ) 
data_sets=( train )
exp_dir=exp/sgmm5_mmi_b0.1

# Train sgmm
if [ ! -f ${exp_dir}/final.mdl ]; then
  ./local_lorelei/run_sgmm.sh
fi

# Decode sgmm
for ds in ${data_sets[@]}; do
  if [ ! -f  ${exp_dir}/decode_fmllr_${data_set}_it1 ]; then
    ./local_lorelei/decode_sgmm.sh --dataset-id ${data_set}
  fi
done

# Find best acoustic scale and best iteration
for ds in ${data_sets[@]}; do
  
  echo "Best WER:  $(grep Avg exp/sgmm5_mmi_b0.1/decode_fmllr_${ds}_it*/score_*/${ds}.ctm.sys | utils/best_wer.sh)"
  sleep 5
  
  decode_score_dir=`dirname $(grep Avg exp/sgmm5_mmi_b0.1/decode_fmllr_${ds}_it*/score_*/${ds}.ctm.sys \
    | utils/best_wer.sh \
    | sed 's/ | /|/g' \
    | rev | cut -d'|' -f1 | rev)`

  decode_dir=`dirname $decode_score_dir`
  a_scale=$(echo $decode_score_dir | rev | cut -d'/' -f1 | cut -d'_' -f1 | rev)

  lattice-scale --inv-acoustic-scale=${a_scale} "ark:gunzip -c ${decode_dir}/lat.*.gz|" ark:- \
    | lattice-1best ark:- ark:- \
    | lattice-add-penalty --word-ins-penalty=0.5 ark:- ark:- \
    | lattice-prune --beam=5 ark:- ark:- \
    | nbest-to-linear ark:- ark:- \
    | ali-to-phones --per-frame ${exp_dir}/final.mdl ark:- ark,t:- \
    | sort > ${exp_dir}/text_${ds}.frame.ali

  lattice-scale --inv-acoustic-scale=${a_scale} "ark:gunzip -c ${decode_dir}/lat.*.gz|" ark:- \
    | lattice-1best ark:- ark:- \
    | lattice-add-penalty --word-ins-penalty=0.5 ark:- ark:- \
    | lattice-prune --beam=5 ark:- ark:- \
    | nbest-to-linear ark:- ark:- \
    | ali-to-phones ${exp_dir}/final.mdl ark:- ark,t:- \
    | sort > ${exp_dir}/text_${ds}.ali

  ./local_lorelei/ali2mlf.py ${exp_dir}/text_${ds}.frame.ali ${exp_dir}/MLF_${ds} data/lang/phones.txt
done
