#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read a barcode with the barcode scanner for the GUI backend.

This will always generate an file with a 6 digit barcode.
On failure the barcode stored will be 000000.

"""

__copyright__ = "Copyright (C) 2020 Nordetect"

import analyseconfig
import filelog

###########################################################################
# We can not import sys (stdout and stderr) before we have set up the
# logging and we want to do as much as possible after this point to get errors
# into our debug log.
filelog.setup_file_log(analyseconfig.barcode_dir, analyseconfig.barcode_log_name)

import sys
from os import makedirs, path

import barscan
from utils import collect_debuginfo, log

makedirs(path.abspath(analyseconfig.log_dir), exist_ok=True)
logfile = path.join(analyseconfig.log_dir, analyseconfig.log_name)
log(logfile, "Starting to get a barcode.")
makedirs(path.abspath(analyseconfig.barcode_dir), exist_ok=True)
try:
    print("")
    print("================================================================================")
    print("Waiting for barcode to be scanned")
    barcode = barscan.scan()
    barscan.save_barcode(barcode, analyseconfig.barcode_file)
except Exception as e:
    collect_debuginfo(e, "barcode")
    # Make the gui happy by making sure we have a correct barcode file
    barscan.save_barcode("000000", analyseconfig.barcode_file)
    message = "ERROR: Failed to get a barcode!"
    log(logfile, message)
    print(message)
    sys.exit(1)
message = "We got barcode {0}.".format(barcode)
log(logfile, message)
print(message)
