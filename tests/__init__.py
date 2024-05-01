import sys
import os

# To avoid ModuleNotFound errors in tests while attempting to import test subjects.
sys.path.append(f"{os.getcwd()}/src")
