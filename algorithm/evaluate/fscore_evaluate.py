#!/usr/bin/python
"""
fscore_evaluate
"""


def evaluate(testset_tmp, classLabelAll, a=1):
    new_classLabel = list(zip(classLabelAll, testset_tmp))
    new_classLabel = list(filter(lambda x: x[0] != None, new_classLabel))
    # 召回率recall
    recall = len(new_classLabel) / len(classLabelAll)

    right_classLabel = list(filter(lambda x: x[0] == x[1], new_classLabel))
    # 正确率precision
    precision = len(right_classLabel) / len(new_classLabel)

    # F-Measure
    return (precision * recall * (a * a + 1)) / (a * a * (precision + recall))
