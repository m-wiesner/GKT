#!/usr/bin/python

import os
import sys
import codecs

def main():

  if len(sys.argv[1:]) < 3:
    print("Usage: ./ali_int2sym.py <ali_file_in> <ali_file_out> <phones.txt>")
    sys.exit(1)

  ALI = sys.argv[1]
  ALI_OUT = sys.argv[2]
  PHONES = sys.argv[3] 


  with codecs.open(PHONES,"r","utf-8") as fp:
    phones_map = {}
    for l in fp:
      l_vals = l.strip().split(" ")
      phones_map[l_vals[1]] = l_vals[0].split("_")[0]

  with codecs.open(ALI,"r","utf-8") as fp:
    with codecs.open(ALI_OUT,"w","utf-8") as fo:
      for l in fp:
        l_vals = l.strip().split(" ")
        fo.write("%s " % l_vals[0])
        for v in l_vals[1:-1]:
          fo.write("%s " % phones_map[v])
        fo.write("%s\n" % phones_map[l_vals[-1]])

if __name__ == "__main__":
  main()
