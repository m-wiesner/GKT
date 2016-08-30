import sys
import numpy as np
import codecs

# The following conversions are all possible
# _________________________________
# |       | ali   | mlf   | python
# |_______|_______|_______|________
# |ali    | N/A   | true  | true
# |_______|_______|_______|________
# |mlf    | true  | N/A   | true
# |_______|_______|_______|________
# |python | true  | true  | N/A
# |_______|_______|_______|________

def ali2dict(path_to_ali,utt_id=True):
  
  ali_dict = {}
  if(utt_id):
    with open(path_to_ali) as fp:
      for l in fp:
        l_vals = l.strip().split(" ")
        ali_dict[l_vals[0]] = " ".join(l_vals[1:])
  else:
    with open(path_to_ali) as fp:
      int_val = 0
      for l in fp:
        ali_dict[int_val] = l.strip()
        int_val += 1
  return ali_dict

def python2frames(python_mlf_format):
  utterances_ref = python_mlf_format.keys()
  label_map = []
  cluster_map = []
  for utt in utterances_ref:
    for seg in python_mlf_format[utt]:
      seg_len = seg[1] - seg[0]
      label_map += [seg[2]]*seg_len
  return label_map
    
def mlf_concat(lbls_dir,keys_file,output,EXT=".lab"):
  '''
    Usage: mlf_concat(labels_directory, keys, output_mlf_file)

    Concatenates list of label files (such as AUD output (.lab)) into a single MLF file.

    Inputs:
      labels_directory -- directory containing individual mlf files
      keys -- file containing a list of all the keys (filenames minus extension) to be scored
      output_mlf_file -- A file with all of the label files concatenated into a single mlf format file
      EXT -- extention to add to keys. Keys are normally utterance ids. Default is .lab
  '''
  
  with open(keys_file,"r") as fp:
    keys = [l.strip() + EXT for l in fp]

  with open(output,"w") as fp:
    fp.write("#!MLF!#\n")
    for l in keys:
      fp.write('"*/%s"\n' % l)
      with open(lbls_dir + "/" + l,"r") as fk:
        for k in fk:
          fp.write("%s\n" % k.strip())
        fp.write(".\n")

def ali2python(ali):
  '''
    Usage: ali2python(ali)

    Inputs:
      ali -- path to alignments file

    Outputs:
      files -- python object representing alignments files.

      files = {utt1: [(start, end, sym), (start, end, sym), ...],
               utt2: [(start, end, sym), (start, end, sym), ...],
               ... }
  '''
  with codecs.open(ali,"r","utf-8") as fp:
    phone2tok = {}
    tok = 0
    for line in fp:
      line_vals = line.strip().split(" ")
      for lv in line_vals[1:]:
        try:
          if(phone2tok[lv]):
            continue 
        except:
          phone2tok[lv] = tok
          tok += 1
  
  sym2phone = {sym:sym for sym in phone2tok.keys()}
  tok2phone = {phone2tok[p]:p for p in phone2tok.keys()}
        
  # Convert utterances to nicer data structure we can work with
  utterances = {}
  with codecs.open(ali,"r","utf-8") as fp:
    for line in fp:
      line_vals = line.strip().split(" ")
      utterances[line_vals[0]] = [phone2tok[sym2phone[i]] for i in line_vals[1:]]

  # Write MLF output
  files = {}
  num_utts = len(utterances.keys())
  for utt_i,utt in enumerate(sorted(utterances.keys())):
    files[utt] = []
    first = np.nonzero(np.hstack((True,(np.diff(utterances[utt]) != 0),True)))[0]
    seg_len = np.diff(first)
    first = first[0:-1]
    last = first + seg_len
    
    for i in range(len(first)):
      files[utt].append((first[i], last[i], tok2phone[utterances[utt][first[i]]]))
  
  return files

