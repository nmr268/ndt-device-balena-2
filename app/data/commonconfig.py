# -*- coding: utf-8 -*-
"""Configuration parts need by both the GUI and the CLI."""

__copyright__ = "Copyright (C) 2020 Nordetect"

tmp_dir = "/tmp/nordetect"     # NMR remove TEMP before balena deploy!
"""Dir to place all temporary information."""

data_dir = "/data"     # NMR remove TEMP before balena deploy!
"""Dir to place all persistent data."""

results_dir = tmp_dir + "/results"
"""Dir to place results from checksample.
This will be cleaned on every check sample start."""

backend_log_name = "backend.log"
"""Name of log file for backend processes and communication with console"""

results_filename = "results.txt"
"""File with final results."""

sample_filename = "sample.png"
"""Sample image file name."""

checksample_log_name = "checksample.log"
"""Name of log file for checksample."""

barcode_dir = tmp_dir
"""Dir we store the barcode file in."""

barcode_file = tmp_dir + "/barcode.txt"
"""Barcode file written by get_barcode."""

barcode_log_name = "barcode.log"
"""Name of log file for get_barcode."""

log_dir = data_dir + "/logs"
"""Log dir (if inside results_dir, it will be cleaned at each start)."""

log_name = "nordetect.log"
"""Name of general log file."""

debug_dir = data_dir + "/debug"
"""Dir to store debug infomation."""

checksample_status_file = tmp_dir + "/checksample.status"
"""File to communicate status. Should not be inside results_dir."""

checksample_pid_file = tmp_dir + "/checksample.pid"
"""File with the checksample daemon PID. Should not be inside results_dir."""
