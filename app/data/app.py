#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2020 Nordetect"

import uuid

from typing import Dict,  Optional, Any
from flask import Flask, send_from_directory, Response, request
from flask_cors import CORS
import os
import os.path
import shutil
import datetime
import json
import glob
import console_client
from subprocess import Popen, call
import requests
import config
import analyseconfig
import math
import user_options
import checksample_com as cs_com       ## NMR comment out in minimal
import utils
import barscan
if config.enabled_wifi:
    import NetworkManager
try:
    from simulate import fake_power
except ImportError:
    fake_power = False


APP_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_FOLDER = os.path.join(APP_DIR, 'react')
TEMPLATE_FOLDER = os.path.join(APP_DIR, 'react')

app = Flask(__name__, static_folder=STATIC_FOLDER, template_folder=TEMPLATE_FOLDER)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

if not os.path.exists(config.tmp_dir):
    os.makedirs(config.tmp_dir)
if not os.path.exists(config.stored_results_dir):
    os.makedirs(config.stored_results_dir)
if not os.path.exists(config.stored_images_dir):
    os.makedirs(config.stored_images_dir)
if not os.path.exists(config.results_dir):
    os.makedirs(config.results_dir)
if not os.path.exists(config.data_dir):
    os.makedirs(config.data_dir)
if not os.path.exists(config.log_dir):
    os.makedirs(config.log_dir)
if not os.path.exists(config.debug_dir):
    os.makedirs(config.debug_dir)

utils.backend_logger(f'*****Starting Flask')

stored_results_directory = config.stored_results_dir
results_directory = config.results_dir
stored_images_directory = config.stored_images_dir
results_file = os.path.join(results_directory, config.results_filename)
credentials_file = config.credentials_file
accounts_file = config.accounts_file
active_account_file = config.active_account_file
user_options_file = config.user_options_file
device_file = config.device_file
barcode_file = config.barcode_file
is_test = config.devtest


#### Initialize system
if os.path.isfile(credentials_file):
    os.remove(credentials_file)
if os.path.isfile(accounts_file):
    os.remove(accounts_file)
if os.path.isfile(active_account_file):
    os.remove(active_account_file)
if os.path.isfile(user_options_file):
    os.remove(user_options_file)
if os.path.isfile(device_file):
    os.remove(device_file)
if os.path.isfile(barcode_file):
    os.remove(barcode_file)

with open(device_file, 'w') as fh:
    fh.write(os.environ.get('HOSTNAME', ''))

barcode_process: Optional[Popen] = None

network_ready = False

api_url = os.environ.get('BALENA_SUPERVISOR_ADDRESS')
api_tkn = os.environ.get('BALENA_SUPERVISOR_API_KEY')

@app.route("/api/analysis/start", methods=["POST"])
def analysis_start() -> Response:
    #utils.backend_logger(f'{request.endpoint} : {request.method} : {request.data} : {request.args} : {request.form} : {request.remote_addr}')

    try:
        global barcode_process
        # Clean up old files before starting
        utils.prepare_for_get_bar_code()
        utils.prepare_for_check_sample()
        # Check if we system is ready
        ## NMR things with ### here are sanitized to avoid exposing confidential code code ###
        analysis_status = cs_com.Status.get_status() ## sanitize
        if analysis_status == cs_com.Status.READY:  ### sanitize
             # Start the analyse process
             cs_com.Control.analyse()      ### sanitize
        else:                             ### sanitize
        # We should be ready, something is wrong
        # As the GUI do not handle failures here right now,
        # we create some result files for it to be happy.
        ### sanitize unindent next block
            utils.make_error_results_file()     # sanitize unindent
            #test_barcode = "testBarcode1"   # sanitize unindent
            #barscan.save_barcode(test_barcode, barcode_file)  # sanitize unindent
            #return Response("analysis started", 200)  # sanitize unindent

        # Get a barcode
        if barcode_process:
            # Make sure old processes are not running
            barcode_process.kill()

        #user_options = get_json_from_file(user_options_file)
        user_options = json.loads(get_file_data(user_options_file))
        use_barcode = user_options['use_barcode']
        if use_barcode:
            barcode_process = Popen(["python3", "get_barcode.py"])

        return Response("analysis started", 200)

    except Exception as e:
        utils.backend_logger(f'{str(e)}')
        return Response("Error: Analysis failed to start", 422)


