#!/usr/bin/python
# Generates a confusion matrix for state-to-label mapping
# files.

import numpy as np
#import matplotlib.pyplot as plt 
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import glob
import sys
import pylab

#Babel Turkish
TURKISH = ['<eps>', '<oov>', '<sss>',
                  '<vns>', 'SIL', '1', '1_"', '1:', '1:_"',
                    '2', '2_"', '2:', '2:_"','5', '5_"', '?',
                    '?_"', 'N', 'N_"', 'S', 'S_"',
                    'Z', 'Z_"', 'a', 'a_"', 'a:', 'a:_"',
                    'b', 'b_"', 'c', 'c_"', 'd', 'd_"',
                    'dZ', 'dZ_"', 'e', 'e_"', 'e:', 
                    'e:_"', 'f', 'f_"', 'g', 'g_"',
                    'gj', 'gj_"', 'h', 'h_"', 'i', 'i_"','i:',
                    'i:_"', 'j', 'j_"', 'k', 'k_"',
                    'l', 'l_"', 'm', 'm_"', 'n', 'n_"',
                    'o', 'o_"', 'o:', 'o:_"', 'p', 'p_"',
                    'r', 'r_"', 'r`', 'r`_"', 's', 's_"',
                    't', 't_"', 'tS', 'tS_"', 'u', 'u_"',
                    'u:', 'u:_"', 'w', 'w_"', 'y', 'y_"',
                    'y:', 'y:_"', 'z', 'z_"']

TURKISH_REDUCED = ['ns','ov', '1', '1:', '2', '2:', '5', '?', 'N', 'S', 'Z', 'a', 'a:','b', 'c', 'd',
                    'dZ', 'e', 'e:', 'f', 'g', 'gj', 'h', 'i', 'i:', 'j', 'k', 'l', 'm', 'n',
                    'o', 'o:', 'p', 'r', 'r`', 's', 't', 'tZ', 'u', 'u:', 'w', 'y', 'y:', 'z']

TURK2REDUCED = {}
for p in TURKISH:
  if p in ("<eps>", "<sss>", "<vns>","SIL"):
    TURK2REDUCED[p] = "ns"
  elif p == "<oov>":
    TURK2REDUCED[p] = "ov"
  else:
    TURK2REDUCED[p] = p.split("_")[0]

# Timit
TIMIT_ALL = ['#h', 'aa', 'ae', 'ah', 'ao', 'aw', 'ax', 'ax-h', 'axr', 'ay', 'b',
       'bcl', 'ch', 'd', 'dcl', 'dh', 'dx', 'eh', 'el', 'em', 'en', 'eng',
       'epi', 'er', 'ey', 'f', 'g', 'gcl', 'h#', 'hh', 'hv', 'ih', 'ix',
       'iy', 'jh', 'k', 'kcl', 'l', 'm', 'n', 'ng', 'nx', 'ow', 'oy', 'p',
       'pau', 'pcl', 'q', 'qcl', 'r', 's', 'sh', 't', 'tcl', 'th', 'uh', 'uw',
       'ux', 'v', 'w', 'y', 'z', 'zh']

# Normal
ALL = ['P', 'B', 'M', 'W', 'F', 'V', 'TH', 'DH', 'T', 'D', 'N',
'S', 'Z', 'L', 'R',  'SH', 'ZH', 'CH', 'JH', 'Y', 'K', 'G', 'NG', 'HH',
'IY', 'IH', 'EH', 'EY', 'AE', 'AA', 'AH', 'AW', 'AO', 'AY', 'UW',
'UH', 'ER', 'OW', 'OY', 'sp']

def dataToArrayDict(phonedict, mapfile, num_units):
  maplist = [mapfile]

  if phonedict == POA_CONSONANTS:
    order = POA_CONSONANTS_ORDER
  elif phonedict == MOA_CONSONANTS:
    order = MOA_CONSONANTS_ORDER
  elif phonedict == FCB_VOWELS:
    order = FCB_VOWELS_ORDER
  phoneCounts = np.zeros((num_units, len(phonedict)))

  for f in maplist:
    fl = open(f, 'r')

    for i, line in enumerate(fl):
      line = line.strip().split()
      phone = line[1]

      for poa in phonedict:
        if phone in phonedict[poa]:
          state = int(line[2])

          phoneIndex = order.index(poa)
          phoneCounts[state - 1][phoneIndex] += 1

    fl.close()

  # for i, line in enumerate(phoneCounts):
  #   print str(i + 1) + ',' + ','.join(map(str, line))
  return phoneCounts, order

