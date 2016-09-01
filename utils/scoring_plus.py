#!/usr/bin/python

from __future__ import print_function
import numpy as np
import sys
import os
import getopt
import scipy.stats as stats

try:
    import B3score
    B3flag=True
except:
    print("B-Cubed scoring package B3score is not installed.")
    print("Try to install with < pip install --user B3score > for B-Cubed scores.")
    print("Continuing ...")
    B3flag=False

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
                    lines.append((int(float(start)/100000.0), int(float(stop)/100000.0), label)) 
            elif(line.strip() == "."):
                files[utterance] = lines
                lines = []
    return files

# Create frame level labels
#def make_frame_labels(ref,mlf):
#    utterances_ref = ref.keys()
#    label_map = []
#    cluster_map = []
#    for utt in utterances_ref:
#        for seg in ref[utt]:
#            seg_len = seg[1] - seg[0]
#            label_map += [seg[2]]*seg_len
#        for seg in mlf[utt]:
#            seg_len = seg[1] - seg[0]
#            cluster_map += [seg[2]]*seg_len
#    
#    last_frame = min((len(label_map),len(cluster_map)))
#    label_map = label_map[0:last_frame]
#    cluster_map = cluster_map[0:last_frame]
#    
#    label2int = {v:i for i,v in enumerate(set(label_map))}
#    cluster2int = {v:i for i,v in enumerate(set(cluster_map))}
#    
#    label_map = [label2int[i] for i in label_map]
#    cluster_map = [cluster2int[i] for i in cluster_map]
#    return [label_map,cluster_map, label2int, cluster2int]
    
def make_segment_labels(ref,mlf):
    label_map = []
    cluster_map = []
         
    for utt in ref.keys():
        ref_utt = ref[utt]
        mlf_utt = mlf[utt]
       
        mu_ref = []
        mode_ref = []
        for seg in ref_utt:
            seg_len = seg[1] - seg[0]
            mu_ref.append(seg[0]+0.5*seg_len)
        
        mu_ref = np.asarray(mu_ref)        
        
        new_utt = []
        cluster_utt = []
        for seg in mlf_utt:
            seg_len = seg[1] - seg[0]
            mu_seg = seg[0] + 0.5*seg_len
            closest_seg = ((mu_seg - mu_ref)**2).argmin()
            new_utt.append(ref_utt[closest_seg][2])
            cluster_utt.append(seg[2])

        cluster_map.extend(cluster_utt)
        label_map.extend(new_utt)

    label2int = {v:i for i,v in enumerate(set(label_map))}
    cluster2int = {v:i for i,v in enumerate(set(cluster_map))}
    
    label_map = [label2int[i] for i in label_map]
    cluster_map = [cluster2int[i] for i in cluster_map]
    return [label_map,cluster_map, label2int, cluster2int]

#def make_voting_segment_labels(ref,mlf):
#    # Get segments from frames
#    [label_map,cluster_map, label2int, cluster2int] = make_frame_labels(ref,mlf)
#
#    label_map = np.array(label_map)
#    cluster_map = np.array(cluster_map)
#    
#    first = np.nonzero(np.hstack((True,(np.diff(cluster_map) != 0),True)))[0]
#    seg_len = np.diff(first) 
#    first = first[0:-1]
#    last = first + seg_len
#    
#    idx = np.array([first,last])
#    
#    segment_clustering = [first]
#    segment_labeling = np.zeros((idx.shape[1],))
#    
#    # Majority Vote
#    for i in xrange(idx.shape[1]):
#        print("\rSegment ", i, " of ", idx.shape[1], sep='', end='') 
#        segment_labeling[i] = stats.mode( label_map[ idx[0][i] : idx[1][i] ] )[0]
#    
#    print("")
#
#    return [label_map, cluster_map]
   