@app.route("/api/analysis/barcode", methods=["GET"])
def barcode_status() -> Response:
    try:
        #utils.backend_logger(f'{request.endpoint} : {request.method} : {request.data} : {request.args} : {request.form} : {request.remote_addr}')
        if os.path.isfile(barcode_file):
            return Response("barcode found", 200)
        else:
            return Response("barcode not present", 422)
    except Exception as e:
        utils.backend_logger(f'{str(e)}')
        return Response("Error: failed to get barcode", 422)

@app.route("/api/analysis/status", methods=["GET"])
def results_status() -> Response:
    #utils.backend_logger(f'{request.endpoint} : {request.method} : {request.data} : {request.args} : {request.form} : {request.remote_addr}')

    # the following block ensures there is a defaut barcode even if user has pressed Skip barcode
    user_options = get_json_from_file(user_options_file)
    use_barcode = user_options['use_barcode']

    if use_barcode:
        if not os.path.isfile(barcode_file):
        # if use_barcode is true but there is no barcode file then it means the user has
        # hit the skip button, so we need to kill the barcode process if it is running
            print(f'***Skip button pressed')
            if barcode_process:
                print(f'***Killing barcode process')
                barcode_process.kill()
            print(f'***Closing scanner')
            barscan.close_scanner()   ## NMR Uncomment in Production!
            barscan.save_barcode('000000', barcode_file)
        else:
            if os.path.getsize(barcode_file) == 0:
                barscan.save_barcode('000000', barcode_file)

    try:
        if os.path.isfile(results_file):
            values = read_analysis(results_file)

            return Response(json.dumps(values), 200)
        else:
            return Response("results not present", 422)
    except Exception as e:
        utils.backend_logger(f'{str(e)}')
        return Response("Error: failed to get results", 422)

def get_json_from_file(myFile):
    input = get_file_data(myFile)
    output = ""
    try:
        output = json.loads(input)
    except ValueError as e:
        output = ""
    return output

@app.route("/api/user/state", methods=["GET"])
def get_state_info() -> Response:

    #try:
    #utils.backend_logger(f'{request.endpoint} : {request.method} : {request.data} : {request.args} : {request.form} : {request.remote_addr}')
    user_options = get_json_from_file(user_options_file)
    account_data = get_json_from_file(active_account_file)
    user_data = get_json_from_file(credentials_file)

    user_options_use_barcode = user_options_model_type = active_account_id =\
    active_account_name = current_user = user_options_use_barcode_t =\
    user_options_model_type_t = None

    if user_options:
        user_options_use_barcode = { True : 1, False : 2 }.get(user_options['use_barcode'])
        user_options_use_barcode_t = { True : 'Used', False : 'Not used' }.get(user_options['use_barcode'])
        user_options_model_type = { "soil" : 1, "water" : 2 }.get(user_options['model_type'])
        user_options_model_type_t = user_options.get('model_type')
    if account_data:
        active_account_id = int(account_data['id'])
        active_account_name = account_data['name']
    if user_data:
        current_user = user_data['username']

    if user_options:
        stored_results_need_upload = read_stored_results(True, True)
    else:
        # we only want this true after the user is logged in
        stored_results_need_upload = False

    try:
        analysis_time = analyseconfig.spot_timing[4] + 20
        #analysis_time = 60 * (math.floor(yellow_time / 60) + 1) + yellow_time
    except:
        analysis_time = 180
    print(f'Analysis time = {analysis_time}')

    nitrate_model = os.environ.get('NITRATE_MODEL')
    phosphate_model = os.environ.get('PHOSPHATE_MODEL')

    return_values = {
            "current_user" : current_user,
            "active_account_id" : active_account_id,
            "active_account_name" : active_account_name,
            "user_options_use_barcode" : user_options_use_barcode,
            "user_options_use_barcode_t" : user_options_use_barcode_t,
            "user_options_model_type" : user_options_model_type,
            "user_options_model_type_t" : user_options_model_type_t,
            "stored_results_need_upload" : stored_results_need_upload,
            "analysis_time" : analysis_time,
            "nitrate_model" : nitrate_model,
            "phosphate_model" : phosphate_model,
    }
    return Response(json.dumps(return_values), 200)

    #except Exception as e:
        #utils.backend_logger(f'{str(e)}')
        #return Response("Error returning state values", 422)

