#!/usr/bin/env python

import argparse
import time
import sys
import numpy as np

try:
    from lsa import lsalib
except ImportError:
    try:
        from . import lsalib
    except ImportError:
        import lsalib

def validate_simulation_params(lengthSeries, numSeries, repNum):
    """Validate simulation parameters for Liquid Association analysis.
    
    Args:
        lengthSeries (int): Total number of measurements across all timepoints and replicates.
                           Must be divisible by repNum.
        numSeries (int): Number of time series to generate (minimum 3 for X, Y, Z variables).
        repNum (int): Number of replicates per timepoint. The actual number of timepoints 
                     will be lengthSeries/repNum.
        
    Raises:
        ValueError: If any parameters are invalid:
            - lengthSeries < 3
            - lengthSeries not divisible by repNum 
            - numSeries < 3 (need at least X, Y, Z series for LA analysis)
    """
    if lengthSeries < 3:
        raise ValueError(f"Length must be at least 3, got {lengthSeries}")
    
    if lengthSeries % repNum != 0:
        raise ValueError(f"Length {lengthSeries} must be divisible by repNum {repNum}")
    
    if numSeries < 3:
        raise ValueError("Need at least 3 series for LLA analysis (X, Y, and Z variables)")

def main():
    """Generate simulated time series data for Liquid Association analysis.
    
    The script generates multiple time series with optional replicates that can be used
    to test Liquid Association analysis. The data format matches what is expected by
    lla_compute.py.
    
    Parameters:
        -L, --lengthSeries: Total number of measurements (default: 50)
                           Will be divided by repNum to get actual timepoints
        -N, --numSeries: Number of series to generate (default: 3)
                        Minimum 3 required for LA analysis (X, Y, Z variables)
        -R, --repNum: Number of replicates per timepoint (default: 1)
                     lengthSeries must be divisible by this
        -T, --trendThresh: Threshold for trend analysis (default: None)
                          If specified, generates trend series
        -M, --simMethod: Simulation method (default: "idn,0,1")
                        Format: "method,param1,param2"
                        Currently only supports:
                        - idn,mean,variance: Independent normal distribution
        -O, --timeSeriesOutput: Output file path (default: None)
                               Tab-delimited format with header:
                               #    T1R1    T1R2    T2R1    T2R2    ...
                               S1   1.234   1.245   2.345   2.356   ...
                               Where TiRj = Timepoint i, Replicate j
    
    Output Format:
        The output file is tab-delimited with:
        - Header row: # T1R1 T1R2 ... T2R1 T2R2 ... (Timepoint/Replicate labels)
        - Data rows: Si value1 value2 ... (Series i values)
        - Values are formatted to 6 decimal places
        
    Data Generation:
        - Base values are generated from normal distribution N(0,1)
        - For replicates, adds 10% random variation N(0,0.1) to base values
        - Data shape is (numSeries, repNum, spotNum) internally
        - Output is reshaped to match lla_compute.py expectations
    """
    __script__ = "lla_sim"
    version_desc = lsalib.safeCmd('lsa_version')
    version_print = "%s (rev: %s) - copyright Li Charlie Xia, lcxia@scut.edu.cn" \
        % (__script__, version_desc)
    print(version_print, file=sys.stderr)

    parser = argparse.ArgumentParser(description="LLA Simulation Tool - Generates time series data for Liquid Association analysis")
    parser.add_argument("-L", "--lengthSeries", dest="lengthSeries",
                       default=50, type=int,
                       help="Total number of measurements. Must be divisible by repNum. Default: 50")
    parser.add_argument("-N", "--numSeries", dest="numSeries",
                       default=3, type=int,
                       help="Number of series to generate (min 3 for X,Y,Z variables). Default: 3")
    parser.add_argument("-R", "--repNum", dest="repNum",
                       default=1, type=int,
                       help="Number of replicates per timepoint. Default: 1")
    parser.add_argument("-T", "--trendThresh", dest="trendThresh",
                       default=None, type=float,
                       help="If specified, generates trend series using this threshold")
    parser.add_argument("-M", "--simMethod", dest="simMethod",
                       default="idn,0,1",
                       help="Simulation method: idn,mean,variance for independent normal distribution. Default: idn,0,1")
    parser.add_argument("-O", "--timeSeriesOutput", dest="timeSeriesOutput",
                       type=argparse.FileType('w'), default=None,
                       help="Output file path for generated time series data (tab-delimited)")

    args = parser.parse_args()

    try:
        # Validate parameters
        validate_simulation_params(args.lengthSeries, args.numSeries, args.repNum)
        
        print("simulating...", file=sys.stderr)
        start_time = time.time()

        spotNum = args.lengthSeries // args.repNum
        if args.trendThresh is not None:
            spotNum += 1

        # Generate series
        if args.simMethod.split(',')[0] == 'idn':
            # Generate base series with shape (numSeries, repNum, spotNum)
            # This matches the expected input format for lla_compute
            allSeries = np.zeros((args.numSeries, args.repNum, spotNum))
            
            for i in range(args.numSeries):
                # Generate base values for each timepoint
                base_values = np.random.normal(0, 1, spotNum)
                
                # Add replicate variation
                for j in range(spotNum):
                    base_value = base_values[j]
                    # Add 10% random variation for replicates
                    variations = np.random.normal(0, 0.1, args.repNum)
                    allSeries[i, :, j] = base_value + variations
        else:
            print("simMethod not implemented", file=sys.stderr)
            return

        if args.timeSeriesOutput is not None:
            # Write header with replicates
            header = ["#"] + [f"T{i}R{j}" 
                            for i in range(1, spotNum + 1)
                            for j in range(1, args.repNum + 1)]
            print("\t".join(header), file=args.timeSeriesOutput)
            
            # Write series - reshape to match expected format
            for i in range(args.numSeries):
                # Reshape to match expected input format: timepoints × replicates
                series_data = allSeries[i].T.flatten()
                row = [f"S{i+1}"] + [f"{x:.6f}" for x in series_data]
                print("\t".join(row), file=args.timeSeriesOutput)

        end_time = time.time()
        print(f"finished in {end_time - start_time:.2f} seconds", file=sys.stderr)

    except Exception as e:
        print(f"Error during simulation: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__=="__main__":
    main()
    exit(0)
