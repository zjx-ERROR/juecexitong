#!/usr/bin/python
"""
accuracy_evaluate
"""


def evaluate(testset_tmp, classLabelAll):
    new_classLabel = list(zip(classLabelAll, testset_tmp))
    new_classLabel = list(filter(lambda x: x[0] != None, new_classLabel))
    right_classLabel = list(filter(lambda x: x[0] == x[1], new_classLabel))
    # 正确率accuracy
    return len(right_classLabel) / len(new_classLabel)
