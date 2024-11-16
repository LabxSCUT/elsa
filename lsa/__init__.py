"""
LSA Package - Local Similarity Analysis and Local Liquid Association Analysis

This package provides tools for analyzing time series data using Local Similarity
Analysis (LSA) and Local Liquid Association (LLA) methods.

Modules:
    compcore: Core computational functions implemented in C++
    lsalib: Python implementation of LSA/LLA algorithms and utilities

The package maintains backward compatibility while using modern PyBind11 bindings
for C++ integration.
"""

# Import and expose the main modules
from . import compcore
from . import lsalib

# Make compcore's symbols available directly from lsa for convenience
from .compcore import (
    LSA_Data,      # Container for LSA input data
    LSA_Result,    # Container for LSA results
    DP_lsa,        # Main LSA computation function
    LLA_Data,      # Container for LLA input data
    LLA_Result,    # Container for LLA results
    DP_lla,        # Main LLA computation function
    calc_LA,       # Static LA calculation
    test           # Test function
)

# Define what symbols are exported
__all__ = [
    'compcore',    # Core computational module
    'lsalib',      # Library of LSA/LLA functions
    # Direct access to core classes and functions
    'LSA_Data',
    'LSA_Result',
    'DP_lsa',
    'LLA_Data',
    'LLA_Result',
    'DP_lla',
    'calc_LA',
    'test'
]

# Package metadata
__version__ = "2.0.0"
__author__ = "Li Charles Xia"
__copyright__ = "Copyright (c) 2008-2024 Li Charles Xia"
__license__ = "BSD"
