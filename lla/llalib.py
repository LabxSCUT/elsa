#lalib.py -- Library of Liquid Association Analysis(LAA) Package
#LICENSE: BSD

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

"""llalib.py -- Library of Liquid Association Analysis(LA) Package

  NOTE: numpy and scipy is required to use thie module
  NOTE: accepts input sequence table as delimited text file 
        with first row is the "Date" and other factor labels and
        first column is the time spot labels
"""

import csv
import sys
import os
import random
import numpy as np
import scipy as sp
import scipy.interpolate
import scipy.stats

try:
    # When running as installed package
    from lsa import lsalib
    from lsa import compcore
except ImportError:
    # When running in debug mode
    try:
        from . import lsalib
        from . import compcore
    except ImportError:
        import lsalib
        import compcore

#global variable, stores calculated p-values.
disp_decimal = 8
kcut_min = 100
Rmax_min = 10
my_decimal = 2    # preset x step size for P_table
pipi = np.pi**2  # pi^2
pipi_inv = 1/pipi
Q_lam_step = 0.05
Q_lam_max = 0.95

### LA with scoutVars functions ###

def applyLA(inputData, scoutVars, factorLabels, bootCI=.95, bootNum=1000, minOccur=.50, 
           pvalueMethod=1000, fTransform=lsalib.simpleAverage, 
           zNormalize=lsalib.noZeroNormalize, resultFile=None):

    col_labels = ['X','Y','Z','LA','lowCI','upCI','P','Q','Xi','Yi','Zi']
    print("\t".join(col_labels), file=resultFile)

    inputFactorNum = inputData.shape[0]
    inputRepNum = inputData.shape[1]
    inputSpotNum = inputData.shape[2]
    scoutNum = len(scoutVars)
    cp = np.array([False]*inputFactorNum**3, dtype='bool') #consider bitvector
    cp.shape = (inputFactorNum, inputFactorNum, inputFactorNum)
    laTable = [None]*inputFactorNum*scoutNum
    pvalues = np.zeros(inputFactorNum*scoutNum, dtype='float')
    timespots = inputSpotNum #same length already assumed
    replicates = inputRepNum
    ti = 0
    
    for i in range(0, scoutNum):
        Xi = scoutVars[i][0] - 1
        Yi = scoutVars[i][1] - 1
        Xo = np.ma.masked_invalid(inputData[Xi], copy=True)
        Yo = np.ma.masked_invalid(inputData[Yi], copy=True)
        
        for j in range(0, inputFactorNum):
            Zi = j
            if Xi == Yi or Xi == Zi or Zi == Yi:
                continue   #ignore invalid entries
            if cp[Xi,Yi,Zi] or cp[Xi,Zi,Yi] or cp[Zi,Xi,Yi] or cp[Zi,Yi,Xi] or cp[Yi,Xi,Zi] or cp[Yi,Zi,Xi]:
                continue   #ignore redundant entries
                
            cp[Xi,Yi,Zi] = True
            Zo = np.ma.masked_invalid(inputData[Zi], copy=True)
            
            Xo_minOccur = np.sum(np.logical_or(np.isnan(lsalib.ma_average(Xo)), 
                                lsalib.ma_average(Xo)==0))/float(timespots) < minOccur
            Yo_minOccur = np.sum(np.logical_or(np.isnan(lsalib.ma_average(Yo)), 
                                lsalib.ma_average(Yo)==0))/float(timespots) < minOccur
            Zo_minOccur = np.sum(np.logical_or(np.isnan(lsalib.ma_average(Zo)), 
                                lsalib.ma_average(Zo)==0))/float(timespots) < minOccur
                                
            if Xo_minOccur or Yo_minOccur or Zo_minOccur:
                continue
            if np.all(Xo.mask) or np.all(Yo.mask) or np.all(Zo.mask):
                continue
                
            LA_score = singleLA(Xo, Yo, Zo, fTransform, zNormalize)

            if pvalueMethod >= 0 or pvalueMethod < 0:
                Xp = np.ma.array(Xo, copy=True)
                Yp = np.ma.array(Yo, copy=True)
                Zp = np.ma.array(Zo, copy=True)
                laP = LApermuPvalue(Xp, Yp, Zp, abs(pvalueMethod), np.abs(LA_score), 
                                  fTransform, zNormalize)
            else:
                print("This should not be reached now", file=sys.stderr)
                
            pvalues[ti] = laP
            
            if bootNum > 0:
                Xb = np.ma.array(Xo, copy=True)
                Yb = np.ma.array(Yo, copy=True)
                Zb = np.ma.array(Zo, copy=True)
                (LA_score, Sl, Su) = LAbootstrapCI(Xb, Yb, Zb, LA_score, bootCI, bootNum, 
                                                 fTransform, zNormalize)
            else:
                (LA_score, Sl, Su) = (LA_score, LA_score, LA_score)

            laTable[ti] = [Xi, Yi, Zi, LA_score, Sl, Su, laP]
            ti += 1

    pvalues = pvalues[:ti]
    laTable = laTable[:ti]
    qvalues = lsalib.storeyQvalue(pvalues)
    
    for k in range(0, len(qvalues)):
        laTable[k] = laTable[k] + [qvalues[k], laTable[k][0]+1, laTable[k][1]+1, laTable[k][2]+1]

    for row in laTable:
        print("\t".join(['%s']*len(col_labels)) % 
              tuple([factorLabels[row[0]], factorLabels[row[1]], factorLabels[row[2]]] + 
                    [f"{v:.{disp_decimal}f}" if isinstance(v, float) else v for v in row[3:]]), 
              file=resultFile)