def python2mlf(files,mlf,ext="ALI"):
  '''
    Usage: python2mlf(files,mlf,ext="ALI")

    Converts python structure storing utterance information to an mlf file.

    Inputs:
      files -- python structure (see ali2python)
      mlf -- output mlf file
      ext -- extension added to each utt_id (default = "ALI")
  '''
  with codecs.open(mlf,"w","utf-8") as fp:
    fp.write("#!MLF!#\n")
    for utt in sorted(files.keys()): 
      fp.write('"*/%s.%s"\n' % (utt,ext))
      for seg in files[utt]:
        fp.write("%d %d %s\n" % (seg[0]*100000,seg[1]*100000,str(seg[2])) ) 
      fp.write(".\n")

def python2ali(files,ali):
  '''
    Usage: python2ali(files,mlf,ext="ALI")

    Converts python structure storing utterance information to an alignment file.

    Inputs:
      files -- python structure (see ali2python)
      ali -- output ali file
  '''

  with codecs.open(ali,"w","utf-8") as fp:
    for utt in sorted(files.keys()):
      fp.write("%s " % utt)
      for seg in files[utt]:
        seg_len = seg[1] - seg[0]
        fp.write("%s " % (" ".join([seg[2]]*seg_len)))
      fp.write("\n")

def change_phones(files,phones):
  '''
    Usage: change_phones(files,phones)

    Maps one labeling set to a new one specified in phones. The phones file
    should be formatted as such:

    new_phone_m1 old_phone_n1
    new_phone_m2 old_phone_n2
    new_phone_m3 old_phone_n3
    ...

    So that the mapping is 1-to-1 or many-to-1, but never 1-many.

    Inputs:
      files -- python structure containing mlf-like data for all utterances
      phones -- path to file defining new mapping

    Function operates on the first input argument.
  ''' 
  # Get phone mapping
  with codecs.open(phones,"r","utf-8") as fp:
    old2new = {}
    for l in fp:
      line_vals = l.strip().split(" ")
      old2new[line_vals[1]] = line_vals[0]

  for utt in files.keys():
    segs = []
    for seg in files[utt]:
      segs.append((seg[0],seg[1],old2new[seg[2]]))
    files[utt] = segs
    
def ali2mlf(ali,mlf,phones=None,ext="ALI"):
  '''
    Usage: ali2mlf(ali,mlf,phones=None)

    Take a kaldi formatted output of alignment, or otherwise kaldi data/text
    file formatted as:

    utt_id1 word1 word2 ....
    utt_id2 word1 word2 ....
    .
    .
    .
    utt_idN word1 word2 ...
    
    and map it to an mlf file formatted as:

    #!MLF!#
    "*/utt_id1.ext"
    0 1100000 a1
    1200000 1500000 a3
    1600000 2500000 a6
    .
    "*/utt_id2.ext"
    0 2100000 a4

    Input:
      ali -- rspecifier kaldi type ali file described above
      mlf -- wspecifer mlf output file
      phones -- path to mapping from symbol set to integers used in ali
      ext -- extension to use for utterance name (default = "ALI")
             we only use this to be consisent in how we make the mlf files
             for compatibility with other scripts.
      
  '''
  # Getting mapping from integers to context independent phones
  if phones:
    with codecs.open(phones,"r","utf-8") as fp:
      sym2phone = {}
      for line in fp:
        [phone,phone_int] = line.strip().split(" ")
        if len(phone.split("_")) == 1:
          sym2phone[phone_int] = phone
        else:
          sym2phone[phone_int] = "_".join(phone.split("_")[0:-1]) 

    phone2tok = {int2phone[p]:i for i,p in enumerate(int2phone.keys())}
    tok2phone = {phone2tok[p]:p for p in phone2tok.keys()}
  else:
    with codecs.open(ali,"r","utf-8") as fp:
      phone2tok = {}
      tok = 0
      for line in fp:
        line_vals = line.strip().split(" ")
        for lv in line_vals[1:]:
          try:
            if(phone2tok[lv]):
              continue 
          except:
            phone2tok[lv] = tok
            tok += 1
    
    sym2phone = {sym:sym for sym in phone2tok.keys()}
    tok2phone = {phone2tok[p]:p for p in phone2tok.keys()}
        
  # Convert utterances to nicer data structure we can work with
  utterances = {}
  with codecs.open(ali,"r","utf-8") as fp:
    for line in fp:
      line_vals = line.strip().split(" ")
      utterances[line_vals[0]] = [phone2tok[sym2phone[i]] for i in line_vals[1:]]

  # Write MLF output
  with open(mlf,"w") as fp:
    fp.write("#!MLF!#\n")
    num_utts = len(utterances.keys())
    for utt_i,utt in enumerate(sorted(utterances.keys())):
      fp.write("\"*/%s.%s\"\n" % (utt,ext))
      first = np.nonzero(np.hstack((True,(np.diff(utterances[utt]) != 0),True)))[0]
      seg_len = np.diff(first)
      first = first[0:-1]
      last = first + seg_len

      for i in range(len(first)):
        fp.write(str(first[i]*100000) + " " + str(last[i]*100000) + " " + str(tok2phone[utterances[utt][first[i]]]) + "\n")

      fp.write(".\n")

