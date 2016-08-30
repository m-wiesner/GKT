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

    # Write input symbols (tokenize pdf ids)
    pdf_ids = {"<eps>":0}
    with open(os.path.join(OUTPUT,"pdf_ids.txt"),"w") as f_pdf_ids:
        f_pdf_ids.write("<eps> 0\n")
        int_val = 1
        for g,v in graphemes.iteritems():
            pdf_ids[g] = {}
            for pdf in v.B[ems[0]].iterkeys():
                f_pdf_ids.write("%s_%s %d\n" % (g, pdf, int_val))
                pdf_ids[g][pdf] = int_val
                int_val += 1

    json.dump(pdf_ids,open(os.path.join(OUTPUT,"pdfs.bin"),"wb"))

    # =============================================
    # FST STRUCTURE FOR FST of HMM
    # =============================================
    # 5 arcs:
    #                            __
    #   1.  pdf_1:sym1 / a11    |  | 2. pdf_1:<eps> / a11
    # 0 --------->--------------- 1 ---------
    # |    4. pdf_2:sym1 / a12              |  3. pdf_2:<eps> / a12
    # |---------->--------------- 2 -----<--
    # |__________________________|
    #       5. <eps> : sym1 / q12

 
    # Write individual fsts
    for g,g_model in graphemes.iteritems():
        with open(os.path.join(OUTPUT,g + ".fst"),"w") as f_mdl:
            # Arc 1.
            weight = -math.log(g_model.A['a11'])
            f_mdl.write("0 1 %s_%s %s %f\n" % (g, 'a11', g, weight))  
            
            # Arc 2.
            weight = -math.log(g_model.A['a11'])
            f_mdl.write("1 1 %s_%s <eps> %f\n" % (g, 'a11', weight))

            # Arc 3.
            weight = -math.log(g_model.A['a12'])
            f_mdl.write("1 2 %s_%s <eps> %f\n" % (g, 'a12', weight))

            # Arc 4.
            weight = -math.log(g_model.A['a12'])
            f_mdl.write("0 2 %s_%s %s %f\n" % (g, 'a12', g, weight))

            # Arc 5.
            weight = -math.log(g_model.A['q12'])
            f_mdl.write("0 2 <eps> %s %f\n" % (g, weight))
            
            # Final state
            f_mdl.write("2")

if __name__ == "__main__":
    main()