def calc_LA(series1, series2, series3):     # the function to calculate LA score
    n1 = len(series1)
    n2 = len(series2)
    n3 = len(series3)
    assert n1==n2 and n2 == n3
    return np.sum(series1*series2*series3)/n1

def singleLA(series1, series2, series3, fTransform, zNormalize): # calculate normalized LA score
    return calc_LA(zNormalize(fTransform(series1)),zNormalize(fTransform(series2)),zNormalize(fTransform(series3)))

def LAbootstrapCI(series1, series2, series3, LA_score, bootCI, bootNum, fTransform, zNormalize, debug=0):
    ### no feasible, skipping bootstraping
    if series1.shape[0] == 1:
        return (LA_score, LA_score, LA_score)

    BS_set = np.zeros(bootNum, dtype='float')
    for i in range(0, bootNum):
        Xb = np.ma.array([ lsalib.sample_wr(series1[:,j], series1.shape[0]) for j in range(0,series1.shape[1]) ]).T
        Yb = np.ma.array([ lsalib.sample_wr(series2[:,j], series2.shape[0]) for j in range(0,series2.shape[1]) ]).T
        Zb = np.ma.array([ lsalib.sample_wr(series3[:,j], series3.shape[0]) for j in range(0,series3.shape[1]) ]).T
        BS_set[i] = calc_LA(Xb, Yb, Zb)
    BS_set.sort()                                 #from smallest to largest
    BS_mean = np.mean(BS_set)
    return ( BS_mean, BS_set[np.floor(bootNum*a1)-1], BS_set[np.ceil(bootNum*a2)-1] )

def LApermuPvalue(series1, series2, series3, pvalueMethod, LA_score, fTransform, zNormalize):
    PP_set = np.zeros(pvalueMethod, dtype='float')
    X = zNormalize(fTransform(series1))
    Y = zNormalize(fTransform(series2))
    Z = np.ma.array(series3)                                               #use = only assigns reference, must use a constructor
    for i in range(0, pvalueMethod):
        np.random.shuffle(Z.T)
        PP_set[i] = calc_LA(X, Y, zNormalize(fTransform(Z)))
    if LA_score >= 0:
        P_two_tail = np.sum(np.abs(PP_set) >= LA_score)/float(pvalueMethod)
    else:
        P_two_tail = np.sum(-np.abs(PP_set) <= LA_score)/float(pvalueMethod)
    return P_two_tail


# ab initio local liquid association analysis functions ###  

