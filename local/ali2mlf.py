#!/usr/bin/python

import os
import sys
import codecs
import numpy as np

def main():

  if len(sys.argv[1:]) < 3:
    print("Usage: ./ali2mlf <rspec_kaldi_ali_file> <wspec_mlf_file> <data/lang/phones.txt>")
    sys.exit(1)

  ali=sys.argv[1]
  mlf=sys.argv[2]
  phones=sys.argv[3]

  # Getting mapping from integers to context independent phones
  with codecs.open(phones,"r","utf-8") as fp:
    int2phone = {}
    for line in fp:
      [phone,phone_int] = line.strip().split(" ")
      if len(phone.split("_")) == 1:
        int2phone[int(phone_int)] = phone
      else:
        int2phone[int(phone_int)] = "_".join(phone.split("_")[0:-1]) 

  phone2tok = {int2phone[p]:i for i,p in enumerate(int2phone.keys())}
  tok2phone = {phone2tok[p]:p for p in phone2tok.keys()}
  # Convert utterances to nicer data structure we can work with
  utterances = {}
  with codecs.open(ali,"r","utf-8") as fp:
    for line in fp:
      line_vals = line.strip().split(" ")
      utterances[line_vals[0]] = [phone2tok[int2phone[int(i)]] for i in line_vals[1:]]
  
  # Write MLF output
  with open(mlf,"w") as fp:
    fp.write("#!MLF!#\n")
    num_utts = len(utterances.keys())
    for utt_i,utt in enumerate(sorted(utterances.keys())):
      sys.stdout.write("Utterance %d of %d \r" % (utt_i + 1, num_utts))
      sys.stdout.flush()
      fp.write("\"*/%s.ALI\"\n" % utt)
      first = np.nonzero(np.hstack((True,(np.diff(utterances[utt]) != 0),True)))[0]
      seg_len = np.diff(first)
      first = first[0:-1]
      last = first + seg_len

      for i in xrange(len(first)):
        fp.write(str(first[i]*100000) + " " + str(last[i]*100000) + " " + str(tok2phone[utterances[utt][first[i]]]) + "\n")
      
      fp.write(".\n")

  print("")

if __name__ == "__main__":
  main()
