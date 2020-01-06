#!/usr/bin/python
__author__ = 'zJx'


"""
hamming_loss
"""


def evaluate(testable, pretable):
    miss_pairs = 0
    for i, j in zip(testable, pretable):
        if i != j:
            miss_pairs += 1
    return miss_pairs / len(testable)

if __name__ == "__main__":
    a = [1, 2, 3, 4]
    b = [2, 2, 3, 4]
    print(evaluate(a, b))

