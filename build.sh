#!/bin/bash
# Clean previous builds
rm -rf build/
rm -f lsa/*.so
rm -f lsa/*.pyc

# Rebuild
python3 setup.py build_ext --inplace
