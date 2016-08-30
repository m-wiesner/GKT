#!/bin/bash

clean_utts=false
aud_train=
aud_test=
aud_name=aud
. ./utils/parse_options.sh

if [ $# -ne 2 ]; then
  echo "Usage: ./local/prepare_clustering.sh [opts] <data_dir> < Clustering_output_dir >"
  echo "  [--clean-utts] -- remove utterances for which no phone-level forced alignment was found"
  echo "  [--aud-train <path>]  -- path to aud mlf on train data"
  echo "  [--aud-test <path>]   -- path to aud mlf on test"
  echo "  [--aud-name <name>]   -- name of aud method (default is aud)"
  exit 1
fi

# Some useful paths and directories that we assume we have
data_dir=$1
eval_path=$2
train_words=${data_dir}/train/text
test_words=${data_dir}/lorelei/text
train_phones=${data_dir}/train/text.ali
test_phones=${data_dir}/lorelei/text.ali
decode_train_phones=exp/sgmm5_mmi_b0.1/text_train.ali
decode_test_phones=exp/sgmm5_mmi_b0.1/text_lorelei.ali
path_to_phones=${data_dir}/lang/phones.txt

mkdir -p $eval_path

if [ ! -f ${eval_path}/train.keys ]; then
  cp data/train_docid.keys ${eval_path}/train.keys
  cp data/test_docid.keys ${eval_path}/test.keys
fi

if [ ! -f ${eval_path}/.words.done ]; then
  echo "---------------------------------------------"
  echo "Creating Word Transcriptions for Clustering"
  echo "---------------------------------------------"

  echo "Train"
  ./local_lorelei/babel2cluster.py $train_words ${eval_path}/words
  echo "Test"
  ./local_lorelei/babel2cluster.py $test_words ${eval_path}/words
  touch ${eval_path}/.words.done
fi

if [ ! -f ${eval_path}/.context.done ]; then
  echo "---------------------------------------------"
  echo "Creating Context Phone Transcriptions for Clustering"
  echo "---------------------------------------------"

  echo "Train"
  ./local_lorelei/babel2cluster.py $train_phones ${eval_path}/context_phones
  echo "Test"
  ./local_lorelei/babel2cluster.py $test_phones ${eval_path}/context_phones
  touch ${eval_path}/.context.done
fi

echo $decode_train_phone
if [ -f $decode_train_phones ] && [ -f $decode_test_phones ] && [ ! -f ${eval_path}/.decode_context.done]; then
  echo "---------------------------------------------"
  echo "Creating Decoded Context Phone Transcriptions for Clustering"
  echo "---------------------------------------------"

  echo "Train"
  ./local_lorelei/babel2cluster.py $decode_train_phones ${eval_path}/decode_context_phones
  echo "dev"
  ./local_lorelei/babel2cluster.py $decode_test_phones ${eval_path}/decode_context_phones
  touch ${eval_path}/.decode_context.done
fi

if [ ! -f ${eval_path}/.phones.done ]; then
  echo "---------------------------------------------"
  echo "Creating Phone Transcriptions for Clustering"
  echo "---------------------------------------------"
  
  cut -d' ' -f1 $path_to_phones | cut -d'_' -f1 > ${eval_path}/tmp_phones
  cut -d' ' -f2 $path_to_phones > ${eval_path}/tmp_ints
  paste -d' ' ${eval_path}/tmp_phones ${eval_path}/tmp_ints > ${eval_path}/phones.txt
  
  # Clean up temporary files
  rm ${eval_path}/tmp*
  ./local_lorelei/words2phones.py ${eval_path}/context_phones ${eval_path}/phones ${eval_path}/phones.txt True
  touch ${eval_path}/.phones.done
fi

if [ -f $decode_test_phones ] && [ -f $decode_train_phones ] && [ ! -f ${eval_path}/.decode.done ]; then
  echo "---------------------------------------------"
  echo "Creating Decoded Phone Transcriptions for Clustering"
  echo "---------------------------------------------"
  ./local_lorelei/words2phones.py ${eval_path}/decode_context_phones ${eval_path}/decode_phones ${eval_path}/phones.txt True
  touch ${eval_path}/.decode.done
fi

if [ ! -z $aud_train ] && [ ! -z $aud_test ] && [ ! -f ${eval_path}/.${aud_name}.done ]; then
  echo "---------------------------------------------"
  echo "Creating AUD Transcriptions for Clustering"
  echo "---------------------------------------------"

  ./local_lorelei/mlf2ali.py $aud_train ${data_dir}/train/${aud_name}
  ./local_lorelei/mlf2ali.py $aud_test ${data_dir}/lorelei/${aud_name}

  ./local_lorelei/babel2cluster.py ${data_dir}/train/${aud_name} ${eval_path}/${aud_name}
  ./local_lorelei/babel2cluster.py ${data_dir}/lorelei/${aud_name} ${eval_path}/${aud_name}
  touch ${eval_path}/.${aud_name}.done
fi


if [ -f ${eval_path}/.words.done ] && [ -f ${eval_path}/.phones.done ] && [ ! -f ${eval_path}/.clean.done ]; then
  if $clean_utts; then
    echo "---------------------------------------------"
    echo "Cleaning words directory to exclude utterances"
    echo "for which no forced alignments were found."
    echo "These may be poorly transcribed utterances, or"
    echo "other forms of speech quality degradation."
    echo "---------------------------------------------"
    
    rm -r ${eval_path}/words

    echo "Train"
    ./local_lorelei/babel2cluster.py $train_words ${eval_path}/words ${data_dir}/train_missing.keys
    echo "Test"
    ./local_lorelei/babel2cluster.py $test_words ${eval_path}/words ${data_dir}/dev_missing.keys
    touch ${eval_path}/.clean.done
  fi
fi

echo "Clustering Data Prepared"
exit 0