def read_stored_results(want_upload_status, active_account_only):
    results = []

    active_account_id = get_json_from_file(active_account_file).get('id', '')

    for f in sorted(glob.glob(os.path.join(stored_results_directory, "*.results.txt"))):

        # skip any file that returns error
        try:
            values = read_analysis(f)

            proceed = False
            if active_account_only:
                if active_account_id == values["account_id"]:
                    proceed = True
            else:
                proceed = True

            if proceed:
                name_info = os.path.basename(f).split(".")
                date_time = datetime.datetime.fromtimestamp(
                    int(name_info[0])).strftime('%Y-%m-%d %H:%M:%S')
                barcode = values["barcode"]
                data = {}
                data['N1'] = values['N1']
                data['N2'] = values['N2']
                data['K'] = values['K']
                data['P'] = values['P']
                result = {"timestamp": date_time, "data": data, "barcode": barcode}   ## NMR XX
                if values["uploaded"] == 'True':
                    uploaded = True
                else:
                    uploaded = False
                    if want_upload_status:
                        # returning True means there are results that need uploading
                        return True

                result = {
                        "timestamp": date_time,
                        "data": data,
                        "barcode": values["barcode"],
                        "data_id": values["data_id"],
                        "sample_id": values["sample_id"],
                        "uploaded": uploaded,
                        "account_id": values["account_id"],    ## NMR TODO should be int
                        "account_name": values["account_name"],
                        "local_id": name_info[0],
                }

                results.append(result)
        except Exception:
            pass


    if want_upload_status:
        # returning True means there are results that need uploading
        return False

    return results

@app.route("/api/analysis/stored_results", methods=["GET"])
def stored_results() -> Response:
    results = read_stored_results(False, True)
    results = list(reversed(results))
    return Response(json.dumps(results), 200)

@app.route("/api/analysis/uploadtest", methods=["POST"])
def upload_test() -> Response:
    testcase = request.form.get("testcase", None)
    print(f'{request.endpoint} : {request.method} : {request.data} : {request.args} : {request.form} : {request.remote_addr}')
    present = 'testcase' in request.form.to_dict()
    if testcase:
        return Response(f'testcase is True {present}', 200)
    return Response(f'testcase is False {present}', 200)

