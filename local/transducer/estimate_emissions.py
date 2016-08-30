#!/usr/bin/python

import math
import sys
import json
import os
import numpy as np
import argparse
import mlf

def tokenize(labels):
    lbl2int = {l:i for i,l in enumerate(set(labels))}
    labels = [lbl2int[l] for l in labels]
    int2lbl = {i:l for l,i in lbl2int.iteritems()}
    return (labels, int2lbl)

def estimate_p_au_given_grapheme(ref_ints, res_ints):
    num_ref = len(set(ref_ints))
    num_res = len(set(res_ints))
    
    ref_ints = np.asarray(ref_ints)
    res_ints = np.asarray(res_ints)
    
    # Compute p(grapheme | letter) on English for example
    # using reference English graphemes and decoded Turkish
    # acoustic units.
    p_au_given_l = np.zeros( (num_ref, num_res) )
    for l in range(num_ref):
        idx = np.where(ref_ints == l)
        if len(idx[0]) > 0:
            p_au_given_l[l] = np.histogram(res_ints[idx], bins=range(0,num_res+1))[0]/float(len(idx[0]))
            
    return p_au_given_l

def main():
    if len(sys.argv[1:]) < 3:
        print("Usage: ./Transducer.py <REF_MLF> <RES_MLF> <OUTFILE>")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("input1", help="Reference MLF of the linguistic units we are "
                                        " attempting to learn.")
    parser.add_argument("input2", help="Response MLF for the acoustic sequence describing "
                                        "the sequence of units we are trying to learn.")
    parser.add_argument("output", help="The output emissions dictionary containing "
                                        "information about the distribution "
                                        "p(acoustic | linguistic) stored as json object.")
    args = parse.parse_args()

    # Initialize emissions distribution for transducer
    REF_FILE = args[1]
    RES_FILE = args[2]
    OUT_FILE = args[3]

    ref = mlf.mlf2python(REF_FILE)
    res = mlf.mlf2python(RES_FILE)
    (ref_labels, res_labels) = mlf.align(ref,res)
    (ref_ints, int2ref) = tokenize(ref_labels)
    (res_ints, int2res) = tokenize(res_labels)
    p_au_given_l = estimate_p_au_given_grapheme(ref_ints, res_ints)
    emissions_dict = {int2ref[i]:{int2res[j]:col for j,col in enumerate(row.tolist())} for i,row in enumerate(p_au_given_l)}
    
    if not os.path.exists(os.path.dirname(OUT_FILE)):
        os.makedirs(os.path.dirname(OUT_FILE))
        
    json.dump(emissions_dict,open(OUT_FILE,"wb"))

if __name__ == "__main__":
    main()
