# -*- coding: utf-8 -*-
"""Configuration parts needed by the GUI."""

__copyright__ = "Copyright (C) 2020 Nordetect"

# We import everything from commonconfig here so we only need to import one
# config file in our other scripts
from commonconfig import *
import os

enabled_wifi = True       # NMR set to True before balena deploy!
"""Flag to be able to disable all wifi."""

devtest = False
"""Flag to activate offline test behaviour"""

upload_image = True
"""Flag to activate upload of analysis images"""

stored_results_dir = "/data/stored_results"  # NMR remove TEMP before balena deploy!
"""Place to store results."""

stored_images_dir = "/data/images"  # NMR remove TEMP before balena deploy!
"""Place to store images."""

base_url = "https://console.nordetect.com"
#base_url = "http://localhost"
"""Server for remote storing of results."""

port = 443
#port = 8000
"""port number on the api server"""

net_timeout = 1
"""timeout in seconds for calls to console API"""

credentials_file = tmp_dir + "/creds.txt"
"""Contains the username and access token to connect with console API"""

accounts_file =  tmp_dir + "/accounts.txt"
"""Contains all the accounts that the currently logged on user has access to"""

active_account_file = tmp_dir + "/active_account.txt"
"""Contains the account that is active at this moment"""

user_options_file =  tmp_dir + "/user_options.txt"
"""Contains the user options"""

device_file = tmp_dir + "/device.txt"
"""Contains the current devices name, set during deployment"""

login_endpoint = "/api/token/"
"""api server: get JWT authentication access token"""

refresh_endpoint = "/api/token/refresh/"
"""api server: JWT authentication refresh token"""

user_endpoint = "/api/auth/user/"
"""api server: get current user"""

account_endpoint = "/api/accounts/?display=min"
"""api server: get current users accounts"""

sample_endpoint = "/api/samples/"
"""api server: add new Sample (formerly barcode)"""

spadata_endpoint = "/api/spadata/"
"""api server: add new analysis to SpaData (formerly pidata)"""

newsample_endpoint = "/api/spadata/?new_sample=true"
"""api server: add new SpaData and Sample together"""

device_error_endpoint = "/api/deviceerrors/"
"""api server: report errors on this device"""

hello_endpoint = "/api/hello/"
"""api server: say hello"""

spaimage_endpoint = "/api/spaimages/"
"""api server: add new image to spaimage"""
