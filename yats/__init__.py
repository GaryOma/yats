import sys
import logging
import os


__version__ = "1.0.0"

if sys.version_info < (3, 6):
    print("You need python 3.6 or later to run yats")
    sys.exit(1)

logging_mode = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'critical': logging.CRITICAL
}

logging_os = os.getenv('LOGGING', 'info')
logging_level = logging_mode[logging_os]
logger = logging.getLogger()
logging.basicConfig(level=logging_level, format=('%(message)s'))