def applyLLAnalysis(cleanData, factorLabels, delayLimit=3, bootCI=.95, bootNum=1000, minOccur=.50,
                   pvalueMethod="perm", precision=1000, fillMethod='linear', normMethod='pnz',
                   fTransform=lsalib.simpleAverage, zNormalize=lsalib.noZeroNormalize, 
                   resultFile=None, qvalue_func=lsalib.storeyQvalue):
    """Apply Liquid Local Analysis to input data using DP_LLA algorithm.
    
    Args:
        inputData: numpy array of shape (factors, replicates, timepoints)
        factorLabels: list of factor names
        delayLimit: maximum time delay to consider (default 3)
        bootCI: confidence interval for bootstrap (default 0.95)
        bootNum: number of bootstrap iterations (default 1000)
        minOccur: minimum occurrence threshold (default 0.50)
        pvalueMethod: method for p-value calculation (default "perm")
        precision: precision for p-value calculation (default 1000)
        fillMethod: method to fill missing values (default 'linear')
        normMethod: method to normalize data (default 'pnz')
        fTransform: function to transform replicates (default simpleAverage)
        zNormalize: function to normalize data (default noZeroNormalize)
        resultFile: file handle to write results (default None)
        qvalue_func: function to calculate q-values (default storeyQvalue)
    """
    col_labels = ['X','Y','Z','LA','lowCI','upCI','P','Q','Xi','Yi','Zi','Delay']
    print("\t".join(col_labels), file=resultFile)

    inputFactorNum = cleanData.shape[0]
    inputRepNum = cleanData.shape[1]
    inputSpotNum = cleanData.shape[2]
    
    # Track computed triplets to avoid redundancy
    triplet = np.array([False]*inputFactorNum**3, dtype='bool')
    triplet.shape = (inputFactorNum, inputFactorNum, inputFactorNum)
    
    # Initialize results storage
    laTable = []
    pvalues = []
    
    # Process each possible triplet
    for Xi in range(inputFactorNum):
        for Yi in range(Xi+1, inputFactorNum):  # Only upper triangle to avoid duplicates
            for Zi in range(inputFactorNum):
                # Skip invalid combinations
                if Xi == Yi or Xi == Zi or Zi == Yi:
                    continue
                if triplet[Xi,Yi,Zi] or triplet[Xi,Zi,Yi] or triplet[Zi,Xi,Yi] or triplet[Zi,Yi,Xi] or triplet[Yi,Xi,Zi] or triplet[Yi,Zi,Xi]:
                    continue
                    
                triplet[Xi,Yi,Zi] = True
                
                # Get data for X, Y, and Z
                Xo = np.ma.masked_invalid(inputData[Xi], copy=True)
                Yo = np.ma.masked_invalid(inputData[Yi], copy=True)
                Zo = np.ma.masked_invalid(inputData[Zi], copy=True)
                
                # Check minimum occurrence criteria
                Xo_valid = np.sum(~np.isnan(lsalib.ma_average(Xo)))/float(inputSpotNum) >= minOccur
                Yo_valid = np.sum(~np.isnan(lsalib.ma_average(Yo)))/float(inputSpotNum) >= minOccur
                Zo_valid = np.sum(~np.isnan(lsalib.ma_average(Zo)))/float(inputSpotNum) >= minOccur
                
                if not (Xo_valid and Yo_valid and Zo_valid):
                    continue
                if np.all(Xo.mask) or np.all(Yo.mask) or np.all(Zo.mask):
                    continue
                
                # Apply transforms and normalization
                X = zNormalize(fTransform(Xo)) # Xo is matrix, X is vector
                Y = zNormalize(fTransform(Yo)) # Yo is matrix, Y is vector
                Z = zNormalize(fTransform(Zo))
                
                # Call DP_LLA from compcore
                try:
                    # Convert numpy arrays to lists for PyBind11
                    X_list = X.tolist()
                    Y_list = Y.tolist()
                    Z_list = Z.tolist()
                    
                    # Create LLA_Data object using new PyBind11 constructor
                    lla_data = compcore.LLA_Data(delayLimit, X_list, Y_list, Z_list)
                    
                    # Call DP_lla with the new object
                    lla_result = compcore.DP_lla(lla_data, True)  # True to keep trace
                    
                    # Extract results
                    LA_score = lla_result.score
                    trace = lla_result.trace
                except Exception as e:
                    print(f"Error in DP_lla computation: {str(e)}", file=sys.stderr)
                    continue
                
                # Calculate p-value
                if isinstance(pvalueMethod, str) and pvalueMethod == "perm":
                    Xp = np.ma.array(X, copy=True)
                    Yp = np.ma.array(Y, copy=True)
                    Zp = np.ma.array(Z, copy=True)
                    laP = LApermuPvalue(Xp, Yp, Zp, precision, np.abs(LA_score), 
                                      fTransform, zNormalize)
                else:
                    precision = abs(int(pvalueMethod))
                    Xp = np.ma.array(X, copy=True)
                    Yp = np.ma.array(Y, copy=True)
                    Zp = np.ma.array(Z, copy=True)
                    laP = LApermuPvalue(Xp, Yp, Zp, precision, np.abs(LA_score),
                                      fTransform, zNormalize)
                
                pvalues.append(laP)
                
                # Calculate bootstrap confidence intervals if requested
                if bootNum > 0:
                    Xb = np.ma.array(Xo, copy=True)
                    Yb = np.ma.array(Yo, copy=True)
                    Zb = np.ma.array(Zo, copy=True)
                    LA_score, Sl, Su = LAbootstrapCI(Xb, Yb, Zb, LA_score, bootCI, bootNum,
                                                   fTransform, zNormalize)
                else:
                    Sl, Su = LA_score, LA_score
               
                trace_length = getLLATraceLength(X, Y, Z, delayLimit)
                best_delay = trace_length - 1 if trace_length > 0 else 0
                laTable.append([Xi, Yi, Zi, LA_score, Sl, Su, laP, best_delay])
    
    # Calculate q-values
    if pvalues:
        qvalues = qvalue_func(np.array(pvalues))
        
        # Add q-values and 1-based indices to results
        for k in range(len(qvalues)):
            laTable[k] = laTable[k][:6] + [qvalues[k], laTable[k][0]+1, laTable[k][1]+1, laTable[k][2]+1, laTable[k][7]]
        
        # Write results
        for row in laTable:
            print("\t".join(['%s']*len(col_labels)) % 
                  tuple([factorLabels[row[0]], factorLabels[row[1]], factorLabels[row[2]]] + 
                        [f"{v:.{disp_decimal}f}" if isinstance(v, float) else v for v in row[3:]]), 
                  file=resultFile)
    else:
        print("No valid triplets found for analysis", file=sys.stderr)