# Create Partitions
def make_partitions(ref,mlf):
    utt_partitions = {}
    utterances_ref = ref.keys()
    for utt in utterances_ref:
        # Grab all the left side boundaries
        mlf_boundaries = set([seg[0] for seg in mlf[utt]])
        ref_boundaries = set([seg[0] for seg in ref[utt]])
        
        # The last boundary label must be < right side boundary of min(mlf[utt][-1], ref[utt][-1])
        min_max_boundary = min([mlf[utt][-1][1],ref[utt][-1][1]])
        max_boundary = max([ mlf[utt][-1][1], ref[utt][-1][1] ])
        segment_boundaries = mlf_boundaries.union(ref_boundaries)
        segment_boundaries = segment_boundaries.difference(range(min_max_boundary,max_boundary+1))
        utt_partitions[utt] = sorted(list(segment_boundaries))
    return utt_partitions

# Map Partitions
def map_partitions(ref,mlf,partitions):
    label_map   = []
    cluster_map = []
    for utt in partitions.keys():
        label_seg = 0
        cluster_seg = 0
        for seg in partitions[utt]:
            while ( ( label_seg < len(ref[utt]) ) and (ref[utt][label_seg][0] <= seg)):
                label_seg += 1
            while ( ( cluster_seg < len(mlf[utt]) ) and   (mlf[utt][cluster_seg][0] <= seg) ):
                cluster_seg += 1
            
            label_map += [ref[utt][label_seg - 1][2]]
            cluster_map += [mlf[utt][cluster_seg - 1][2]]
    
    label2int = {v:i for i,v in enumerate(set(label_map))}
    cluster2int = {v:i for i,v in enumerate(set(cluster_map))}
    
    label_map = [label2int[i] for i in label_map]
    cluster_map = [cluster2int[i] for i in cluster_map]
    return [label_map,cluster_map, label2int, cluster2int]

# Map Partitions
def map_partitions_utt(ref,mlf,partitions):
    label_map   = {}
    cluster_map = {}
    for utt in partitions.keys():
        label_seg = 0
        cluster_seg = 0
        label_map[utt] = []
        cluster_map[utt] = []
        for seg in partitions[utt]:
            while ( ( label_seg < len(ref[utt]) ) and (ref[utt][label_seg][0] <= seg)):
                label_seg += 1
            while ( ( cluster_seg < len(mlf[utt]) ) and   (mlf[utt][cluster_seg][0] <= seg) ):
                cluster_seg += 1
            
            label_map[utt] += [ref[utt][label_seg - 1][2]]
            cluster_map[utt] += [mlf[utt][cluster_seg - 1][2]]
    
    return [label_map,cluster_map]

# Calculate Information Theoretic Quantities
def calculate_information_metrics(label_map, cluster_map):
    num_labels = len(set(label_map))
    num_clusters = len(set(cluster_map))
    
    # Compute marginal distribution
    p_k = np.histogram(cluster_map, bins=range(0,num_clusters+1))[0] / float(len(cluster_map))

    cluster_map = np.array(cluster_map)
    label_map = np.array(label_map)

    # Compute conditional and joint distributions
    p_l_given_k = np.zeros((num_clusters,num_labels))
    for k in range(num_clusters):
        idx = np.where(cluster_map == k)
        if(len(idx[0]) > 0):
            p_l_given_k[k] = np.histogram(label_map[idx], bins=range(0,num_labels+1))[0] / float(len(idx[0]))
        
    p_l = np.dot(p_l_given_k.T , p_k)
    p_lk = p_l_given_k * p_k[:,np.newaxis]

    # Add a small value to prevent divide by zero errors
    p_k += np.finfo(float).eps
    p_l += np.finfo(float).eps
    p_lk += np.finfo(float).eps
    
    # Compute entropies
    H_k  = -(p_k*np.log2(p_k)).sum()
    H_l  = -(p_l*np.log2(p_l)).sum()
    H_lk = -(p_lk*np.log2(p_lk)).sum()
    H_l_given_k = H_lk - H_k
    Information = H_l - H_l_given_k
    Perplexity = 2**H_l_given_k
    NMI_1 = 2*Information / ( H_l + H_k )
    NMI_2 = Information / H_l
    return [Perplexity, Information, NMI_1, NMI_2, H_l, H_k]

