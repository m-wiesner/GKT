#!/usr/local/bin/pypy

from __future__ import print_function
import pickle
import sys
import os
from Transducer import Grapheme, Utterance
import argparse
import json
import mlf

DEF_MIN_LL = -999.0

def usage():
    print(" Usage: ./make_transducer.py [opts] <EMISSIONS> <REF_ALI> <AUD_ALI> <OUTPUT>")
    print("     --iter : specify the number of training iterations. Default = 8")
    print("     --train_size : specify what fraction of input data to train on. Default = 1.0")
    print("     --add_1_smooth: specify the add val parameter for smoothing HMM arc counts. Default = 0.01")

def main():
    if len(sys.argv[1:]) == 0:
        usage()
        sys.exit(1)
       
    # Parser Arguments 
    parser = argparse.ArgumentParser()
    parser.add_argument("input1", help="rspecifier alignment format such as "
                                        "the output of ali-to-phones in kaldi.")
    parser.add_argument("input2", help="rspecifier alignment format such as "
                                        "the output of ali-phones in kaldi.")
    parser.add_argument("output", help="wspecifier pickled list of trained "
                                        "Grapheme HMM objects.")
    parser.add_argument("emissions", help="rspecifier distributions p(aud | graph) "
                                            "stored in json format.")
    parser.add_argument("-I","--iters", action="store", help="Number of iterations of training.",
                        type=int, default=8)
    parser.add_argument("-T","--train_size", action="store", help="Fraction of the matched "
                        "input files over which to train.", type=float, default=1.0)
    parser.add_argument("-L","--add_1_smooth", action="store", help="Smoothing "
                                        "value for HMM arcs", type=float, default = 0.01)
    
    args = parser.parse_args()
    
    EMISSIONS = args.emissions
    REF_ALI  = args.input1
    RES_ALI  = args.input2
    OUTFILE  = args.output
    ITERS    = args.iters
    TRAINING_SIZE = args.train_size
    LAM = args.add_1_smooth
    
    # Get training and tesing test
    ref_utterances = mlf.ali2dict(REF_ALI)
    train_utterances = mlf.ali2dict(RES_ALI)
    train_utterances = {u:train_utterances[u] for u in ref_utterances.iterkeys()}
    emissions_dict = json.load(open(EMISSIONS,"rb"))
    
    graphemes = {name: Grapheme(name,emissions,lam=LAM) for name,emissions in emissions_dict.iteritems()}    
    num_utts = len(ref_utterances.keys())
    train_keys = sorted(train_utterances.keys())[0:int(num_utts*TRAINING_SIZE)]
    num_train = len(train_keys)

    LL_old = DEF_MIN_LL
    for i in range(ITERS):
        print("Iteration ", i )
        LL = 0.0
        num_frames = 0.0
        for i_u,u in enumerate(train_keys,start=1):
            sys.stdout.write("Created utterance %d of %d\r" % (i_u,num_train) )
            sys.stdout.flush()
            utt = Utterance(u,ref_utterances[u],graphemes)
            seq = train_utterances[u].split(" ")
            num_frames += len(seq)
            LL += utt.train_sequence(seq)

        LL /= num_frames   
        if LL >= LL_old:
            LL_old = LL
        else:
            print("ERROR")
            print("LL: %f, LL_old: %f" % (LL, LL_old))

        print(" ") 
        print("LL: %f" % LL )
        for g in graphemes.itervalues():
            g.update()

    pickle.dump(graphemes, open( OUTFILE, "wb" ) )

# Initialize inputs from unigram distribution of grapheme level alignments
if __name__ == "__main__":
    main()
 
