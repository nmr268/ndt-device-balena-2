
__copyright__ = "Copyright (C) 2020 Nordetect"

import requests
import json
import config
import os
from typing import Any, Dict, Tuple
from time import process_time
import utils


def get_headers() -> Dict[str, str]:
    creds_s = utils.get_file_data(config.credentials_file)
    creds_data = json.loads(creds_s)
    token = creds_data.get("token", None)
    headers = {
        'content-type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    return headers

def get_auth_headers() -> Dict[str, str]:
    creds_s = utils.get_file_data(config.credentials_file)
    creds_data = json.loads(creds_s)
    token = creds_data.get("token", None)
    headers = {
        'Authorization': f'Bearer {token}',
    }
    return headers

def find_sample(data: Any) -> Tuple[str, int]:

    sample_endpoint = f'{config.base_url}:{config.port}{config.sample_endpoint}'

    headers=get_headers()
    use_barcode = data["use_barcode"]

    if use_barcode:
        params = {
                'account_id': f'{data["account"]}',
                'barcode': f'{data["barcode"]}',
        }
    else:
        params = {
                'account_id': f'{data["account"]}',
                'sample_id': f'{data["sample_id"]}',
        }

    try:
        raw_response = requests.get(sample_endpoint, params=params, headers=headers, timeout=config.net_timeout)
    except Exception as e:
        utils.backend_logger(f'Error finding sample: {str(e)}')
        return f'There is a problem connecting with Nordetect server', 500
    return raw_response.text, raw_response.status_code

def create_sample(sample_data: Any) -> Tuple[str, int]:

    sample_endpoint = f'{config.base_url}:{config.port}{config.sample_endpoint}'

    headers=get_headers()
    # user_options = json.loads(utils.get_file_data(config.user_options_file))
    # use_barcode = user_options["use_barcode"]

    try:
        raw_response = requests.post(sample_endpoint, data=json.dumps(sample_data), headers=headers, timeout=config.net_timeout)
    except Exception as e:
        utils.backend_logger(f'Error creating sample: {str(e)}')
        return f'There is a problem connecting with Nordetect server', 500
    return raw_response.text, raw_response.status_code

def create_spadata(data: Any) -> Tuple[str, int]:

    spadata_endpoint = f'{config.base_url}:{config.port}{config.spadata_endpoint}'
    headers=get_headers()

    try:
        raw_response = requests.post(spadata_endpoint, data=json.dumps(data), headers=headers, timeout=config.net_timeout)
    except Exception as e:
        utils.backend_logger(f'create spadata error: {str(e)}')
        return f'There is a problem connecting with Nordetect server', 500

    return raw_response.text, raw_response.status_code

def create_spaimage(data: Any, file: str) -> Tuple[str, int]:

    spaimage_endpoint = f'{config.base_url}:{config.port}{config.spaimage_endpoint}'
    headers=get_auth_headers()

    try:
        files = {
            'image': (file, open(file, 'rb'), 'application/octet-stream'),
        }
    except FileNotFoundError as e:
        utils.backend_logger(f'{data.get("sample")} , {file}  not found')
        files = None

    try:
        raw_response = requests.post(spaimage_endpoint, data=data, files=files, headers=headers, timeout=config.net_timeout)
    except Exception as e:
        utils.backend_logger(f'{str(e)}')
        return f'There is a problem connecting with Nordetect server', 500

    return raw_response.text, raw_response.status_code



def login(login_data: Dict[str,  str]) -> Tuple[str, int]:

    endpoint = f'{config.base_url}:{config.port}{config.login_endpoint}'

    headers = {'content-type': 'application/json'}

    try:
        raw_response = requests.post(
                endpoint,
                headers=headers,
                data=json.dumps(login_data),
                timeout=config.net_timeout
        )
        return raw_response.text, raw_response.status_code
    except Exception as e:
        utils.backend_logger(f'login error: {str(e)}')
    return f'There is a problem connecting with Nordetect server', 500

def user_accounts(creds_data: Dict[str,  str]) -> Tuple[str, int]:

    endpoint = f'{config.base_url}:{config.port}{config.account_endpoint}'

    token = creds_data["token"]
    headers = {
        'content-type': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    try:
        raw_response = requests.get(endpoint, headers=headers, timeout=config.net_timeout)
        return raw_response.text, raw_response.status_code
    except Exception as e:
        utils.backend_logger(f'user accounts error: {str(e)}')   ## NMR TODO  see if we can refine this error
        return f'There is a problem connecting with Nordetect server', 500

def hello() -> Tuple[str, int]:

    endpoint = f'{config.base_url}:{config.port}{config.hello_endpoint}'

    headers = {
        'content-type': 'application/json',
    }

    try:
        #tstart = process_time()
        raw_response = requests.get(endpoint, headers=headers, timeout=config.net_timeout)
        #tend = process_time()
        #print (f'hello {tend - tstart}')
        return raw_response.text, raw_response.status_code
    except Exception as e:
        #utils.backend_logger(f'hello error: {str(e)}')   ## NMR TODO  see if we can refine this error
        return f'There is a problem connecting with Nordetect server', 500

def upload_error(data: Dict[str,  str]) -> Tuple[str, int]:

    headers=get_headers()
    endpoint = f'{config.base_url}:{config.port}{config.device_error_endpoint}'

    try:
        raw_response = requests.post(
                endpoint,
                headers=headers,
                data=json.dumps(data),
                timeout=config.net_timeout
                )
        return raw_response.text, raw_response.status_code
    except Exception as e:
        #utils.backend_logger(f'upload error: {str(e)}')   ## NMR TODO  see if we can refine this error
        return f'There is a problem connecting with Nordetect server', 500
