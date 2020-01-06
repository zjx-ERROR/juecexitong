#!/usr/bin/python
__author__ = 'zJx'

from sklearn.metrics import jaccard_similarity_score

"""
jacard_evaluate
"""


def evaluate(testable, pretable):
    return jaccard_similarity_score(testable, pretable)


if __name__ == "__main__":
    a = [1,2,3,4]
    b = [2,2,3,4]
    print(evaluate(a,b))