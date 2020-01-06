#!/usr/bin/python

__author__ = 'zJx'

"""
关联度检验
"""


def evaluate(testtmp, pretmp):
    # 关联度检验大于60%即符合要求
    # 分辨率0<p<1,一般取0.5
    P = 0.5
    testtmp = testtmp.copy()
    for i in range(len(testtmp)):
        testtmp[i] = abs(testtmp[i] - pretmp[i])

    r = 0
    for i in testtmp:
        r += (min(testtmp) + max(testtmp) * P) / (i + max(testtmp) * P)

    r = (r / len(testtmp))

    if r > 0.6:
        r_identify = '关联度检验符合要求'
    else:
        r_identify = '关联度检验符合不要求'
    return r,r_identify


if __name__ == "__main__":
    test = [511.625534, 523.535416, 535.722543, 548.193369]
    pred = [477.0, 504.0, 534.0, 549.0]
    print(evaluate(test, pred))