def LLApermuPvalue(X, Y, Z, delayLimit, precisionP, LA_score, fTransform, zNormalize):
    """
    Perform permutation test for Local Liquid Association.

    Args:
        X, Y, Z (np.array): Sequence data for X, Y, and Z.
        precisionP (int): Number of permutations.
        LA_score (float): Observed LA score.
        fTransform (function): Function to transform data.
        zNormalize (function): Function to normalize data.

    Returns:
        float: p-value
    """
    PP_set = np.zeros(precisionP, dtype='float')
    Xz = zNormalize(fTransform(X))
    Yz = zNormalize(fTransform(Y))
    Zz = zNormalize(fTransform(Z))

    for i in range(precisionP):
        np.random.shuffle(Zz.T)  # Shuffle Z in place
        lla_data = compcore.LLA_Data(delayLimit, Xz, Yz, Zz)
        PP_set[i] = compcore.DP_lla(lla_data).score

    if LA_score >= 0:
        P_two_tail = np.sum(np.abs(PP_set) >= LA_score) / float(precisionP)
    else:
        P_two_tail = np.sum(-np.abs(PP_set) <= LA_score) / float(precisionP)
    return P_two_tail

def LLAbootstrapCI(X, Y, Z, LA_score, delayLimit, bootCI, bootNum, fTransform, zNormalize):
    """
    Perform bootstrap CI estimation for Liquid Association.

    Args:
        X, Y, Z (np.array): Sequence data for X, Y, and Z.
        LA_score (float): Initial LA score.
        bootCI (float): Confidence interval size.
        bootNum (int): Number of bootstraps.
        fTransform (function): Function to transform data.
        zNormalize (function): Function to normalize data.

    Returns:
        tuple: (LA_score, lower CI, upper CI)
    """
    if X.shape[0] == 1:
        return (LA_score, LA_score, LA_score)

    BS_set = np.zeros(bootNum, dtype='float')
    for i in range(bootNum):
        Xb = zNormalize(fTransform(np.ma.array([np.random.choice(X, size=X.shape[0], replace=True) for _ in range(X.shape[1])]).T))
        Yb = zNormalize(fTransform(np.ma.array([np.random.choice(Y, size=Y.shape[0], replace=True) for _ in range(Y.shape[1])]).T))
        Zb = zNormalize(fTransform(np.ma.array([np.random.choice(Z, size=Z.shape[0], replace=True) for _ in range(Z.shape[1])]).T))
        
        lla_data = compcore.LLA_Data(delayLimit, Xb, Yb, Zb)
        BS_set[i] = compcore.DP_lla(lla_data).score

    BS_set.sort()
    a1 = (1 - bootCI) / 2.0
    a2 = bootCI + (1 - bootCI) / 2.0
    return (LA_score, BS_set[int(np.floor(bootNum * a1))], BS_set[int(np.ceil(bootNum * a2))])

def getLLATraceLength(X, Y, Z, delayLimit):
    """
    Get the length of the optimal alignment trace from DP_lla algorithm.
    
    Args:
        X, Y, Z (np.array): Input sequences
        delayLimit (int): Maximum allowed delay between sequences
        
    Returns:
        int: Length of the optimal alignment trace
    """
    try:
        # Create LLA_Data object
        lla_data = compcore.LLA_Data(delayLimit, X, Y, Z)
        
        # Run DP_lla with keep_trace=True to ensure trace is computed
        lla_result = compcore.DP_lla(lla_data, True)
        
        # Return the length of the trace vector
        return len(lla_result.trace)
    except Exception as e:
        print(f"Error getting trace length: {str(e)}", file=sys.stderr)
        return 0