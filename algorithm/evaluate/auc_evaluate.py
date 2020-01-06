#!/usr/bin/python
from sklearn.metrics import roc_curve
from sklearn.metrics import auc
import numpy as np

"""
auc_evaluate
"""


def evaluate(label, pre_label):
    fpr, tpr, threshoulds = roc_curve(label, pre_label, pos_label=2)
    # auc
    return auc(fpr, tpr)
