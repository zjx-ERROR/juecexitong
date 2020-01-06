#!/usr/bin/python
import random
"""
recall_evaluate
"""
def evaluate(testset_tmp, classLabelAll):
    pos = random.choice(testset_tmp)

    classLabel = list(zip(classLabelAll, testset_tmp))
    classLabel = list(filter(lambda x: x[1] == pos, classLabel))

    new_classLabel = list(filter(lambda x: x[0] == x[1], classLabel))

    # 召回率recall
    return len(new_classLabel) / len(classLabel)
