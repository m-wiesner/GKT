#! /usr/bin/python

import sys
import codecs
import os

def main():
  if(len(sys.argv[1:]) < 2):
    print("Usage: ./local_lorelei/babel2cluster.py <data/train/text> <clustering/words> [missing utterances]")
    print(" Converts utterances in an ali format file for BABEL data into "
            "documents, where each document is a conversation with one "
            "utterance on each line, with no utterance_id")

    sys.exit(1)
  
  missing_utterances = []
  if(len(sys.argv[1:]) == 3):
    with codecs.open(sys.argv[3],"r","utf-8") as fp:
      missing_utterances = [l.strip() for l in fp]

  INPUT  = sys.argv[1] 
  OUTPUT = sys.argv[2]
  
  if( not os.path.exists(OUTPUT)):
    os.makedirs(OUTPUT)  

  doc_ids = []
  with codecs.open(INPUT,"r","utf-8") as fp:
    # Initialize utt_id to none
    doc_id_curr = None
    
    # For each line write to a new file for each new utt_id
    for line in fp:
      
      # Retrieve transcription and utterance id 
      line_parts = line.strip().split(" ")
      doc_id_new = "_".join(line_parts[0].split("_")[0:4])
      utt_id = line_parts[0]
      if(utt_id not in missing_utterances):
        utt_transcription = " ".join(line_parts[1:])
      else:
        utt_transcription = ""
      if(doc_id_new != doc_id_curr):
        doc_ids.append(doc_id_new)
        if(doc_id_curr):
          fpo.close()
        fpo = codecs.open(OUTPUT + "/" + doc_id_new + ".txt", "w", "utf-8")     
      fpo.write("%s\n" % utt_transcription)
      doc_id_curr = doc_id_new
    fpo.close()

if __name__ == "__main__":
  main() 
       
    
