import sys


__version__ = "1.0.0"

if sys.version_info < (3, 6):
    print("You need python 3.6 or later to run yats")
    sys.exit(1)
