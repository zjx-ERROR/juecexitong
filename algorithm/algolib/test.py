#!/usr/bin/python
print("begin test")
import sys
import os
sys.path.append(os.path.abspath("../evaluate"))
print(sys.path)
print("==============")
print(os.path.abspath("../evaluate"))
import fscore_evaluate
print("end test")
