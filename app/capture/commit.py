"""Commits the gathered dataset to the server.

This script uploads the pictures, captured with capture.py, to the incoming folder on the
server, creating a subfolder called "<datasetname>_<deviceid>".
This script can be run without elevated privilidges.

Example:
    $ python3 commit.py <datasetname> <deviceid>
"""

import os
import sys


#### Easy changeable settings #####
serverip = "18.195.101.153"
serverip_2 = "3.250.145.40"
incomingpath = "/home/ubuntu/ndt-preprocessing/incoming"


def commit():
    """Commits the gathered dataset to the server.

    The code will verify if a datasetname and device id is provided,
    and ask the user to provide one if they are not found.
    In addition, the script will test if the server already has a folder with the
    intended name, and add a _<int> to the end of the name to prevent loss of data. 

    Arguments:
        datasetname(str): The name of the captured dataset
        deviceid(str): The ID of the device used for capturing
    """
    
   # Path to folder with with raw_images
    folderpath = "raw_images"

    # get a dataset name from commadnlien argument or from user
    try:
        device_id = sys.argv[2]
        datasetname = sys.argv[1] + '_{}'.format(device_id)

        
    except Exception:
        device_id = input("No device id provided, please provide a id to continue:")
        datasetname = input("No dataset name provided, please provide a datasetname to continue:")
        if datasetname == "":
            print("No datasetname provided, exiting script")
            sys.exit(1)
        
        datasetname = datasetname + '_{}'.format(device_id)

    # list exisitng files to prevent overwriting exisitng data
    try:
        existing_files = os.popen('ssh ubuntu@{} ls {}'.format(serverip, incomingpath)).read()
    except Exception:
        print('Failed to establish SSH connection to {}'.format(serverip))
        sys.exit(1)

    # Add some numbers to the datasetname, if it already exists
    if datasetname in existing_files:
        originalName = datasetname
        i = 1
        while datasetname in existing_files:
            datasetname = originalName + '_{}'.format(i)
            i = i+1
            
        print("A dataset with name {} already exists. Renaming to {}".format(originalName,datasetname))

    # Upload the data
    print('Uploading data to: ubuntu@{}:{}/{}'.format(serverip, incomingpath, datasetname))
    try:
        os.system('scp -r {} ubuntu@{}:{}/{}'.format(folderpath, serverip, incomingpath, datasetname))
        print('Data successfully uploaded')
    except Exception:
        print('Failed to copy files to {}'.format(serverip))
        sys.exit(1)

    # copy to second server incoming folder
    print('Uploading data from ubuntu@{}:{}/{} to: ubuntu@{}:{}/{}'.format(serverip, incomingpath, datasetname, serverip_2, incomingpath, datasetname))
    try:
        scp = 'scp -r -i "~/.ssh/aws.pem" {}/{} ubuntu@{}:{}/{}'.format(incomingpath, datasetname, serverip_2, incomingpath, datasetname)
        os.system('ssh -t ubuntu@{} {}'.format(serverip, scp))
        print('Data successfully uploaded')
    except Exception:
        print('Failed to copy files from {} to {}'.format(serverip, serverip_2))
        sys.exit(1)

if __name__ == '__main__':
    commit()
