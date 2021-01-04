#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Code to do the preprocessing and predictions of a sample image."""

__copyright__ = "Copyright (C) 2020 Nordetect"

import analyseconfig

import sys
from subprocess import run, PIPE
import os.path
#import numpy as np
#from PIL import Image
#import pandas as pd
from typing import Optional, List

from predictor import Predictor
from utils import create_default_results, Results


def cut(filepath: str) -> None:
    # Process files in folder
    print("Running newdetect.py in subprocess")
    # Until newdetect get fixed, we need to run it from the dir it is in.
    newdetect_path = os.path.join(analyseconfig.app_dir, 'newdetect')
    res = run(["python3", 'newdetect.py', 'training', filepath],
              cwd=newdetect_path, stdout=PIPE, stderr=PIPE)
    if res.stdout:
        print(res.stdout.decode("utf-8", "replace"))
    if res.stderr:
        print(res.stderr.decode("utf-8", "replace"), file=sys.stderr)
    res.check_returncode()


def predict_sample(resultdir: str, imagename: str, spots: List[int], results: Optional[Results] = None) -> Results:
    # Post process the images for use by the prediction algorithm
    print("Pre-process image")
    cut(os.path.join(resultdir, imagename))

    # find images
    path = os.path.join(resultdir, "training_results")
    files = os.listdir(path)
    suffix = 'csv'
    files = [filename for filename in files if filename.endswith(suffix)]

    # make predictions
    predictor = Predictor()

    if results is None:
        results = create_default_results()

    csv_path = os.path.join(path, files[0])
    intensities = []
    with open(csv_path, 'r') as infile:
        lines = infile.readlines()
    for line in lines:
        name, intensitystr = line.strip().split(',')
        intensities.append(float(intensitystr))

    error = None
    for spot in spots:
        try:
            spotindex = spot-1
            intensity = intensities[spotindex]

            realname = analyseconfig.spot_gui_names[spotindex]
            color = analyseconfig.spot_model_names[spotindex]
            if not analyseconfig.spot_active[spotindex]:
                # Just write 0 for uknown values
                print('Not using spot {0} at the moment'.format(spot))
                prediction = 0
            else:
                print(color)
                print('Predicting spot {0}, {1}'.format(str(spot), color))
                prediction = predictor.predict(intensity, color)

            print("Prediction: {0}".format(prediction))
            results[realname] = prediction
            #out.write("{}: {:.2f}\n".format(realname, prediction))
            '''
            img_name = [filename for filename in files if filename.endswith('{}.png'.format(spot))][0]
            img_path = os.path.join(path, img_name)
            image = np.array(Image.open(img_path))

            color = analyseconfig.spot_model_names[spotindex]
            realname = analyseconfig.spot_gui_names[spotindex]

            print('Predicting spot {}'.format(str(spot)))
            prediction = predictor.predict(image, color)


            print("Prediction: {}".format(prediction))
            out.write("{}: {:.2f}\n".format(realname, prediction))
            '''
        except Exception as e:
            if not error:
                error = e
    if error:
        raise error

    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 predictNewSample <sample dir> <sample file> <spot>",  file=sys.stderr)
        sys.exit(1)
    results = predict_sample(sys.argv[1],  sys.argv[2],  [int(sys.argv[3])])
    print(results)