@app.route("/api/analysis/upload", methods=["POST"])
def analysis_upload() -> Response:
    #utils.backend_logger(f'{request.endpoint} : {request.method} : {request.data} : {request.args} : {request.form} : {request.remote_addr}')

    local_id = request.form.get("local_id", None)

    store_local = request.form.get("store_local", "false")
    store_local = { 'true' : True, 'false' : False }.get(store_local)

    new_sample = request.form.get("new_sample", "false")
    new_sample = { 'true' : True, 'false' : False }.get(new_sample)

    message, status = console_client.hello()

    noNetwork = False
    if not (status == 401):
        noNetwork = True

    if local_id:
        if noNetwork:
            return Response(f'no network', 422)

        files = glob.glob(os.path.join(stored_results_directory, f'{local_id}.results.txt'))
        if files:
            if len(files) > 1:
                utils.backend_logger(f'More than one stored file found with name: {local_id}.results.txt')
                return Response("More than one stored file was found", 422)
            stored_results_file = files[0]
            values = read_analysis(stored_results_file)
            barcode = values['barcode']
            device_name = read_device_name(device_file)
            account_id = values["account_id"]
            account_name = values["account_name"]
            ## NMR check id sample_id is in the request, otherwise lift it from the stored_results file
            has_sample_id = 'sample_id' in request.form.to_dict()
            if has_sample_id:
                sample_id = request.form.get("sample_id", '')
            else:
                sample_id = values["sample_id"]
                if sample_id:
                    has_sample_id = True
                else:
                    has_sample_id = False
            results_values = {}
            results_values["N1"] = values["N1"]
            results_values["N2"] = values["N2"]
            results_values["K"] = values["K"]
            results_values["P"] = values["P"]
            results_time = local_id
            if barcode:
                use_barcode = True
            else:
                use_barcode = False
            nitrate_file = f'{stored_images_directory}/{local_id}.nitrate.png'
            phosphate_file = f'{stored_images_directory}/{local_id}.phosphate.png'
        else:
            utils.backend_logger(f'no file found called {local_id}.results.txt')
            return Response(f'no file found called {local_id}.results.txt', 422)

    else:
        if not os.path.isfile(results_file):
            utils.backend_logger(f'Results file not found')
            return Response("Results file not found", 422)       ## NMR no results_file available

        stored_results_file = None
        #user_options = get_json_from_file(user_options_file)
        user_options = json.loads(get_file_data(user_options_file))
        use_barcode = user_options['use_barcode']

        results_time = os.path.getmtime(results_file)
        results_values = read_analysis(results_file)
        if use_barcode:
            barcode = read_barcode(barcode_file)
        else:
            barcode = ""
        #barcode = read_barcode(barcode_file)        ## NMR can get exception here YY
        device_name = read_device_name(device_file)
        account_data = json.loads(get_file_data(active_account_file))
        account_name = account_data["name"]
        account_id = account_data["id"]
        has_sample_id = 'sample_id' in request.form.to_dict()
        sample_id = request.form.get("sample_id", '')
        nitrate_file = f'{results_directory}/nitrate/sample.png'
        phosphate_file = f'{results_directory}/phosphate/sample.png'


    timestamp = str(int(results_time))
    analyzed = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

    spa_data = results_values
    spa_data["analyzed"] = analyzed
    spa_data["device"] = device_name

    #print(f'HERE2 sample_id = {sample_id}, use_barcode = {use_barcode}, has_sample_id = {has_sample_id}, barcode = {barcode}')

    if store_local:
        data_id = ""
        write_stored_results(False, data_id, sample_id, stored_results_file)
        case7 = {
                'case' : 'case7',
                'uploaded' : False,
                'stored' : True
                }
        return Response(json.dumps(case7), 200)

    if new_sample:
        ##############
        # create sample
        data = {
                'account' : account_id,
                'sample_id' : sample_id,
                }

        if use_barcode:
            data["barcode"] = barcode
            if not has_sample_id:
                data["sample_id"] = barcode
        else:
            data["barcode"] = ""

        #print(f'HERE3: Creating sample with data: {data}  use_barcode = {use_barcode}')

        status = 500
        if not noNetwork:
            message, status = console_client.create_sample(data)

        if not (status >= 200 and status < 400):
            if 'A sample with this sample_id already exists in this account' in message:
                case8 = {
                        'case' : 'case8',
                        'text' : f'A sample with this sample_id {sample_id} already exists in account {account_name}',
                        'uploaded' : False,
                        'stored' : False,
                        'local_id' : local_id
                        }
                return Response(json.dumps(case8), 200)
            if 'A sample with this barcode already exists in this account' in message:
                case8 = {
                        'case' : 'case9',
                        'text' : f'A sample with barcode {barcode} already exists in account {account_name}',
                        'uploaded' : False,
                        'stored' : False,
                        'local_id' : local_id
                        }
                return Response(json.dumps(case8), 200)
            utils.backend_logger(f'upload error 1: {status} : {message}')
            write_stored_results(False, "", sample_id, stored_results_file)
            return Response("upload error 1", 422)

        message_s = json.loads(message)
        sample = message_s['id']
        sample_id = message_s['sample_id']
        ############
        #sample, sample_id = create_sample(account_id, sample_id, barcode, use_barcode)
        spa_data["sample"] = sample

        status = 500
        if not noNetwork:
            message, status = console_client.create_spadata(spa_data)
        #message_s = json.loads(message)
        if not (status >= 200 and status < 400):
            utils.backend_logger(f'upload error 2: {status} : {message}')
            write_stored_results(False, "", sample_id, stored_results_file)
            return Response("upload error 2", 422)#message_s = json.loads(message)
        message_s = json.loads(message)

        spaimage_data = {"sample": sample, "image": "sample.png", "tag": f'nitrate : {spa_data.get("N1")}'}
        status = 500
        if not noNetwork:
            message, status = console_client.create_spaimage(spaimage_data, nitrate_file)
        if not (status >= 200 and status < 400):
            utils.backend_logger(f'upload error 3: {status} : {message}')
            #write_stored_results(False, "", sample_id, stored_results_file)
            #return Response("upload error 3", 422)
        spaimage_data = {"sample": sample, "image": "sample.png", "tag": f'phosphate : {spa_data.get("P")}'}
        status = 500
        if not noNetwork:
            message, status = console_client.create_spaimage(spaimage_data, phosphate_file)
        if not (status >= 200 and status < 400):
            utils.backend_logger(f'upload error 4: {status} : {message}')
            #write_stored_results(False, "", sample_id, stored_results_file)
            #return Response("upload error 4", 422)

        data_id = message_s['data_id']
        case5 = {
                'case' : 'case5',
                'text' : f'Your analysis is saved and linked to sample_id {sample_id} and barcode {barcode} created in account {account_name}',
                'uploaded' : True,
                'stored' : True
                }

        case6 = {
                'case' : 'case6',
                'text' : f'Your analysis is saved and linked to sample_id {sample_id} created in account {account_name}',
                'uploaded' : True,
                'stored' : True
                }

        write_stored_results(True, data_id, sample_id, stored_results_file)

        if use_barcode:
            return Response(json.dumps(case5), 200)
        else:
            return Response(json.dumps(case6), 200)

    else:
        ########
        # find sample
        data = {
            'account' : account_id,
            }

        if use_barcode:
            data["use_barcode"] = True
            data["barcode"] = barcode
            data["sample_id"] = ""
        else:
            data["use_barcode"] = False
            data["barcode"] = ""
            data["sample_id"] = sample_id

        status = 500
        if not noNetwork:
            message, status = console_client.find_sample(data)

        if not (status >= 200 and status < 400):
            utils.backend_logger(f'upload error 5: {status} : {message}')
            write_stored_results(False, "", sample_id, stored_results_file)
            return Response("upload error 5", 422)

        message_s = json.loads(message)

        if message_s:
            if len(message_s) > 1:
                utils.backend_logger(f'upload error 6 :More than one sample found: {len(message_s)}')
                write_stored_results(False, "", "", stored_results_file)
                return Response("upload error 6", 422)
            sample = message_s[0]['id']
            sample_id = message_s[0]['sample_id']
        else:
            sample = None

        #return None, sample_id
        ##############################
        #sample, sample_id = find_sample(account_id, sample_id, barcode, use_barcode)
        if sample:
            spa_data["sample"] = sample
            status = 500
            if not noNetwork:
                message, status = console_client.create_spadata(spa_data)
            #message_s = json.loads(message)

            if not (status >= 200 and status < 400):
                utils.backend_logger(f'upload error 7: {status} : {message}')
                write_stored_results(False, "", sample_id, stored_results_file)
                return Response("upload error 7", 422)

            message_s = json.loads(message)

            spaimage_data = {"sample": sample, "image": "sample.png", "tag": f'nitrate : {spa_data.get("N1")}'}
            message, status = console_client.create_spaimage(spaimage_data, nitrate_file)
            if not (status >= 200 and status < 400):
                utils.backend_logger(f'upload error 8: {status} : {message}')
                #write_stored_results(False, "", sample_id, stored_results_file)
                #return Response("upload error 8", 422)
            spaimage_data = {"sample": sample, "image": "sample.png", "tag": f'phosphate : {spa_data.get("P")}'}
            status = 500
            if not noNetwork:
                message, status = console_client.create_spaimage(spaimage_data, phosphate_file)
            if not (status >= 200 and status < 400):
                utils.backend_logger(f'upload error 9: {status} : {message}')
                #write_stored_results(False, "", sample_id, stored_results_file)
                #return Response("upload error 9", 422)

            data_id = message_s['data_id']
            write_stored_results(True, data_id, sample_id, stored_results_file)

            case3 = {
                    'case' : 'case3',
                    'text' : f'Your analysis is saved and linked to sample_id {sample_id} and barcode {barcode} in account {account_name}',
                    "uploaded": True,
		            "stored": True
                    }

            case4 = {
                    'case' : 'case4',
                    'text' : f'Your analysis is saved and linked to sample_id {sample_id} in account {account_name}',
                    "uploaded": True,
		            "stored": True
                    }

            if use_barcode:
                return Response(json.dumps(case3), 200)
            else:
                return Response(json.dumps(case4), 200)


        else:
        # else return case1 or case2
            case1 = {
                    'case' : 'case1',
                    'text' : f'There is currently no sample with barcode {barcode} in account {account_name}',
                    'uploaded': False,
		            'stored': False,
                    'local_id': local_id
                    }

            case2 = {
                    'case' : 'case2',
                    'sample_id' : sample_id,
                    'text' : f'There is currently no sample with sample_id {sample_id} in account {account_name}',
                    'uploaded': False,
		            'stored': False,
                    'local_id': local_id
                    }
            if use_barcode:
                return Response(json.dumps(case1), 200)
            else:
                return Response(json.dumps(case2), 200)

