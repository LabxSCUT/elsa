#!/usr/bin/env python3
import numpy as np
import sys
import os

# Add the parent directory to the Python path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lsa._compcore import *; print(dir())

from lsa._compcore import LLA_Data, DP_lla
import numpy as np

def test_dp_lla():
    """Test calc LA the DP_lla function with simple data"""
    print("Testing DP_lla functionality...")
    
    try:
        # Create simple test data
        X = [1.0, 2.0, 3.0, 4.0, 5.0]
        Y = [2.0, 3.0, 4.0, 5.0, 6.0]
        Z = [3.0, 4.0, 5.0, 6.0, 7.0]
        
        # Create LLA_Data object
        print("Creating LLA_Data object...")
        lla_data = LLA_Data(2, X, Y, Z)  # delayLimit = 2
        
        # Run DP_lla
        print("Running DP_lla...")
        result = DP_lla(lla_data, True)
        
        print(f"\nResults:")
        print(f"Score: {result.score}")
        print(f"Trace length: {len(result.trace)}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Starting DP_lla test...\n")
    success = test_dp_lla()
    print(f"\nTest {'passed' if success else 'failed'}") 