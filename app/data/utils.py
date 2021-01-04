# -*- coding: utf-8 -*-
"""Some small helper utilities."""

__copyright__ = "Copyright (C) 2020 Nordetect"

import analyseconfig
import config      ## NMR

import os
import sys
from os import path, makedirs,  remove as removefile
from shutil import rmtree
from time import time
from traceback import format_exception
from subprocess import run
from typing import Optional, Dict
import console_client
import json


Results = Dict[str, float]


backend_log_file = os.path.join(analyseconfig.log_dir, analyseconfig.backend_log_name)  ## NMR

def create_default_results() -> Results:
    """Generate some results with default values before a run.

    Returns:
        Results representing default state.

    """
    results = {}
    for spotindex, guiname in enumerate(analyseconfig.spot_gui_names):
        if guiname:
            if analyseconfig.spot_active[spotindex]:
                results[guiname] = -1.0
            else:
                results[guiname] = 0.0
    return results


def create_error_results() -> Results:
    """Generate some results representing errors.

    Returns:
        Results representing error state.

    """
    import random # NMR
    results = {}
    for guiname in analyseconfig.spot_gui_names:
        if guiname:
            #results[guiname] = -1.0   # NMR
            results[guiname] = 195.6   # NMR
            #results[guiname] = round(float(random.randint(1, 100)),1)  # NMR
    return results


def save_results(dirname: str, filename: str, results: Results) -> None:
    """Store the results of an analysis in a file.

    Parameters:
        dirname: Existing directory to store the results file.
        filename: File to store the results in.
        results: A results dictonary of name->value mappings to store.

    """
    filepath = path.join(dirname, filename)
    with open(filepath, 'w') as outfile:
        for name, value in results.items():
            outfile.write("{0}: {1:.2f}\n".format(name, value))


def load_results(dirname: str, filename: str, results: Optional[Results] = None) -> Results:
    """Load results from a file.

    Parameters:
        dirname: Directory holding the results file.
        filename: File holding the results.
        results: Default result values for values not found in the file.
    Returns:
        The results read will be returned as a dictonary of name->value.

    """
    if results is None:
        results = create_error_results()
    filepath = path.join(dirname, filename)
    with open(filepath, 'r') as infile:
        lines = infile.readlines()
    for line in lines:
        name, valuestring = line.strip().split(': ')
        results[name] = float(valuestring)
    return results


def log(filename: str, text: str) -> None:
    """Append the text the file with a timestamp in front."""
    with open(filename, "a") as file:
        print("{0} : {1}".format(int(time()), text), file=file)


def collect_debuginfo(e: Exception, part: str = "") -> None:
    """Collect debug information and store it in a file for later use.

    Parameters:
        e: Exception to collect debug information about.
        part: Part of the system where the error occured.

    """
    # TODO: Add check for space left on device before storing error info.
    print(e, file=sys.stderr)
    e_type, e_exception, e_traceback = sys.exc_info()
    e_lines = format_exception(e_type, e_exception, e_traceback)
    print(">>>>>>>>>>>>> Uexpected exit from task! <<<<<<<<<<<<<<", file=sys.stderr)
    print(''.join(e_lines), file=sys.stderr)
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<", file=sys.stderr)
    # Pack up debug info
    makedirs(path.abspath(analyseconfig.debug_dir), exist_ok=True)
    tar_work_dir, pack_dir = path.split(path.abspath(analyseconfig.tmp_dir))
    debug_file = 'debug_{0}{1}.tgz'.format(part, int(time()))
    debug_path = path.join(analyseconfig.debug_dir, debug_file)
    res = run(["tar", 'czf', debug_path, '-C', tar_work_dir, pack_dir])
    if res.returncode != 0:
        print("Could not store debug info!", file=sys.stderr)


def prepare_for_get_bar_code() -> None:
    """Clean up old leftover files and create dirs as needed."""
    barcode_dir = path.abspath(analyseconfig.barcode_dir)
    try:
        removefile(path.join(barcode_dir, analyseconfig.barcode_log_name))
    except FileNotFoundError:
        pass
    try:
        removefile(analyseconfig.barcode_file)
    except FileNotFoundError:
        pass
    # Create a new dir to put results in.
    makedirs(barcode_dir, exist_ok=True)


def prepare_for_check_sample() -> None:
    """Clean up old leftover files and create dirs as needed."""
    # TODO: Add check for space left on device before we start the process.
    results_dir = path.abspath(analyseconfig.results_dir)
    # Clean out left over data
    try:
        rmtree(results_dir)
    except FileNotFoundError:
        pass
    # Create a new dir to put results in.
    makedirs(results_dir)


def make_error_results_file() -> None:
    """Make the gui happy by making sure we have a correct results.txt."""
    try:
        results = load_results(analyseconfig.results_dir, analyseconfig.results_filename)
    except Exception:
        results = create_error_results()
    # NMR check result directory exists
    if not os.path.exists(analyseconfig.results_dir):
        os.makedirs(analyseconfig.results_dir)
    save_results(analyseconfig.results_dir, analyseconfig.results_filename, results)
    logfile = path.join(analyseconfig.log_dir, analyseconfig.log_name)
    log(logfile, "ERROR: Failed to checked a sample!")

def backend_logger(log_string: str) -> None:
    """NMR Handle any errors related to the API including logging"""
    def calling_function() -> str:
        import sys
        return sys._getframe(2).f_code.co_name

    if not os.path.exists(backend_log_file):
        open(backend_log_file, 'w').close()

    log(backend_log_file, f'{calling_function()} : {log_string}')
    print(f'{calling_function()} : {log_string}')

    try:
        if os.path.isfile(config.active_account_file):
            account_data = json.loads(get_file_data(config.active_account_file))
            account_name = account_data.get('name', '')

        if os.path.isfile(config.credentials_file):
            creds_data = json.loads(get_file_data(config.credentials_file))
            username = creds_data.get('username', '')

        if os.path.isfile(config.device_file):
            device = get_file_data(config.device_file)

        data = {
            'function': calling_function(),
            'error_text': log_string,
            'device' : 'TestDevice1',
            'account' : account_name,
            'user' : username,
        }

        message, status = console_client.upload_error(data)

        if not (status >= 200 and status < 400):
            print(f'Error in logging to console')
    except:
        print(f'backend_logger: no upload')

def get_file_data(filename: str) -> str:
    """NMR Shared function for file reading"""
    if not os.path.isfile(filename):
        return ""
    with open(filename, 'r') as file:
        return file.read()