def save_images(timestamp: str) -> None:
    """
        Save images created during analysis
        Samples are located in directories of the form:
        /tmp/nordetect/results/nitrate/sample.png
        /tmp/nordetect/results/phosphate/sample.png

        and are placed into the directory
        /data/images
    """

    if not os.path.exists(stored_images_directory):
        print(f'***Make stored images dir {stored_images_directory}')
        os.makedirs(stored_images_directory)

    analytes = ['nitrate', 'phosphate',]

    for analyte in analytes:
        image_file = f'{results_directory}/{analyte}/sample.png'
        filename_new = f'{timestamp}.{analyte}.png'
        try:
            shutil.move(image_file, os.path.join(stored_images_directory, filename_new))
        except Exception as e:
            utils.backend_logger(f'Could not write {filename_new} {repr(e)}')

def write_stored_results(uploaded: bool, data_id: str, sample_id: str, stored_results_file: str) -> None:

    """
        K: -1.00
        N2: -1.00
        N1: -1.00
        P: -1.00
        barcode: 000000000000
        uploaded: True
        data_id: 2020-09-2209:11:16.270480.7944_3_1
        sample_id: 2020-09-2209:11:16.270480.7944
        account_name: TestFarm3
        account_id: 3
    """
    if stored_results_file:
        # take info from file, rm old file and make new
        file = stored_results_file
        values = read_analysis(file)
        barcode = values["barcode"]
        account_name = values["account_name"]
        account_id = values["account_id"]

        with open(file, 'w') as fh:     ## NMR XX CHECK
            fh.write(f'N1: {values["N1"]}\
            \nN2: {values["N2"]}\
            \nP: {values["P"]}\
            \nK: {values["K"]}\
            \nbarcode: {barcode}\
            \nuploaded: {uploaded}\
            \ndata_id: {data_id}\
            \nsample_id: {sample_id}\
            \naccount_name: {account_name}\
            \naccount_id: {account_id}')

    else:
        results_time = os.path.getmtime(results_file)
        account_data = json.loads(get_file_data(active_account_file))
        account_name = account_data["name"]
        account_id = account_data["id"]

        #user_options = get_json_from_file(user_options_file)
        user_options = json.loads(get_file_data(user_options_file))
        use_barcode = user_options['use_barcode']
        if use_barcode:
            barcode = read_barcode(barcode_file)
        else:
            barcode = ""

        # setup for local storage
        if not os.path.exists(stored_results_directory):
            os.makedirs(stored_results_directory)

        timestamp = str(int(results_time))

        filename_new = f'{timestamp}.results.txt'   # NMR ## changed timestamp on results file

        with open(results_file, 'a') as fh:     ## NMR XX CHECK
            fh.write(f'barcode: {barcode}\
            \nuploaded: {uploaded}\
            \ndata_id: {data_id}\
            \nsample_id: {sample_id}\
            \naccount_name: {account_data["name"]}\
            \naccount_id: {account_data["id"]}')

        shutil.move(results_file, os.path.join(stored_results_directory, filename_new))

        save_images(timestamp)