def mlf2ali(mlf,ali):
  '''
    Usage: mlf2ali(mlf,ali)

    Converts mlf file to kaldi style transcription.

    utt_id1 tok1 tok2 ...
    utt_id2 tok1 tok2 ...

    Input: mlf - rspecifer mlf file
           ali - wspecifer ali file
  '''
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

def mlf2python(filename):
  '''
    Usage: mlf2python(filename)
      filename -- mlf file

    Converts the mlf file into a dictionary. Each key is utterance id. The value
    corresponding to each key is a list of segments. Each segment has 3 values.
    The first value is the beginning frame of the segnment, the second value is 
    the last frame of the segment and the last value is the label of the segment.
  
    output:
      files = {utt1 : [ [0 11 'SIL'], [12 15 'H'], [16 25 'A'], [26 30 'H'], [31 41 'A'] ], utt2 : ...}
  '''

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

def align(ref,res):
  '''
    Usage: align(reference_mlf, response_mlf)
      
      Aligns the response mlf to the reference mlf.

      Arguments: reference_mlf -- the python representation of reference mlf
                 response_mlf  -- the python representation of response mlf

  '''
  
  ref_labels = []
  res_labels = []

  for utt in ref.keys():
    # Only use utterances common to both ref and res
    try:
      ref_utt = ref[utt]
      res_utt = res[utt]
    except KeyError:
      continue

    mu_ref = np.asarray([ 0.5*(seg[0] + seg[1]) for seg in ref_utt])
    
    new_lbls = []
    res_lbls = []
    for seg in res_utt:
      closest_seg = ((0.5*(seg[0] + seg[1]) - mu_ref)**2).argmin()
      new_lbls.append(ref_utt[closest_seg][2])
      res_lbls.append(seg[2])
          
    ref_labels.extend(new_lbls)
    res_labels.extend(res_lbls)
  
  return (ref_labels, res_labels)

def collect_reference_transcriptions(ref,res):
  '''
    Usage: collect_reference_transcriptions(ref,res)

    Reformats reference and response mlfs as such:
      ref_transcription = {'seg1': [[trans1], [trans2], [trans3], ...]}

    Arguments:
      ref -- reference python representation of mlf
      res -- response python representation of mlf
  '''
  
  ref_transcriptions = {}

  for utt in ref.keys():
    try:
      res_utt = res[utt]
      mu_ref = np.asarray([ 0.5*(seg[0] + seg[1]) for seg in ref[utt] ])
      closest_segs = np.asarray([ ((0.5*(seg[0] + seg[1]) - mu_ref)**2).argmin() for seg in res_utt])
   
      previous_seg = None
      for i,seg in enumerate(closest_segs):
        if previous_seg != seg:
          # Add previous segment to the dictionary entry ref_seg
          try:
            ref_transcriptions[ref[utt][seg][2]].append([res_utt[i][2]])
          except KeyError:
            ref_transcriptions[ref[utt][seg][2]] = [[res_utt[i][2]]]
          # Start new example of the new ref_seg
        else:
          ref_transcriptions[ref[utt][seg][2]][-1] += [res_utt[i][2]]
        
        previous_seg = seg
    
    except KeyError:
      continue         
  
  return ref_transcriptions

