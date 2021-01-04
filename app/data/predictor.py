"""Predictor module

    This module holds the necessary code to predict new samples in production
"""

import analyseconfig

import numpy as np
import pickle
import os
#from tflite_runtime.interpreter import Interpreter
import polynomial

class Predictor:
    """Predictor class.

    This class loads the train model, and is meant to provide an easy way to
    use the make predictions.

    Example:
        $ predictor = Predictor()

        $ result = predictor(sample_data,color)
    """

    def __init__(self):
        '''Class init function.

        Loads a classifier for yellow,pink and blue color detection.
        Defines a three neural networks (yellow,pink,blue), and loads the trained wheights.
        '''

        self.models = {'nitrate': None,
                       'phosphate': None}

        nitrate_model_path = os.path.join(analyseconfig.app_dir, 'models/nitrate')
        phosphate_model_path = os.path.join(analyseconfig.app_dir, 'models/phosphate')

        nitrate_model_path = os.path.join(nitrate_model_path, "nitrate-%s.p" % os.environ["NITRATE_MODEL"])
        model = pickle.load(open(nitrate_model_path, "rb"))
        self.models['nitrate'] = model

        phosphate_model_path = os.path.join(phosphate_model_path, "phosphate-%s.p" % os.environ["PHOSPHATE_MODEL"])
        model = pickle.load(open(phosphate_model_path, "rb"))
        self.models['phosphate'] = model

    def predict(self, intensity, ion):
        '''Predict is the main use of the Predictor class.

        Predict takes an input sample, and calls the model defined by the color parameter.

        args:
            intensity(np.array): A numpy array containing the cutout image of the spot to predict.
            ion(string): What ion to analyse  (nitrate, phosphate)


        returns:
            output(int): Predicted value of the smample.

        '''

        model = self.models[ion]

        output = model.predict(np.array(intensity).reshape(-1, 1))[0]

        return output
