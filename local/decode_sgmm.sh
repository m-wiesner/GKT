set -e
set -o pipefail

. conf/common_vars.sh || exit 1;
. ./cmd.sh
. ./lang.conf

dataset_id=lorelei
my_nj=64
skip_kws=true
skip_stt=false
extra_kws=false
skip_scoring=false
wip=0.5

. ./utils/parse_options.sh
####################################################################
##
## FMLLR decoding
##
####################################################################

dataset_dir=data/${dataset_id}

echo $dataset_dir
echo $dataset_id
if [ ! -f data/langp_test/.done ]; then
  
  echo "Copying data/langp/tri5_ali"
  cp -R data/langp/tri5_ali/ data/langp_test
  cp data/lang/G.fst data/langp_test
  touch data/langp_test/.done
fi
decode=exp/tri5/decode_${dataset_id}
if [ ! -f ${decode}/.done ]; then
  echo ---------------------------------------------------------------------
  echo "Spawning decoding with SAT models  on" `date`
  echo ---------------------------------------------------------------------
  utils/mkgraph.sh \
    data/langp_test exp/tri5 exp/tri5/graph |tee exp/tri5/mkgraph.log

  mkdir -p $decode
  #By default, we do not care about the lattices for this step -- we just want the transforms
  #Therefore, we will reduce the beam sizes, to reduce the decoding times
  steps/decode_fmllr_extra.sh --skip-scoring true --beam 10 --lattice-beam 4\
    --nj $my_nj --cmd "$decode_cmd" "${decode_extra_opts[@]}"\
    exp/tri5/graph ${dataset_dir} ${decode} |tee ${decode}/decode.log
  touch ${decode}/.done
fi

####################################################################
## SGMM2 decoding
## We Include the SGMM_MMI inside this, as we might only have the DNN systems
## trained and not PLP system. The DNN systems build only on the top of tri5 stage
####################################################################
if [ -f exp/sgmm5/.done ]; then
  decode=exp/sgmm5/decode_fmllr_${dataset_id}
  if [ ! -f $decode/.done ]; then
    echo ---------------------------------------------------------------------
    echo "Spawning $decode on" `date`
    echo ---------------------------------------------------------------------
    utils/mkgraph.sh \
      data/langp_test exp/sgmm5 exp/sgmm5/graph |tee exp/sgmm5/mkgraph.log

    mkdir -p $decode
    steps/decode_sgmm2.sh --skip-scoring true --use-fmllr true --nj $my_nj \
      --cmd "$decode_cmd" --transform-dir exp/tri5/decode_${dataset_id} "${decode_extra_opts[@]}"\
      exp/sgmm5/graph ${dataset_dir} $decode |tee $decode/decode.log
    touch $decode/.done
  fi

  ####################################################################
  ##
  ## SGMM_MMI rescoring
  ##
  ####################################################################

  for iter in 1 2 3 4; do
      # Decode SGMM+MMI (via rescoring).
    decode=exp/sgmm5_mmi_b0.1/decode_fmllr_${dataset_id}_it$iter
    if [ ! -f $decode/.done ]; then

      mkdir -p $decode
      steps/decode_sgmm2_rescore.sh  --skip-scoring true \
        --cmd "$decode_cmd" --iter $iter --transform-dir exp/tri5/decode_${dataset_id} \
        data/langp_test ${dataset_dir} exp/sgmm5/decode_fmllr_${dataset_id} $decode | tee ${decode}/decode.log

      touch $decode/.done
    fi
  done

  #We are done -- all lattices has been generated. We have to
  #a)Run MBR decoding
  #b)Run KW search
  for iter in 1 2 3 4; do
    # Decode SGMM+MMI (via rescoring).
    decode=exp/sgmm5_mmi_b0.1/decode_fmllr_${dataset_id}_it$iter
      local/run_kws_stt_task2.sh --cer $cer --max-states $max_states \
        --skip-scoring $skip_scoring --extra-kws $extra_kws --wip $wip \
        --cmd "$decode_cmd" --skip-kws $skip_kws --skip-stt $skip_stt  \
      "${lmwt_plp_extra_opts[@]}" \
      ${dataset_dir} data/langp_test $decode
  done
fi