def dataToArray(phoneList, mapfile, num_units):
  maplist = [mapfile]

  phoneCounts = np.zeros((num_units, len(phoneList)))
  phones = []

  for f in maplist:
    fl = open(f, 'r')

    for i, line in enumerate(fl):
      line = line.strip().split()
      if(phoneList == TURKISH_REDUCED):
        phone = TURK2REDUCED[line[1]]
      else:
        phone = line[1]

      if phone in phoneList:
        state = int(line[2])
        
        phoneIndex = phoneList.index(phone)
        phoneCounts[state][phoneIndex] += 1

    fl.close()

  # for i, line in enumerate(phoneCounts):
  #   print str(i + 1) + ',' + ','.join(map(str, line))
  return phoneCounts, phoneList

# To diagonal matrix without loss of rows
def arrayToDiagonal(phoneStateMatrix, alphabet, num_units):
  phoneCounts = np.zeros((num_units, len(alphabet)))
  yTicks = list(range(num_units))

  # Dictionary mapping each phone to the rows for which it is
  # most representative, e.g. {'B': [1, 5, 8]}
  mostRepresentativePhones = {}
  for i, row in enumerate(phoneStateMatrix):
    # Get rid of rows of all zeroes in final matrix
    # if np.sum(row) == 0:
    #   continue

    phoneIndex = np.where(row == max(row))[0][0]
    phone = alphabet[phoneIndex]

    if phone not in mostRepresentativePhones:
      mostRepresentativePhones[phone] = []
    # i is 1 less than actual phone group #
    mostRepresentativePhones[phone].append(i)

  bubbleSort(phoneStateMatrix, mostRepresentativePhones, alphabet)

  # Create diagonal matrix by going through each phone's
  # list of representative phone rows and adding them to final matrix
  i = 0
  for phone in alphabet:
    if phone in mostRepresentativePhones:
      for rowNum in mostRepresentativePhones[phone]:
        phoneCounts[i] = phoneStateMatrix[rowNum]
        yTicks[i] = rowNum
        i += 1

  (phoneCounts, yTicks) = removeZeroArrays(phoneCounts, yTicks)
  yTicks = [x + 1 for x in yTicks]
  return phoneCounts, yTicks

def bubbleSort(matrix, mostRepresentativePhones, alphabet):
  for phone in mostRepresentativePhones:
    rowList = mostRepresentativePhones[phone]
    phoneIndex = alphabet.index(phone)

    swapped = True
    while (swapped):
      swapped = False
      for i in range(len(rowList) - 1):
        aSum = sum(matrix[rowList[i]])
        bSum = sum(matrix[rowList[i + 1]])

        if aSum == 0:
          aNorm = 0
        else:
          aNorm = matrix[rowList[i]][phoneIndex] / aSum
        if bSum == 0:
          bNorm = 0
        else:
          bNorm = matrix[rowList[i + 1]][phoneIndex] / bSum

        if aNorm > bNorm:
          rowList[i], rowList[i + 1] = rowList[i + 1], rowList[i]
          swapped = True

def removeZeroArrays(matrix, yTicks):
  for i in range(len(matrix) - 1, -1, -1):
    row = matrix[i]
    if sum(row) == 0:
      matrix = np.delete(matrix, i, 0)
      yTicks.pop(i)

  return matrix, yTicks

# To diagonal matrix with loss of rows
# Cleaner but we lose more information
def arrayToDiagonalClean(phoneStateMatrix, alphabet, num_units):
  phoneCounts = np.zeros((num_units, len(alphabet)))
  yTicks = list(range(num_units))
  alphabetCopy = []

  # Find most representative phone for each group
  for i, row in enumerate(phoneStateMatrix):
    phoneIndex = np.where(row == max(row))[0][0]
    phone = alphabet[phoneIndex]

    if phone not in alphabetCopy:
      swap(yTicks, i, phoneIndex)

      alphabetCopy.append(phone)
      phoneCounts[phoneIndex] = row

  return phoneCounts, yTicks

def swap(myList, i, j):
  temp = myList[i]
  myList[i] = myList[j]
  myList[j] = temp

