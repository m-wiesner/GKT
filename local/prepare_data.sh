#!/bin/bash

. ./lang.conf
. ./cmd.sh
. ./conf/common_vars.sh
. ./conf/aud.conf

# Check that train_list points to limited LP
lists_dir=`dirname $train_data_list`
lexicon=data/local/lexicon.txt
aud_only=false

. ./utils/parse_options.sh

#Preparing dev10h and train directories
if [ ! -f data/raw_train_data/.done ]; then
    echo ---------------------------------------------------------------------
    echo "Subsetting the TRAIN set"
    echo ---------------------------------------------------------------------

    local/make_corpus_subset.sh "$train_data_dir" "$train_data_list" ./data/raw_train_data
    touch data/raw_train_data/.done
fi

if [ ! -d data/raw_dev10h_data ]; then
  echo ---------------------------------------------------------------------
  echo "Subsetting the DEV10H set"
  echo ---------------------------------------------------------------------
  local/make_corpus_subset.sh "$dev10h_data_dir" "$dev10h_data_list" ./data/raw_dev10h_data || exit 1
  touch data/raw_dev10h_data/.done
fi

if [ ! -d data/raw_FLP_data ]; then
  echo ---------------------------------------------------------------------
  echo "Subsetting the FLP set"
  echo ---------------------------------------------------------------------
  local/make_corpus_subset.sh "$train_data_dir" "${lists_dir}/train.FullLP.list" ./data/raw_FLP_data || exit 1
  touch data/raw_FLP_data/.done
fi

