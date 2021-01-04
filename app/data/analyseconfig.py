# -*- coding: utf-8 -*-
"""Configuration for analysing tools like checksample.

This module adjust the python module path so you should import it before
any other non-system modules.
Note that configuration also used by the GUI is found in commonconfig.
all part of commonconfig is imported here, so you only need to import one
config in modules.

"""

__copyright__ = "Copyright (C) 2020 Nordetect"

import os
import sys
import pickle
# We import everything from commonconfig here so we only need to import one
# config file in our other scripts
from commonconfig import *

#################################################################
# Leave this section as it is unless you know what you are doing.

run_dir = os.getcwd()
"""The dir we are in when calling the program."""

sys.path.append(run_dir)
"""We add that to the path so we can override stuff like simulate."""

app_dir = os.path.dirname(os.path.abspath(__file__))
"""The application dir (where this script is also living)."""

#################################################################

# Add the path for python modules installed locally
sys.path.append('/home/pi/pythonmodules')

#################################################################

# Spots on the sample image is used for testing different values.
# There are 5 spots arranged in a pentagon with the one spot on top,
# two to the sides and two at the bottom. They are numbered as follows:
#      (1)
# (5)       (2)
#
#   (4)  (3)
#
# The following lists to get a value for spot x use [x-1] as python lists are
# zero indexed. Unused elements are given "empty" values.
spot_active = [False, False, False, True, True]
"""Is the spot being used for analyzis at the moment?"""
spot_model_names = ['', '', '', 'nitrate', 'phosphate']
"""Names used for the spots in the model."""
spot_gui_names = ['', 'K', 'N2', 'N1', 'P']
"""Names used for the spots in the GUI."""
spot_light_color = ['', '', '', 'green', 'red']
"""Light used when capturing images for use with the spot."""

nitrate_timing = {1: 15, 2: 135, 3: 55}
phosphate_timing = {1: 115, 2: 180, 3: 90, 4: 90}
nitrate_model, phosphate_model = int(os.environ["NITRATE_MODEL"]), int(os.environ["PHOSPHATE_MODEL"])
if nitrate_model not in nitrate_timing.keys():
    raise Exception("%s not a valid Nitrate model!" % nitrate_model)
if phosphate_model not in phosphate_timing.keys():
    raise Exception("%s not a valid Phosphate model!" % phosphate_model)
spot_timing = [-1, -1, -1, nitrate_timing[nitrate_model], phosphate_timing[phosphate_model]]
"""Time to capture the images in seconds since start."""

average_times = [-1, 0, 1]
"""Capture times relative to spot timing to take averages over."""
