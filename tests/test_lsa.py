#!/usr/bin/env python3
import numpy as np
import sys
import os

# Add the parent directory to the Python path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lsa._compcore import *; print(dir())

# You can use either of these import styles:
# Style 1: Direct import from _compcore
from lsa._compcore import LSA_Data, DP_lsa

# Style 2: Package import (if __init__.py is set up correctly)
# from lsa import LSA_Data, DP_lsa

def test_dp_lsa():
    """Test the DP_lsa function with simple data"""
    print("Testing DP_lsa functionality...")
    
    try:
        # Create simple test data
        X = [1.0, 2.0, 3.0, 4.0, 5.0]
        Y = [2.0, 3.0, 4.0, 5.0, 6.0]
        
        # Create LSA_Data object
        print("Creating LSA_Data object...")
        lsa_data = LSA_Data(2, X, Y)  # delayLimit = 2
        
        # Run DP_lsa
        print("Running DP_lsa...")
        result = DP_lsa(lsa_data, True)
        
        print(f"\nResults:")
        print(f"Score: {result.score}")
        print(f"Trace length: {len(result.trace)}")
        if len(result.trace) > 0:
            print(f"First trace point: {result.trace[0]}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Starting LSA test...\n")
    success = test_dp_lsa()
    print(f"\nTest {'passed' if success else 'failed'}") 