# Map Clusters to Labels
def clusters2labels(label_map, cluster_map, N=1):
    num_labels = len(set(label_map))
    num_clusters = len(set(cluster_map))
    
    cluster_map = np.array(cluster_map)
    label_map = np.array(label_map)

    # Compute conditional and joint distributions
    p_l_given_k = np.zeros((num_clusters,num_labels))
    for k in range(num_clusters):
        idx = np.where(cluster_map == k)
        if(len(idx[0]) > 0):
            p_l_given_k[k] = np.histogram(label_map[idx], bins=range(0,num_labels+1))[0] / float(len(idx[0]))
    
    clust2lbl = { k:l.argsort()[-N:] for k,l in enumerate(p_l_given_k)}

    return clust2lbl

# Transcribe Sequence
def transcribe_sequence(clust2lbl, cluster_sequence):
    estimated_labels = []
    for seg in cluster_sequence:
        estimated_labels.append(clust2lbl[seg])
    
    return estimated_labels

# Write Sequences out to a File
def write_sequences_to_file(labels, estimated_labels, label2int, output):
    if(len(labels) != len(estimated_labels)):
        sys.stderr.write("Input sequences not of same length.")
        sys.exit(1)
    
    int2label = {v: k for k, v in label2int.items()}
    # Length of N-best    
    n_best_length = len(estimated_labels[0])
    with open(output,"w",) as fp:
        for l in range(len(labels)):
            fp.write("%s " % labels[l])
            for n in range(n_best_length):
                fp.write("%s " % int2label[estimated_labels[l][n_best_length-1-n]])
            fp.write("\n")
            
# Calculate Phone Error Rate
def calculate_PER(label_map, cluster_map, N=1):
    clust2lbl = clusters2labels(label_map, cluster_map, N=N)
    
    # Convert everything to numpy for convenience
    label_map = np.array(label_map)
    cluster_map = np.array(cluster_map)
    
    matches = np.zeros((cluster_map.size,))
    for seg_i,seg in enumerate(cluster_map):
        matches[seg_i] = (label_map[seg_i] in clust2lbl[seg])
    
    return matches.sum()/float(matches.size)
    
