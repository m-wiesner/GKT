#!/usr/bin/python

import os
import sys
import codecs

def main():
  if len(sys.argv[1:]) < 2:
    print("Usage: ./words2graphs.py <rspecifier_word_file> <wspecifier_grapheme_file>")
    sys.exit(1) 

  words = sys.argv[1]
  graphs = sys.argv[2]
  
  with codecs.open(words,"r","utf-8") as fp:
    with codecs.open(graphs,"w","utf-8") as fo:
      for line in fp:
        line_words = line.strip().split(" ")
        for w in line_words:
          if not w.startswith("<"):
            fo.write("%s " % " ".join(w.lower()))
          else:
            fo.write("%s " % w)
        fo.write("\n")
        
if __name__ == "__main__":
  main()