def get_file_data(filename: str) -> str:
    if not os.path.isfile(filename):
        return ""
    with open(filename, 'r') as file:
        return file.read()


@app.route("/api/poweroff", methods=["POST"])
def poweroff() -> Response:
    #utils.backend_logger(f'{request.endpoint} : {request.method} : {request.data} : {request.args} : {request.form} : {request.remote_addr}')
    if fake_power:
        call(["killall", "/usr/lib/chromium/chromium"])
    else:
        requests.post(api_url + "/v1/shutdown?apikey=" + api_tkn, headers={'Content-Type': 'application/json'})
        #call(["sudo", "shutdown", "now"])
    return Response("poweroff", 200)


@app.route("/api/user/isloggedin", methods=["GET"])
def is_logged_in() -> Response:
    #utils.backend_logger(f'{request.endpoint} : {request.method} : {request.data} : {request.args} : {request.form} : {request.remote_addr}')
    if os.path.isfile(credentials_file):
        return Response("Creds Found", 200)
    else:
        return Response("Creds not Found", 422)

@app.route("/api/user/login", methods=["POST"])
def user_login() -> Response:
    #utils.backend_logger(f'{request.endpoint} : {request.method} : {request.data} : {request.args} : {request.form} : {request.remote_addr}')

    username = request.form["username"]
    password = request.form["password"]
    #utils.backend_logger(f'Login endpoint called with {username} and {password}')
    creds_file = credentials_file


    if not username and is_test:
        return Response("Running test without username", 200)

    login_data = {
        'username': username,
        'password': password,
    }

    try:
        message, status = console_client.login(login_data)
    except Exception as e:
        utils.backend_logger(f'login error: {str(e)}')   ## NMR TODO  see if we can refine this error
        return Response("There is a problem connecting with Nordetect server", 422)

    if not (status >= 200 and status < 400):
        utils.backend_logger(f'login error: {status} : {message}')
        if os.path.exists(creds_file):
            os.remove(creds_file)
        if status == 400:
            return Response("Username or password is incorrect", 400)
        else:
            return Response("There is a problem connecting with Nordetect server", 422)

    response = json.loads(message)
    access_token = response.get('token')
    creds_data = {}

    creds_data["username"] = login_data["username"]
    creds_data["token"] = access_token

    with open(creds_file, 'w') as fh:
        fh.write(json.dumps(creds_data))

    utils.backend_logger(f'{login_data["username"]} logged in')
    return Response("Login succeeded", 200)