# Calculate all metrics
def main():
    opts,args = getopt.getopt(sys.argv[1:],"hp:t:","[]")
  
    output_map_file = None
    output_dir = None 
    for o,a in opts:
        if(o in ("-h", "--help")):
            print("Usage: python scoring_plus.py [opts ] <ref.mlf> <lab.mlf>")
            print(" opts:")
            print("     -h -- help")
            print("     -p <output_map_file> -- create .map file for plotting using plotData.py")
            print("     -t <output_dir> -- transcribe all utterances and place them in output_dir")
            sys.exit()

        if(o == "-t"):
            output_dir = a
        if(o == "-p"):
            output_map_file = a
       
    if (len(args) < 2):
        print("Usage: python scoring_plus.py [opts ] <ref.mlf> <lab.mlf>")
        sys.exit(1)
         
    lattice_size = 5
    ref_file = args[0]
    mlf_file = args[1]
     
    ref = mlf2python(ref_file)
    mlf = mlf2python(mlf_file)

    # Remove keys in references with no match in the mlf
    matching_keys = set(ref.keys()) & set(mlf.keys())
    number_keys_removed = len(ref.keys()) - len(matching_keys)
    number_keys_removed_mlf = len(mlf.keys()) - len(matching_keys)
    ref = {k : ref[k] for k in matching_keys}
    mlf = {k: mlf[k] for k in matching_keys}
    print("%d keys were removed from reference." % number_keys_removed)
    print("%d keys were removed from mlf." % number_keys_removed_mlf)
    
    partitions = make_partitions(ref,mlf)
    print("Making response partitions")
    [label_map, cluster_map, label2int, cluster2int] = map_partitions(ref,mlf,partitions)
    #print("Making frame level transcription")
    #[label_map_frames, cluster_map_frames, f_label2int, f_cluster2int] = make_frame_labels(ref,mlf) 
    print("Making segment level transcription")
    [label_map_segs, cluster_map_segs, c_label2int, c_cluster2int] = make_segment_labels(ref,mlf)

 
    num_ref_units = len(label2int.keys()) 
    num_proposed_units = len(cluster2int.keys())
    
    print("# reference units: %d" % num_ref_units)
    print("# proposed units: %d" % num_proposed_units)

    [P,I,NMI_1,NMI_2,H_l,H_k] = calculate_information_metrics(label_map, cluster_map) 
    #[Pf,If,NMI_1f,NMI_2f,H_lf, H_kf] = calculate_information_metrics(label_map_frames, cluster_map_frames) 
    [Pc,Ic,NMI_1c,NMI_2c,H_lc,H_kc] = calculate_information_metrics(label_map_segs, cluster_map_segs)

    if(B3flag):
        [FB3,_,_] = B3score.calc_b3(label_map,cluster_map)
        #[FB3f,_,_] = B3score.calc_b3(label_map_frames, cluster_map_frames)
        [FB3c,_,_] = B3score.calc_b3(label_map_segs, cluster_map_segs)


    print("2*I(X;Y)/(H(X) + H(Y)) Boundary union: %.4f" % NMI_1)
    #print("2*I(X;Y)/(H(X) + H(Y)) Frame level: %.4f" % NMI_1f)
    print("* 2*I(X;Y)/(H(X) + H(Y)) Closest center: %.4f" % NMI_1c)
    print("")
    print("I(X;Y)/(H(X)) Boundary union: %.4f" % NMI_2)
    #print("I(X;Y)/(H(X)) Frame level: %.4f" % NMI_2f)
    print("* I(X;Y)/(H(X)) Closest center: %.4f" % NMI_2c)
    print("")
    print("Perplexity Boundary union: %.4f" % P)
    #print("Perplexity Frame level: %.4f" % Pf)
    print("* Perplexity Closest center: %.4f" % Pc)
    print("")
    print("I(X;Y) Boundary union: %.4f" % I)
    #print("I(X;Y) Frame level: %.4f" % If)
    print("* I(X;Y) Closest center: %.4f" % Ic) 
    print("")
    print("H(X) Boundary union: %.4f" % H_l)
    #print("H(X) Frame level: %.4f" % H_lf)
    print("* H(X) Closest center: %.4f" % H_lc)
    print("")
    print("H(Y) Boundary union: %.4f" % H_k)
    #print("H(Y) Frame level: %.4f" % H_kf)
    print("* H(Y) Closest center: %.4f" % H_kc)

    if(B3flag):
      print("")
      print("F-bcubed Boundary union: %.4f" % FB3)
      #print("F-bcubed Frame level: %.4f" % FB3f)
      print("* F-bcubed Closest center: %.4f" % FB3c)
    
    # ------------------- Plot Confusion Matrix ------------------------
    # Map 61 phone label integers to Timit phones
    if(output_map_file):
        print("Creating boundary union .map file")
        int2label = {v:k for k,v in label2int.items()}
        phones = [int2label[l] for l in label_map]
        # Create .map file
        with open(output_map_file,"w") as fp:
            for i in range(len(phones)):
                fp.write("%d %s %s\n" % (0,phones[i],cluster_map[i]))

        print("Creating closest segment .map file")
        int2label = {v:k for k,v in c_label2int.items()}
        phones = [int2label[l] for l in label_map_segs]
        # Create .map file
        output_map_name = os.path.basename(output_map_file)
        output_map_dir  = os.path.dirname(output_map_file)
        closest_output = output_map_dir + "/closest_" + output_map_name
        with open(closest_output,"w") as fp:
            for i in range(len(phones)):
                fp.write("%d %s %s\n" % (0,phones[i],cluster_map_segs[i]))


    # ------------------- Write Transcripts ----------------------------
    # Define mapping of clusters to labels
    if(output_dir):
        [label_map_utt, cluster_map_utt] = map_partitions_utt(ref,mlf,partitions)
        clust2lbl = clusters2labels(label_map, cluster_map, N=lattice_size)
    
        # For each utterance write a new file
        for utt in cluster_map_utt.keys():
            output = output_dir + "/" + utt + ".txt"
            # Transduce cluster values to integers
            cluster_map_utt_ints = [ cluster2int[seg] for seg in cluster_map_utt[utt] ]
        
            # Estimate labels from clust2lbl mapping
            estimated_labels_utt = transcribe_sequence(clust2lbl, cluster_map_utt_ints)
        
            # Write a file for each 
            write_sequences_to_file(label_map_utt[utt], estimated_labels_utt, label2int, output)
                     
if __name__ == "__main__":
    main()

