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

try:
    # When running as installed package
    from lsa import lsalib
    from lsa.lsalib import noZeroNormalize, percentileNormalize, noneNormalize
    from lsa.lsalib import simpleAverage, sdAverage, simpleMedian, madMedian
    from lsa.lsalib import fillMissing, ma_average, percentileZNormalize
    from lla import llalib
except ImportError:
    # When running in debug mode
    try:
        from . import lsalib
        from .lsalib import noZeroNormalize, percentileNormalize, noneNormalize
        from .lsalib import simpleAverage, sdAverage, simpleMedian, madMedian
        from .lsalib import fillMissing, ma_average, percentileZNormalize
        from . import llalib
    except ImportError:
        import lsalib
        from lsalib import noZeroNormalize, percentileNormalize, noneNormalize
        from lsalib import simpleAverage, sdAverage, simpleMedian, madMedian
        from lsalib import fillMissing, ma_average, percentileZNormalize
        import llalib

def main():
    __script__ = "lla_compute"
    version_desc = lsalib.safeCmd('lsa_version')
    version_print = "%s (rev: %s) - copyright Li Charlie Xia, lcxia@scut.edu.cn" \
        % (__script__, version_desc)
    print(version_print, file=sys.stderr)
    print("Local Liquid Association Analysis Tool", file=sys.stderr)

    # define arguments: delayLimit, fillMethod, pvalueMethod
    parser = argparse.ArgumentParser(description="Local Liquid Association Analysis Tool")

    parser.add_argument("dataFile", metavar="dataFile", type=argparse.FileType('r'), 
                       help="input data file: m by (r * s) tab delimited text; \n \
                             first row starts with '#' as header; \n \
                             m variables, r replicates, s time spots")
    parser.add_argument("resultFile", metavar="resultFile", type=argparse.FileType('w'), 
                       help="output result file")
    parser.add_argument("-d", "--delayLimit", dest="delayLimit", default=3, type=int,
                       help="maximum time delay (default: 3, range: 0-6)")
    parser.add_argument("-p", "--pvalueMethod", dest="pvalueMethod", default="perm",
                       help="p-value calculation method (default: perm)")
    parser.add_argument("-x", "--precision", dest="precision", default=1000, type=int,
                       help="precision for p-value calculation (default: 1000)")
    parser.add_argument("-b", "--bootNum", dest="bootNum", default=0, type=int,
                       choices=[0, 100, 200, 500, 1000, 2000],
                       help="bootstrap iterations for CI (default: 0)")
    parser.add_argument("-r", "--repNum", dest="repNum", default=1, type=int,
                       help="replicates per time spot (default: 1)")
    parser.add_argument("-s", "--spotNum", dest="spotNum", default=4, type=int,
                       help="number of time spots (default: 4)")
    parser.add_argument("-m", "--minOccur", dest="minOccur", default=0.50, type=float,
                       help="minimum occurrence threshold (default: 0.50)")
    parser.add_argument("-t", "--transFunc", dest="transFunc", default='simple',
                       choices=['simple', 'SD', 'Med', 'MAD'],
                       help="replicate summarization method (default: simple)")
    parser.add_argument("-f", "--fillMethod", dest="fillMethod", default='linear',
                       choices=['none', 'zero', 'linear', 'quadratic', 'cubic', 'slinear', 'nearest'],
                       help="missing value fill method (default: linear)")
    parser.add_argument("-n", "--normMethod", dest="normMethod", default='pnz',
                       choices=['percentile', 'pnz', 'none'],
                       help="data normalization method (default: pnz)")

    args = parser.parse_args()

    # Print parameters
    print("\t".join(['delayLimit','fillMethod','pvalueMethod','dataFile','resultFile',
                    'repNum','spotNum','bootNum','transFunc','normMethod','precision']))
    print("\t".join(['%s']*11) % (args.delayLimit, args.fillMethod, args.pvalueMethod,
                                 args.dataFile.name, args.resultFile.name, args.repNum,
                                 args.spotNum, args.bootNum, args.transFunc,
                                 args.normMethod, args.precision))

    # Assign transform function
    if args.transFunc == 'SD':
        fTransform = lsalib.sdAverage
    elif args.transFunc == 'Med':
        fTransform = lsalib.simpleMedian
    elif args.transFunc == 'MAD':
        fTransform = lsalib.madMedian
    else:
        fTransform = lsalib.simpleAverage

    # Check transform function compatibility
    if args.repNum < 5 and args.transFunc == 'SD':
        print("Not enough replicates for SD-weighted averaging, using simpleAverage", file=sys.stderr)
        fTransform = lsalib.simpleAverage

    if args.repNum < 5 and args.transFunc == 'MAD':
        print("Not enough replicates for MAD, using simpleMedian", file=sys.stderr)
        fTransform = lsalib.simpleMedian

    # Assign normalization function
    if args.normMethod == 'none':
        zNormalize = lsalib.noneNormalize
    elif args.normMethod == 'percentile':
        zNormalize = lsalib.percentileNormalize
    elif args.normMethod == 'pnz':
        zNormalize = lsalib.percentileZNormalize
    else:
        zNormalize = lsalib.noZeroNormalize

    # Read and process input data
    try:
        firstData = np.genfromtxt(args.dataFile, comments='#', delimiter='\t',
                               missing_values=['na','','NA'],
                               filling_values=np.nan,
                               usecols=list(range(1, args.spotNum*args.repNum+1)),
                               dtype=float)
        args.dataFile.seek(0)
        factorLabels = np.genfromtxt(args.dataFile, comments='#', delimiter='\t',
                                  usecols=[0], dtype=str).tolist()
    except Exception as e:
        print(f"Error reading data file: {str(e)}", file=sys.stderr)
        print("Please check input format:", file=sys.stderr)
        print("- Tab delimited text file", file=sys.stderr)
        print("- First row starts with '#' as header", file=sys.stderr)
        print("- First column contains factor labels", file=sys.stderr)
        print(f"- {args.spotNum * args.repNum} numeric columns expected", file=sys.stderr)
        sys.exit(1)

    # Reshape and clean data
    factorNum = firstData.shape[0]
    cleanData = np.zeros((factorNum, args.repNum, args.spotNum), dtype='float')
    for i in range(factorNum):
        for j in range(args.repNum):
            cleanData[i,j] = firstData[i][j::args.repNum]
            cleanData[i,j] = fillMissing(cleanData[i,j], args.fillMethod)

    # Run analysis
    start_time = time.time()
    try:
        llalib.applyLLAnalysis(cleanData, factorLabels,
                            delayLimit=args.delayLimit,
                            bootCI=0.95,
                            bootNum=args.bootNum,
                            minOccur=args.minOccur,
                            pvalueMethod=args.pvalueMethod,
                            precision=args.precision,
                            fillMethod=args.fillMethod,
                            normMethod=args.normMethod,
                            fTransform=fTransform,
                            zNormalize=zNormalize,
                            resultFile=args.resultFile)
    except Exception as e:
        print(f"Error during analysis: {str(e)}", file=sys.stderr)
        sys.exit(1)

    print("Finishing up...", file=sys.stderr)
    args.resultFile.close()
    end_time = time.time()
    print(f"Time elapsed {end_time-start_time:.2f} seconds", file=sys.stderr)

if __name__=="__main__":
    main()
