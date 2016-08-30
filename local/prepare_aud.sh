#!/bin/bash
# Check input arguments
if [ $# -ne 0 ]; then
  echo "Usage: local_lorelei/prepare_aud.sh"
  exit 1;
fi

# Get commandline arguments
. ./lang.conf
. ./cmd.sh
. ./conf/common_vars.sh

# Check that train_list points to limited LP
lists_dir=`dirname $train_data_list`

#Preparing dev10h and train directories
if [ ! -f data/raw_train_data/.done ]; then
  echo ---------------------------------------------------------------------
  echo "Subsetting the TRAIN set"
  echo ---------------------------------------------------------------------

  local/make_corpus_subset.sh "$train_data_dir" "$train_data_list" ./data/raw_train_data
  touch data/raw_train_data/.done
fi

if [ ! -f data/raw_dev10h_data/.done ]; then
  echo ---------------------------------------------------------------------
  echo "Subsetting the DEV10H set"
  echo ---------------------------------------------------------------------
  local/make_corpus_subset.sh "$dev10h_data_dir" "$dev10h_data_list" ./data/raw_dev10h_data || exit 1
  touch data/raw_dev10h_data/.done
fi

if [ ! -f data/raw_FLP_data/.done ]; then
  echo ---------------------------------------------------------------------
  echo "Subsetting the FLP set"
  echo ---------------------------------------------------------------------
  local/make_corpus_subset.sh "$train_data_dir" "${lists_dir}/train.FullLP.list" ./data/raw_FLP_data || exit 1
  touch data/raw_FLP_data/.done
fi

if [ ! -f data/raw_lorelei_data/.done ]; then
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
if [ ! -f data/local/.lexicon.done ]; then  
  echo ---------------------------------------------------------------------
  echo "Preparing lexicon in data/local on" `date`
  echo ---------------------------------------------------------------------
  local/make_lexicon_subset.sh $train_data_dir/transcription $lexicon_file data/local/filtered_lexicon.txt
  
  local/prepare_lexicon.pl  --phonemap "$phoneme_mapping" \
    $lexiconFlags $lexicon_file data/local
  
  touch data/local/.lexicon.done
fi

if [ ! -f data/lorelei/.done ]; then  
  echo "------------------------------"
  echo "Making Ground Truth Data for Lorelei Set"
  echo "------------------------------"
  # For when ground_truth transcripts are needed
  mkdir -p data/lorelei
  echo "Preparing training"
  ./local/prepare_acoustic_training_data.pl --vocab data/local/lexicon.txt --fragmentMarkers \-\*\~ \
    $lorelei_data_dir data/lorelei > data/lorelei/skipped_utts.log
  touch data/lorelei/.done
fi

if [ ! -f data/train/.done ]; then
  echo "-----------------------------"
  echo "Making Data for Train"
  echo "-----------------------------"  
  mkdir -p data/train
  echo "Preparing training"
  ./local/prepare_acoustic_training_data.pl --vocab data/local/lexicon.txt --fragmentMarkers \-\*\~ \
    $train_data_dir data/train > data/train/skipped_utts.log
  touch data/train/.done
fi

# Actual AUD part. We just needed the above for other things.
if [ ! -f data/.aud.done ]; then
  echo "----------------------------------------"
  echo "Creating .scp and .keys files"
  echo "----------------------------------------"
  
  # Create document ID keys for potential later evaluation
  cut -d'.' -f1 data/train/segments | cut -d'_' -f1-4 | sort -u > data/train_docid.keys
  cut -d'.' -f1 data/lorelei/segments | cut -d'_' -f1-4 | sort -u > data/test_docid.keys
  
  cat data/train_docid.keys data/test_docid.keys | sort -u > data/all_docid.keys
  
  # ---------- This section adds timing and breaks files into smaller utterances. ---------
  # Get all keys from the segments files
  cut -d' ' -f1 data/train/segments > data/train.keys
  cut -d' ' -f1 data/lorelei/segments > data/dev.keys
  
  # Concatenate train and dev keys to form all keys
  cat data/train.keys data/dev.keys > data/all.keys
  
  # Create 2 variables, train_files, and dev_files, which are paths to training
  # and dev data with the slashes escaped so that they can be read by sed.
  train_files="$(echo $train_data_dir | sed "s/\//\\\\\//g")"
  dev_files="$(echo $lorelei_data_dir | sed "s/\//\\\\\//g")"
  
  # Add .sph to the end of each filename in segments, and prepend the absolute path as well.
  cut -d' ' -f2 data/train/segments | sed 's/$/.sph/g' | sed "s/^/${train_files}\/audio\//g" > data/train_scp.txt
  cut -d' ' -f2 data/lorelei/segments | sed 's/$/.sph/g' | sed "s/^/${dev_files}\/audio\//g" > data/dev_scp.txt
  
  # Get the start times for each filename in segments
  cut -d' ' -f3 data/train/segments > data/train_start.txt
  cut -d' ' -f3 data/lorelei/segments > data/dev_start.txt
  
  # Get the end times for each filename in segments
  cut -d' ' -f4 data/train/segments > data/train_end.txt
  cut -d' ' -f4 data/lorelei/segments > data/dev_end.txt
  
  # Paste the start and end times to the end of each file in train_scp.txt. 
  # Delimit the file and times by [
  paste -d'[' data/train_scp.txt data/train_start.txt data/train_end.txt > data/train_scp_times.txt
  paste -d'[' data/dev_scp.txt data/dev_start.txt  data/dev_end.txt > data/dev_scp_times.txt
  
  # Paste the keys to the end of each file separated by :
  paste -d':' data/train_scp_times.txt data/train.keys > data/train.scp
  paste -d':' data/dev_scp_times.txt data/dev.keys > data/dev.scp
  
  # Concatenate train and dev .scp files to make all.scp
  cat data/train.scp data/dev.scp > data/all.scp
  
  # Clean up directory a little
  rm data/*.txt
  
  echo "-----------------------------------------------------"
  echo "Checking that the .scp and .keys files are correct"
  echo "-----------------------------------------------------"
  
  num_keys=$(wc -l data/all.keys | cut -d' ' -f1)
  num_scp=$(wc -l data/all.scp | cut -d' ' -f1)
  
  num_train=$(wc -l data/train.keys | cut -d' ' -f1)
  num_dev=$(wc -l data/dev.keys | cut -d' ' -f1)
  num_total=$(($num_train + $num_dev))
  
  [ $num_keys -eq $num_scp ] && [ $num_total -eq $num_scp ] || exit 1 
    
  touch data/.aud.done
fi

echo "Data seems to have been successfully prepared"
