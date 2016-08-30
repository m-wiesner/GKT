#!/usr/bin/python

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import codecs
import sys

if len(sys.argv[1:]) == 0:
  print("Usage: ./local_lorelei/bar_stats.py STATS1, STATS2, ... ")
  sys.exit(1)

if len(sys.argv[1:]) > 7:
  print("Too many input arguments. 7 or fewer supported.")
  sys.exit(1)

values = {}
for f in sys.argv[1:]:
  with codecs.open(f,"r","utf-8") as fp:
    values[f] = [(l.strip().split(" ")[0],float(l.strip().split(" ")[1])) for l in fp]


# Find max number of x's to plot
max_num = 0
for f in values.keys():
  if(len(values[f]) > max_num):
    max_num = len(values[f])

colors = 'brgcmyk'
for i_f,f in enumerate(values.keys()):
  plt.bar(range(len(values[f])), [i[1] for i in values[f]], width=0.6, alpha=(0.9/(i_f + 1)), color=colors[i_f], hold=True)

plt.savefig("_".join(sys.argv[1:])+".png", format='png')

