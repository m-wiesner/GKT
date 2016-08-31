#!/usr/bin/python
import os 
import sys
import codecs
import pdb

def main():
  if len(sys.argv[1:]) < 2:
    print("Usage: ./local_lorelei/calc_phone_statistics.py MLF FREQ DUR")
    print("     Create a file with duration statistics of MLF file")
    sys.exit(1)

  # Read in MLF file
  MLF = sys.argv[1]
  FREQ = sys.argv[2]
  DUR = sys.argv[3]
  files = mlf2python(MLF)
  
  # Compute Frequencies and durations for each symbol
  pdb.set_trace()
  durations = {}
  frequencies = {}
  for f in files.keys():
    for seg in files[f]:
      # When key is present
      try:
        durations[seg[2]].append(seg[1] - seg[0])
        frequencies[seg[2]] += 1

      # When key is not present
      except:
        durations[seg[2]] = [seg[1] - seg[0]]
        frequencies[seg[2]] = 1

  
  num_tokens = sum([frequencies[f] for f in frequencies.keys()])
  frequencies = [(f,frequencies[f]/float(num_tokens)) for f in frequencies.keys()]
  frequencies.sort(key=lambda x:x[1])
  
  avg_durations = [(d,sum(durations[d])/float( len(durations[d])) ) for d in durations.keys()]
  avg_durations.sort(key=lambda x:x[1])
   
  with codecs.open(FREQ,"w","utf-8") as fp:
    for f in frequencies:
      fp.write("%s %.4f\n" % (f[0],f[1])) 

  with codecs.open(DUR,"w","utf-8") as fp:
    for d in avg_durations:
      fp.write("%s %.4f\n" % (d[0],d[1]))

def mlf2python(filename):
  files = {}
  with open(filename,"r") as fp:
    lines = []
    for line in fp:
      if(not line.strip() == "#!MLF!#" and not line.strip() == "."):
        if (line.strip().startswith('"')):
          utterance = line.strip().split(".")[0].split("/")[1]
        else:
          [start, stop, label] = line.strip().split(" ")
          lines.append([int(float(start)/100000.0), int(float(stop)/100000.0), label]) 
      elif(line.strip() == "."):
        files[utterance] = lines
        lines = []
  return files

if __name__ == "__main__":
  main()



