import numpy as np


class Polynomial:
    def __init__(self, order=2):
        self.order = order
        self.coef = np.ndarray(order)

    def fit(self, x, y):
        self.coef = np.polyfit(x, y, self.order)
        return self

    def predict(self, x):
        return np.polyval(self.coef, np.squeeze(x, axis=-1))