def plotConfusionMatrix(phoneStateMatrix, alphabet, yTicks = 0):
  if yTicks == 0:
    yTicks = list(range(1, num_units + 1))

  norm_conf = getMatrix(phoneStateMatrix)

  fig = plt.figure()
  plt.clf()
  ax = fig.add_subplot(111)
  res = ax.imshow(np.array(norm_conf), cmap=plt.cm.Blues,interpolation='nearest', aspect='auto')
  width = len(phoneStateMatrix)
  height = len(phoneStateMatrix[0])

  for x in range(width):
      for y in range(height):
          ax.annotate(str(int(phoneStateMatrix[x][y])), xy=(y, x), 
                      horizontalalignment='center',
                      verticalalignment='center')

  cb = fig.colorbar(res)

  setTitle()
  setTicks(alphabet, yTicks)

  plt.show()

def plotBubbleCM(phoneStateMatrix, alphabet, yTicks = 0):
  if yTicks == 0:
    yTicks = list(range(1, num_units + 1))

  norm_conf = getMatrix(phoneStateMatrix)

  # print norm_conf
  x_axis = []
  y_axis = []
  z_colors = []
  z_size = []

  width = len(norm_conf)
  height = len(norm_conf[0])

  # sumRows = [sum(x) for x in phoneStateMatrix]
  sumColumns = phoneStateMatrix.sum(axis=0)

  for i in range(width):
    for j in range(height):
      if norm_conf[i][j] != 0:
        x_axis.append(j)
        y_axis.append(width - i - 1)
        z_colors.append(norm_conf[i][j])
        z_size.append(750 * int(phoneStateMatrix[i][j]) /
          sumColumns[j]) 
  cm = plt.cm.get_cmap(plt.cm.YlGnBu)
   
  fig, ax = plt.subplots()
  sc = ax.scatter(x_axis,y_axis,s=z_size,c=z_colors,cmap=cm,
    linewidth=0,alpha=0.75,marker="o")
  ax.grid()
  fig.colorbar(sc)

  setTitle()
  setTicks(alphabet, yTicks)

  pylab.ylim([-1, width + 1])
  pylab.xlim([-1, height])

  plt.show()

def getMatrix(phoneStateMatrix):
  norm_conf = []
  for i in phoneStateMatrix:
      a = 0
      tmp_arr = []
      a = sum(i, 0)
      for j in i:
        if (a == 0): 
          tmp_arr.append(0)
        else:
            tmp_arr.append(float(j)/float(a))
      norm_conf.append(tmp_arr)

  return norm_conf

def setTitle():
    plt.title(sys.argv[1].replace(".map",""), fontsize=14)

def setTicks(alphabet, yTicks):
  reverse = yTicks[::-1]
  plt.xticks(list(range(len(alphabet))), alphabet)
  plt.yticks(list(range(len(yTicks))), reverse)

  plt.tick_params(axis='both', labelsize=8)
  
  plt.xlabel("Phones")
  plt.ylabel("States")

def main():
  if len(sys.argv[1:]) < 2:
    print("Usage: ./plotData.py <map_file> <phone_set>")
    print(" phone_sets -- TURKISH, TURKISH_REDUCED, TIMIT_ALL, ALL")
    sys.exit(1)

  PHONE_SET = sys.argv[2]
  MAP_FILE = sys.argv[1]
  print(PHONE_SET)
  print(MAP_FILE)

  with open(MAP_FILE,"r") as fp:
    units = [l.strip().split(" ")[2] for l in fp.readlines()]
    num_units  = len(set(units)) 
    print("Number of units: %d" % num_units)
  
  if PHONE_SET == "TURKISH_REDUCED":
    PHONE_LIST = TURKISH_REDUCED
  elif PHONE_SET == "TURKISH":
    PHONE_LIST = TURKISH
  elif PHONE_SET == "TIMIT":
    PHONE_LIST = TIMIT
  elif PHONE_SET == "TIMIT_ALL":
    PHONE_LIST = TIMIT_ALL
  elif PHONE_SET == "ALL":
    PHONE_LIST = ALL

  phoneCounts, phones = dataToArray(PHONE_LIST, MAP_FILE, num_units)
  #phoneCounts, phones = dataToArray(CONSONANTS)

  # Diagonal matrix w/out row loss
  newPhoneCounts, phoneList = arrayToDiagonal(phoneCounts, phones, num_units)
  # plotConfusionMatrix(newPhoneCounts, phones, phoneList)
  plotBubbleCM(newPhoneCounts, phones, phoneList)

  filename_title = sys.argv[1].strip() + ".eps";
  plt.savefig(filename_title);

if __name__ == "__main__":
  main()
