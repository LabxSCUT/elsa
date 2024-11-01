#!/usr/bin/env python
#lsa-compute -- computation script for LSA package to perform lsa table calculation 

#License: BSD

#Copyright (c) 2008 Li Charles Xia
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions
#are met:
#1. Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#2. Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#3. The name of the author may not be used to endorse or promote products
#   derived from this software without specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
#IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
#OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
#INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
#NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
#THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#public libs
import sys, csv, re, os, time, argparse, string, tempfile
#numeric libs
import numpy as np
import scipy as sp
from lsa import lsalib
from lla import llalib

def main():  

  __script__ = "lla_compute"
  version_desc = lsalib.safeCmd('lsa_version')
  version_print = "%s (rev: %s) - copyright Li Charlie Xia, lcxia@scut.edu.cn" \
    % (__script__, version_desc)
  print(version_print, file=sys.stderr)

  # define arguments: delayLimit, fillMethod, pvalueMethod
  parser = argparse.ArgumentParser(description="New LSA Commandline Tool")

  parser.add_argument("dataFile", metavar="dataFile", type=argparse.FileType('r'), help="the input data file,\n \
                        m by (r * s)tab delimited text; top left cell start with '#' to mark this is the header line; \n \
                        m is number of variables, r is number of replicates, s it number of time spots; \n \
                        first row: #header  s1r1 s1r2 s2r1 s2r2; second row: x  ?.?? ?.?? ?.?? ?.??; for a 1 by (2*2) data")
  parser.add_argument("resultFile", metavar="resultFile", type=argparse.FileType('w'), help="the output result file")
  parser.add_argument("-e", "--extraFile", dest="extraFile", default="",
                        help="specify an extra datafile, otherwise the first datafile will be used \n \
                            and only lower triangle entries of pairwise matrix will be computed")
  parser.add_argument("-d", "--delayLimit", dest="delayLimit", default=3, type=int, 
                    	help="specify the maximum delay possible, default: 3,\n choices: 0 to 6")
  parser.add_argument("-p", "--pvalueMethod", dest="pvalueMethod", default=1000, type=int,
                    	help="specify the method=sgn(pvalueMethod) and precision=1/abs(pvalueMethod) for p-value estimation, \n \
                            default: pvalueMethod=1000, i.e. precision=0.001 and mode=permutation \n \
                            mode +: permutation approximaton; -: theoretical approximation. ")
  parser.add_argument("-b", "--bootNum", dest="bootNum", default=0, type=int, choices=[0, 100, 200, 500, 1000, 2000],
                    	help="specify the number of bootstraps for 95%% confidence interval estimation, default: 100,\n \
                          choices: 0, 100, 200, 500, 1000, 2000. \n \
                          Setting bootNum=0 avoids bootstrap. Bootstrap is not suitable for non-replicated data.")   #use %% to print %
  parser.add_argument("-r", "--repNum", dest="repNum", default=1, type=int,
                    	help="specify the number of replicates each time spot, default: 1,      \n \
                          must be provided and valid. ")
  parser.add_argument("-s", "--spotNum", dest="spotNum", default=4, type=int, 
                    	help="specify the number of time spots, default: 4,                     \n \
                          must be provided and valid. ")
  parser.add_argument("-t", "--transFunc", dest="transFunc", default='simple', choices=['simple', 'SD', 'Med', 'MAD'],
                      help="specify the method to summarize replicates data, default: simple, \n \
                          choices: simple, SD, Med, MAD                                       \n \
                          NOTE:                                                               \n \
                          simple: simple averaging                                            \n \
                          SD: standard deviation weighted averaging                           \n \
                          Med: simple Median                                                  \n \
                          MAD: median absolute deviation weighted median;" )
  parser.add_argument("-f", "--fillMethod", dest="fillMethod", default='linear', 
                        choices=['none', 'zero', 'linear', 'quadratic', 'cubic', 'slinear', 'nearest'],
                    	help= "specify the method to fill missing, default: none,               \n \
                          choices: none, zero, linear, quadratic, cubic, slinear, nearest  \n \
                          operation AFTER normalization:  \n \
                          none: fill up with zeros ;   \n \
                          operation BEFORE normalization:  \n \
                          zero: fill up with zero order splines;           \n \
                          linear: fill up with linear splines;             \n \
                          slinear: fill up with slinear;                   \n \
                          quadratic: fill up with quadratic spline;             \n \
                          cubic: fill up with cubic spline;                \n \
                          nearest: fill up with nearest neighbor") 
  parser.add_argument("-n", "--normMethod", dest="normMethod", default='pnz', choices=['percentile', 'pnz', 'none'],
                      help= "specify the method to normalize data, default: percentile,       \n \
                          choices: percentile, none                                        \n \
                          NOTE:                                                         \n \
                          percentile: percentile normalization, including zeros                                    \n \
                          pnz: percentile normalization, excluding zeros                                    \n \
                          none or a float number for variance: no normalization and calculate Ptheo with user specified variance, default=1 ")
  
  arg_namespace = parser.parse_args()

  #get arguments
  print("lsa-compute - copyright Li Charlie Xia, lixia@stanford.edu", file=sys.stderr)
  
  delayLimit = vars(arg_namespace)['delayLimit']
  fillMethod = vars(arg_namespace)['fillMethod']
  normMethod = vars(arg_namespace)['normMethod']
  pvalueMethod = vars(arg_namespace)['pvalueMethod']
  dataFile = vars(arg_namespace)['dataFile']				#dataFile
  extraFile = vars(arg_namespace)['extraFile']				#extraFile
  resultFile = vars(arg_namespace)['resultFile']			#resultFile
  repNum = vars(arg_namespace)['repNum']
  transFunc = vars(arg_namespace)['transFunc']
  bootNum = vars(arg_namespace)['bootNum']
  spotNum = vars(arg_namespace)['spotNum']

  #assign transform function
  if transFunc == 'SD':
    fTransform = lsalib.sdAverage
  elif transFunc == 'Med':
    fTransform = lsalib.simpleMedian   # Median
  elif transFunc == 'MAD':
    fTransform = lsalib.madMedian      # Median/MAD
  else:
    fTransform = lsalib.simpleAverage   # fallback to default Avg
  
  #check transFunc and repNum compatibility
  if repNum < 5 and ( transFunc == 'SD' ):
    print("Not enough replicates for SD-weighted averaging, fall back to simpleAverage", file=sys.stderr)
    transFunc = 'simple'

  if repNum < 5 and ( transFunc == 'MAD' ):
    print("Not enough replicates for Median Absolute Deviation, fall back to simpleMedian", file=sys.stderr)
    transFunc = 'Med'

  #check normMethod
  varianceX=1
  if normMethod == 'none':
    zNormalize = lsalib.noneNormalize
  elif normMethod == 'percentile':
    zNormalize = lsalib.percentileNormalize
  elif normMethod == 'pnz':
    zNormalize = lsalib.percentileZNormalize
  elif normMethod != None:
    zNormalize = lsalib.noZeroNormalize
    varianceX = float(normMethod)
  else:
    zNormalize = lsalib.noZeroNormalize # fallback to default
  
  print("\t".join(['delayLimit','fillMethod','pvalueMethod','dataFile','resultFile','repNum','spotNum','bootNum','transFunc','normMethod','xVariance']))
  print("\t".join(['%s']*11) % (delayLimit,fillMethod,pvalueMethod,dataFile.name,resultFile.name,repNum,spotNum,bootNum,transFunc,normMethod,str(varianceX)))
  
  #start timing main
  start_time = time.time()

  #datafile handling
  onDiag = False
  try:
    firstData = np.genfromtxt(dataFile, comments='#', delimiter='\t', 
                             missing_values=['na','','NA'], 
                             filling_values=np.nan, 
                             usecols=list(range(1, spotNum*repNum+1)),
                             dtype=float)
    dataFile.seek(0)  #rewind
    firstFactorLabels = np.genfromtxt(dataFile, comments='#', delimiter='\t', 
                                     usecols=[0], dtype=str).tolist()
    
    if not extraFile:
        onDiag = True
        dataFile.seek(0)  #rewind
        secondData = firstData.copy()
        secondFactorLabels = firstFactorLabels.copy()
    else:
        try:
            with open(extraFile, 'r') as extraData:
                secondData = np.genfromtxt(extraData, comments='#', delimiter='\t',
                                         missing_values=['na','','NA'],
                                         filling_values=np.nan,
                                         usecols=list(range(1, spotNum*repNum+1)),
                                         dtype=float)
                extraData.seek(0)
                secondFactorLabels = np.genfromtxt(extraData, comments='#', 
                                                 delimiter='\t',
                                                 usecols=[0], 
                                                 dtype=str).tolist()
        except Exception as e:
            print(f"Error reading extra file: {str(e)}", file=sys.stderr)
            sys.exit(1)
            
  except Exception as e:
    print(f"Error reading data file: {str(e)}", file=sys.stderr)
    print("Please check the input format, spotNum and repNum.", file=sys.stderr)
    print("Input should be a tab-delimited text file with:", file=sys.stderr)
    print("- First line starting with '#' as column names", file=sys.stderr)
    print("- First column as factor labels", file=sys.stderr)
    print("- Comment lines starting with '#'", file=sys.stderr)
    print(f"- {spotNum * repNum} numeric cells for {repNum}-replicated {spotNum}-timepoint series data", file=sys.stderr)
    sys.exit(1)

  # Verify data dimensions
  if firstData.shape[1] != spotNum * repNum:
      print(f"Error: Input data has {firstData.shape[1]} columns but expected {spotNum * repNum}", file=sys.stderr)
      sys.exit(1)

  ###print rawData, factorLabels
  cleanData = []
  for rawData in [firstData, secondData]:
    factorNum = rawData.shape[0]
    tempData = np.zeros((factorNum, repNum, spotNum), dtype='float')
    for i in range(factorNum):
        for j in range(repNum):
            tempData[i,j] = rawData[i][j::repNum]  # Changed array indexing
    
    for i in range(factorNum):
        for j in range(repNum):
            tempData[i,j] = lsalib.fillMissing(tempData[i,j], fillMethod)
    
    cleanData.append(tempData)

  # Create scout variables for all possible pairs
  scoutVars = []
  factorNum = firstData.shape[0]
  for i in range(factorNum):
      for j in range(i+1, factorNum):
          scoutVars.append((i+1, j+1))  # +1 because indices in applyLA are 1-based

  # Call applyLA with the correct parameters
  llalib.applyLA(cleanData[0], scoutVars, firstFactorLabels, 
                 bootCI=0.95, bootNum=bootNum,
                 minOccur=0.50, pvalueMethod=abs(pvalueMethod),
                 fTransform=fTransform, zNormalize=zNormalize,
                 resultFile=resultFile)

  print("finishing up...", file=sys.stderr)
  resultFile.close()
  end_time=time.time()
  print(f"time elapsed {end_time-start_time} seconds", file=sys.stderr)

if __name__=="__main__":
  main()