@app.route("/api/user/options", methods=["GET"])
def get_user_options() -> Response:
    #utils.backend_logger(f'{request.endpoint} : {request.method} : {request.data} : {request.args} : {request.form} : {request.remote_addr}')

    try:
        options = user_options.options
        return Response(json.dumps(options), 200)
    except Exception as e:
        return Response(repr(e), 400)

@app.route("/api/user/options", methods=["POST"])
def set_user_options() -> Response:
    #utils.backend_logger(f'{request.endpoint} : {request.method} : {request.data} : {request.args} : {request.form} : {request.remote_addr}')

    user_options = {}

    use_barcode = request.form["use_barcode"]
    if use_barcode == '1':
        user_options['use_barcode'] = True
    else:
        user_options['use_barcode'] = False
    model_type = request.form["model_type"]
    if model_type == '1':
        user_options['model_type'] = 'soil'
    else:
        user_options['model_type'] = 'water'
    #https://stackoverflow.com/questions/10434599/get-the-data-received-in-a-flask-request
    #user_options['use_barcode'] = request.get_json(force=True)["use_barcode"]

    with open(user_options_file, 'w') as fh:
        fh.write(json.dumps(user_options))

    return Response("user_options updated", 200)

@app.route("/api/user/set_account", methods=["POST"])
def set_active_account() -> Response:
    #utils.backend_logger(f'{request.endpoint} : {request.method} : {request.data} : {request.args} : {request.form} : {request.remote_addr}')

    active_account = {}
    active_account['id'] = request.form["id"]
    active_account['name'] = request.form["name"]

    with open(active_account_file, 'w') as fh:
        fh.write(json.dumps(active_account))

    return Response("active_account updated", 200)

@app.route("/api/user/accounts", methods=["GET"])
def get_user_accounts() -> Response:
    #utils.backend_logger(f'{request.endpoint} : {request.method} : {request.data} : {request.args} : {request.form} : {request.remote_addr}')

    if is_test:
        message = '[{"id": 1, "name" : "Test-Mode"}]'
        return Response(message, 200)

    creds_data = get_file_data(credentials_file)

    if 'username' not in creds_data:
        return Response("Please Login", 422)
    if 'token' not in creds_data:
        return Response("Please Login", 422)

    message, status = console_client.user_accounts(json.loads(creds_data))

    if not (status >= 200 and status < 400):
        utils.backend_logger(f'error getting accounts: {status} : {message}')
        if os.path.exists(accounts_file):
            os.remove(accounts_file)
        return Response("Failed to get user accounts", 422)
    else:
        with open(accounts_file, 'w') as fh:      ## NMR XX actually do we need this file ?
            fh.write(message)
        return Response(message, 200)


@app.route("/api/user/wifi", methods=["GET"])
def wifi_list() -> Response:
    #utils.backend_logger(f'{request.endpoint} : {request.method} : {request.data} : {request.args} : {request.form} : {request.remote_addr}')
    #### Initialize system
    # if os.path.isfile(user_options_file):
    #     print(f'*****REMOVING USER_OPTIONS_FILE 2*******')
    #     os.remove(user_options_file)

    ssid_list = []
    if config.enabled_wifi:
        for dev in NetworkManager.NetworkManager.GetDevices():
            if dev.DeviceType != NetworkManager.NM_DEVICE_TYPE_WIFI:
                continue
            for ap in dev.GetAccessPoints():
                ssid_list.append(ap.Ssid)
        if ssid_list:
            return Response(json.dumps(ssid_list), 200)
        else:
            return Response('No networks available, please try again later', 422)

    return Response(json.dumps(ssid_list), 200)

