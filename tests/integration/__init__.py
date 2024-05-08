import sys
import os

# To avoid ModuleNotFound errors in tests while attempting to import test subjects.
# To be investigated here: https://mozilla-hub.atlassian.net/browse/DENG-3667
sys.path.append(f"{os.getcwd()}/src")
