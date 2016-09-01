#! /usr/bin/python 

import pickle
import sys
import os
import math
from Transducer import Grapheme
import argparse
import json

def main():
    if len(sys.argv[1:]) < 2:
        print("Usage: ./transducer-to-pdfArc-fst.py <input_pickled_model> <output_dir>")
        sys.exit(1)  
    
    parser = argparse.ArgumentParser()
    parser.add_argument("model",help="rspecifier path to pickled transducer model.")
    parser.add_argument("output_dir",help="directory in which all fst models "
                                            "will be created and stored.")
    args = parser.parse_args()

    MODEL = args.model
    OUTPUT = args.output_dir

    # Create output directory if output directory does not exist
    if not os.path.exists(OUTPUT):
        os.makedirs(OUTPUT)

    # Load the model
    graphemes = pickle.load(open(MODEL,"rb"))

    # Write output symbols (tokenize graphemes) 
    osyms = sorted(graphemes.keys())
    with open(os.path.join(OUTPUT,"osyms.txt"),"w") as f_osyms:
        f_osyms.write("<eps> 0\n")
        int_val = 1
        for osym in osyms: 
            f_osyms.write("%s %d\n" % (osym,int_val))
            int_val += 1

    # Write acoustic unit symbols (tokenize auds emissions)
    ems = sorted(graphemes[osyms[0]].emissions.keys())
    with open(os.path.join(OUTPUT,"ems.txt"),"w") as f_ems:
        f_ems.write("<eps> 0\n")
        int_val = 1
        for e in ems: 
            f_ems.write("%s %d\n" % (e, int_val))
            int_val += 1             

    # Write FSTs for each grapheme
    for g,g_model in graphemes.iteritems():
        with open(os.path.join(OUTPUT,g+ ".fst"),"w") as f_mdl: 
            for sym in g_model.B.iterkeys():
                weight1 = -math.log(g_model.A['a11'] * g_model.B[sym]['a11']) 
                weight2 = -math.log(g_model.A['a12'] * g_model.B[sym]['a12'])
                 
                f_mdl.write("0 1 %s %s %f\n" % (sym, g, weight1)) 
                f_mdl.write("1 1 %s <eps> %f\n" % (sym, weight1)) 
                f_mdl.write("0 2 %s %s %f\n" % (sym, g, weight2)) 
                f_mdl.write("1 2 %s <eps> %f\n" % (sym, weight2)) 
            
            # Null arc
            weight_null = -math.log(g_model.A['q12'])
            f_mdl.write("0 2 <eps> %s %f\n" % (g, weight_null))
            
            # Final state
            f_mdl.write("2")

if __name__ == "__main__":
    main()