if [ ! -d data/raw_lorelei_data ]; then
  echo ---------------------------------------------------------------------
  echo "Subsetting the LORELEI set"
  echo ---------------------------------------------------------------------
  mkdir -p ./data/tmp_lorelei/{audio,transcription}

  # Remove files from train_list that are in limited LP list.
  # Add to this the dev10h list and use as the evaluation for LORELEI
  # Create new folder with all data used for Lorelei Evaluation
  comm -23 ${lists_dir}/train.FullLP.list ${lists_dir}/train.LimitedLP.list \
    | cat - ${lists_dir}/dev.list > ./data/tmp_lorelei/list

  cp -P ./data/raw_dev10h_data/audio/* ./data/tmp_lorelei/audio/
  cp -P ./data/raw_dev10h_data/transcription/* ./data/tmp_lorelei/transcription/

  cp -P ./data/raw_FLP_data/audio/* ./data/tmp_lorelei/audio/
  cp -P ./data/raw_FLP_data/transcription/* ./data/tmp_lorelei/transcription/
  local/make_corpus_subset.sh data/tmp_lorelei data/tmp_lorelei/list data/raw_lorelei_data || exit 1
  touch data/raw_lorelei_data/.done
fi

lorelei_data_dir=`readlink -f ./data/raw_lorelei_data`
train_data_dir=`readlink -f ./data/raw_train_data`
dev10h_data_dir=`readlink -f ./data/raw_train_data`
flp_data_dir=`readlink -f ./data/raw_FLP_data`

mkdir -p data/local
if [[ ! -f $lexicon || $lexicon -ot "$lexicon_file" ]]; then
  echo ---------------------------------------------------------------------
  echo "Preparing lexicon in data/local on" `date`
  echo ---------------------------------------------------------------------
  # We are interested in the full lexicon when looking at reference
  # transcripts even for the lorelei set.
  local/prepare_lexicon.pl  --phonemap "$phoneme_mapping" \
    $lexiconFlags $lexicon_file data/local
fi

mkdir -p data/lang
if [[ ! -f data/lang/L.fst || data/lang/L.fst -ot $lexicon ]]; then
  echo ---------------------------------------------------------------------
  echo "Creating L.fst etc in data/lang on" `date`
  echo ---------------------------------------------------------------------
  utils/prepare_lang.sh \
    --share-silence-phones true \
    data/local $oovSymbol data/local/tmp.lang data/lang
fi

if [[ ! -f data/train/wav.scp || data/train/wav.scp -ot "$train_data_dir" ]]; then
  echo ---------------------------------------------------------------------
  echo "Preparing acoustic training lists in data/train on" `date`
  echo ---------------------------------------------------------------------
  mkdir -p data/train
  local/prepare_acoustic_training_data.pl \
    --vocab $lexicon --fragmentMarkers \-\*\~ \
    $train_data_dir data/train > data/train/skipped_utts.log
  touch data/train/.done
fi

if [[ ! -f data/lorelei/wav.scp || data/lorelei/wav.scp -ot "$lorelei_data_dir" ]]; then
  echo ---------------------------------------------------------------------
  echo "Preparing acoustic training lists in data/train on" `date`
  echo ---------------------------------------------------------------------
  mkdir -p data/lorelei
  local/prepare_acoustic_training_data.pl \
    --vocab $lexicon --fragmentMarkers \-\*\~ \
    $lorelei_data_dir data/lorelei > data/lorelei/skipped_utts.log
  touch data/lorelei/.done
fi

if [[ ! -f data/srilm/lm.gz || data/srilm/lm.gz -ot data/train/text ]]; then
  echo ---------------------------------------------------------------------
  echo "Training SRILM language models on" `date`
  echo ---------------------------------------------------------------------
  local/train_lms_srilm.sh  --oov-symbol "$oovSymbol"\
    --train-text data/train/text data data/srilm
fi

if [[ ! -f data/lang/G.fst || data/lang/G.fst -ot data/srilm/lm.gz ]]; then
  echo ---------------------------------------------------------------------
  echo "Creating G.fst on " `date`
  echo ---------------------------------------------------------------------
  local/arpa2G.sh data/srilm/lm.gz data/lang data/lang
fi


if [ ! -f data/train/.plp.done ]; then
  
  echo ---------------------------------------------------------------------
  echo "Starting plp feature extraction for data/train in plp on" `date`
  echo ---------------------------------------------------------------------

  if $use_pitch; then
    steps/make_plp_pitch.sh --cmd "$train_cmd" --nj $train_nj data/train exp/make_plp_pitch/train plp
  else
    steps/make_plp.sh --cmd "$train_cmd" --nj $train_nj data/train exp/make_plp/train plp
  fi
  utils/fix_data_dir.sh data/train
  steps/compute_cmvn_stats.sh data/train exp/make_plp/train plp
  utils/fix_data_dir.sh data/train
  touch data/train/.plp.done
fi


if [ ! -f data/lorelei/.plp.done ]; then
  echo ---------------------------------------------------------------------
  echo "Starting plp feature extraction for data/lorelei in plp on" `date`
  echo ---------------------------------------------------------------------

  if $use_pitch; then
    steps/make_plp_pitch.sh --cmd "$train_cmd" --nj $train_nj data/lorelei exp/make_plp_pitch/lorelei plp
  else
    steps/make_plp.sh --cmd "$train_cmd" --nj $train_nj data/lorelei exp/make_plp/lorelei plp
  fi
  utils/fix_data_dir.sh data/lorelei
  steps/compute_cmvn_stats.sh data/lorelei exp/make_plp/lorelei plp
  utils/fix_data_dir.sh data/lorelei
  touch data/lorelei/.plp.done
fi

if [ ! -f data/train/stm ]; then
  echo --------------------------------------------------------------------
  echo "Preparing stm files"
  echo --------------------------------------------------------------------
  local/prepare_stm.pl --fragmentMarkers \-\*\~ data/train || exit 1
  local/prepare_stm.pl --fragmentMarkers \-\*\~ data/lorelei || exit 1
fi

if [ ! -f ${fea_dir}/.done ]; then
  echo ---------------------------------------------------------------------
  echo "Converting features for use in AUD" `date`
  echo ---------------------------------------------------------------------
  ./local_lorelei/extract_features.sh 
  touch ${fea_dir}/.done
fi


if [ ! -f data/.aud.done ]; then
  echo ---------------------------------------------------------------------
  echo "Making keys files for AUD" `date`
  echo ---------------------------------------------------------------------

  cut -d' ' -f1 data/train/feats.scp > data/train/keys
  cut -d' ' -f1 data/lorelei/feats.scp > data/lorelei/keys
  cat data/train/keys data/lorelei/keys > data/keys
   
  cut -d'.' -f1 data/train/segments | cut -d'_' -f1-4 | sort -u > data/train_docid.keys
  cut -d'.' -f1 data/lorelei/segments | cut -d'_' -f1-4 | sort -u > data/test_docid.keys
  
  cat data/train_docid.keys data/test_docid.keys | sort -u > data/all_docid.keys

  touch data/.aud.done
fi

if $aud_only; then
  echo "aud-only requested so exiting."
  exit 1
fi

mkdir -p exp

if [ ! -f data/train_sub3/.done ]; then
  echo ---------------------------------------------------------------------
  echo "Subsetting monophone training data in data/train_sub[123] on" `date`
  echo ---------------------------------------------------------------------
  numutt=`cat data/train/feats.scp | wc -l`;
  utils/subset_data_dir.sh data/train  5000 data/train_sub1
  if [ $numutt -gt 10000 ] ; then
    utils/subset_data_dir.sh data/train 10000 data/train_sub2
  else
    (cd data; ln -s train train_sub2 )
  fi
  if [ $numutt -gt 20000 ] ; then
    utils/subset_data_dir.sh data/train 20000 data/train_sub3
  else
    (cd data; ln -s train train_sub3 )
  fi

  touch data/train_sub3/.done
fi

if [ ! -f exp/mono/.done ]; then
  echo ---------------------------------------------------------------------
  echo "Starting (small) monophone training in exp/mono on" `date`
  echo ---------------------------------------------------------------------
  steps/train_mono.sh \
    --boost-silence $boost_sil --nj 8 --cmd "$train_cmd" \
    data/train_sub1 data/lang exp/mono
  touch exp/mono/.done
fi

if [ ! -f exp/tri1/.done ]; then
  echo ---------------------------------------------------------------------
  echo "Starting (small) triphone training in exp/tri1 on" `date`
  echo ---------------------------------------------------------------------
  steps/align_si.sh \
    --boost-silence $boost_sil --nj 12 --cmd "$train_cmd" \
    data/train_sub2 data/lang exp/mono exp/mono_ali_sub2

  steps/train_deltas.sh \
    --boost-silence $boost_sil --cmd "$train_cmd" $numLeavesTri1 $numGaussTri1 \
    data/train_sub2 data/lang exp/mono_ali_sub2 exp/tri1

  touch exp/tri1/.done
fi


echo ---------------------------------------------------------------------
echo "Starting (medium) triphone training in exp/tri2 on" `date`
echo ---------------------------------------------------------------------
if [ ! -f exp/tri2/.done ]; then
  steps/align_si.sh \
    --boost-silence $boost_sil --nj 24 --cmd "$train_cmd" \
    data/train_sub3 data/lang exp/tri1 exp/tri1_ali_sub3

  steps/train_deltas.sh \
    --boost-silence $boost_sil --cmd "$train_cmd" $numLeavesTri2 $numGaussTri2 \
    data/train_sub3 data/lang exp/tri1_ali_sub3 exp/tri2

  local/reestimate_langp.sh --cmd "$train_cmd" --unk "$oovSymbol" \
    data/train_sub3 data/lang data/local/ \
    exp/tri2 data/local/dictp/tri2 data/local/langp/tri2 data/langp/tri2

  touch exp/tri2/.done
fi

echo ---------------------------------------------------------------------
echo "Starting (full) triphone training in exp/tri3 on" `date`
echo ---------------------------------------------------------------------
if [ ! -f exp/tri3/.done ]; then
  steps/align_si.sh \
    --boost-silence $boost_sil --nj $train_nj --cmd "$train_cmd" \
    data/train data/langp/tri2 exp/tri2 exp/tri2_ali

  steps/train_deltas.sh \
    --boost-silence $boost_sil --cmd "$train_cmd" \
    $numLeavesTri3 $numGaussTri3 data/train data/langp/tri2 exp/tri2_ali exp/tri3

  local/reestimate_langp.sh --cmd "$train_cmd" --unk "$oovSymbol" \
    data/train data/lang data/local/ \
    exp/tri3 data/local/dictp/tri3 data/local/langp/tri3 data/langp/tri3

  touch exp/tri3/.done
fi

echo ---------------------------------------------------------------------
echo "Starting (lda_mllt) triphone training in exp/tri4 on" `date`
echo ---------------------------------------------------------------------
if [ ! -f exp/tri4/.done ]; then
  steps/align_si.sh \
    --boost-silence $boost_sil --nj $train_nj --cmd "$train_cmd" \
    data/train data/langp/tri3 exp/tri3 exp/tri3_ali

  steps/train_lda_mllt.sh \
    --boost-silence $boost_sil --cmd "$train_cmd" \
    $numLeavesMLLT $numGaussMLLT data/train data/langp/tri3 exp/tri3_ali exp/tri4

  local/reestimate_langp.sh --cmd "$train_cmd" --unk "$oovSymbol" \
    data/train data/lang data/local \
    exp/tri4 data/local/dictp/tri4 data/local/langp/tri4 data/langp/tri4

  touch exp/tri4/.done
fi

echo ---------------------------------------------------------------------
echo "Starting (SAT) triphone training in exp/tri5 on" `date`
echo ---------------------------------------------------------------------

if [ ! -f exp/tri5/.done ]; then
  steps/align_si.sh \
    --boost-silence $boost_sil --nj $train_nj --cmd "$train_cmd" \
    data/train data/langp/tri4 exp/tri4 exp/tri4_ali

  steps/train_sat.sh \
    --boost-silence $boost_sil --cmd "$train_cmd" \
    $numLeavesSAT $numGaussSAT data/train data/langp/tri4 exp/tri4_ali exp/tri5

  local/reestimate_langp.sh --cmd "$train_cmd" --unk "$oovSymbol" \
    data/train data/lang data/local \
    exp/tri5 data/local/dictp/tri5 data/local/langp/tri5 data/langp/tri5

  touch exp/tri5/.done
fi

if [ ! -f exp/tri5_ali/.done ]; then
  echo ---------------------------------------------------------------------
  echo "Starting exp/tri5_ali on" `date`
  echo ---------------------------------------------------------------------
  steps/align_fmllr.sh \
    --boost-silence $boost_sil --nj $train_nj --cmd "$train_cmd" \
    data/train data/langp/tri5 exp/tri5 exp/tri5_ali

  local/reestimate_langp.sh --cmd "$train_cmd" --unk "$oovSymbol" \
    data/train data/lang data/local \
    exp/tri5_ali data/local/dictp/tri5_ali data/local/langp/tri5_ali data/langp/tri5_ali

  touch exp/tri5_ali/.done
fi

# Align Lorelei Ground Truth set
echo "---------------------------------------------------------------"
echo "Aligning Lorelei set. FLP - LLP + DEV10h"
echo "---------------------------------------------------------------"

./steps/align_fmllr.sh --boost-silence 1.5 --nj 16 --cmd "queue.pl -l arch=*64" \
  data/lorelei data/langp/tri5 exp/tri5 exp/tri5_ali_lorelei

echo "Train"
ali-to-phones exp/tri5/final.mdl ark:"gunzip -c exp/tri5_ali/ali.*.gz |" ark,t:- | sort > data/train/text.ali
echo "Test"
ali-to-phones exp/tri5/final.mdl ark:"gunzip -c exp/tri5_ali_lorelei/ali.*.gz |" ark,t:- | sort > data/lorelei/text.ali

echo "---------------------------------------------------------------"
echo "Get a frame level alignment to be used for NMI computation"
echo "---------------------------------------------------------------"
ali-to-phones --per-frame exp/tri5/final.mdl ark:"gunzip -c exp/tri5_ali/ali.*.gz |" ark,t:- | sort > data/train/text.frame.ali

ali-to-phones --per-frame exp/tri5/final.mdl ark:"gunzip -c exp/tri5_ali_lorelei/ali.*.gz |" ark,t:- | sort > data/lorelei/text.frame.ali

echo "Making MLF"
./local_lorelei/ali2mlf.py data/train/text.frame.ali data/train/MLF data/lang/phones.txt
./local_lorelei/ali2mlf.py data/lorelei/text.frame.ali data/lorelei/MLF data/lang/phones.txt

echo "---------------------------------------------------------------"
echo "Find utterances that could not be forced aligned"
echo "---------------------------------------------------------------"

comm -23 <(cut -d' ' -f1 data/train/text | sort) <(cut -d' ' -f1 data/train/text.ali | sort) > data/train_missing.keys
comm -23 <(cut -d' ' -f1 data/lorelei/text | sort) <(cut -d' ' -f1 data/lorelei/text.ali | sort) > data/dev_missing.keys


echo "---------------------------------------------------------------"
echo "Preparing data for clustering experiments"
echo "---------------------------------------------------------------"

./local_lorelei/prepare_clustering.sh data ${eval_path}
