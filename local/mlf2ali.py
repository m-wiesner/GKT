#!/usr/bin/python

import sys

def main():
  if len(sys.argv[1:]) < 2:
    print("Usage: ./mlf2ali.py <rspecifer_mlf> <wspecifer_ali>")
    sys.exit(1)

  mlf = sys.argv[1]
  ali = sys.argv[2]
  
  with open(mlf,"r") as fp:
    with open(ali,"w") as fo:
      utt = []
      for l in fp:
        line = l.strip()
        # Ignore these lines #!MLF!#
        if line != "#!MLF!#":
          # Catch file name formatted as ("*/NAME.EXT")
          if line.startswith('"*/'):
            utt.append(line.split('"*/')[1].split(".")[0])
          elif line == ".":
            fo.write("%s\n" % " ".join(utt))
            utt = []
          else:
            utt.append(line.split(" ")[2])           

if __name__ == "__main__":
  main()