@app.route("/api/user/network_status", methods=["GET"])
def wifi_status() -> Response:

    ## nmr make a ping to console.nordetect.com

    # if config.enabled_wifi:
    #     command = "ping -c 2 $(ip route | grep default | awk '{print $3}') | grep transmitted | awk '{print $6}'"
    #     import subprocess
    #     process = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True)
    #     result = process.stdout
    #     print(f'wifi_status result = {result}')
    #     if '0%' in result:
    #         return Response(json.dumps({ "network_status": 'OK'}), 200)
    #     else:
    #         return Response(json.dumps({ "network_status": 'DOWN'}), 200)

    message, status = console_client.hello()
    #print(f'WIFI_STATUS: {message}, {status}')
    if not (status == 401):
        #print(f'WIFI_STATUS: {message}, {status}')
        return Response(json.dumps({ "network_status": 'DOWN'}), 200)
    return Response(json.dumps({ "network_status": 'OK'}), 200)

def connect_to_wifi(ssid: str, password: str) -> None:
    if config.enabled_wifi:
        settings = {
            u'802-11-wireless': {
                u'ssid': ssid,
                u'mode': u'infrastructure',
                u'security': u'802-11-wireless-security',
            },
            u'connection': {
                u'uuid': str(uuid.uuid4()),
                u'id': u'Connection {0}'.format(ssid),
                u'type': u'802-11-wireless',
            },
            u'ipv4': {
                u'method': u'auto',
            },
            u'802-11-wireless-security': {
                u'key-mgmt': u'wpa-psk',
                u'auth-alg': u'open',
                u'psk': password,
            },
            u'ipv6': {
                u'method': u'auto',
            }
        }


        c = NetworkManager.Settings.AddConnection(settings)

        for dev in NetworkManager.NetworkManager.GetDevices():
            if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
                NetworkManager.NetworkManager.ActivateConnection(c, dev, "/")
                break


@app.route("/api/user/wifi", methods=["POST"])
def wifi_connect() -> Response:
    utils.backend_logger(f'{request.endpoint} : {request.method} : {request.data} : {request.args} : {request.form} : {request.remote_addr}')
    utils.backend_logger(f'REQUEST HEADERS = {dict(request.headers)}')
    utils.backend_logger(f'BROWSER = {request.user_agent.platform}, {request.user_agent.browser}, {request.user_agent.version}')
    network_ready = False
    if config.enabled_wifi:
        ssid = request.form["ssid"]
        password = request.form["password"]

        try:
            connect_to_wifi(ssid, password)
            return Response("ok", 200)
        except Exception as e:
            network_ready = False
            utils.backend_logger(f'Tried connecting with {ssid}, {password}')
            utils.backend_logger(f'{str(e)}')
        else:
            network_ready = True

        if network_ready:
            return Response("ok", 200)
        else:
            return Response("Unable to connect to network", 422)

    return Response("ok", 200)

#def read_analysis(filename: str) -> Dict[str, float]:  ## NMR XX
def read_analysis(filename: str):   ## NMR XX FIX THIS
    with open(filename, 'r') as datafile:
        lines = datafile.readlines()
    values = {}

    for s in lines:
        s_list = s.split(":")
        element = s_list[0]
        value_str = s_list[1].strip("\n")
        if element in ['N1', 'N2', 'K', 'P']:
            value = float(value_str.replace(" ", ""))
            value = round(value, 1)
            values[element] = value
        else:
            values[element] = value_str.replace(" ", "")   ## NMR CHECK why we need this

    return values

def read_barcode(barcode_filename: str) -> str:
    with open(barcode_filename, 'r') as datafile:
        #return int(datafile.read())
        return datafile.read().strip('\n')

def read_device_name(device_filename: str) -> str:
    with open(device_filename, 'r') as datafile:
        #return int(datafile.read())
        return datafile.read().strip('\n')

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path: str) -> Response:
    #### Initialize system
    # if os.path.isfile(user_options_file):
    #     print(f'*****REMOVING USER_OPTIONS_FILE 3*******')
    #     os.remove(user_options_file)
    if(path == ""):
        return send_from_directory('react', 'index.html')
    else:
        if(os.path.exists("react/" + path)):
            return send_from_directory('react', path)
        else:
            return send_from_directory('react', 'index.html')


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
