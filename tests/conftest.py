import os
import sys

prject_root = os.path.join(os.path.dirname(__file__), '..')
print("Project Root", prject_root)
sys.path.insert(0, prject_root)
print("sys.path", sys.path)